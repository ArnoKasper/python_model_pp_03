class Order(object):
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
        self.name = f"order_{self.attributes['name']}_{'%07d' % self.identifier}"
        self.line = self.attributes['line']
        self.requirements = self.attributes['requirements']
        self.material_type = self.attributes['material_type']
        self.item_name = self.attributes['name']
        self.enter_inventory = self.attributes['enter_inventory']
        self.materials = []

        # give customized names
        if self.item_name == 'customized':
            requirements = self.requirements
            self.requirements = self.sim.random_generator.sample(requirements, 1)

        # data params
        self.entry_time = self.sim.env.now
        self.material_available_time = 0
        self.release_time = 0
        self.pool_time = 0
        self.completion_time = 0
        self.inventory_departure_time = 0
        self.demand_time = 0

        # pool params
        self.release = False
        self.material_available = False
        self.first_entry = True
        self.in_inventory = False

        # routing sequence params
        if self.sim.model_panel.LINE_STRUCTURE[self.line]['routing_configuration'] in ["GFS", "PJS"]:
            self.routing_sequence = self.sim.random_generator.sample(
                self.sim.model_panel.MANUFACTURING_FLOOR_LAYOUT[self.line],
                self.sim.random_generator.randint(1, len(self.sim.model_panel.MANUFACTURING_FLOOR_LAYOUT[self.line])))
            # Sort the routing if necessary
            if self.sim.model_panel.LINE_STRUCTURE[self.line]['routing_configuration'] == "GFS":
                self.routing_sequence.sort()  # GFS or PFS require sorted list of stations
        elif self.sim.model_panel.LINE_STRUCTURE[self.line]['routing_configuration'] == "PFS":
            self.routing_sequence = self.sim.model_panel.MANUFACTURING_FLOOR_LAYOUT[self.line].copy()
        else:
            raise Exception("no valid manufacturing process selected")

        # Make a variable independent from routing sequence to allow for queue switching
        self.routing_sequence_data = self.routing_sequence[:]

        # process time
        self.process_time = {}
        self.process_time_cumulative = 0
        self.remaining_process_time = 0

        # priority
        self.dispatching_priority = {}
        for i, work_centre in enumerate(self.sim.model_panel.MANUFACTURING_FLOOR_LAYOUT[self.line]):
            self.dispatching_priority[work_centre] = 0

        # data collection variables
        self.queue_entry_time = {}
        self.proc_finished_time = {}
        self.queue_time = {}
        self.order_start_time = {}
        self.wc_state = {}  # tracks which machine was used

        for WC in self.routing_sequence:
            if self.sim.model_panel.PROCESS_TIME_DISTRIBUTION[self.item_name] == "2_erlang_truncated":
                self.process_time[WC] = self.sim.general_functions.two_erlang_truncated(
                    mean=self.sim.model_panel.MEAN_PROCESS_TIME[self.item_name]
                )
            elif self.sim.model_panel.PROCESS_TIME_DISTRIBUTION[self.item_name] == "exponential":
                self.process_time[WC] = self.sim.general_functions.exponential(
                    mean=self.sim.model_panel.MEAN_PROCESS_TIME[self.item_name]
                )
            elif self.sim.model_panel.PROCESS_TIME_DISTRIBUTION[self.item_name] == "uniform":
                self.process_time[WC] = self.sim.general_functions.uniform(
                    mean=self.sim.model_panel.MEAN_PROCESS_TIME[self.item_name]
                )
            else:
                raise Exception("no valid process time distribution selected")
            self.process_time_cumulative += self.process_time[WC]
            self.remaining_process_time += self.process_time[WC]
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
                                                  self.sim.policy_panel.sequencing_rule_attributes[self.line])

        # coupling params
        self.coupling_priority = self.pool_priority
        self.loose_couplings = []
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
        self.name = f"material_{self.attributes['name']}_{'%07d' % self.identifier}"

    def __str__(self):
        return self.name

    def __eq__(self, other):
        return self.identifier == other