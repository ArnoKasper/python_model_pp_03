from operator import itemgetter


class Release(object):
    def __init__(self, simulation):
        """
        the process with discrete capacity sources
        :param simulation: simulation object
        """
        self.sim = simulation
        self.index_sorting_removal = 0
        self.index_order_object = 1
        self.index_priority = 2

        self.periodic_processes = {}
        self.activate_continuous_trigger = {}
        self.activate_continuous_release = {}
        self.activate_periodic_release = {}
        self.measure = {}
        self.tracking_variable = {}

        # initialize release
        self.initialize_release()
        return

    def initialize_release(self):
        for line, attributes in self.sim.model_panel.LINE_STRUCTURE.items():
            self.tracking_variable[line] = self.sim.policy_panel.release_technique_attributes[line]['tracking_variable']
            # check if release tracking variable is work centre specific
            if self.sim.policy_panel.release_technique_attributes[line]['tracking_variable'] == 'work_centre':
                self.sim.policy_panel.released[line] = {}
                self.sim.policy_panel.completed[line] = {}
                release_target = self.sim.policy_panel.release_target[line]
                self.sim.policy_panel.release_target[line] = {}
                # add new tracking variable for
                for work_centre in self.sim.model_panel.WORK_CENTRES[line].keys():
                    self.sim.policy_panel.released[line][work_centre] = 0
                    self.sim.policy_panel.completed[line][work_centre] = 0
                    self.sim.policy_panel.release_target[line][work_centre] = release_target
            # check if periodic release must be activated
            if self.sim.policy_panel.release_technique_attributes[line]['periodic']:
                self.activate_periodic_release[line] = True
                # start process
                self.periodic_processes[line] = self.sim.env.process(self.periodic_release(line=line))

            # activate or deactivate continuous trigger
            self.activate_continuous_trigger[line] = self.sim.policy_panel.release_technique_attributes[line]['trigger']
            self.activate_continuous_release[line] = self.sim.policy_panel.release_technique_attributes[line]['continuous']
            # set measurement for release
            self.measure[line] = self.sim.policy_panel.release_technique_attributes[line]['measure']
        return

    def put_in_pool(self, order, line):
        # update order priority
        self.set_pool_priority(order=order, line=line)
        # put order in pool
        pool_item = self.pool_item(order=order, line=line)
        self.sim.model_panel.POOLS[line].put(pool_item)
        # activate release mechanism
        self.activate_release(line=line, order=order)
        return

    def activate_release(self, line, work_centre=None, order=None):
        # control for release
        if self.activate_continuous_release[line]:
            self.continuous_release(line=line)
        # activate continuous trigger mechanisms
        if self.activate_continuous_trigger[line]:
            if order is not None:
                work_centre = order.routing_sequence[0]
                self.continuous_trigger_activation(line=line, work_centre=work_centre)
            elif work_centre is not None:
                self.sim.release.continuous_trigger_activation(line=line, work_centre=work_centre)
            else:
                starving_work_centres = self.collect_starving_work_centres_work_centres(line)
                for starving_work_centres in self.sim.model_panel.WORK_CENTRES[line]:
                    self.continuous_trigger(line=line,  work_centre=work_centre)
        return

    def set_pool_priority(self, order, line):
        if self.sim.policy_panel.sequencing_rule[line] == "FCFS":
            order.pool_priority = order.identifier
        elif self.sim.policy_panel.sequencing_rule[line] == "SPT":
            order.pool_priority = list(order.process_time.values())[0]
        elif self.sim.policy_panel.sequencing_rule[line] in ["PRD", "MODCS"]:
            order.pool_priority = order.pool_priority
        elif self.sim.policy_panel.sequencing_rule[line] == "EDD":
            order.pool_priority = order.due_date
        elif self.sim.policy_panel.sequencing_rule[line] == "SLACK":
            order.pool_priority = order.due_date - self.sim.env.now - order.remaining_process_time
        elif self.sim.policy_panel.sequencing_rule[line] == "INVENTORY":
            order.pool_priority = self.sim.inventory.inventory_priority(item=order.item_name)
        else:
            raise Exception('no valid pool sequencing rule selected')

        # update priorities if needed
        if self.sim.policy_panel.material_allocation[line] == 'loose_coupling':
            order.coupling_priority = order.pool_priority
            order.pool_priority = self.sim.dynamic_coupling.pool_priority(order=order)
        return

    @staticmethod
    def pool_item(order, line):
        pool_item = [1,  # removal integer
                     order,
                     order.pool_priority,
                     line,
                     order.item_name]
        return pool_item

    def release_from_pool(self, line, release_now):
        """
        removes an order from the queue
        :param work_center: work_center number indicating the number of the capacity source
        :return: void
        """
        release_now[self.index_sorting_removal] = 0
        # sort the queue
        self.sim.model_panel.POOLS[line].items.sort(key=itemgetter(self.index_sorting_removal))
        self.sim.model_panel.POOLS[line].get()
        return

    def get_release_list(self, line):
        """
        find which orders have can be made as material is available, and turn the pool
        """
        # setup params
        release_list = list()
        # if there are no items in the pool, return
        if len(self.sim.model_panel.POOLS[line].items) == 0:
            return None, True
        # get the items that for which there are materials available
        pool_list = self.sim.model_panel.POOLS[line].items
        for pool_item in pool_list:
            order = pool_item[self.index_order_object]
            # update priorities
            self.set_pool_priority(order=order, line=line)
            # check materials
            if self.sim.inventory.material_availability_check(order=order, line=line):
                # allow release
                release_list.append(pool_item)
        # if there are no items ready in the pool
        if len(release_list) == 0:
            return None, True
        else:
            return release_list, False

    def dedicate_materials_to_orders(self, order):
        """
        dedicate materials to the an order
        """
        # material requirements satisfied, remove materials from inventory
        material_list = self.sim.inventory.collect_materials(requirements=order.requirements)
        # add materials to the order
        order.materials.extend(material_list)
        return

    def control_measure(self, order, line, work_centre=None):
        """
        function that contributes the correct load measure
        """
        if self.measure[line] == "WIP":
            return 1
        elif self.measure[line] == "workload" and work_centre is None:
            return sum(order.process_time.values())
        elif self.measure[line] == "workload" and work_centre is not None:
            return order.process_time[work_centre] / (order.routing_sequence_data.index(work_centre) + 1)
        else:
            raise Exception('failed review the correct tracking measure for release')

    def release_review(self, order, line):
        """
        function that reviews if an order can be released
        """
        release = True
        if self.tracking_variable[line] == 'total':
            released = self.sim.policy_panel.released[line] + self.control_measure(order=order, line=line)
            completed = self.sim.policy_panel.completed[line]
            check = released - completed
            if check < 0:
                raise Exception('more orders completed than released')
            # compare against target
            if released - completed > self.sim.policy_panel.release_target[line]:
                release = False
                return release
        elif self.tracking_variable[line] == 'work_centre':
            released = self.sim.policy_panel.released[line].copy()
            completed = self.sim.policy_panel.completed[line].copy()
            for work_centre in order.routing_sequence:
                # contribute
                released[work_centre] += self.control_measure(order=order, work_centre=work_centre, line=line)
                # compare against target
                if released[work_centre] - completed[work_centre] > \
                        self.sim.policy_panel.release_target[line][work_centre]:
                    release = False
                    return release
        else:
            raise Exception('failed review the correct tracking variable for release')
        return release

    def starvation_release_review(self, order, work_centre):
        if order.routing_sequence[0] == work_centre:
            return True
        else:
            return False

    def contribute_release(self, order, line):
        """
        contribute order or load depending on the tracking viable
        """
        if self.tracking_variable[line] == 'total':
            # contribute
            self.sim.policy_panel.released[line] += self.control_measure(order=order, line=line)
        elif self.tracking_variable[line] == 'work_centre':
            for work_centre in order.routing_sequence:
                # contribute following aggregate load method Oosterman et al., 2000
                self.sim.policy_panel.released[line][work_centre] += self.control_measure(order=order,
                                                                                          work_centre=work_centre,
                                                                                          line=line)
        elif self.tracking_variable[line] == 'none':
            self.sim.policy_panel.released[line] += 1
        else:
            raise Exception('failed review the correct tracking variable for release')
        return

    def contribute_completed(self, order, line, work_centre=None):
        """
        contribute order or load depending on the tracking viable
        """
        if self.tracking_variable[line] == 'total':
            # contribute
            self.sim.policy_panel.completed[line] += self.control_measure(order=order, line=line)
        elif self.tracking_variable[line] == 'work_centre':
            # contribute following aggregate load method Oosterman et al., 2000
            self.sim.policy_panel.completed[line][work_centre] += self.control_measure(order=order,
                                                                                       work_centre=work_centre,
                                                                                       line=line)
        elif self.tracking_variable[line] == 'none':
            self.sim.policy_panel.completed[line] += 1
        else:
            raise Exception('failed review the correct tracking variable for release')
        return

    def release(self, line, review_condition="target", attr=None):
        # sequence the orders currently in the pool
        self.sim.model_panel.POOLS[line].items.sort(key=itemgetter(self.index_priority))
        # get valid pool items
        pool_list, break_loop = self.get_release_list(line=line)
        # indicate release
        next_release = False
        # orders in pool
        if not break_loop:
            # contribute the load from each item in the pool
            for i, order_list in enumerate(pool_list):
                order = order_list[self.index_order_object]
                # review
                if review_condition == 'target':
                    order.release = self.release_review(order=order, line=line)
                elif review_condition == 'immediate':
                    order.release = True
                elif review_condition == 'starvation':
                    order.release = self.starvation_release_review(order=order, work_centre=attr['work_centre'])
                else:
                    raise Exception(f'{review_condition} is an invalid review condition')
                # release if allowed
                if order.release:
                    # contribute load but do not track for immediate release
                    self.contribute_release(order=order, line=line)
                    # allocate materials to orders
                    self.dedicate_materials_to_orders(order=order)
                    # remove order from pool
                    self.release_from_pool(line=line, release_now=order_list)
                    # the orders are send to the process, but dispatch after release period
                    self.sim.process.put_in_queue(order=order)
                    """
                    indicate if an additional release is possible. 
                    so, there might be new options, but first the materials need to be updated
                    """
                    # indicate if an additional release is possible
                    next_release = True
                    if review_condition == 'starvation':
                        next_release = False
                    return break_loop, next_release
            # no nex release possible as all orders in the pool cannot be released
            return break_loop, next_release
        else:
            return break_loop, next_release

    def periodic_release(self, line):
        """
        Workload Control Periodic release using aggregate load. See workings in Land 2004.
        """
        periodic_interval = self.sim.policy_panel.release_technique_attributes[line]['check_period']
        while True:
            # deactivate release period, ensure dispatching
            self.sim.process.starvation_dispatch(line=line)
            yield self.sim.env.timeout(periodic_interval)
            # set the list of released orders
            while True:
                break_loop, next_release = self.release(line=line)
                # condition 1: no orders in the pool
                if break_loop:
                    break
                # condition 2: still orders in the pool but no next release possible
                if not next_release:
                    break

    def continuous_release(self, line):
        """
        Workload Control: continuous release using corrected aggregate load. See workings in Fernandes et al., 2017
        """
        while True:
            if self.sim.policy_panel.release_technique[line] == "immediate":
                break_loop, next_release = self.release(line=line, review_condition='immediate')
            else:
                break_loop, next_release = self.release(line=line)

            # condition 1: no orders in the pool
            if break_loop:
                break
            # condition 2: still orders in the pool but no next release possible
            if not next_release:
                break

    def continuous_trigger(self, work_centre, line):
        """
        Workload Control: continuous release using aggregate load. See workings in Thürer et al, 2014.
        Part of LUMS COR
        """
        # must be adapted so we can get orders in the pool that
        break_loop, next_release = self.release(line=line,
                                                review_condition="starvation",
                                                attr={'work_centre': work_centre})
        return

    def control_queue_empty(self, line, work_centre):
        """
        controls if the queue is empty
        :param: work_center:
        :return: bool
        """
        in_system = len(self.sim.model_panel.QUEUES[line][work_centre].items) + \
                    len(self.sim.model_panel.WORK_CENTRES[line][work_centre].users)
        return in_system <= 0

    def continuous_trigger_activation(self, work_centre, line):
        """
        feedback mechanism for continuous release
        :param work_centre:
        """
        # control the if the the amount of orders in or before the work centre is equal or less than one
        if self.control_queue_empty(work_centre=work_centre, line=line):
            self.continuous_trigger(work_centre=work_centre, line=line)

    def collect_starving_work_centres_work_centres(self, line):
        starving_work_centres = []
        for work_centre in self.sim.model_panel.WORK_CENTRES[line]:
            if self.control_queue_empty(work_centre=work_centre, line=line):
                starving_work_centres.append(work_centre)
        return starving_work_centres

    def update_release(self, line, order, work_centre, completed=False):
        """
        add the processed load and trigger continuous release if required.
        :param order:
        :param work_centre:
        :return:
        """
        # remove load
        if completed and self.tracking_variable[line] == 'total':
            # only update load if order is completed
            self.contribute_completed(line=line, order=order)
        elif self.tracking_variable[line] == 'work_centre':
            # update tracking variable after each operation is completed
            self.contribute_completed(line=line, order=order, work_centre=work_centre)
        # activate release mechanism
        self.activate_release(line=line, work_centre=work_centre)

