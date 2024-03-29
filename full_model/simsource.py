from random import Random
from flowitem import Order

class Demand(object):
    def __init__(self, simulation):
        """
        :param simulation:
        :param stationary:
        """
        self.sim = simulation
        self.random_generator = Random()
        self.random_generator.seed(999999)
        """
        note, these generators are NOT independent
        """

        # key params
        self.mean_demand_quantity = 1
        self.inventory_threshold = 1

        self.mean_time_between_arrivals = self.sim.model_panel.MEAN_TIME_BETWEEN_ARRIVAL
        return

    def generate_random_arrival_exp(self):
        i = 1
        while True:
            # create an order object and give it a name
            order = Order(simulation=self.sim, identifier=i)
            self.sim.data.order_input_counter += 1
            # add the order from the order book, if necessary
            if self.sim.policy_panel.release_technique == "DRACO" or self.sim.policy_panel.dispatching_rule == "FOCUS":
                self.sim.system_state_dispatching.input_order_book(order=order)
            # check replenishment
            if self.sim.policy_panel.material_replenishment == "PoHed":
                self.sim.generation.pooled_hedging_input_check(order=order)
            # release control
            self.sim.release.put_in_pool(order=order)
            # next inter arrival time
            inter_arrival_time = self.random_generator.expovariate(1 / self.mean_time_between_arrivals)
            yield self.sim.env.timeout(inter_arrival_time)
            i += 1
            if self.sim.env.now >= (self.sim.model_panel.WARM_UP_PERIOD + self.sim.model_panel.RUN_TIME) \
                    * self.sim.model_panel.NUMBER_OF_RUNS:
                break
