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
        self.NUMBER_OF_RUNS: int = 100  # number of replications

        # manufacturing process and order characteristics
        self.SHOP_ATTRIBUTES = {"work_centres": 6,
                                'routing_configuration': 'PJS'}
        # manufacturing system
        self.MANUFACTURING_FLOOR_LAYOUT: List[str, ...] = []
        # make pool
        self.POOLS: Pool = Pool(sim=self.sim,
                                env=self.sim.env,
                                id=f"pool"
                                )
        # make work centers
        self.WORK_CENTRES: Dict[...] = {}
        self.QUEUES: Dict[...] = {}
        for i in range(0, self.SHOP_ATTRIBUTES["work_centres"]):
            # construct layout
            self.MANUFACTURING_FLOOR_LAYOUT.append(f'WC{i}')
            # add machines
            self.WORK_CENTRES[f'WC{i}']: Machine = Machine(sim=self.sim,
                                                           env=self.sim.env,
                                                           capacity_slots=1,
                                                           id=f"WC{i}"
                                                           )
            # add queues
            self.QUEUES[f'WC{i}']: Queue = Queue(sim=self.sim,
                                                 env=self.sim.env,
                                                 id=f"WC{i}"
                                                 )

        # set inter arrival time
        self.AIMED_UTILIZATION: float = 0.9
        self.MEAN_PROCESS_TIME: float = 1
        self.MEAN_TIME_BETWEEN_ARRIVAL = self.general_functions.arrival_time_calculator(
            wc_and_flow_config=self.SHOP_ATTRIBUTES['routing_configuration'],
            manufacturing_floor_layout=self.MANUFACTURING_FLOOR_LAYOUT,
            aimed_utilization=self.AIMED_UTILIZATION,
            mean_process_time=self.MEAN_PROCESS_TIME,
            number_of_machines=1)

        # queue and pool sorting control keys
        self.index_sorting_removal = 0
        self.index_order_object = 1
        self.index_priority = 2

        """
        process time distributions
            - 2_erlang_truncated
            - exponential
            - uniform
        """
        self.PROCESS_TIME_DISTRIBUTION = '2_erlang_truncated' # 'exponential' # '2_erlang' #

        # orders
        """
        - material quantity needed
            - 1, 2, 3
        - material request
            - constant: each order request the same number of items
            - variable: each order request a variable number of items
            - no_materials: no material needs, for debugging
        """
        self.material_requirements_distribution = 'uniform'
        self.material_quantity = 2
        self.material_request = 'constant'

        self.order_attributes = {"name": "customized",
                                 "order_type": 'customized',
                                 'enter_inventory': False,
                                 "generation": 'demand',
                                 'expected_mean': self.MEAN_PROCESS_TIME}

        # materials
        self.SKU: Dict[...] = {}
        self.material_types = ['A', 'B', 'C', 'D', 'E', "F"]
        # self.material_types = ['A']
        self.materials = {}
        self.expected_replenishment_time = 5
        for type in self.material_types:
            self.materials[type] = {'name': f'{type}',
                                    'enter_inventory': True,
                                    "generation": 'BSS',
                                    'expected_lead_time': self.expected_replenishment_time}
            self.SKU[type]: Inventory = Inventory(sim=self.sim,
                                                  env=self.sim.env,
                                                  id=f"{type}"
                                                  )
        """
        - immediate, i.e., replenishment time is zero.
        - supplier, i.e., replenishment time is non-zero
        """
        self.DELIVERY = "supplier" # "immediate"
        self.SUPPLY_DISTRIBUTION = 'exponential'
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
        self.due_date_method: str = 'constant'
        self.DD_constant_value: float = 42
        self.DD_random_min_max: List[int, int] = [30, 52]
        self.DD_total_work_content_value: float = 10

        # generation
        """
        types of generation techniques
            - BSS (base-stock system)
        """
        self.generated = {}
        self.delivered = {}
        self.generation_technique = {}
        self.generation_attributes = {}
        """
                    
        material_reordering: when to send a replenishment order
            - release
            - arrival 
        """
        self.material_reordering = 'arrival'

        # assume that all orders have the same generation process
        for type, material in self.sim.model_panel.materials.items():
            self.generation_technique[type] = material['generation']
            self.generation_attributes[type] = GENERATION_TECHNIQUE_ATTRIBUTES[material['generation']].copy()

        # release
        """
        types of release techniques
            - immediate
            - DRACO
            - CONWIP
            - CONLOAD
            - WLC: pure_periodic_release
            - WLC: pure_continuous release
            - WLC: LUMS_COR
        
        for methods that use process time
            - stochastic 
            - deterministic 
        
        types of release sequencing rules
            - FCFS
            - PRD
            - EDD
            - SPT
        """
        # release technique
        # self.release_technique = "DRACO"
        self.release_technique = "immediate"
        # self.release_technique = "LUMS_COR"
        self.release_technique_attributes = RELEASE_TECHNIQUE_ATTRIBUTES[self.release_technique].copy()
        self.release_process_times = 'deterministic'

        # tracking variables
        self.released = 0
        self.completed = 0
        self.release_target = 18

        # pool rule
        self.sequencing_rule = "PRD"
        self.sequencing_rule_attributes = POOL_RULE_ATTRIBUTES["PRD"].copy()

        # dispatching
        """
        dispatching rules available
            - FCFS
            - FISFO
            - SLACK
            - SPT
            - ODD_land, following Land et al. (2014)
            - FOCUS, following Kasper et al. (2023)
        """
        self.dispatching_mode = "priority_rule"
        self.dispatching_rule = "FCFS" # "FOCUS" #

        # material allocation
        """
        material allocation
            - availability
            - rationing
                - requires a rationing rule
                    - FCFS
                    - SPT
                    - FOCUS
        """
        self.material_allocation = "availability"
        self.rationing_rule = "FCFS"
        return


GENERATION_TECHNIQUE_ATTRIBUTES = {
    'exponential': {},
    'BSS': {'reorder_point': 8, 'generated': 0, 'delivered': 0},
}

RELEASE_TECHNIQUE_ATTRIBUTES = {

    'immediate': {'tracking_variable': 'none',
                  'measure': 'none',
                  'periodic': False,
                  'continuous': True,
                  'trigger': False,
                  'non_hierarchical': False},
    'DRACO': {'tracking_variable': 'total',
              'measure': 'WIP',
              'periodic': False,
              'continuous': False,
              'trigger': False,
              'non_hierarchical': True},
    'CONWIP': {'tracking_variable': 'total',
               'measure': 'WIP',
               'periodic': False,
               'continuous': True,
               'trigger': False,
               'non_hierarchical': False},
    'CONWIP_trig': {'tracking_variable': 'total',
                    'measure': 'WIP',
                    'periodic': False,
                    'continuous': True,
                    'trigger': True,
                    'non_hierarchical': False},
    'CONLOAD': {'tracking_variable': 'total',
                'measure': 'workload',
                'periodic': False,
                'continuous': True,
                'trigger': False,
                'non_hierarchical': False},
    'pure_periodic_release': {'tracking_variable': 'work_centre',
                              'measure': 'workload',
                              'periodic': True,
                              'continuous': False,
                              'trigger': False,
                              'check_period': 4,
                              'non_hierarchical': False},
    'LUMS_COR': {'tracking_variable': 'work_centre',
                 'measure': 'workload',
                 'periodic': True,
                 'continuous': False,
                 'trigger': True,
                 'check_period': 4,
                 'non_hierarchical': False}
}

POOL_RULE_ATTRIBUTES = {
    'FCFS': {},
    'PRD': {'PRD_k': 4},
    'EDD': {},
}
