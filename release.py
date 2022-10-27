from operator import itemgetter


class Release(object):
    def __init__(self, simulation):
        """
        the process with discrete capacity sources
        :param simulation: simulation object
        """
        self.sim = simulation
        self.index_sorting_removal = self.sim.model_panel.index_sorting_removal
        self.index_order_object = self.sim.model_panel.index_order_object
        self.index_priority = self.sim.model_panel.index_priority
        self.index_material_priority = 4

        self.release_technique = self.sim.policy_panel.release_technique

        # release triggered
        self.periodic_processes = False
        self.activate_continuous_trigger = False
        self.activate_continuous_release = False
        self.activate_periodic_release = False
        self.activate_non_hierarchical = False

        # release measurement information
        self.measure = None
        self.tracking_variable = None

        # initialize release
        self.initialize_release()
        return

    def initialize_release(self):
        self.tracking_variable = self.sim.policy_panel.release_technique_attributes['tracking_variable']
        # check if release tracking variable is work centre specific
        if self.tracking_variable == 'work_centre':
            self.sim.policy_panel.released = {}
            self.sim.policy_panel.completed = {}
            release_target = {}
            # add new tracking variable for
            for work_centre in self.sim.model_panel.WORK_CENTRES.keys():
                self.sim.policy_panel.released[work_centre] = 0
                self.sim.policy_panel.completed[work_centre] = 0
                release_target[work_centre] = self.sim.policy_panel.release_target
            self.sim.policy_panel.release_target = release_target
        # check if periodic release must be activated
        if self.sim.policy_panel.release_technique_attributes['periodic']:
            self.activate_periodic_release = True
            # start process
            self.periodic_processes = self.sim.env.process(self.periodic_release())

        # activate or deactivate continuous trigger
        self.activate_continuous_trigger = self.sim.policy_panel.release_technique_attributes['trigger']
        self.activate_continuous_release = self.sim.policy_panel.release_technique_attributes['continuous']
        self.activate_non_hierarchical = self.sim.policy_panel.release_technique_attributes['non_hierarchical']
        # set measurement for release
        self.measure = self.sim.policy_panel.release_technique_attributes['measure']
        return

    def put_in_pool(self, order):
        # update order priority
        self.set_pool_priority(order=order)
        # set rationing rule
        if self.sim.policy_panel.material_allocation == 'rationing':
            self.set_material_priority(order=order)
        # put order in pool
        pool_item = self.pool_item(order=order)
        self.sim.model_panel.POOLS.put(pool_item)
        # activate release mechanism
        if self.sim.policy_panel.release_technique == "DRACO":
            self.sim.system_state_dispatching.full_control_mode(trigger_mode='arrival', order=order)
        else:
            self.activate_release(order=order)
        return

    def activate_release(self, work_centre=None, order=None, material_arrival=False):
        # control for continuous release
        if self.activate_continuous_release:
            self.continuous_release()
        # activate continuous trigger mechanisms
        if self.activate_continuous_trigger:
            if order is not None:
                # new order arrival
                work_centre = order.routing_sequence[0]
                if self.control_queue_empty(work_centre=work_centre):
                    self.continuous_trigger(work_centre=work_centre)
            elif work_centre is not None:
                # operation completed at work centre
                if self.control_queue_empty(work_centre=work_centre):
                    self.continuous_trigger(work_centre=work_centre)
            elif material_arrival and self.sim.model_panel.DELIVERY != "immediate":
                # new material arrival
                for potential_starving_work_centre in self.sim.model_panel.WORK_CENTRES:
                    if self.control_queue_empty(work_centre=potential_starving_work_centre):
                        self.continuous_trigger(work_centre=potential_starving_work_centre)
        return

    def set_material_priority(self, order):
        if self.sim.policy_panel.rationing_rule == "FISFO":
            order.material_priority = order.arrival_time
        elif self.sim.policy_panel.sequencing_rule == "EDD":
            order.material_priority = order.due_date
        elif self.sim.policy_panel.rationing_rule == "Material":
            q = len(order.requirements)
            r = len(order.routing_sequence)
            order.material_priority = order.arrival_time + (q/(q + r)) * (order.due_date - order.arrival_time)
        else:
            raise Exception('no valid rationing rule selected')

    def set_pool_priority(self, order):
        """
         if self.sim.policy_panel.release_technique in ['immediate']:
            order.pool_priority = order.arrival_time
        else:
        """
        if self.sim.policy_panel.sequencing_rule == "FISFO":
            order.pool_priority = order.arrival_time
        elif self.sim.policy_panel.sequencing_rule == "EDD":
            order.pool_priority = order.due_date
        elif self.sim.policy_panel.sequencing_rule == "Capacity":
            order.pool_priority = order.due_date
        else:
            raise Exception('no valid pool sequencing rule selected')
        return

    @staticmethod
    def pool_item(order):
        pool_item = [1,  # removal integer
                     order,
                     order.pool_priority,
                     order.name,
                     order.material_priority]
        return pool_item

    def release_from_pool(self, release_now):
        """
        removes an order from the queue
        :param work_center: work_center number indicating the number of the capacity source
        :return: void
        """
        release_now[self.index_sorting_removal] = 0
        # sort the queue
        self.sim.model_panel.POOLS.items.sort(key=itemgetter(self.index_sorting_removal))
        self.sim.model_panel.POOLS.get()
        return

    def get_release_list(self):
        """
        find which orders have can be made as material is available, and turn the pool
        """
        # update rationing sequence, if applicable
        if self.sim.policy_panel.material_allocation == 'rationing':
            self.sim.inventory.rationing_sequence_update()
        # setup params
        release_list = list()
        # if there are no items in the pool, return
        if len(self.sim.model_panel.POOLS.items) == 0:
            return None, True
        # get the items that for which there are materials available
        pool_list = self.sim.model_panel.POOLS.items
        for pool_item in pool_list:
            order = pool_item[self.index_order_object]
            # update priorities
            self.set_pool_priority(order=order)
            # check materials
            if self.sim.inventory.material_check(order=order):
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

    def control_measure(self, order, work_centre=None):
        """
        function that contributes the correct load measure
        """
        if self.measure == "WIP":
            return 1
        elif self.measure == "workload" and work_centre is None:
            return sum(order.process_time_release.values())
        elif self.measure == "workload" and work_centre is not None:
            return order.process_time_release[work_centre] / (order.routing_sequence_data.index(work_centre) + 1)
        else:
            raise Exception('failed review the correct tracking measure for release')

    def release_review(self, order):
        """
        function that reviews if an order can be released
        """
        release = True
        if self.tracking_variable == 'total':
            released = self.sim.policy_panel.released + self.control_measure(order=order)
            completed = self.sim.policy_panel.completed
            check = released - completed
            if check < 0:
                raise Exception('more orders completed than released')
            # compare against target
            if released - completed > self.sim.policy_panel.release_target:
                release = False
                return release
        elif self.tracking_variable == 'work_centre':
            released = self.sim.policy_panel.released.copy()
            completed = self.sim.policy_panel.completed.copy()
            for work_centre in order.routing_sequence:
                # contribute
                released[work_centre] += self.control_measure(order=order, work_centre=work_centre)
                # compare against target
                if released[work_centre] - completed[work_centre] > \
                        self.sim.policy_panel.release_target[work_centre]:
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

    def contribute_release(self, order):
        """
        contribute order or load depending on the tracking viable
        """
        if self.tracking_variable == 'total':
            # contribute
            self.sim.policy_panel.released += self.control_measure(order=order)
        elif self.tracking_variable == 'work_centre':
            for work_centre in order.routing_sequence:
                # contribute following aggregate load method Oosterman et al., 2000
                self.sim.policy_panel.released[work_centre] += self.control_measure(order=order,
                                                                                          work_centre=work_centre)
        elif self.tracking_variable == 'none':
            self.sim.policy_panel.released += 1
        else:
            raise Exception('failed review the correct tracking variable for release')
        return

    def contribute_completed(self, order, work_centre=None):
        """
        contribute order or load depending on the tracking viable
        """
        if self.tracking_variable == 'total':
            # contribute
            self.sim.policy_panel.completed += self.control_measure(order=order)
        elif self.tracking_variable == 'work_centre':
            # contribute following aggregate load method Oosterman et al., 2000
            self.sim.policy_panel.completed[work_centre] += self.control_measure(order=order,
                                                                                       work_centre=work_centre)
        elif self.tracking_variable == 'none':
            self.sim.policy_panel.completed += 1
        else:
            raise Exception('failed review the correct tracking variable for release')
        return

    def release(self, review_condition="target", attr=None, put_in_queue=True):
        # sequence the orders currently in the pool
        self.sim.model_panel.POOLS.items.sort(key=itemgetter(self.index_priority))
        # get valid pool items
        pool_list, break_loop = self.get_release_list()
        # indicate release
        next_release = False
        # orders in pool
        if not break_loop:
            # contribute the load from each item in the pool
            for i, order_list in enumerate(pool_list):
                order = order_list[self.index_order_object]
                # review
                if review_condition == 'target':
                    order.release = self.release_review(order=order)
                elif review_condition == 'immediate':
                    order.release = True
                elif review_condition == 'starvation':
                    order.release = self.starvation_release_review(order=order, work_centre=attr['work_centre'])
                else:
                    raise Exception(f'{review_condition} is an invalid review condition')
                # release if allowed
                if order.release:
                    next_release = True
                    if review_condition == 'starvation':
                        next_release = False
                    # contribute load but do not track for immediate release
                    self.contribute_release(order=order)
                    # remove order from pool
                    self.release_from_pool(release_now=order_list)
                    # allocate materials to orders
                    self.dedicate_materials_to_orders(order=order)
                    # the orders are send to the process, but dispatch after release period
                    dispatch = True
                    if self.activate_periodic_release and review_condition != 'starvation':
                        dispatch = False
                    # put the order in the queue
                    if put_in_queue:
                        self.sim.process.put_in_queue(order=order, dispatch=dispatch)
                    # indicate if an additional release is possible
                    return break_loop, next_release
            # no nex release possible as all orders in the pool cannot be released
            return break_loop, next_release
        else:
            return break_loop, next_release

    def release_non_hierarchical(self, order_list, order):
        # contribute load
        self.contribute_release(order=order)
        # remove order from pool
        self.release_from_pool(release_now=order_list)
        # allocate materials to orders
        self.dedicate_materials_to_orders(order=order)
        return

    def periodic_release(self):
        """
        Workload Control Periodic release using aggregate load. See workings in Land 2004.
        """
        periodic_interval = self.sim.policy_panel.release_technique_attributes['check_period']
        while True:
            # deactivate release period, ensure dispatching
            self.sim.process.starvation_dispatch()
            yield self.sim.env.timeout(periodic_interval)
            # set the list of released orders
            while True:
                break_loop, next_release = self.release()
                # condition 1: no orders in the pool
                if break_loop:
                    break
                # condition 2: still orders in the pool but no next release possible
                if not next_release:
                    break

    def continuous_release(self):
        """
        Workload Control: continuous release using corrected aggregate load. See workings in Fernandes et al., 2017
        """
        while True:
            if self.sim.policy_panel.release_technique == "immediate":
                break_loop, next_release = self.release(review_condition='immediate')
            else:
                break_loop, next_release = self.release()

            # condition 1: no orders in the pool
            if break_loop:
                break
            # condition 2: still orders in the pool but no next release possible
            if not next_release:
                break

    def continuous_trigger(self, work_centre):
        """
        Workload Control: continuous release using aggregate load. See workings in Thürer et al, 2014.
        Part of LUMS COR
        """
        # must be adapted so we can get orders in the pool that
        break_loop, next_release = self.release(review_condition="starvation",
                                                attr={'work_centre': work_centre})
        return

    def control_queue_empty(self, work_centre):
        """
        controls if the queue is empty
        :param: work_center:
        :return: bool
        """
        in_system = len(self.sim.model_panel.QUEUES[work_centre].items) + \
                    len(self.sim.model_panel.WORK_CENTRES[work_centre].users)
        if in_system == 0:
            return True
        else:
            return False

    def collect_starving_work_centres_work_centres(self):
        starving_work_centres = []
        for work_centre in self.sim.model_panel.WORK_CENTRES:
            if self.control_queue_empty(work_centre=work_centre):
                starving_work_centres.append(work_centre)
        return starving_work_centres

    def update_release(self, order, work_centre, completed=False):
        """
        add the processed load and trigger continuous release if required.
        :param order:
        :param work_centre:
        :return:
        """
        # remove load
        if completed and self.tracking_variable == 'total':
            # only update load if order is completed
            self.contribute_completed(order=order)
        elif self.tracking_variable == 'work_centre':
            # update tracking variable after each operation is completed
            self.contribute_completed(order=order, work_centre=work_centre)
        # activate release mechanism
        if not self.sim.policy_panel.release_technique == "DRACO":
            self.activate_release(work_centre=work_centre)
        return

    def material_needs(self):
        # specify material needs for each item
        material_needs = {}
        for item_type, material in self.sim.model_panel.materials.items():
            material_needs[item_type] = 0
        # no material needs
        if len(self.sim.model_panel.POOLS.items) == 0:
            return material_needs
        # determine the material needs
        pool_list = self.sim.model_panel.POOLS.items
        for pool_item in pool_list:
            order = pool_item[self.index_order_object]
            material_needs[order.requirements[0]] += 1
        return material_needs

    def material_planned_release_date(self, order):
        n = len(self.sim.model_panel.material_types)
        q = len(order.requirements)
        return order.arrival_time + ((order.due_date - order.arrival_time) / n) * q

    def capacity_planned_release_date(self, order):
        m = len(self.sim.model_panel.MANUFACTURING_FLOOR_LAYOUT)
        r = len(order.routing_sequence)
        return order.arrival_time + ((order.due_date - order.arrival_time) / m) * r

    def integrated_planned_release_date(self, order):
        q = len(order.requirements)
        r = len(order.routing_sequence)
        return order.arrival_time + (order.due_date - order.arrival_time) * (q / (q + r))