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
        self.items = self.sim.model_panel.items
        self.BOM = self.sim.model_panel.BOM
        self.dependencies = self.sim.model_panel.dependencies

        # settings
        self.allow_backorders = True
        self.backorders = {}

        self.initialize()
        return

    def initialize(self):
        if self.allow_backorders:
            for item in self.items:
                self.backorders[item] = []

    def put_in_inventory(self, order):
        inventory_item = self.inventory_item(order=order)
        self.sim.model_panel.SKU[order.item_name].put(inventory_item)
        # update state
        order.in_inventory = True
        # control backorders
        if self.allow_backorders:
            self.control_backorders(item=order.item_name)
        # update as material has arrived
        self.inventory_update_release(order=order)
        return

    @staticmethod
    def inventory_item(order):
        inventory_item = [1, # removal integer
                          order,
                          order.completion_time,
                          order.item_name
                          ]
        return inventory_item

    def remove_from_inventory(self, item):
        """
        removes an order from the queue
        :param work_center: work_center number indicating the number of the capacity source
        :return: void
        """
        # update generation process
        self.sim.generation.check_generation(item=item)
        # sort the stock keeping unit
        self.sim.model_panel.SKU[item].items.sort(key=itemgetter(self.index_sorting_removal))
        self.sim.model_panel.SKU[item].get()
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
            # update data and add to material list
            material_list.append(material)
        return material_list

    def get_inventory_item(self, item, demand_time=0):
        self.sim.model_panel.SKU[item].items.sort(key=itemgetter(self.index_sorting_removal))
        item_list = self.sim.model_panel.SKU[item].items[0]
        item_list[self.index_sorting_removal] = 0
        self.remove_from_inventory(item=item)
        order = item_list[self.index_order_object]
        # collect data
        if order.enter_inventory:
            order.inventory_departure_time = self.sim.env.now
            order.demand_time = demand_time
            self.sim.process.data_collection_final(order=order, line=order.line)
        return order

    def material_availability_check(self, order, line):
        """
        check of the materials are available
        :param requirements: list with the name of the materials that need to be collected
        :return material_list: return a list with the collected materials
        """
        # control material requirements, if none, release
        requirements = order.requirements
        if not len(requirements) == 0:
            # control inventories for requirements
            if self.sim.policy_panel.material_allocation[line] == 'availability':
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

    def inventory_update_release(self, order):
        initialize_release = self.dependencies[order.item_name]
        for item, attributes in self.BOM.items():
            if item in initialize_release:
                line = attributes['line']
                self.sim.release.activate_release(line=line)
        return

    def control_backorders(self, item):
        if len(self.backorders[item]) > 0:
            # pick backorders, assume FCFS
            customer = self.backorders[item].pop(0)
            delivered_order = self.get_inventory_item(item=item, demand_time=customer.customer_arrival_time)
            customer.order.append(delivered_order)
        return

    def inventory_priority(self, item):
        stock_levels = len(self.sim.model_panel.SKU[item].items)
        return stock_levels / self.sim.policy_panel.generation_attributes[item]['generation_target']
