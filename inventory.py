from operator import itemgetter


class Inventory(object):
    def __init__(self, simulation):
        """
        methods related to inventory operations.
        :param simulation: simulation object
        """
        self.sim = simulation
        self.index_sorting_removal = self.sim.model_panel.index_sorting_removal
        self.index_order_object = self.sim.model_panel.index_order_object
        self.index_priority = self.sim.model_panel.index_priority
        self.materials = self.sim.model_panel.materials
        self.material_sequence = {}
        return

    def put_in_inventory(self, order):
        inventory_item = self.inventory_item(order=order)
        self.sim.model_panel.SKU[order.type].put(inventory_item)
        # update state
        order.in_inventory = True
        # update as material has arrived
        self.inventory_update_release()
        return

    @staticmethod
    def inventory_item(order):
        inventory_item = [1,  # removal integer
                          order,
                          order.material_delivery_time,
                          order.name
                          ]
        return inventory_item

    def remove_from_inventory(self, item):
        """
        removes an order from the queue
        :param work_center: work_center number indicating the number of the capacity source
        :return: void
        """
        # sort the stock keeping unit
        self.sim.model_panel.SKU[item].items.sort(key=itemgetter(self.index_sorting_removal))
        self.sim.model_panel.SKU[item].get()

        # update generation process
        self.sim.generation.check_generation(item_type=item)
        return

    def collect_materials(self, requirements):
        """
        collect materials from inventory, assume that all materials are available
        :param requirements: list with the name of the materials that need to be collected
        :return material_list: return a list with the collected materials
        """
        material_list = []
        for component in requirements:
            # pick component and remove from inventory
            material = self.get_inventory_item(item=component)
            material.material_commitment_time = self.sim.env.now
            # update data and add to material list
            material_list.append(material)
        return material_list

    def get_inventory_item(self, item):
        self.sim.model_panel.SKU[item].items.sort(key=itemgetter(self.index_sorting_removal))
        item_list = self.sim.model_panel.SKU[item].items[0]
        item_list[self.index_sorting_removal] = 0
        self.remove_from_inventory(item=item)
        material = item_list[self.index_order_object]
        return material

    def inventory_availability_check(self, item, amount=1):
        if len(self.sim.model_panel.SKU[item].items) >= amount:
            return True
        else:
            return False

    def material_check(self, order):
        """
        check of the materials are available
        :param requirements: list with the name of the materials that need to be collected
        :return material_list: return a list with the collected materials
        """
        # control material requirements, if none, release
        requirements = order.requirements
        if not len(requirements) == 0:
            # control inventories for the required item
            availability_dict = {}
            # check availability for each item
            for item in requirements:
                # allocate material based on allocation policy
                if self.sim.policy_panel.material_allocation == 'rationing':
                    inventory_level = self.material_sequence[item][order.identifier]
                elif self.sim.policy_panel.material_allocation == 'availability':
                    inventory_level = 1
                else:
                    raise Exception(
                        f'unknown material allocation policy {self.sim.policy_panel.material_allocation_rule}')

                # check materials
                if self.inventory_availability_check(item=item, amount=inventory_level):
                    # inventory available, pick component
                    availability_dict[item] = True
                else:
                    availability_dict[item] = False

            # control if all the orders material requirements are satisfied
            if all(available == True for available in availability_dict.values()):
                # collect data, check if this is the first time when the materials are available
                if not order.material_available:
                    order.material_available_time = self.sim.env.now
                return True
            else:
                # materials not available for this order
                return False
        else:
            # collect data
            if not order.material_available:
                order.material_available_time = self.sim.env.now
            return True

    def inventory_update_release(self):
        if self.sim.policy_panel.release_technique == "DRACO":
            self.sim.system_state_dispatching.full_control_mode(trigger_mode='supply')
        else:
            self.sim.release.activate_release(material_arrival=True)
        return

    def rationing_sequence_update(self):
        # sort the pool
        pool = self.sim.model_panel.POOLS.items.copy()
        pool.sort(key=itemgetter(self.sim.release.index_material_priority))
        # update rationing sequence for each material type
        for material in self.materials:
            # check for each order in the pool
            self.material_sequence[material] = {}
            nr_in_sequence = 1
            for i, pool_order in enumerate(pool):
                order = pool_order[self.index_order_object]
                # material check
                if material in order.requirements:
                    self.material_sequence[material][order.identifier] = nr_in_sequence
                    nr_in_sequence += 1
            # entire pool established
            self.material_sequence[material]['total_demand'] = (nr_in_sequence - 1)
        return
