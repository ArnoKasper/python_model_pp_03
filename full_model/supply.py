from random import Random
from flowitem import Material
from capacity_sources import Machine
import numpy as np


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

        # disruption parameters
        self.start_time_disruption = self.sim.model_panel.RUN_TIME/2
        self.item_type_disrupted = []
        self.pick_disrupted_item()
        return

    def delivery(self, item_type):
        if self.supply_situation == 'parallel':
            self.sim.env.process(self.parallel_delivery(item_type=item_type))
        elif self.supply_situation == 'capacitated':
            self.sim.env.process(self.capacitated_delivery(item_type=item_type))
        return

    def pick_disrupted_item(self):
        material_types = self.sim.model_panel.material_types.copy()
        for run in range(0, self.sim.model_panel.NUMBER_OF_RUNS):
            material = self.sim.NP_random_generator['disruption'].choice(a=material_types, size=1, replace=True)
            self.item_type_disrupted.append(material)
        return

    def disruption_index(self, item_type):
        t = self.sim.env.now
        run_number = int(t / (self.sim.model_panel.WARM_UP_PERIOD + self.sim.model_panel.RUN_TIME)) + 1
        if item_type != self.item_type_disrupted[run_number - 1]:
            # this item is not disrupted
            return 1
        else:
            # check if there is a disruption
            run_start_time = (run_number - 1) * (self.sim.model_panel.WARM_UP_PERIOD + self.sim.model_panel.RUN_TIME)
            disruption_starts = run_start_time + self.sim.model_panel.WARM_UP_PERIOD + self.start_time_disruption
            disruption_ends = disruption_starts + self.sim.model_panel.disruption_duration
            if t < disruption_starts or t > disruption_ends:
                return 1
            else:
                time_evolved = t - disruption_starts
                disruption_index = (self.sim.model_panel.disruption_severity / self.sim.model_panel.disruption_duration)
                return 1 + (disruption_index * (self.sim.model_panel.disruption_duration - time_evolved))

    def parallel_delivery(self, item_type):
        # determine the expected time
        if not self.sim.model_panel.DISRUPTION:
            mean_replenishment_time = self.sim.model_panel.materials[item_type]['expected_lead_time']
        else:
            mean_replenishment_time = self.disruption_index(item_type=item_type) * \
                                      self.sim.model_panel.materials[item_type]['expected_lead_time']
        # get stochastic value
        if self.sim.model_panel.SUPPLY_DISTRIBUTION == 'constant':
            shipping_time = mean_replenishment_time
        elif self.sim.model_panel.SUPPLY_DISTRIBUTION == 'exponential':
            shipping_time = self.sim.NP_random_generator['supply'].exponential(mean_replenishment_time)
        elif self.sim.model_panel.SUPPLY_DISTRIBUTION == 'k_erlang':
            shipping_time = self.sim.NP_random_generator['supply'].gamma(scale=mean_replenishment_time/self.sim.model_panel.supply_k,
                                                                         shape=self.sim.model_panel.supply_k)
        elif self.sim.model_panel.SUPPLY_DISTRIBUTION == 'normal':
            shipping_time = -np.inf
            while shipping_time < 0:
                shipping_time = self.sim.NP_random_generator['supply'].normal(loc=mean_replenishment_time,
                                                                              scale=self.sim.model_panel.supply_sigma)
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
        # determine the expected time
        if not self.sim.model_panel.DISRUPTION:
            mean_replenishment_time = self.sim.model_panel.materials[item_type]['expected_lead_time']
        else:
            mean_replenishment_time = self.disruption_index(item_type=item_type) * \
                                      self.sim.model_panel.materials[item_type]['expected_lead_time']
        # get stochastic value
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
