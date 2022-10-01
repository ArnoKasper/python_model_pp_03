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
        # inventory
        self.activate_inventory = True

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
        self.P_j = list()

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
        self.weights = [1] * len(self.function_names)
        self.functions_activated = dict()
        for i, name in enumerate(self.function_names):
            self.functions_activated[name] = self.weights[i]
        self.max_impact_list = [0] * len(self.weights)
        return

    def dispatching_mode(self, queue_list, work_centre):
        """
        assumes the use of IMM as release procedure
        """
        # remove impact values previous decision
        self.max_impact_list = [0] * len(self.weights)
        # update state variables
        self.update_system_state_variables(work_centre=work_centre)
        # get impact of each order in queue
        for i, order_item in enumerate(queue_list):
            projected_impact_list = self._get_weighted_impact(order_item=order_item, work_centre=work_centre)
            # attach impact to the order
            order_item[self.index_priority] = sum(projected_impact_list)
            # find highest impact for this selection moment
            if sum(projected_impact_list) > sum(self.max_impact_list):
                self.max_impact_list = projected_impact_list
            # - 1 because simulation model minimizes
            order_item[self.index_priority] = order_item[self.index_priority] * -1
        return queue_list

    def full_control_mode(self, work_centre=None, order=None, trigger_mode='dispatching'):
        """
        control approach of DRACO
        work_centre:    the work_centre that idle
        order:          order object
        trigger_mode:   trigger mode, can be 'arrival', 'supply' and 'dispatching'
        """
        # print(trigger_mode)
        # depending on the triggering mode, the work centre needs to be found
        if trigger_mode == 'arrival':
            # control if the queue is not empty
            if not self.sim.release.control_queue_empty(work_centre=order.routing_sequence[0]):
                # work centre not starting; return
                return None, True
            else:
                # work centre is idling, needs a new order
                # material check, update allocation variables if rationing is used
                if self.sim.policy_panel.material_allocation == 'rationing':
                    self.sim.inventory.rationing_sequence_update()
                # do the material check
                if self.sim.inventory.material_check(order=order):
                    # material available, allow for release.
                    work_centre = order.routing_sequence[0]
                else:
                    # work centre starving, but materials are not there
                    return None, True
        elif trigger_mode == 'supply':
            for potential_starving_work_centre in self.sim.model_panel.WORK_CENTRES:
                starving_work_centre = []
                if self.sim.release.control_queue_empty(work_centre=potential_starving_work_centre):
                    starving_work_centre.append(potential_starving_work_centre)
                """
                there must be a selection procedure when material is scare to identify where to send the order to
                """
                # choose work centre
                if len(starving_work_centre) == 0:
                    return None, True
                elif len(starving_work_centre) == 1:
                    work_centre = starving_work_centre[0]
                else:
                    # multiple work centres starving, choose randomly
                    work_centre = self.sim.random_generator.sample(starving_work_centre, 1)
                    print('random choice made!')

        # get the orders in the queue and pool
        queue_list = self.sim.model_panel.QUEUES[work_centre].items.copy()
        entire_pool_list, pool_empty = self.sim.release.get_release_list()
        # check orders in pool
        if not pool_empty:
            # find the orders in the pool that start at work centre
            pool_list = self.get_release_list(pool_list=entire_pool_list, work_centre=work_centre)
        else:
            # no orders in the pool
            pool_list = []

        # control if dispatching is possible
        if len(queue_list) + len(pool_list) == 0:
            # no orders to process, leave the machine idle.
            return None, True

        # remove impact values previous decision
        self.max_impact_list = [0] * len(self.weights)
        # update state variables
        self.update_system_state_variables(work_centre=work_centre)
        # get impact of each order in queue or pool
        dispatching_options = pool_list + queue_list  # first queue, then pool
        # loop over all orders
        for i, order_item in enumerate(dispatching_options):
            projected_impact_list = self._get_weighted_impact(order_item=order_item, work_centre=work_centre)
            # attach impact to the order
            order_item[self.index_priority] = sum(projected_impact_list)
            # find highest impact for this selection moment
            if sum(projected_impact_list) > sum(self.max_impact_list):
                self.max_impact_list = projected_impact_list
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

    def _get_weighted_impact(self, order_item, work_centre):
        order = order_item[self.index_order_object]
        # params
        process_time = order.process_time[work_centre]
        process_times = order.process_time.copy()
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

        # get projected impact values
        impact_list = []
        """
        supply element
        """
        stock_level = 10 + 1
        inventory_impact = []
        if self.activate_inventory:
            sigma = 0

        inventory_impact = sum([j * 1 / len(inventory_impact) for j in inventory_impact])
        """
        release element
        """
        release_impact = []
        # workload target
        if self.activate_release_WIP_target:
            rho = 0
            # release (order in pool)
            if order.first_entry:
                # more orders in the system than cap
                if self.WIP < (2*self.WIP_target):
                    rho = 1 - (self.WIP / (2*self.WIP_target))
                else:
                    rho = 0
            # release (order in queue)
            if not order.first_entry:
                # more load in the system than target
                if self.WIP < (2*self.WIP_target):
                    rho = (self.WIP / (2*self.WIP_target))
                else:
                    rho = 1
            release_impact.append(rho)
        release_impact = sum([j * 1/len(release_impact) for j in release_impact])

        """
        dispatching element
        """
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

        dispatching_impact = sum([j * 1/len(dispatching_impact) for j in dispatching_impact])

        # aggregate all impact functions into list
        projected_impact = [dispatching_impact * 1/2, release_impact * 1/2]
        return projected_impact

    def update_system_state_variables(self, work_centre):
        """ set system-state variables """
        # dispatching
        self.T_list = list()
        self.A_dict = dict()
        self.S_list = list()
        self.V_list = list()

        """ update all state variables """
        for i, pool_order in enumerate(self.sim.model_panel.POOLS.items):
            processing_order = pool_order[self.index_order_object]
            # pick remaining process time
            process_times = []
            for k, operation in enumerate(processing_order.routing_sequence):
                process_times.append(processing_order.process_time[operation])
            # order params
            slack, slack_opn = self.get_dispatching_variables(order=processing_order)
            self.append_system_state_variables(
                process_times=process_times,
                slack=slack,
                slack_opn=slack_opn
            )

        # get state information from orders currently in process
        self.WIP = 0
        for j, WC in enumerate(self.work_centre_layout):
            # processing order
            if len(self.sim.model_panel.WORK_CENTRES[WC].users) == 1:
                self.WIP += 1
                processing_order = self.sim.model_panel.WORK_CENTRES[WC].users[0].self
                # pick remaining process time
                process_times = []
                for k, operation in enumerate(processing_order.routing_sequence):
                    process_times.append(processing_order.process_time[operation])
                # order params
                slack, slack_opn = self.get_dispatching_variables(order=processing_order)
                self.append_system_state_variables(
                    process_times=process_times,
                    slack=slack,
                    slack_opn=slack_opn
                )

            # get state information from orders currently in queues
            for i, queueing_order in enumerate(self.sim.model_panel.QUEUES[WC].items):
                self.WIP += 1
                processing_order = queueing_order[self.index_order_object]
                # pick remaining process time
                process_times = []
                for k, operation in enumerate(processing_order.routing_sequence):
                    process_times.append(processing_order.process_time[operation])
                # order params
                slack, slack_opn = self.get_dispatching_variables(order=processing_order)
                self.append_system_state_variables(
                    process_times=process_times,
                    slack=slack,
                    slack_opn=slack_opn
                )

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
                        pool_WC = self.get_release_list(pool_list=pool, work_centre=WC)
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
        return slack, slack_opn

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
    def slack(d_i, t, k, sum_p_ij):
        return (d_i - t - sum_p_ij) / k

    @staticmethod
    def normalization(x_min, x_max, x):
        result = 0
        if (x_max - x_min) != 0:
            result = (x_max - x) / (x_max - x_min)
        return result

    def get_release_list(self, pool_list, work_centre):
        return_list = []
        for order_list in pool_list:
            if order_list[self.index_order_object].routing_sequence[0] == work_centre:
                return_list.append(order_list)
        return return_list

    def __str__(self):
        return "DRACO"

