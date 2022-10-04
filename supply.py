from random import Random
from flowitem import Material
from capacity_sources import Machine


class Supply(object):
    def __init__(self, simulation):
        self.sim = simulation
        self.random_generator: Random = Random()
        self.random_generator.seed(999999)
        self.mean_replenishment_time = self.sim.model_panel.expected_replenishment_time

        """
        supply process
            - parallel 
            - capacitated
        """
        self.supply_situation = 'parallel'

        # make supplier
        if self.supply_situation == 'capacitated':
            self.supplier = Machine(sim=self.sim,
                                    env=self.sim.env,
                                    capacity_slots=1,
                                    id=f"supplier"
                                    )
        return

    def delivery(self, item_type):
        if self.supply_situation == 'parallel':
            self.sim.env.process(self.parallel_delivery(item_type=item_type))
        elif self.supply_situation == 'capacitated':
            self.sim.env.process(self.capacitated_delivery(item_type=item_type))
        return

    def parallel_delivery(self, item_type):
        mean_replenishment_time = self.sim.model_panel.materials[item_type]['expected_lead_time']
        if self.sim.model_panel.SUPPLY_DISTRIBUTION == 'constant':
            shipping_time = mean_replenishment_time
        elif self.sim.model_panel.SUPPLY_DISTRIBUTION == 'exponential':
            shipping_time = self.sim.NP_random_generator['supply'].exponential(mean_replenishment_time)
        else:
            raise Exception(f'unknown replenishment time distribution')
        # get material expected_lead_time
        material = Material(simulation=self.sim,
                            identifier=self.sim.generation.identifier(),
                            attributes=self.sim.model_panel.materials[item_type])
        # find replenishment time
        yield self.sim.env.timeout(shipping_time)
        # determine delivery time
        material.material_delivery_time = self.sim.env.now
        material.material_shipping_time = shipping_time
        # put in inventory
        self.sim.inventory.put_in_inventory(material=material)
        return

    def capacitated_delivery(self, item_type):
        mean_replenishment_time = self.sim.model_panel.materials[item_type]['expected_lead_time']
        if self.sim.model_panel.SUPPLY_DISTRIBUTION == 'constant':
            shipping_time = mean_replenishment_time
        elif self.sim.model_panel.SUPPLY_DISTRIBUTION == 'exponential':
            shipping_time = self.sim.NP_random_generator['supply'].exponential(mean_replenishment_time)
        else:
            raise Exception(f'unknown replenishment time distribution')
        # get material expected_lead_time
        material = Material(simulation=self.sim,
                            identifier=self.sim.generation.identifier(),
                            attributes=self.sim.model_panel.materials[item_type])
        # find replenishment time
        req = self.supplier.request(priority=self.sim.env.now)
        # yield a request
        with req as req:
            yield req
            # Request is finished, order directly processed
            yield self.sim.env.timeout(shipping_time)
        # determine delivery time
        material.material_delivery_time = self.sim.env.now
        material.material_shipping_time = shipping_time
        # put in inventory
        self.sim.inventory.put_in_inventory(material=material)
        return
