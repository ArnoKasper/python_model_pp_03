from random import Random
from flowitem import Material


class Supply(object):
    def __init__(self, simulation):
        self.sim = simulation
        self.random_generator: Random = Random()
        self.random_generator.seed(999999)
        self.mean_replenishment_time = self.sim.model_panel.expected_replenishment_time
        return

    def delivery(self, item_type):
        mean_replenishment_time = self.sim.model_panel.materials[item_type]['expected_lead_time']
        if self.sim.model_panel.SUPPLY_DISTRIBUTION == 'constant':
            replenishment_time = mean_replenishment_time
        elif self.sim.model_panel.SUPPLY_DISTRIBUTION == 'exponential':
            replenishment_time = self.sim.random_generator.expovariate(1 / mean_replenishment_time)
        else:
            raise Exception(f'unknown replenishment time distribution')
        # get material expected_lead_time
        material = Material(simulation=self.sim,
                            identifier=self.sim.generation.identifier(),
                            attributes=self.sim.model_panel.materials[item_type])
        # find replenishment time
        yield self.sim.env.timeout(replenishment_time)
        # determine delivery time
        material.delivery_time = self.sim.env.now
        material.replenishment_time = replenishment_time
        # put in inventory
        self.sim.inventory.put_in_inventory(order=material)
        return

