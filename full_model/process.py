from operator import itemgetter
import random


class Process(object):
    def __init__(self, simulation):
        """
        the process with discrete capacity sources
        :param simulation: simulation object
        """
        self.sim = simulation
        self.index_sorting_removal = self.sim.model_panel.index_sorting_removal
        self.index_order_object = self.sim.model_panel.index_order_object
        self.index_priority = self.sim.model_panel.index_priority
        self.dispatching_rule = self.sim.policy_panel.dispatching_rule
        self.random_generator = random.Random()
        self.random_generator.seed(999999)

        self.work_centre_occupied = {}
        for work_centre in self.sim.model_panel.MANUFACTURING_FLOOR_LAYOUT:
            self.work_centre_occupied[work_centre] = False
        return

    def put_in_queue(self, order, dispatch=True):
        """
        controls if an order can immediately be send to a capacity source or needs to be put in the queue.
        :param order: order object
        :param dispatch: determine whether to dispatch or not
        :return:
        """
        if order.first_entry:
            # first time entering the floor
            order.release_time = self.sim.env.now
            order.pool_time = order.release_time - order.arrival_time
            order.first_entry = False
            order.release = True
            order.location = "system"
            if self.dispatching_rule == "ODD_land":
                self.sim.general_functions.ODD_land_adaption(order=order)

        # get work centre
        work_centre = order.routing_sequence[0]
        order.queue_entry_time[work_centre] = self.sim.env.now

        # put the order in the queue
        queue_item = self.queue_item(order=order, work_centre=work_centre)
        self.sim.model_panel.QUEUES[work_centre].put(queue_item)

        # control if dispatching is needed
        if len(self.sim.model_panel.WORK_CENTRES[work_centre].users) == 0 and dispatch:
            self.dispatch_order(work_centre=work_centre)
            return  # order dispatched, return to avoid duplication
        return

    def starvation_dispatch(self):
        for work_centre in self.sim.model_panel.WORK_CENTRES.keys():
            if len(self.sim.model_panel.WORK_CENTRES[work_centre].users) == 0:
                pass
                self.dispatch_order(work_centre=work_centre)
        return

    def release_from_queue(self, work_centre):
        """
        removes an order from the queue
        :param work_centre: work_center number indicating the number of the capacity source
        :return: void
        """
        # sort the queue
        self.sim.model_panel.QUEUES[work_centre].items.sort(key=itemgetter(self.index_sorting_removal))
        self.sim.model_panel.QUEUES[work_centre].get()
        return

    def update_priority(self, order, work_centre):
        # select using priority rule
        if self.dispatching_rule == "FCFS":
            order.dispatching_priority[work_centre] = self.sim.env.now
        elif self.dispatching_rule == "FISFO":
            order.dispatching_priority[work_centre] = order.arrival_time
        elif self.dispatching_rule == 'EDD':
            order.dispatching_priority[work_centre] = order.due_date
        elif self.dispatching_rule == "SPT":
            order.dispatching_priority[work_centre] = order.process_time[work_centre]
        elif self.dispatching_rule == "SLACK":
            order.dispatching_priority[work_centre] = order.due_date - self.sim.env.now - order.remaining_process_time
        elif self.dispatching_rule == "ODD_land":
            order.dispatching_priority[work_centre] = order.ODDs[work_centre]
        elif self.dispatching_rule == "FOCUS":
            order.dispatching_priority[work_centre] = 0
        else:
            raise Exception("no valid priority rule defined")
        return

    def queue_item(self, order, work_centre):
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
        if not self.sim.policy_panel.release_technique == "DRACO":
            self.update_priority(order=order, work_centre=work_centre)
        # get queue list and return
        return self.get_queue_item(order=order, work_centre=work_centre)

    @staticmethod
    def get_queue_item(order, work_centre):
        queue_item = [1,  # removal integer
                      order,  # order object
                      order.dispatching_priority[work_centre],  # order priority
                      order.routing_sequence[0]  # next operation
                      ]
        return queue_item

    def dispatch(self, order, work_centre):
        # remove from the queue
        self.release_from_queue(work_centre=work_centre)

        # set params and start process
        self.work_centre_occupied[work_centre] = True
        order.process = self.sim.env.process(
            self.sim.process.capacity_process(order=order, work_centre=order.routing_sequence[0]))
        return

    def dispatch_order(self, work_centre):
        """
        Dispatch the order with the highest priority to the capacity source
        :param work_centre: work_center number indicating the number of the capacity source
        :return:
        """
        # get new order for dispatching
        if self.sim.policy_panel.release_technique == "DRACO":
            order_list, break_loop = self.sim.system_state_dispatching.full_control_mode(work_centre=work_centre,
                                                                                         trigger_mode='dispatching')
        else:
            order_list, break_loop = self.get_most_urgent_order(work_centre=work_centre)

        # no orders in queue
        if break_loop:
            return

        # get the order object
        order = order_list[self.index_order_object]
        # and dispatch
        self.dispatch(order=order, work_centre=work_centre)
        return

    def get_most_urgent_order(self, work_centre):
        """
        Update all priorities and routing steps in the queue
        :param work_centre: work_center number indicating the number of the capacity source
        :param machine: the name of the machine
        :return: order, boolean: break_loop, boolean: free_load
        """
        # if there are no items in the queue, return
        if len(self.sim.model_panel.QUEUES[work_centre].items) == 0:
            return None, True

        # update queue list depending on dispatching mode
        if self.dispatching_rule == "FOCUS":
            queue_list = self.sim.model_panel.QUEUES[work_centre].items
            dispatching_options = self.sim.system_state_dispatching.dispatching_mode(queue_list=queue_list,
                                                                            work_centre=work_centre)
        else:
            # get the list of queueing items
            dispatching_options = self.sim.model_panel.QUEUES[work_centre].items
        # setup params
        dispatching_list = list()
        # find order with highest impact or priority
        for i, order_list in enumerate(dispatching_options):
            # update priority
            order = order_list[self.index_order_object]
            self.update_priority(order=order, work_centre=work_centre)
            # add to queue
            dispatching_list.append(order_list)

        # select order with highest impact or priority, find the correct priority
        order_item = sorted(dispatching_list, key=itemgetter(self.index_priority))[
            0]  # sort and pick with highest priority

        # set to zero to pull out of pull
        order_item[self.index_sorting_removal] = 0
        return order_item, False

    def capacity_process(self, order, work_centre):
        """
        The process with capacity sources
        :param order: order object
        :param work_centre: work_center number indicating the number of the capacity source
        :param machine: the name of the machine
        :return: void
        """
        # set params
        order.work_center_RQ = self.sim.model_panel.WORK_CENTRES[work_centre]
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
            self.work_centre_occupied[work_centre] = False

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
            self.sim.data.order_output_counter += 1
            self.sim.data.accumulated_process_time += order.process_time_cumulative
            self.data_collection_final(order=order)

            # stimulate release upstream
            self.sim.release.update_release(order=order,
                                            work_centre=work_centre,
                                            completed=True)
            # remove the order from the order book, if necessary
            if self.sim.policy_panel.release_technique == "DRACO" or self.dispatching_rule == "FOCUS":
                self.sim.system_state_dispatching.output_order_book(order=order)
        else:
            # activate new release
            self.put_in_queue(order=order)
            self.sim.release.update_release(order=order,
                                            work_centre=work_centre,
                                            completed=False)
        # next action for the work centre
        self.dispatch_order(work_centre=work_centre)
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

    def data_collection_final(self, order):
        """
        Collect data finished order
        :param order: order object
        :return: void
        """
        # update order data
        order.update_material_data()
        # print(order.release_time)
        # setup list
        df_list = list()
        df_list.append(order.identifier)
        df_list.append(order.name)
        df_list.append(order.completion_time - order.arrival_time)
        df_list.append(order.pool_time)
        df_list.append(order.completion_time - order.release_time)
        df_list.append(order.completion_time - order.due_date)
        df_list.append(max(0, (order.completion_time - order.due_date)))
        df_list.append(max(0, self.heavenside(x=(order.completion_time - order.due_date))))
        df_list.append(order.material_available_time - order.arrival_time)
        df_list.append(order.material_replenishment_time)
        df_list.append(order.inventory_time)
        df_list.append(order.material_present)
        df_list.append(len(order.routing_sequence_data))
        df_list.append(len(order.requirements))

        # save list
        self.sim.data.append_run_list(result_list=df_list)
        return

    @staticmethod
    def heavenside(x):
        if x > 0:
            return 1
        return -1
