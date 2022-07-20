from operator import itemgetter


class Inventory(object):
    def __init__(self, simulation):
        """
        methods related to inventory operations.
        :param simulation: simulation object
        """
        self.sim = simulation
        self.index_sorting_removal = 0
        self.index_order_object = 1
        self.index_priority = 2
        self.materials = self.sim.model_panel.materials

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
        inventory_item = [1, # removal integer
                          order,
                          order.delivery_time,
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
            material.allocation_time = self.sim.env.now
            # update data and add to material list
            material_list.append(material)
        return material_list

    def get_inventory_item(self, item, demand_time=0):
        self.sim.model_panel.SKU[item].items.sort(key=itemgetter(self.index_sorting_removal))
        item_list = self.sim.model_panel.SKU[item].items[0]
        item_list[self.index_sorting_removal] = 0
        self.remove_from_inventory(item=item)
        order = item_list[self.index_order_object]
        return order

    def material_availability_check(self, order):
        """
        check of the materials are available
        :param requirements: list with the name of the materials that need to be collected
        :return material_list: return a list with the collected materials
        """
        # control material requirements, if none, release
        requirements = order.requirements
        if not len(requirements) == 0:
            # control inventories for requirements
            if self.sim.policy_panel.material_allocation == 'availability':
                material_availability_dict = {}
                for item in requirements:
                    # assume unique stock keeping unit for each item
                    if len(self.sim.model_panel.SKU[item].items) != 0:
                        # inventory available, pick component
                        material_availability_dict[item] = True
                    else:
                        material_availability_dict[item] = False
            else:
                raise Exception(f'unknown material availability rule {self.sim.policy_panel.material_allocation_rule}')
            # control if material requirements are satisfied, if not continue
            if all(available == True for available in material_availability_dict.values()):
                # collect data
                if not order.material_available:
                    order.material_available_time = self.sim.env.now
                return True
            else:
                return False
        else:
            # collect data
            if not order.material_available:
                order.material_available_time = self.sim.env.now
            return True

    def inventory_update_release(self):
        self.sim.release.activate_release(material_arrival=True)
        return

