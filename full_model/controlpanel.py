from typing import Dict, List, ClassVar
from generalfunctions import GeneralFunctions
from capacity_sources import Machine, Queue, Pool, Inventory
import exp_paramaters as parameters


class ModelPanel(object):
    def __init__(self, experiment_number: int, simulation: ClassVar) -> None:
        self.experiment_number: int = experiment_number
        self.sim: ClassVar = simulation
        self.print_info: bool = True
        self.print_results: bool = True
        experimental_params_dict = parameters.get_interactions()
        self.params_dict: Dict[...] = experimental_params_dict[self.experiment_number]
        self.general_functions: GeneralFunctions = GeneralFunctions(simulation=self.sim)

        # project names
        self.project_name: str = "Innsbruck"
        self.experiment_name: str = self.project_name + "_"
        self.names_variables = ["name",
                                'release_technique',
                                "material_complexity",
                                "material_replenishment",
                                "material_allocation",
                                "release_target",
                                "holding_cost",
                                "WIP_cost",
                                "earliness_cost",
                                "tardiness_cost"
                                ]
        self.indexes = self.names_variables.copy()
        self.experiment_name: str = f'{self.project_name}_'
        for i in self.indexes:
            self.experiment_name += str(self.params_dict[i]) + "_"

        # simulation parameters
        self.WARM_UP_PERIOD: int = 5000  # warm-up period simulation model
        self.RUN_TIME: int = 10000  # run time simulation model
        self.NUMBER_OF_RUNS: int = 5  # 150  # number of replications

        # manufacturing process and order characteristics
        self.SHOP_ATTRIBUTES = {"work_centres": 6,
                                'routing_configuration': "GFS"
                                }
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
            - 2_erlang
            - exponential
            - uniform
        """
        self.PROCESS_TIME_DISTRIBUTION = '2_erlang'

        # orders
        """
        - material quantity needed
            - 1, 2, 3
        - material request
            - constant: each order request the same number of items
            - variable: each order request a variable number of items
            - no_materials: no material needs, for debugging
        """
        self.material_types = ['A', 'B', 'C', 'D', 'E']
        self.material_requirements_distribution = 'uniform'
        self.material_quantity = self.params_dict["material_complexity_dict"]["material_quantity"]
        self.material_quantity_range = [*range(1, len(self.material_types) + 1)]
        self.material_request = self.params_dict["material_complexity_dict"]["material_request"]

        self.order_attributes = {"name": "customized",
                                 "order_type": 'customized',
                                 'enter_inventory': False,
                                 "generation": 'demand',
                                 'expected_mean': self.MEAN_PROCESS_TIME}

        # materials
        self.SKU: Dict[...] = {}
        self.materials = {}
        self.expected_replenishment_time = 50
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
        supply modes
            - immediate, i.e., replenishment time is zero.
            - supplier, i.e., replenishment time is non-zero
        supply distributions
            - constant
            - exponential
            - normal
                - need to define sigma
            - k_erlang
                need to define k
        """
        self.DELIVERY = "supplier"  # "immediate"
        self.SUPPLY_DISTRIBUTION = 'normal'
        self.supply_k = 2
        self.supply_sigma = 10
        # disruption
        self.DISRUPTION = False
        self.disruption_severity = 1
        self.disruption_duration = 500

        # costs
        self.holding_cost = self.params_dict["holding_cost"]
        self.WIP_cost = self.params_dict["WIP_cost"]
        self.earliness_cost = self.params_dict["earliness_cost"]
        self.tardiness_cost = self.params_dict["tardiness_cost"]
        return


class PolicyPanel(object):
    def __init__(self, experiment_number: int, simulation) -> None:
        self.sim = simulation
        self.experiment_number: int = experiment_number
        self.params_dict: Dict[...] = parameters.experimental_params_dict[self.experiment_number]
        # due date determination
        """
        due date procedure
            - random
            - constant
            - total_work_content
            - total_routing_content
        """
        self.due_date_method: str = 'random'
        self.DD_constant_value: float = 55
        self.DD_random_min_max: List[int, int] = [45, 75]
        average_routing_length = (1 + len(self.sim.model_panel.MANUFACTURING_FLOOR_LAYOUT)) / 2
        self.DD_total_work_content_value: float = self.DD_constant_value / average_routing_length
        self.DD_total_routing_content_value: float = self.DD_constant_value / average_routing_length

        # generation
        """
        types of generation techniques
            - BSS (base-stock system)
        """
        self.material_replenishment = self.params_dict['material_replenishment']
        self.reorder_level = self.sim.general_functions.reorder_point(replenishment_type=self.material_replenishment,
                                                                      a_min_max=self.DD_random_min_max)
        print(self.reorder_level)
        self.generated = {}
        self.delivered = {}
        self.generation_technique = {}
        self.generation_attributes = {}
        """
                    
        reorder_moment: when to send a replenishment order
            - release
            - arrival 
        """
        self.reorder_moment = 'arrival'

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
            - MPRD
            - CPRD
            - IPRD
        """
        # release technique
        self.release_technique = self.params_dict['release_technique']  # "DRACO" # "immediate" #
        self.release_technique_attributes = RELEASE_TECHNIQUE_ATTRIBUTES[self.release_technique].copy()
        self.release_process_times = 'deterministic'

        # system state dispatching rule
        """
        what rule to use for DRACO
            - FOCUS (Kasper et al., 2022)
            - IPD: integrates a dispatching rule with 
        """
        self.ssd_rule = "IPD"

        # tracking variables
        self.released = 0
        self.completed = 0
        self.release_target = self.params_dict['release_target']

        # pool rule
        self.sequencing_rule = 'PRD'
        self.sequencing_rule_attributes = POOL_RULE_ATTRIBUTES[self.sequencing_rule].copy()
        # set queueing estimate
        mean_p = self.sim.model_panel.MEAN_PROCESS_TIME
        mean_q = self.sim.general_functions.get_mean_q()
        self.sequencing_rule_attributes['PRD_k'] = mean_p + mean_q
        # dispatching
        """
        dispatching rules available
            - FCFS
            - FISFO
            - FISHOPFO (first in shop)
            - SLACK
            - SPT
            - ODD_land, following Land et al. (2014)
            - FOCUS, following Kasper et al. (2023)
        """
        self.dispatching_mode = "priority_rule"
        self.dispatching_rule = 'FCFS'  # 'EDD' # "FISFO"

        # material allocation
        """
        material allocation
            - NHB --> No Hold Back
            - HB --> Hold Back 
                - requires a rationing rule
                    - FCFS
                    - SPT
                    - EDD
                    - SLACK
                    - PRD
                - requires a rationing threshold => 0 
        """
        self.material_allocation = self.params_dict['material_allocation']  # 'availability'
        self.rationing_rule = 'PRD'
        self.rationing_threshold = 0
        return


GENERATION_TECHNIQUE_ATTRIBUTES = {
    'exponential': {},
    'BSS': {'generated': 0, 'delivered': 0},
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
    'PRD': {'PRD_k': 6.625},
    'FISFO': {},
    'EDD': {},
    'CPRD': {},
    'MPRD': {},
    'IPRD': {}
}