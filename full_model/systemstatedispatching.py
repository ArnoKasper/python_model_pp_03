import math
from operator import itemgetter
import numpy as np


class SystemStateDispatching(object):

    def __init__(self, simulation):
        # function params
        self.sim = simulation
        self.work_centre_layout = self.sim.model_panel.MANUFACTURING_FLOOR_LAYOUT
        self.index_sorting_removal = 0
        self.index_order_object = 1
        self.index_priority = 2

        """ system-state variables """
        self.last_update_system_state_variables = -1
        self.order_book = {}

        # release
        self.activate_release_WIP_target = True
        if self.activate_release_WIP_target:
            self.WIP_target = self.sim.policy_panel.release_target
        self.current_queue_list = []
        self.current_pool_list = []
        self.number_of_orders_in_system = 0
        self.WIP = 0
        self.total_workload = 0

        # dispatching
        self.T_list = list()
        self.A_dict = dict()
        self.S_list = list()
        self.V_list = list()

        # IPD
        self.IPD_pool_max = np.inf
        self.IPD_pool_min = 0
        self.IPD_dispatching_max = np.inf
        self.IPD_dispatching_min = 0

        # FOCUS
        self.p_ij_min = 0
        self.p_ij_mean = 0
        self.p_ij_max = np.inf
        self.slack_min = 0
        self.slack_mean = 0
        self.slack_max = np.inf
        self.slack_opn_min = 0
        self.slack_opn_mean = 0
        self.slack_opn_max = np.inf

        self.function_names = ["pi", "xi", "tau", "delta"]
        self.weights = [1, 0, 1, 0]
        self.functions_activated = dict()
        for i, name in enumerate(self.function_names):
            self.functions_activated[name] = self.weights[i]
        self.max_impact_list = [0] * len(self.weights)
        return

    def dispatching_mode(self, queue_list, work_centre):
        """
        assumes the use of IMM as release procedure
        """
        # update state variables
        self.FOCUS_update_system_state_variables(work_centre=work_centre)
        # get impact of each order in queue
        for i, order_item in enumerate(queue_list):
            projected_impact = self.FOCUS(order=order_item[self.index_order_object], work_centre=work_centre)
            # attach impact to the order
            order_item[self.index_priority] = projected_impact
            # - 1 because simulation model minimizes
            order_item[self.index_priority] = order_item[self.index_priority] * -1
        return queue_list

    def full_control_mode(self, work_centre=None, order=None, trigger_mode='dispatching', material=None):
        """
        control approach of DRACO
        work_centre:    the work_centre that idle
        order:          order object
        trigger_mode:   trigger mode, can be 'arrival', 'supply' and 'dispatching'
        """
        # depending on the triggering mode, the work centre needs to be found
        if trigger_mode == 'arrival':
            # control if the queue is not empty
            if not self.sim.release.control_queue_empty(work_centre=order.routing_sequence[0]):
                # work centre not starting; return
                return None, True
            else:
                # work centre is idling, needs a new order
                # update the material allocation policy, if necessary
                if self.sim.policy_panel.material_allocation == 'HB':
                    self.sim.inventory.rationing_sequence_update()
                # do the material check
                if self.sim.inventory.material_check(order=order):
                    # material available, allow for release.
                    work_centre = order.routing_sequence[0]
                else:
                    # work centre starving, but materials are not there
                    return None, True
        elif trigger_mode == 'supply':
            # check if there are orders in pool
            if len(self.sim.model_panel.POOLS.items) == 0:
                # no orders to dedicate the materials to
                return None, True
            # orders available, check if a work centre is idling.
            idle_work_centre = []
            for potential_starving_work_centre in self.sim.model_panel.WORK_CENTRES:
                if self.sim.release.control_queue_empty(work_centre=potential_starving_work_centre):
                    idle_work_centre.append(potential_starving_work_centre)
            # check for starvation
            if len(idle_work_centre) == 0:
                # no need to release
                return None, True
            # check if orders in the pool move to a idling work centre, i.e. a starving one
            starving_work_centre_with_orders = []
            for starving_wc in idle_work_centre:
                for order_list in self.sim.model_panel.POOLS.items:
                    order = order_list[self.index_order_object]
                    wc_check = order.routing_sequence[0] == starving_wc  # check gateway
                    material_check = material in order.requirements  # check material
                    if wc_check and material_check:
                        # release is possible
                        starving_work_centre_with_orders.append(starving_wc)
            # check if release is possible
            if len(starving_work_centre_with_orders) == 0:
                # no starving work centres; no need to release
                return None, True
            elif len(starving_work_centre_with_orders) == 1:  # check there are multiple gateways
                # only work centre starving, select work centre and continue
                work_centre = starving_work_centre_with_orders[0]
            else:
                # multiple work centres starving, choose according to (pool) priority
                work_centre = self.starvation_work_centre_choice(starving_work_centres=starving_work_centre_with_orders,
                                                                 material=material)
                if work_centre is None:
                    raise Exception('DRACO: no work centre chosen, while order is starving!')

        # get the orders in the queue and pool
        queue_list = self.sim.model_panel.QUEUES[work_centre].items.copy()
        # get the pool of orders with materials available
        entire_pool_list, pool_empty = self.sim.release.get_release_list()
        # check orders in pool
        if not pool_empty:
            # find the orders in the pool that start at work centre
            pool_list = self.get_workcentre_specific_release_list(pool_list=entire_pool_list, work_centre=work_centre)
        else:
            # no orders in the pool
            pool_list = []

        # control if dispatching is possible
        if len(queue_list) + len(pool_list) == 0:
            # no orders to process, leave the machine idle.
            return None, True

        # update state variables
        self.DRACO_update_system_state_variables(work_centre=work_centre)
        # get impact of each order in queue or pool
        dispatching_options = pool_list + queue_list  # first queue, then pool
        # loop over all orders
        for i, order_item in enumerate(dispatching_options):
            projected_impact = self.DRACO(order_item=order_item,
                                          work_centre=work_centre,
                                          pool_length=len(pool_list))
            # attach impact to the order
            order_item[self.index_priority] = projected_impact
            # - 1 because simulation model minimizes
            order_item[self.index_priority] = order_item[self.index_priority] * -1

        # select the order with the highest impact
        order_list = sorted(dispatching_options, key=itemgetter(self.index_priority))[0]

        # indicate that the order must be removed
        order_list[self.index_sorting_removal] = 0

        # find if order is in the pool or queue
        """
        if the order is in the pool, it needs to be released, dedicate materials to it and send it to the queue
        """
        order_selected = order_list[self.index_order_object]
        if order_selected.location == "pool":
            # order in the pool, apply the release procedure
            # release the order and dedicate materials to it
            self.sim.release.release_non_hierarchical(order_list=order_list, order=order_selected)
            # data collection
            order_selected.queue_entry_time[work_centre] = self.sim.env.now
            # first time entering the floor
            order_selected.release_time = self.sim.env.now
            order_selected.pool_time = order_selected.release_time - order_selected.arrival_time
            order_selected.first_entry = False
            order_selected.release = True
            order_selected.location = "system"
            # put the order in the queue
            queue_item = self.sim.process.queue_item(order=order_selected, work_centre=work_centre)
            self.sim.model_panel.QUEUES[work_centre].put(queue_item)
            queue_item[self.index_sorting_removal] = 0  # indicate that the order can be dispatched

        # depending on the trigger, send order to the system
        if trigger_mode in ['supply', 'arrival']:
            self.sim.process.dispatch(order=order_selected, work_centre=work_centre)
        elif trigger_mode == 'dispatching':
            return order_list, False
        else:
            raise Exception('DRACO, no valid triggering condition identified')

    def R(self, released):
        """
        DRACO release element
        """
        release_impact = []
        # workload target
        if self.activate_release_WIP_target:
            rho = 0
            # release (order in pool)
            if not released:
                # more orders in the system than cap
                if self.WIP < (2 * self.WIP_target):
                    rho = 1 - (self.WIP / (2 * self.WIP_target))
                else:
                    rho = 0
            # release (order in queue)
            if released:
                # more load in the system than target
                if self.WIP < (2 * self.WIP_target):
                    rho = (self.WIP / (2 * self.WIP_target))
                else:
                    rho = 1
            release_impact.append(rho)
        return sum([j * 1 / len(release_impact) for j in release_impact])

    def D(self, order, work_centre, pool_length):
        if self.sim.policy_panel.ssd_rule == "FOCUS":
            projected_impact = self.FOCUS(order=order, work_centre=work_centre)
        elif self.sim.policy_panel.ssd_rule == "IPD":
            # select condition
            if pool_length != 0:
                priority = self.IPD(order=order, condition='pool')
                projected_impact = self.normalization(x=priority,
                                                         x_min=self.IPD_pool_min,
                                                         x_max=self.IPD_pool_max)

                # check projected impact
                if projected_impact > 1:
                    raise Exception("projected_impact > 1")
                elif projected_impact < 0:
                    raise Exception("projected_impact < 0")
            else:
                priority = self.IPD(order=order, condition='queue')
                projected_impact = - priority
        elif self.sim.policy_panel.ssd_rule == "SINGLE":
            priority = self.IPD(order=order, condition='pool')
            projected_impact = self.normalization(x=priority,
                                                  x_min=self.IPD_pool_min,
                                                  x_max=self.IPD_pool_max)
        else:
            raise Exception("no valid priority rule defined")
        return projected_impact

    def DRACO(self, order_item, work_centre, pool_length):
        order = order_item[self.index_order_object]
        # get projected impact values
        """
        release element
        """
        release_impact = self.R(released=order.release)
        """
        dispatching element
        """
        dispatching_impact = self.D(order=order, work_centre=work_centre, pool_length=pool_length)
        # aggregate all impact functions into list
        projected_impact = sum([dispatching_impact * 1 / 2, release_impact * 1 / 2])
        return projected_impact

    def FOCUS(self, order, work_centre):
        """
        FOCUS dispatching element
        """
        # params
        process_time = order.process_time[work_centre]
        routing_list = order.routing_sequence.copy()
        slack = self.slack(
            d_i=order.due_date,
            t=self.sim.env.now,
            k=1,
            sum_p_ij=order.remaining_process_time
        )
        slack_opn = self.slack(
            d_i=order.due_date,
            t=self.sim.env.now,
            k=len(routing_list),
            sum_p_ij=order.remaining_process_time
        )

        dispatching_impact = []
        # obtain pi
        if self.functions_activated["pi"] > 0:
            pi_pij_impact = 1 - (process_time / self.p_ij_max)
            dispatching_impact.append(pi_pij_impact)
        # obtain xi
        if self.functions_activated["xi"] > 0:
            return_value = self.xi_idleness_impact(
                order=order,
                process_time=process_time,
                upstream_starvation_dict=self.A_dict
            )
            if return_value > 0:
                xi_starvation_impact = 1 - (return_value / self.p_ij_max)
            else:
                xi_starvation_impact = 0
            dispatching_impact.append(xi_starvation_impact)
        # obtain tau
        if self.functions_activated["tau"] > 0:
            if slack > 0:
                tau_slack_impact = 1 - (slack / self.slack_max)
            else:
                tau_slack_impact = 1
            dispatching_impact.append(tau_slack_impact)
        # obtain delta
        if self.functions_activated["delta"] > 0:
            if slack_opn > 0:
                delta_slack_per_operation_impact = 1 - (slack_opn / self.slack_opn_max)
            else:
                delta_slack_per_operation_impact = 1
            dispatching_impact.append(delta_slack_per_operation_impact)
        return sum([j * 1 / len(dispatching_impact) for j in dispatching_impact])

    def IPD(self, order, condition):
        if condition == 'pool':
            # pool sequence rules
            if self.sim.policy_panel.sequencing_rule == "FISFO":
                priority = self.sim.env.now - order.arrival_time
            elif self.sim.policy_panel.sequencing_rule == "EDD":
                priority = order.due_date
            elif self.sim.policy_panel.rationing_rule == "PRD":
                priority = order.planned_release_time
            else:
                raise Exception('no valid pool sequencing rule selected for IPD')
        elif condition == 'queue':
            # dispatching rules
            if self.sim.policy_panel.dispatching_rule == "FCFS":
                priority = order.queue_entry_time[order.routing_sequence[0]]
            elif self.sim.policy_panel.dispatching_rule == "FISFO":
                priority = self.sim.env.now - order.arrival_time
            elif self.sim.policy_panel.dispatching_rule == "FI-SHOP-FO":
                priority = self.sim.env.now - order.release_time
            elif self.sim.policy_panel.dispatching_rule == "EDD":
                priority = order.due_date - self.sim.env.now
            else:
                raise Exception('no valid dispatching rule selected for IPD')
        else:
            raise Exception('no valid IPD procedure')
        return priority

    def DRACO_update_system_state_variables(self, work_centre):
        # special case for focus
        if self.sim.policy_panel.ssd_rule == 'FOCUS':
            self.FOCUS_update_system_state_variables(work_centre=work_centre)
            return

        """ set system-state variables """
        self.S_list = list()
        self.V_list = list()

        """ gather info state variables """
        self.WIP = 0
        for id, order in self.order_book.items():
            # collect WIP
            if order.release:
                self.WIP += 1
            # collect dispatching/pool priority
            if self.sim.policy_panel.ssd_rule == 'IPD':
                # self.S_list.append(self.IPD(order=order, condition='pool'))
                if order.routing_sequence[0] == work_centre:
                    self.S_list.append(self.IPD(order=order, condition='pool'))
                if order.release:
                    self.V_list.append(self.IPD(order=order, condition='queue'))
            elif self.sim.policy_panel.ssd_rule == 'SINGLE':
                self.S_list.append(self.IPD(order=order, condition='pool'))

        """ update all state variables """
        if not len(self.S_list) == 0:
            self.IPD_pool_max = max(self.S_list)
            self.IPD_pool_min = min(self.S_list)
        if not len(self.V_list) == 0:
            self.IPD_dispatching_max = max(self.V_list)
            self.IPD_dispatching_min = min(self.V_list)
        return

    def starvation_work_centre_choice(self, starving_work_centres, material):
        min_priority = np.inf
        min_work_centre = None
        for order_list in self.sim.model_panel.POOLS.items:
            order = order_list[self.index_order_object]
            # collect dispatching/pool priority
            if self.sim.policy_panel.ssd_rule in ['IPD', 'SINGLE']:
                material_check = material in order.requirements
                work_centre_check = order.routing_sequence[0] in starving_work_centres
                if material_check and work_centre_check:
                    priority = self.IPD(order=order, condition='pool')
                    if priority < min_priority:
                        min_priority = priority
                        min_work_centre = order.routing_sequence[0]
        return min_work_centre

    def FOCUS_update_system_state_variables(self, work_centre):
        """ check if update is needed """
        if self.last_update_system_state_variables == self.sim.env.now:
            return
        self.last_update_system_state_variables = self.sim.env.now
        """ set system-state variables """
        # dispatching
        self.T_list = list()
        self.A_dict = dict()
        self.S_list = list()
        self.V_list = list()

        """ update all state variables """
        self.WIP = 0
        for id, order in self.order_book.items():
            # control if the order is released
            if order.release:
                self.WIP += 1
            # get dispatching variables
            remaining_process_times, slack, slack_opn = self.get_dispatching_variables(order=order)
            self.append_system_state_variables(process_times=remaining_process_times,
                                               slack=slack,
                                               slack_opn=slack_opn)

        """ 
        update system state params 
        """
        # dispatching variables
        if not len(self.T_list) == 0:
            self.p_ij_min = min(self.T_list)
            self.p_ij_max = max(self.T_list)
            self.p_ij_mean = sum(self.T_list) / len(self.T_list)

        if not len(self.S_list) == 0:
            self.slack_min = min(self.S_list)
            self.slack_max = max(self.S_list)
            self.slack_mean = sum(self.S_list) / len(self.S_list)

        if not len(self.V_list) == 0:
            self.slack_opn_min = min(self.V_list)
            self.slack_opn_max = max(self.V_list)
            self.slack_opn_mean = sum(self.V_list) / len(self.V_list)

        # order book
        self.number_of_orders_in_system = len(self.V_list)

        # find if a work centre is starving
        if self.functions_activated["xi"] > 0:
            for j, WC in enumerate(self.work_centre_layout):
                if WC != work_centre:
                    # get the pool
                    pool, _ = self.sim.release.get_release_list()
                    if pool is not None:
                        # split pool into subsets based on their gateway.
                        pool_WC = self.get_workcentre_specific_release_list(pool_list=pool, work_centre=WC)
                        if len(pool_WC) > 0:
                            pool_empty = False
                        else:
                            pool_empty = True
                    else:
                        pool_empty = True
                    # indicate empty gateway
                    if len(self.sim.model_panel.QUEUES[WC].items) == 0 and pool_empty:
                        self.A_dict[WC] = 1
                    else:
                        self.A_dict[WC] = 0
                else:
                    self.A_dict[WC] = 0
        return

    def append_system_state_variables(self, process_times, slack, slack_opn):
        self.T_list.extend(process_times)
        self.S_list.append(slack)
        self.V_list.append(slack_opn)
        return

    def get_dispatching_variables(self, order):
        # remaining_process_times
        remaining_process_times = self.remaining_process_times(routing_sequence=order.routing_sequence,
                                                               process_times=order.process_time)
        # slack
        slack = self.slack(d_i=order.due_date,
                           t=self.sim.env.now,
                           k=1,
                           sum_p_ij=order.remaining_process_time)
        # slack opn
        slack_opn = self.slack(d_i=order.due_date,
                               t=self.sim.env.now,
                               k=len(order.routing_sequence),
                               sum_p_ij=order.remaining_process_time
                               )
        return remaining_process_times, slack, slack_opn

    @staticmethod
    def xi_idleness_impact(order, process_time, upstream_starvation_dict):
        if len(order.routing_sequence) >= 2:
            if upstream_starvation_dict != 0:
                for WC, indicator in upstream_starvation_dict.items():
                    if order.routing_sequence[1] == WC and indicator == 1:
                        return process_time
                return 0
            else:
                return 0
        else:
            return 0

    @staticmethod
    def remaining_process_times(routing_sequence, process_times):
        remaining_process_times = []
        for k, operation in enumerate(routing_sequence):
            remaining_process_times.append(process_times[operation])
        return remaining_process_times

    @staticmethod
    def slack(d_i, t, k, sum_p_ij):
        return (d_i - t - sum_p_ij) / k

    @staticmethod
    def normalization(x_min, x_max, x):
        result = 0
        if (x_max - x_min) != 0:
            result = (x_max - x) / (x_max - x_min)
        return result

    def get_workcentre_specific_release_list(self, pool_list, work_centre):
        return_list = []
        for order_list in pool_list:
            if order_list[self.index_order_object].routing_sequence[0] == work_centre:
                return_list.append(order_list)
        return return_list

    def input_order_book(self, order):
        self.order_book[order.identifier] = order
        return

    def output_order_book(self, order):
        del self.order_book[order.identifier]
        return

    def get_wip(self):
        wip = 0
        for _, order in self.order_book.items():
            # control if the order is released
            if order.release:
                wip += 1
        return wip

    def __str__(self):
        return "DRACO"
