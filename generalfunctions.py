import random
import numpy as np


class GeneralFunctions(object):
    def __init__(self, simulation):
        self.sim = simulation
        self.random_generator = random.Random()
        self.random_generator.seed(999999)
        return

    @staticmethod
    def arrival_time_calculator(wc_and_flow_config, manufacturing_floor_layout, aimed_utilization,
                                mean_process_time, number_of_machines):
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
        if wc_and_flow_config == "GFS" or wc_and_flow_config == "PJS":
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
        return self.random_generator.expovariate(lambd=1/mean)

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

    def add_constant_DD(self):
        """
        allocate due date to order by adding a constant
        :param order:
        :return: Due Date value
        """
        return self.sim.env.now + self.sim.policy_panel.DD_constant_value

    def total_work_content(self, order):
        """
        allocate due date to order by total work content
        :param order:
        :return: Due Date value
        """
        return self.sim.env.now + (order.process_time_cumulative * self.sim.policy_panel.DD_total_work_content_value)

    def ODD_land_adaption(self, order):
        """
        update ODD's following Land et al. (2014)
        :param order:
        """
        slack = order.due_date - self.sim.env.now
        if slack >= 0:
            for WC in order.routing_sequence:
                order.ODDs[WC] = self.sim.env.now + (order.routing_sequence.index(WC) + 1) *\
                                 (slack / len(order.routing_sequence))
        else:
            for WC in order.routing_sequence:
                order.ODDs[WC] = self.sim.env.now
        return
