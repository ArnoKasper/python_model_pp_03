from typing import Dict, List, ClassVar
from generalfunctions import GeneralFunctions
from capacity_sources import Machine, Queue, Pool, Inventory


class ModelPanel(object):
    def __init__(self, experiment_number: int, simulation: ClassVar) -> None:
        self.experiment_number: int = experiment_number
        self.sim: ClassVar = simulation
        self.print_info: bool = True
        self.print_results: bool = True
        self.general_functions: GeneralFunctions = GeneralFunctions(simulation=self.sim)

        # project names
        self.project_name: str = "InnsbrückProject"
        self.experiment_name: str = self.project_name + "_"

        # simulation parameters
        self.WARM_UP_PERIOD: int = 3000  # warm-up period simulation model
        self.RUN_TIME: int = 10000  # run time simulation model
        self.NUMBER_OF_RUNS: int = 1  # 00  # number of replications

        # process and arrival times
        self.AIMED_UTILIZATION: float = 0.9
        self.ORDER_MEAN_PROCESS_TIME: float = 1

        # manufacturing process and order characteristics
        self.LINE_STRUCTURE = {'line_1': {'work_centres': 1,
                                          'routing_configuration': 'PFS',
                                          'release_technique': 'immediate'},
                               'line_2': {"work_centres": 1,
                                          'routing_configuration': 'PFS',
                                          'release_technique': 'immediate'}
                               }
        # manufacturing system
        self.MEAN_TIME_BETWEEN_ARRIVAL: Dict[...] = {}
        self.MANUFACTURING_FLOOR_LAYOUT: Dict[...] = {}
        self.WORK_CENTRES: Dict[...] = {}  # The manufacturing floor floor
        self.QUEUES: Dict[...] = {}
        self.POOLS: Dict[...] = {}
        for line, attributes in self.LINE_STRUCTURE.items():
            self.MANUFACTURING_FLOOR_LAYOUT[line]: List[str, ...] = []
            # make line pool
            self.POOLS[line]: Pool = Pool(sim=self.sim,
                                          env=self.sim.env,
                                          id=f"{line}"
                                          )
            # make work centers
            self.WORK_CENTRES[line]: Dict[...] = {}
            self.QUEUES[line]: Dict[...] = {}
            for i in range(0, attributes["work_centres"]):
                # construct layout
                self.MANUFACTURING_FLOOR_LAYOUT[line].append(f'WC{i}')
                # add machines
                self.WORK_CENTRES[line][f'WC{i}']: Machine = Machine(sim=self.sim,
                                                                     env=self.sim.env,
                                                                     capacity_slots=1,
                                                                     id=f"WC{i}"
                                                                     )
                # add queues
                self.QUEUES[line][f'WC{i}']: Queue = Queue(sim=self.sim,
                                                           env=self.sim.env,
                                                           id=f"WC{i}"
                                                           )

            # set interarrival time
            self.MEAN_TIME_BETWEEN_ARRIVAL[line] = self.general_functions.arrival_time_calculator(
                wc_and_flow_config=self.LINE_STRUCTURE[line]['routing_configuration'],
                manufacturing_floor_layout=self.MANUFACTURING_FLOOR_LAYOUT[line],
                aimed_utilization=self.AIMED_UTILIZATION,
                mean_process_time=self.ORDER_MEAN_PROCESS_TIME,
                number_of_machines=1)

        # bill of materials
        self.component_items = ['A', 'B']
        self.BOM = {"customized": {"name": "customized",
                                   "material_type": 'customized',
                                   "requirements": self.component_items,
                                   'enter_inventory': False,
                                   "generation": 'exponential',
                                   'expected_mean': self.ORDER_MEAN_PROCESS_TIME,
                                   "line": "line_1"}
                    }

        item_mean_process_time = round(
            self.MEAN_TIME_BETWEEN_ARRIVAL['line_1']/self.MEAN_TIME_BETWEEN_ARRIVAL['line_2'], 5)
        component_item = {'name': '',
                          "material_type": "end",
                          "requirements": [],
                          'enter_inventory': True,
                          "generation": 'control_loop',
                          'expected_mean': item_mean_process_time,
                          "line": "line_2"}

        # make BOM complete
        for item in self.component_items:
            component_item['name'] = item
            self.BOM[item] = component_item.copy()

        self.items = []
        self.dependencies = None
        self.build_dependencies()

        # make item-specific stock keeping units (SKU)
        self.SKU: Dict[...] = {}
        self.MEAN_PROCESS_TIME: Dict[...] = {}
        self.PROCESS_TIME_DISTRIBUTION: Dict[...] = {}
        self.STD_DEV_PROCESS_TIME: Dict[...] = {}
        for item in self.BOM.keys():
            self.MEAN_PROCESS_TIME[item] = self.BOM[item]['expected_mean']
            self.PROCESS_TIME_DISTRIBUTION[item] = 'exponential'
            self.STD_DEV_PROCESS_TIME[item] = 0.5
            self.SKU[item]: Inventory = Inventory(sim=self.sim,
                                                  env=self.sim.env,
                                                  id=f"{item}"
                                                  )

        # demand
        """
        demand types
            - constant
            - exponential
            - exponential_quantity
            - forecast (not implemented)
        """
        self.DEMAND_RATE: float = 0.9
        self.DEMAND_TYPE: str = 'exponential'
        return

    def build_dependencies(self):
        # get all items
        for item, attributes in self.BOM.items():
            self.items.append(item)
        # make dependencies
        dependencies = {}
        for component in reversed(self.items):
            dependencies[component] = []
            for item, attributes in self.BOM.items():
                # check if component is needed for product
                if component in attributes['requirements']:
                    dependencies[component].append(item)
        self.dependencies = dependencies
        return


