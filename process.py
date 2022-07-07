from operator import itemgetter
import random


class Process(object):
    def __init__(self, simulation):
        """
        the process with discrete capacity sources
        :param simulation: simulation object
        """
        self.sim = simulation
        self.index_sorting_removal = 0
        self.index_order_object = 1
        self.index_priority = 2
        self.dispatching_rule = self.sim.policy_panel.dispatching_rule
        self.random_generator = random.Random()
        self.random_generator.seed(999999)

        self.work_centre_occupied = {}
        for line in self.sim.model_panel.LINE_STRUCTURE.keys():
            self.work_centre_occupied[line] = {}
            for work_centre in self.sim.model_panel.MANUFACTURING_FLOOR_LAYOUT[line]:
                self.work_centre_occupied[line][work_centre] = False
        return

    def put_in_queue(self, order):
        """
        controls if an order can immediately be send to a capacity source or needs to be put in the queue.
        :param order: order object
        :return:
        """
        if order.first_entry:
            # first time entering the floor
            order.release_time = self.sim.env.now
            order.pool_time = order.release_time - order.entry_time
            order.first_entry = False

        # get work centre
        line = order.line
        work_centre = order.routing_sequence[0]
        order.queue_entry_time[work_centre] = self.sim.env.now

        # control if dispatching is needed
        queue_item = self.queue_item(order=order, work_centre=work_centre, line=line)
        self.sim.model_panel.QUEUES[line][work_centre].put(queue_item)
        if not self.work_centre_occupied[line][work_centre]:
        # if len(self.sim.model_panel.WORK_CENTRES[line][work_centre].users) == 0:
            self.dispatch_order(line=line, work_centre=work_centre)
            return  # order dispatched, return to avoid duplication
        return

    def starvation_dispatch(self, line):
        for work_centre in self.sim.model_panel.WORK_CENTRES[line].keys():
            if len(self.sim.model_panel.WORK_CENTRES[line][work_centre].users) == 0:
                self.dispatch_order(line=line, work_centre=work_centre)
        return

    def release_from_queue(self, work_center, line):
        """
        removes an order from the queue
        :param work_center: work_center number indicating the number of the capacity source
        :return: void
        """
        # sort the queue
        self.sim.model_panel.QUEUES[line][work_center].items.sort(key=itemgetter(self.index_sorting_removal))
        self.sim.model_panel.QUEUES[line][work_center].get()
        return

    def update_priority(self, order, line, work_centre):
        # select using priority rule
        if self.dispatching_rule[line] == "FCFS":
            order.dispatching_priority[work_centre] = self.sim.env.now
        elif self.dispatching_rule[line] == "SLACK":
            order.dispatching_priority[work_centre] = order.due_date - self.sim.env.now - order.remaining_process_time
        elif self.dispatching_rule[line] == "INVENTORY":
            order.dispatching_priority[work_centre] = self.sim.inventory.inventory_priority(item=order.item_name)
        else:
            raise Exception("no valid priority rule defined")
        return

    def queue_item(self, order, work_centre, line):
        """
        make a list of attributes that needs ot be put into the queue
        :param order: order object
        :param work_centre: the work center name
        :return:queue_item

        Key for the queue_item list
        0: order object
        1: dispatching priority
        2: next step
        3: release index
        """
        # set priority
        self.update_priority(order=order, line=line, work_centre=work_centre)
        # get queue list and return
        return self.get_queue_item(order=order, work_centre=work_centre)

    @ staticmethod
    def get_queue_item(order, work_centre):
        queue_item = [1,  # removal integer
                      order,  # order object
                      order.dispatching_priority[work_centre],  # order priority
                      order.routing_sequence[0]  # next operation
                      ]
        return queue_item

    def dispatch_order(self, line, work_centre):
        """
        Dispatch the order with the highest priority to the capacity source
        :param work_centre: work_center number indicating the number of the capacity source
        :param line: the name of the production line
        :return:
        """
        # get new order for release
        order_list, break_loop = self.get_most_urgent_order(line=line, work_centre=work_centre)

        # no orders in queue
        if break_loop:
            return

        # get the order object
        order = order_list[self.index_order_object]

        self.release_from_queue(work_center=order.routing_sequence[0], line=line)
        # set params and start process
        self.work_centre_occupied[line][work_centre] = True
        order.process = self.sim.env.process(
            self.sim.process.capacity_process(order=order, line=line, work_centre=order.routing_sequence[0]))
        return

    def get_most_urgent_order(self, line, work_centre):
        """
        Update all priorities and routing steps in the queue
        :param work_centre: work_center number indicating the number of the capacity source
        :param machine: the name of the machine
        :return: order, boolean: break_loop, boolean: free_load
        """
        # setup params
        dispatching_list = list()

        # if there are no items in the queue, return
        if len(self.sim.model_panel.QUEUES[line][work_centre].items) == 0:
            return None, True

        # get the list of queueing items
        queue_list = self.sim.model_panel.QUEUES[line][work_centre].items
        # find order with highest impact or priority
        for i, order_list in enumerate(queue_list):
            # update priority
            order = order_list[self.index_order_object]
            self.update_priority(order=order, line=line, work_centre=work_centre)
            # add to queue
            dispatching_list.append(order_list)

        # select order with highest impact or priority, find the correct priority
        order_item = sorted(dispatching_list, key=itemgetter(self.index_priority))[0]  # sort and pick with highest priority

        # set to zero to pull out of pull
        order_item[self.index_sorting_removal] = 0
        return order_item, False

    def capacity_process(self, order, line, work_centre):
        """
        The process with capacity sources
        :param order: order object
        :param work_centre: work_center number indicating the number of the capacity source
        :param machine: the name of the machine
        :return: void
        """
        self.sim.data.order_input_counter[line] += 1
        # set params
        order.work_center_RQ = self.sim.model_panel.WORK_CENTRES[line][work_centre]
        req = order.work_center_RQ.request(priority=order.dispatching_priority[work_centre])
        req.self = order
        order.order_start_time[work_centre] = self.sim.env.now

        # start processing, update order state
        order.wc_state[work_centre] = "IN_PROCESS"
        # yield a request
        with req as req:
            yield req
            # Request is finished, order directly processed
            yield self.sim.env.timeout(order.process_time[work_centre])
            # order is finished and released from the machine
            self.work_centre_occupied[line][work_centre] = False

        # update order state
        order.wc_state[work_centre] = "PASSED"

        # update the routing list to avoid re-entrance
        order.routing_sequence.remove(work_centre)

        # collect data
        self.data_collection_intermediate(order=order, work_center=work_centre)

        # next action for the order
        if len(order.routing_sequence) == 0:
            # order completed, collect data, the completion time
            order.completion_time = self.sim.env.now
            # general data collection
            self.sim.data.order_output_counter[line] += 1
            self.sim.data.accumulated_process_time[line] += order.process_time_cumulative

            if order.enter_inventory:
                # put in inventory
                self.sim.inventory.put_in_inventory(order=order)
            else:
                order.inventory_departure_time = self.sim.env.now
                self.data_collection_final(order=order, line=line)

            # stimulate release upstream
            self.sim.release.update_release(line=line,
                                            order=order,
                                            work_centre=work_centre,
                                            completed=True)
        else:
            # activate new release
            self.put_in_queue(order=order)
            self.sim.release.update_release(line=line,
                                            order=order,
                                            work_centre=work_centre,
                                            completed=False)
        # next action for the work centre
        self.dispatch_order(line=line, work_centre=work_centre)
        return

    def data_collection_intermediate(self, order, work_center):
        """
        Collect data between routing steps
        :param order: order object
        :param work_center: work_center number indicating the number of the capacity source
        :return: void
        """
        order.remaining_process_time -= order.process_time[work_center]
        order.proc_finished_time[work_center] = self.sim.env.now
        order.queue_time[work_center] = order.order_start_time[work_center] - order.queue_entry_time[work_center]
        return

    def data_collection_final(self, order, line):
        """
        Collect data finished order
        :param order: order object
        :return: void
        
        key list
            0: line
            1: identifier
            2: product_name
            3: throughput_time
            4: material_waiting_time
            5: shop_throughput_time
            6: lateness
            7: tardiness
            8: tardy
        """
        # setup list
        df_list = list()
        df_list.append(line)
        df_list.append(order.identifier)
        df_list.append(order.item_name)
        df_list.append(order.completion_time - order.entry_time)
        df_list.append(order.inventory_departure_time - order.completion_time)
        df_list.append(order.material_available_time - order.entry_time)
        df_list.append(order.completion_time - order.release_time)
        df_list.append(order.completion_time - order.due_date)
        df_list.append(max(0, (order.completion_time - order.due_date)))
        df_list.append(max(0, self.heavenside(x=(order.completion_time - order.due_date))))

        # save list
        self.sim.data.append_run_list(result_list=df_list)
        return

    @staticmethod
    def heavenside(x):
        if x > 0:
            return 1
        return -1
