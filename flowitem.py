import numpy as np


class Order(object):
    def __init__(self,
                 simulation,
                 identifier):
        """
        object having all attributes of the an flow item
        :param simulation: simulation object stored in simulation_model.py
        :return: void
        """
        self.sim = simulation
        self.identifier = identifier
        self.location = "pool"
        self.attributes = self.sim.model_panel.order_attributes
        self.name = f"order_{'%07d' % self.identifier}"
        self.materials = []

        # copy the material list
        material_types = self.sim.model_panel.material_types.copy()
        # settings check
        if len(material_types) < self.sim.model_panel.material_quantity:
            raise Exception("higher quantity requested than possible")

        if self.sim.model_panel.material_request == "constant":
            self.requirements = self.sim.NP_random_generator['inventory'].choice(a=material_types,
                                                                                 size=self.sim.model_panel.material_quantity,
                                                                                 replace=False
                                                                                 )
        elif self.sim.model_panel.material_request == "variable":
            nr_materials = self.sim.NP_random_generator['inventory'].choice(a=np.array(self.sim.model_panel.material_quantity_range),
                                                                            size=1,
                                                                            replace=False) + 1
            self.requirements = self.sim.NP_random_generator['inventory'].choice(a=material_types,
                                                                                 size=nr_materials,
                                                                                 replace=False)
        elif self.sim.model_panel.material_request == "no_materials":
            self.requirements = []
        else:
            raise Exception("no valid material request procedure")

        # material priority
        self.material_priority = 0

        # data params
        self.arrival_time = self.sim.env.now
        self.material_available_time = 0
        self.release_time = 0
        self.pool_time = 0
        self.completion_time = 0
        self.material_replenishment_time = 0
        self.inventory_time = 0

        # pool params
        self.release = False
        self.material_available = False
        self.first_entry = True
        self.in_inventory = False

        # routing sequence params
        if self.sim.model_panel.SHOP_ATTRIBUTES['routing_configuration'] in ["GFS", "PJS"]:
            self.routing_sequence = self.sim.random_generator.sample(
                self.sim.model_panel.MANUFACTURING_FLOOR_LAYOUT,
                self.sim.random_generator.randint(1, len(self.sim.model_panel.MANUFACTURING_FLOOR_LAYOUT)))
            # Sort the routing if necessary
            if self.sim.model_panel.SHOP_ATTRIBUTES['routing_configuration'] == "GFS":
                self.routing_sequence.sort()  # GFS or PFS require sorted list of stations
        elif self.sim.model_panel.SHOP_ATTRIBUTES['routing_configuration'] == "PFS":
            self.routing_sequence = self.sim.model_panel.MANUFACTURING_FLOOR_LAYOUT.copy()
        else:
            raise Exception("no valid manufacturing process selected")

        # Make a variable independent from routing sequence to allow for queue switching
        self.routing_sequence_data = self.routing_sequence[:]

        # process time
        self.process_time = {}
        self.process_time_release = {}
        self.process_time_cumulative = 0
        self.remaining_process_time = 0
        self.material_present = self.material_present()

        # dispatching priority
        self.dispatching_priority = {}
        for i, work_centre in enumerate(self.sim.model_panel.MANUFACTURING_FLOOR_LAYOUT):
            self.dispatching_priority[work_centre] = 0

        # data collection variables
        self.queue_entry_time = {}
        self.proc_finished_time = {}
        self.queue_time = {}
        self.order_start_time = {}
        self.wc_state = {}  # tracks which machine was used

        for WC in self.routing_sequence:
            # process time
            if self.sim.model_panel.PROCESS_TIME_DISTRIBUTION == "2_erlang_truncated":
                self.process_time[WC] = self.sim.general_functions.two_erlang_truncated(
                    mean=self.sim.model_panel.MEAN_PROCESS_TIME
                )
            elif self.sim.model_panel.PROCESS_TIME_DISTRIBUTION == "2_erlang":
                self.process_time[WC] = self.sim.general_functions.two_erlang(
                    mean=self.sim.model_panel.MEAN_PROCESS_TIME
                )
            elif self.sim.model_panel.PROCESS_TIME_DISTRIBUTION == "exponential":
                self.process_time[WC] = self.sim.general_functions.exponential(
                    mean=self.sim.model_panel.MEAN_PROCESS_TIME
                )
            elif self.sim.model_panel.PROCESS_TIME_DISTRIBUTION == "uniform":
                self.process_time[WC] = self.sim.general_functions.uniform(
                    mean=self.sim.model_panel.MEAN_PROCESS_TIME
                )
            else:
                raise Exception("no valid process time distribution selected")

            # general process time variables
            if self.sim.policy_panel.release_process_times == "deterministic":
                self.process_time_release[WC] = self.process_time[WC]
            elif self.sim.policy_panel.release_process_times == "stochastic":
                self.process_time_release[WC] = self.sim.model_panel.MEAN_PROCESS_TIME
            else:
                raise Exception("unknown if process times for release are known or unknown")

            self.process_time_cumulative += self.process_time[WC]
            self.remaining_process_time += self.process_time[WC]

            # order progress data
            self.queue_entry_time[WC] = 0
            self.proc_finished_time[WC] = 0
            self.queue_time[WC] = 0
            self.order_start_time[WC] = 0
            self.wc_state[WC] = "NOT_PASSED"

        # due date
        if self.sim.policy_panel.due_date_method == "random":
            self.due_date = self.sim.general_functions.random_value_DD()
        elif self.sim.policy_panel.due_date_method == "constant":
            self.due_date = self.sim.general_functions.add_constant_DD()
        elif self.sim.policy_panel.due_date_method == "total_work_content":
            self.due_date = self.sim.general_functions.total_work_content(order=self)
        else:
            raise Exception("no valid due date procedure selected")

        # ORR pool sequence rule
        self.pool_priority = 0
        if self.sim.policy_panel.sequencing_rule in ["PRD"]:
            self.pool_priority = self.due_date - (len(self.routing_sequence) *
                                                  self.sim.policy_panel.sequencing_rule_attributes['PRD_k'])
        if self.sim.policy_panel.dispatching_rule == "ODD_land":
            self.ODDs = {}
        return

    def material_present(self):
        if self.sim.inventory.material_check(order=self, fill_rate_check=True):
            return 1
        else:
            return 0

    def update_material_data(self):
        if len(self.materials) > 0:
            material_replenishment_time = []
            inventory_time = []
            for material in self.materials:
                material_replenishment_time.append(material.material_shipping_time)
                inventory_time.append(material.material_commitment_time - material.material_delivery_time)
            self.material_replenishment_time = sum(material_replenishment_time) / len(material_replenishment_time)
            self.inventory_time = sum(inventory_time)
        else:
            self.material_replenishment_time = 0
            self.inventory_time = 0
        return

    def __str__(self):
        return self.name

    def __eq__(self, other):
        return self.identifier == other


class Material(object):
    def __init__(self,
                 simulation,
                 identifier,
                 attributes):
        """
        object having all attributes of the an flow item
        :param simulation: simulation object stored in simulation_model.py
        :return: void
        """
        self.sim = simulation
        self.identifier = identifier
        self.attributes = attributes
        self.type = self.attributes['name']
        self.name = f"material_{self.attributes['name']}_{'%07d' % self.identifier}"

        self.material_arrival_time = self.sim.env.now
        self.material_delivery_time = self.sim.env.now
        self.material_shipping_time = 0
        self.material_commitment_time = 0

    def __str__(self):
        return self.name

    def __eq__(self, other):
        return self.identifier == other