class PolicyPanel(object):
    def __init__(self, experiment_number: int, simulation) -> None:
        self.sim = simulation
        self.experiment_number: int = experiment_number

        # due date determination
        """
        due date procedure
            - random
            - constant
            - total_work_content
        """
        self.due_date_method: str = 'random'
        self.DD_constant_value: float = 42
        self.DD_random_min_max: List[int, int] = [30, 52]
        self.DD_factor_K_value: int = 12
        self.DD_total_work_content_value: float = 8

        # generation
        """
        types of generation techniques
            - constant
            - exponential
            - control_loop
            - MRP
            - dynamic_coupling
        """
        self.generation_technique = {}
        self.generated = {}
        self.delivered = {}
        self.generation_target = {}
        self.generation_attributes = {}

        # assume that all orders have the same generation process
        for item, attributes in self.sim.model_panel.BOM.items():
            self.generation_technique[item] = {'technique': attributes["generation"], 'line': attributes["line"]}
            self.generation_attributes[item] = GENERATION_TECHNIQUE_ATTRIBUTES[attributes['generation']].copy()

        # release
        """
        types of release techniques
            - immediate
            - CONWIP
            - CONLOAD
            - WLC: pure_periodic_release
            - WLC: pure_continuous release
            - WLC: LUMS_COR
            
        types of release sequencing rules
            - FCFS
            - PRD
            - EDD
            - SPT
            - INVENTORY (requires inventory)
        """
        # release technique
        self.release_technique = {}
        self.release_technique_attributes = {}
        self.release_target = {}
        # tracking variables
        self.released = {}
        self.completed = {}
        # pool rule
        self.sequencing_rule = {}
        self.sequencing_rule_attributes = {}
        # set for all lines
        for line, attributes in self.sim.model_panel.LINE_STRUCTURE.items():
            # release technique
            self.release_technique[line] = attributes['release_technique']
            self.release_technique_attributes[line] = RELEASE_TECHNIQUE_ATTRIBUTES[attributes['release_technique']].copy()
            # tracking variables
            self.released[line] = 0
            self.completed[line] = 0
            self.release_target[line] = 30
            # pool rule
            self.sequencing_rule[line] = "PRD"
            self.sequencing_rule_attributes[line] = POOL_RULE_ATTRIBUTES["PRD"].copy()

        # set line specific release loops
        self.release_target['line_1'] = 7
        self.release_target['line_2'] = 20

        self.sequencing_rule['line_1'] = "PRD"
        self.sequencing_rule['line_2'] = "INVENTORY"


        # dispatching
        """
        dispatching rules available
            - FCFS
            - SLACK
            - INVENTORY (requires inventory)
        """
        self.dispatching_mode = {'line_1': "priority_rule", 'line_2': "priority_rule"}
        self.dispatching_rule = {'line_1': "FCFS", 'line_2': "FCFS"}

        # material allocation
        """
        material allocation
            - availability
            
        """
        self.material_allocation = {'line_1': "availability", 'line_2': "availability"}
        return


GENERATION_TECHNIQUE_ATTRIBUTES = {
    'exponential': {},
    'control_loop': {'generation_target': 10, 'generated': 0, 'delivered': 0},
}

RELEASE_TECHNIQUE_ATTRIBUTES = {
    'immediate': {'tracking_variable': 'none',
                  'measure': 'none',
                  'periodic': False,
                  'continuous': True,
                  'trigger': False},
    'CONWIP': {'tracking_variable': 'total',
               'measure': 'WIP',
               'periodic': False,
               'continuous': True,
               'trigger': False},
    'CONLOAD': {'tracking_variable': 'total',
                'measure': 'workload',
                'periodic': False,
                'continuous': True,
                'trigger': False},
    'pure_periodic_release': {'tracking_variable': 'work_centre',
                              'measure': 'workload',
                              'periodic': True,
                              'continuous': False,
                              'trigger': False,
                              'check_period': 4},
    'LUMS_COR': {'tracking_variable': 'work_centre',
                 'measure': 'workload',
                 'periodic': True,
                 'continuous': True,
                 'trigger': True,
                 'check_period': 4},
}

POOL_RULE_ATTRIBUTES = {
    'FCFS': {},
    'PRD': {'PRD_k': 4},
}
