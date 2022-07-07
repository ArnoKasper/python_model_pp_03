from random import Random

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

        self.mean_time_between_demand = (1/self.sim.model_panel.DEMAND_RATE) * self.mean_demand_quantity
        return

    def generate_random_demand_exp(self, item):
        i = 1
        while True:
            # count demand
            self.sim.data.demanded_items_counter += 1
            customer = Customer(simulation=self.sim, item=item)
            customer.item = item
            # control if demand is available
            if len(self.sim.model_panel.SKU[item].items) >= self.inventory_threshold:
                # inventory available, pick order and deliver, yay!
                delivered_order = self.sim.inventory.get_inventory_item(item=item, demand_time=self.sim.env.now)
                customer.order.append(delivered_order)
                # collect data
                self.sim.data.demanded_items_fulfilled += 1
            else:
                # nah, customer must wait, add to backorder list
                if self.sim.inventory.allow_backorders:
                    self.sim.inventory.backorders[item].append(customer)

            # find next demand time
            if self.sim.model_panel.DEMAND_TYPE == 'constant':
                inter_demand_time = self.mean_time_between_demand
            elif self.sim.model_panel.DEMAND_TYPE == 'exponential':
                inter_demand_time = self.sim.random_generator.expovariate(1 / self.mean_time_between_demand)
            elif self.sim.model_panel.DEMAND_TYPE == 'exponential_quantity':
                inter_demand_time = self.sim.random_generator.expovariate(1 / self.mean_time_between_demand)
                raise NotImplementedError(f'self.sim.model_panel.DEMAND_TYPE {self.sim.model_panel.DEMAND_TYPE}')
            else:
                raise Exception("no valid demand technique chosen")

            yield self.sim.env.timeout(inter_demand_time)
            i += 1
            # break statement
            if self.sim.env.now >= (self.sim.model_panel.WARM_UP_PERIOD + self.sim.model_panel.RUN_TIME) \
                    * self.sim.model_panel.NUMBER_OF_RUNS:
                break


class Customer(object):
    def __init__(self, simulation, item):
        """
        methods related to the customer
        :param simulation: simulation object
        """
        self.sim = simulation
        self.item = item

        # orders
        self.order = []

        # data params
        self.customer_arrival_time = self.sim.env.now
        self.customer_departure_time = 0
        return