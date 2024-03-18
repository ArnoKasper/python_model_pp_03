import random
import numpy as np
import math
import scipy.stats as st

class GeneralFunctions(object):
    def __init__(self, simulation):
        self.sim = simulation
        self.random_generator = random.Random()
        self.random_generator.seed(999999)
        return

    @staticmethod
    def arrival_time_calculator(wc_and_flow_config,
                                manufacturing_floor_layout,
                                aimed_utilization,
                                mean_process_time,
                                number_of_machines):
        """
        compute the inter arrival time
        :param wc_and_flow_config: the configuration
        :param manufacturing_floor_layout: the configuration of flow
        :param aimed_utilization: the average utilization
        :param mean_process_time: the average process time
        :param number_of_machines: number of machines for each station
        :return: inter arrival time
        """
        mean_amount_work_centres = 0
        if wc_and_flow_config in ["GFS", "PJS", "PJSR"]:
            mean_amount_work_centres = (len(manufacturing_floor_layout) + 1) / 2
        elif wc_and_flow_config == "PFS":
            mean_amount_work_centres = len(manufacturing_floor_layout)
        # calculate the mean inter-arrival time
        # (mean amount of machines / amount of machines / utilization * 1 / amount of machines)
        inter_arrival_time = mean_amount_work_centres / len(manufacturing_floor_layout) * \
                             1 / aimed_utilization * \
                             mean_process_time / number_of_machines
        # round the float to five digits accuracy
        inter_arrival_time = round(inter_arrival_time, 5)
        return inter_arrival_time

    def k_erlang(self, mean, k):
        """
        two erlang distribution
        :return: voi
        """
        rate = mean * k
        return_value = 0
        for k in range(0, k):
            return_value += self.random_generator.expovariate(rate)
        return return_value

    def two_erlang_truncated(self, mean):
        """
        two erlang distribution
        :return: void
        """
        mean_process_time_adj = 1.975
        # pull truncated value
        return_value = np.inf
        while return_value > 4:
            return_value = self.random_generator.expovariate(mean_process_time_adj) + \
                           self.random_generator.expovariate(mean_process_time_adj)
        return return_value

    def exponential(self, mean):
        """
        exponential distribution
        :return: void
        """
        return self.random_generator.expovariate(lambd=1 / mean)

    def uniform(self, mean):
        return self.random_generator.uniform(0, 2 * mean)

    def random_value_DD(self):
        """
        allocate random due date to order
        :return: Due Date value
        """
        return_value = self.sim.env.now + self.random_generator.uniform(
            self.sim.policy_panel.DD_random_min_max[0],
            self.sim.policy_panel.DD_random_min_max[1]
        )
        return return_value

    def order_random_value_DD(self, order):
        """
        allocate random due date to order
        :return: Due Date value
        """
        a_i = self.random_generator.uniform(
            self.sim.policy_panel.DD_order_random_min_max[0],
            self.sim.policy_panel.DD_order_random_min_max[1]
        )
        return self.sim.env.now + a_i + order.planned_manufacturing_lead_time

    def add_constant_DD(self):
        """
        allocate due date to order by adding a constant
        :param order:
        :return: Due Date value
        """
        return self.sim.env.now + self.sim.policy_panel.DD_constant_value

    def total_work_content_DD(self, order):
        """
        allocate due date to order by total work content
        :param order:
        :return: Due Date value
        """
        return self.sim.env.now + (order.process_time_cumulative * self.sim.policy_panel.DD_total_work_content_value)

    def number_of_operations_DD(self, order):
        """
        allocate due date to order by total work content
        :param order:
        :return: Due Date value
        """
        return self.sim.env.now + (
                    len(order.routing_sequence_data) * self.sim.policy_panel.DD_total_routing_content_value)

    def ODD_land_adaption(self, order):
        """
        update ODD's following Land et al. (2014)
        :param order:
        """
        slack = order.due_date - self.sim.env.now
        if slack >= 0:
            for WC in order.routing_sequence:
                order.ODDs[WC] = self.sim.env.now + (order.routing_sequence.index(WC) + 1) * \
                                 (slack / len(order.routing_sequence))
        else:
            for WC in order.routing_sequence:
                order.ODDs[WC] = self.sim.env.now
        return

    def get_mean_q(self):
        mean_p = self.sim.model_panel.MEAN_PROCESS_TIME
        rho = self.sim.model_panel.AIMED_UTILIZATION
        cv_a = 1
        if self.sim.model_panel.PROCESS_TIME_DISTRIBUTION == '2_erlang':
            cv_p = 0.5
        elif self.sim.model_panel.PROCESS_TIME_DISTRIBUTION == 'exponential':
            cv_p = 1
        else:
            raise Exception('cannot set queue for the given process time distribution')
        return mean_p * (rho / (1 - rho)) * ((cv_a ** 2 + cv_p ** 2) / 2)

    def get_mean_manufacturing_lead_time(self):
        mean_r = (len(self.sim.model_panel.MANUFACTURING_FLOOR_LAYOUT) + 1) / 2
        mean_p = self.sim.model_panel.MEAN_PROCESS_TIME
        mean_q = self.get_mean_q()
        return mean_r * (mean_p + mean_q)

    def z_score(self, prob):
        return st.norm.ppf(prob)

    def station_planned_lead_time(self, r_i):
        """
        old procedure
        alpha = 1 / 0.5**2      # shape ==  1/CV^2 process time distribution
        beta = 1/alpha * mu_p   # scale ==  1/alpha * mean process time
        # third_moment_estimate = alpha * (alpha + 1) * (alpha + 2) * beta**3 # without error
        third_moment_estimate = alpha * (alpha + 1) * (alpha + 1) * beta**3
        v_p = 2/(1**2)
        v_q = mu_q ** 2 + (arrival_rate * third_moment_estimate) / (3 * (1 - utilization))
        """
        # see Kleinrock 1976, Volume II, eq. 1.82 & 1.87
        # expected station throughput time
        utilization = self.sim.model_panel.AIMED_UTILIZATION
        mu_p = self.sim.model_panel.MEAN_PROCESS_TIME

        arrival_rate = utilization / mu_p
        production_rate = 1 / mu_p

        # moments processing time distribution
        erlang_k = 2
        rate = erlang_k / mu_p
        var_p = erlang_k/(rate**2)
        sigma_p = var_p ** (1/2)
        skewness_p = 2 / erlang_k ** (1/2)

        # second moment: # E[X^2] = Var(X) + [E(S)]^2
        second_moment = var_p + mu_p ** 2
        # third moment: E[X^2] = Skew(X) * [Std(X)]^3 + [E(S)]^3 + 3 * E(S) * Var(x)
        third_moment = skewness_p * sigma_p ** 3 + mu_p ** 3 + 3 * mu_p * var_p

        # expected station throughput time
        '''
        three options with the same outcome: 
        mu_q = ((arrival_rate * second_moment)/2) / (1 - utilization)  # formulation Kleindorf
        mu_q = (arrival_rate * second_moment) / (2 * (1 - arrival_rate * mu_p))  # formulation Ross
        # reviewer proposal
        r_1 = (second_moment / (1 + 1) * mu_p)
        mu_q = utilization / (1 - utilization) * r_1
        '''
        mu_q = ((arrival_rate * second_moment)/2) / (1 - utilization)  # formulation Kleindorf
        mu_t = mu_q + mu_p

        # station throughput time, assume independence
        """
        two options with the same outcome: 
        var_q = mu_q ** 2 + (arrival_rate * third_moment) / (3 * (1 - utilization)) # formulation Kleindorf
        r_1 = (second_moment / (1 + 1) * mu_p)
        r_2 = (third_moment / (2 + 1) * mu_p)
        # reviewer proposal
        var_q = (utilization / (1 - utilization) ** 2) * (utilization * (r_1 ** 2) + (1 - utilization) * r_2)
        """
        var_q = mu_q ** 2 + (arrival_rate * third_moment) / (3 * (1 - utilization))  # formulation Kleindorf
        var_t = var_p + var_q

        # critical value
        c_e = self.sim.model_panel.earliness_cost
        c_t = self.sim.model_panel.tardiness_cost
        F_t = c_t / (c_t + c_e)
        z = self.z_score(prob=F_t)
        # print(3.5*mu_t + z * math.sqrt(3.5*var_t))
        return r_i*mu_t + z * math.sqrt(r_i*var_t)

    def get_expected_demand_during_supply_lead_time_theta(self, replenishment_type, a_min_max):
        mean_material_quantity = self.sim.model_panel.material_quantity
        n = len(self.sim.model_panel.material_types)
        arrival_rate = 1/self.sim.model_panel.MEAN_TIME_BETWEEN_ARRIVAL
        # determine demand rate
        delta_k = mean_material_quantity * (arrival_rate/n)

        if replenishment_type == 'PoHed':
            L = self.sim.model_panel.expected_replenishment_time
            o_max = max(a_min_max)
            o_min = min(a_min_max)
            theta_A = delta_k * max(0, (L-o_max)) * (max(0, o_max)/o_max)  # early demand
            theta_B = delta_k * ((min(L, o_max) - max(0, o_min)) / 2) * (max(0, (min(L, o_max) - max(0, o_min))) / (o_max - o_min))  # regular demand
            theta_C = delta_k * L * max(0, (-o_min / (o_max - o_min)))  # rush demand
            theta = theta_A + theta_B + theta_C
        elif replenishment_type == 'ExHed':
            L = self.sim.model_panel.expected_replenishment_time
            theta = delta_k * L
        else:
            raise Exception(f'cannot beta for the given replenishment type {replenishment_type}')
        return theta

    def hedging_policy(self, replenishment_type, a_min_max):
        c_h = self.sim.model_panel.holding_cost
        c_t = self.sim.model_panel.tardiness_cost
        F_s = c_t / (c_h + c_t)
        theta = self.get_expected_demand_during_supply_lead_time_theta(replenishment_type=replenishment_type, a_min_max=a_min_max)
        sigma_L = math.sqrt(theta)
        z = self.z_score(prob=F_s)
        # compute stock level, assume round up
        stock_level = int(theta + z * sigma_L) + 1
        reorder_point = stock_level - 1
        return reorder_point