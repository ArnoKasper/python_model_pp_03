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
            # release control
            self.sim.release.put_in_pool(order=order)
            # next inter arrival time
            inter_arrival_time = self.random_generator.expovariate(1 / self.mean_time_between_arrivals)
            yield self.sim.env.timeout(inter_arrival_time)
            i += 1
            if self.sim.env.now >= (self.sim.model_panel.WARM_UP_PERIOD + self.sim.model_panel.RUN_TIME) \
                    * self.sim.model_panel.NUMBER_OF_RUNS:
                break
