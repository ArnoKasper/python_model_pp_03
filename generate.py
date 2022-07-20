from random import Random
from flowitem import Material


class Generation(object):
    def __init__(self, simulation):
        """
        :param simulation:
        :param stationary:
        """
        self.sim = simulation
        self.random_generator = Random()
        self.random_generator.seed(999999)

        # key params
        self.i = 1
        self.generation_technique = self.sim.policy_panel.generation_technique
        self.generation_attributes = self.sim.policy_panel.generation_attributes

        return

    def initialize_generation(self):
        for item_type, generation in reversed(self.generation_technique.items()):
            if generation == 'BSS':
                # generation via control loop
                self.sim.generation_process[item_type] = "BSS"
                # assume that average is already in inventory, while the other is on its way
                reorder_point = self.generation_attributes[item_type]['reorder_point']
                kick_start = int(reorder_point/2)
                for _ in range(0, kick_start):
                    # make an order
                    generated = self.generate_control_loop(item_type=item_type, warmup=True)
                for _ in range(0, (reorder_point - kick_start)):
                    # make an order
                    generated = self.generate_control_loop(item_type=item_type)
            else:
                raise Exception(f"generation process {self.generation_technique} is not known")

    def generate_control_loop(self, item_type, warmup=False):
        if self.sim.generation_process[item_type] == 'BSS':
            inventory_level = len(self.sim.model_panel.SKU[item_type].items)
            in_process = self.generation_attributes[item_type]['generated'] - self.generation_attributes[item_type]['delivered']

            # determine how material reorder policy
            if self.sim.policy_panel.material_reordering == "arrival":
                material_needs = self.sim.release.material_needs()
                arrival_correction = material_needs[item_type]
            elif self.sim.policy_panel.material_reordering == "release":
                arrival_correction = 0
            else:
                raise Exception(f"material reorder policy unknown")

            # control if loop allows new generation
            if (inventory_level + in_process - arrival_correction) < self.generation_attributes[item_type]['reorder_point']:
                if self.sim.model_panel.DELIVERY == "supplier":
                    if not warmup:
                        self.generate_and_replenish(item_type=item_type)
                    elif warmup:
                        self.generate_and_put_in_inventory(item_type=item_type)
                elif self.sim.model_panel.DELIVERY == "immediate":
                    self.generate_and_put_in_inventory(item_type=item_type)
                else:
                    raise Exception(f"supplier process unknown")
                # add
                self.generation_attributes[item_type]['generated'] += 1
                # generation
                generation = True
            else:
                # no new order is generated
                generation = False
        else:
            # no valid generator
            generation = False
        return generation

    def generate_and_replenish(self, item_type):
        # start supplier process
        self.sim.env.process(self.sim.supplier.delivery(item_type=item_type))
        return

    def generate_and_put_in_inventory(self, item_type):
        # generate new order: create an order object and give it a name
        material = Material(simulation=self.sim,
                            identifier=self.identifier(),
                            attributes=self.sim.model_panel.materials[item_type])
        # put material in inventory
        self.sim.inventory.put_in_inventory(order=material)
        return

    def check_generation(self, item_type):
        generation = True
        if self.sim.generation_process[item_type] == 'BSS':
            # subtract
            self.generation_attributes[item_type]['delivered'] += 1
            # control if new generation is item_type
            while True:
                generation = self.generate_control_loop(item_type=item_type)
                if not generation:
                    # no more new generations
                    break
                else:
                    Exception("BSS wants to reorder more than one item")
        else:
            raise Exception("no valid generation procedure selected")
        return generation

    def identifier(self):
        i = self.i
        self.i += 1
        return i
