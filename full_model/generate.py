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
        for item_type, generation in self.generation_technique.items():
            if generation == 'order_up_to':
                # generation via control loop
                self.sim.generation_process[item_type] = "order_up_to"
                # assume that average is already in inventory, while the other is on its way
                reorder_point = self.sim.policy_panel.reorder_level
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
        if self.sim.generation_process[item_type] == 'order_up_to':
            on_hand_k = self.sim.inventory.on_hand_inventory[item_type]
            in_process_k = self.generation_attributes[item_type]['generated'] - self.generation_attributes[item_type]['delivered']
            on_order_k = in_process_k - on_hand_k
            backorders = self.backorder()
            backorder_k = backorders[item_type]

            # determine how material reorder policy
            if self.sim.policy_panel.material_replenishment == "PoHed":
                advance_replenishments = self.pooled_hedging()
                reorder_correction = advance_replenishments[item_type]
            elif self.sim.policy_panel.material_replenishment == "ExHed":
                advance_replenishments = self.external_hedging()
                reorder_correction = advance_replenishments[item_type]
            else:
                raise Exception(f"material replenishment policy unknown")

            # determine basic order-up-to variables
            inventory_positions = on_hand_k + on_order_k - backorder_k
            order_up_to = reorder_correction + self.sim.policy_panel.reorder_level + 1

            # control if loop allows new generation
            # if (on_hand_k + on_order_k - pool_correction) < self.sim.policy_panel.reorder_level + 1:
            if inventory_positions < order_up_to:
                if self.sim.model_panel.DELIVERY == "supplier":
                    if not warmup:
                        # send a replenishment order ot the supplier
                        self.generate_and_replenish(item_type=item_type)
                    elif warmup:
                        # for warmup, the orders are directly placed in the inventory
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
        self.sim.supplier.delivery(item_type=item_type)
        return

    def generate_and_put_in_inventory(self, item_type):
        # generate new order: create an order object and give it a name
        material = Material(simulation=self.sim,
                            identifier=self.identifier(),
                            attributes=self.sim.model_panel.materials[item_type])
        # put material in inventory
        self.sim.inventory.put_in_inventory(material=material)
        return

    def check_generation(self, item_type):
        generation = True
        if self.sim.generation_process[item_type] == 'order_up_to':
            # subtract
            self.generation_attributes[item_type]['delivered'] += 1
            # control if new generation is item_type
            while True:
                generation = self.generate_control_loop(item_type=item_type)
                if not generation:
                    # no more new generations
                    break
                else:
                    Exception("order_up_to wants to reorder more than one item")
        else:
            raise Exception("no valid generation procedure selected")
        return generation

    def identifier(self):
        i = self.i
        self.i += 1
        return i

    def external_hedging(self):
        # specify material needs for each item
        advance_replenishments = {}
        for item_type, material in self.sim.model_panel.materials.items():
            advance_replenishments[item_type] = 0
        return advance_replenishments

    def pooled_hedging(self):
        # specify material needs for each item
        advance_replenishments = {}
        for item_type, material in self.sim.model_panel.materials.items():
            advance_replenishments[item_type] = 0
        # no material needs
        if len(self.sim.model_panel.POOLS.items) == 0:
            return advance_replenishments
        # determine the material needs
        pool_list = self.sim.model_panel.POOLS.items
        for pool_item in pool_list:
            order = pool_item[self.sim.release.index_order_object]
            # check if the order requires this material type
            for requirement in order.requirements:
                # check if pool time is within replenishment lead time
                L_R_k = self.sim.model_panel.materials[requirement]['expected_lead_time']
                # check if replenishment is necessary
                if order.planned_release_time - L_R_k <= self.sim.env.now:
                    advance_replenishments[requirement] += 1
                # else: early demand, do not replenish
        return advance_replenishments

    def pooled_hedging_input_check(self, order):
        for requirement in order.requirements:
            L_R_k = self.sim.model_panel.materials[requirement]['expected_lead_time']
            o_i = order.planned_release_time - self.sim.env.now
            # check if this is early demand
            if o_i > L_R_k:
                self.sim.env.process(self.pooled_hedging_early_demand(order=order, material_k=requirement))
        return

    def pooled_hedging_early_demand(self, order, material_k):
        L_R_k = self.sim.model_panel.materials[material_k]['expected_lead_time']
        replenishment_time = order.planned_release_time - L_R_k
        yield self.sim.env.timeout(replenishment_time)
        # initiate replenishment
        generation = self.generate_control_loop(item_type=material_k)
        return

    def backorder(self):
        # specify material needs for each item
        on_hand = {}
        backorders = {}
        for item_type, material in self.sim.model_panel.materials.items():
            on_hand[item_type] = self.sim.inventory.on_hand_inventory[item_type]
            backorders[item_type] = 0
        # no material needs
        if len(self.sim.model_panel.POOLS.items) == 0:
            return backorders
        # determine the material needs
        pool_list = self.sim.model_panel.POOLS.items
        for pool_item in pool_list:
            order = pool_item[self.sim.release.index_order_object]
            # check if the order requires this material type
            for requirement in order.requirements:
                # check if replenishment is necessary
                if order.planned_release_time <= self.sim.env.now and on_hand[requirement] == 0:
                    backorders[requirement] += 1
        return backorders
