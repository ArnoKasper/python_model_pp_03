"""
Project: pp_03
Made By: Arno Kasper
Version: 1.1.0
"""

DRACO_WIP_target = [20, 25, 40]
CONWIP_WIP_target = [40, 50, 80]
material_replenishment = ['ExHed', 'PoHed']
material_allocation = ['NHB', 'HB']
release_technique = ["DRACO", 'CONWIP', "BIL"]
material_complexity = ['single', 'multiple', 'random']
cost_ratio = ['moderate', 'low', 'high']

material_complexity_dict = {'single': {'material_quantity': 1, "material_request": "constant"},
                            'multiple': {'material_quantity': 3, "material_request": "constant"},
                            'random': {'material_quantity': 3, "material_request": "variable"}}

cost_ratios_dict = {'high': {'holding_cost': 0.25, 'WIP_cost': 1, 'earliness_cost': 0.5, 'tardiness_cost': 9},
                    'moderate': {'holding_cost': 0.25, 'WIP_cost': 1, 'earliness_cost': 0.5, 'tardiness_cost': 5},
                    'low': {'holding_cost': 0.25, 'WIP_cost': 1, 'earliness_cost': 0.5, 'tardiness_cost': 3},
                    'super_low': {'holding_cost': 0.25, 'WIP_cost': 1, 'earliness_cost': 0.5, 'tardiness_cost': 1.5}
                    }

due_date_dict = {'main': {'v_min': -2.75, 'v_max': 52.25},
                 'sensitivity': {'v_min': -2.75, 'v_max': 27.5}}

experimental_params_dict = []


def get_interactions():
    cost_ratio = ['high', 'low', 'moderate']
    """
    dd_setting = 'main'
    # BIL
    for m_complexity in material_complexity:
        for mat_all in material_allocation:
            for mat_repl in material_replenishment:
                for cr in cost_ratio:
                    params_dict = dict()
                    params_dict["name"] = "BIL"
                    params_dict["release_technique"] = "BIL"
                    params_dict["material_complexity"] = m_complexity
                    params_dict["material_complexity_dict"] = material_complexity_dict[m_complexity]
                    params_dict["material_allocation"] = mat_all
                    params_dict["material_replenishment"] = mat_repl
                    params_dict["release_target"] = None
                    params_dict["dd_setting"] = dd_setting
                    params_dict["v_min"] = due_date_dict[dd_setting]["v_min"]
                    params_dict["v_max"] = due_date_dict[dd_setting]["v_max"]
                    params_dict["cost_ratio"] = cr
                    params_dict["holding_cost"] = cost_ratios_dict[cr]["holding_cost"]
                    params_dict["WIP_cost"] = cost_ratios_dict[cr]["WIP_cost"]
                    params_dict["earliness_cost"] = cost_ratios_dict[cr]["earliness_cost"]
                    params_dict["tardiness_cost"] = cost_ratios_dict[cr]["tardiness_cost"]
                    params_dict["utilization"] = 0.9
                    params_dict["stations"] = 6
                    experimental_params_dict.append(params_dict)

    # CONWIP
    for m_complexity in material_complexity:
        for mat_all in material_allocation:
            for T in CONWIP_WIP_target:
                for mat_repl in material_replenishment:
                    for cr in cost_ratio:
                        params_dict = dict()
                        params_dict["name"] = "CONWIP"
                        params_dict["release_technique"] = "CONWIP"
                        params_dict["material_complexity"] = m_complexity
                        params_dict["material_complexity_dict"] = material_complexity_dict[m_complexity]
                        params_dict["material_allocation"] = mat_all
                        params_dict["material_replenishment"] = mat_repl
                        params_dict["release_target"] = T
                        params_dict["dd_setting"] = dd_setting
                        params_dict["v_min"] = due_date_dict[dd_setting]["v_min"]
                        params_dict["v_max"] = due_date_dict[dd_setting]["v_max"]
                        params_dict["cost_ratio"] = cr
                        params_dict["holding_cost"] = cost_ratios_dict[cr]["holding_cost"]
                        params_dict["WIP_cost"] = cost_ratios_dict[cr]["WIP_cost"]
                        params_dict["earliness_cost"] = cost_ratios_dict[cr]["earliness_cost"]
                        params_dict["tardiness_cost"] = cost_ratios_dict[cr]["tardiness_cost"]
                        params_dict["utilization"] = 0.9
                        params_dict["stations"] = 6
                        experimental_params_dict.append(params_dict)

    # DRACO
    for m_complexity in material_complexity:
        for mat_all in material_allocation:
            for T in DRACO_WIP_target:
                for mat_repl in material_replenishment:
                    for cr in cost_ratio:
                        params_dict = dict()
                        params_dict["name"] = "DRACO"
                        params_dict["release_technique"] = "DRACO"
                        params_dict["material_complexity"] = m_complexity
                        params_dict["material_complexity_dict"] = material_complexity_dict[m_complexity]
                        params_dict["material_allocation"] = mat_all
                        params_dict["material_replenishment"] = mat_repl
                        params_dict["release_target"] = T
                        params_dict["dd_setting"] = dd_setting
                        params_dict["v_min"] = due_date_dict[dd_setting]["v_min"]
                        params_dict["v_max"] = due_date_dict[dd_setting]["v_max"]
                        params_dict["cost_ratio"] = cr
                        params_dict["holding_cost"] = cost_ratios_dict[cr]["holding_cost"]
                        params_dict["WIP_cost"] = cost_ratios_dict[cr]["WIP_cost"]
                        params_dict["earliness_cost"] = cost_ratios_dict[cr]["earliness_cost"]
                        params_dict["tardiness_cost"] = cost_ratios_dict[cr]["tardiness_cost"]
                        params_dict["utilization"] = 0.9
                        params_dict["stations"] = 6
                        experimental_params_dict.append(params_dict)
    """
    """
    # due date sensitivity experiments 
    dd_setting = 'sensitivity'
    # BIL
    for m_complexity in material_complexity:
        for mat_all in material_allocation:
            for mat_repl in material_replenishment:
                for cr in cost_ratio:
                    params_dict = dict()
                    params_dict["name"] = "sensitivity"
                    params_dict["release_technique"] = "BIL"
                    params_dict["material_complexity"] = m_complexity
                    params_dict["material_complexity_dict"] = material_complexity_dict[m_complexity]
                    params_dict["material_allocation"] = mat_all
                    params_dict["material_replenishment"] = mat_repl
                    params_dict["release_target"] = None
                    params_dict["dd_setting"] = dd_setting
                    params_dict["v_min"] = due_date_dict[dd_setting]["v_min"]
                    params_dict["v_max"] = due_date_dict[dd_setting]["v_max"]
                    params_dict["cost_ratio"] = cr
                    params_dict["holding_cost"] = cost_ratios_dict[cr]["holding_cost"]
                    params_dict["WIP_cost"] = cost_ratios_dict[cr]["WIP_cost"]
                    params_dict["earliness_cost"] = cost_ratios_dict[cr]["earliness_cost"]
                    params_dict["tardiness_cost"] = cost_ratios_dict[cr]["tardiness_cost"]
                    params_dict["utilization"] = 0.9
                    params_dict["stations"] = 6
                    experimental_params_dict.append(params_dict)

    # CONWIP
    for m_complexity in material_complexity:
        for mat_all in material_allocation:
            for T in CONWIP_WIP_target:
                for mat_repl in material_replenishment:
                    for cr in cost_ratio:
                        params_dict = dict()
                        params_dict["name"] = "sensitivity"
                        params_dict["release_technique"] = "CONWIP"
                        params_dict["material_complexity"] = m_complexity
                        params_dict["material_complexity_dict"] = material_complexity_dict[m_complexity]
                        params_dict["material_allocation"] = mat_all
                        params_dict["material_replenishment"] = mat_repl
                        params_dict["release_target"] = T
                        params_dict["dd_setting"] = dd_setting
                        params_dict["v_min"] = due_date_dict[dd_setting]["v_min"]
                        params_dict["v_max"] = due_date_dict[dd_setting]["v_max"]
                        params_dict["cost_ratio"] = cr
                        params_dict["holding_cost"] = cost_ratios_dict[cr]["holding_cost"]
                        params_dict["WIP_cost"] = cost_ratios_dict[cr]["WIP_cost"]
                        params_dict["earliness_cost"] = cost_ratios_dict[cr]["earliness_cost"]
                        params_dict["tardiness_cost"] = cost_ratios_dict[cr]["tardiness_cost"]
                        params_dict["utilization"] = 0.9
                        params_dict["stations"] = 6
                        experimental_params_dict.append(params_dict)

    # DRACO
    for m_complexity in material_complexity:
        for mat_all in material_allocation:
            for T in DRACO_WIP_target:
                for mat_repl in material_replenishment:
                    for cr in cost_ratio:
                        params_dict = dict()
                        params_dict["name"] = "sensitivity"
                        params_dict["release_technique"] = "DRACO"
                        params_dict["material_complexity"] = m_complexity
                        params_dict["material_complexity_dict"] = material_complexity_dict[m_complexity]
                        params_dict["material_allocation"] = mat_all
                        params_dict["material_replenishment"] = mat_repl
                        params_dict["release_target"] = T
                        params_dict["dd_setting"] = dd_setting
                        params_dict["v_min"] = due_date_dict[dd_setting]["v_min"]
                        params_dict["v_max"] = due_date_dict[dd_setting]["v_max"]
                        params_dict["cost_ratio"] = cr
                        params_dict["holding_cost"] = cost_ratios_dict[cr]["holding_cost"]
                        params_dict["WIP_cost"] = cost_ratios_dict[cr]["WIP_cost"]
                        params_dict["earliness_cost"] = cost_ratios_dict[cr]["earliness_cost"]
                        params_dict["tardiness_cost"] = cost_ratios_dict[cr]["tardiness_cost"]
                        params_dict["utilization"] = 0.9
                        params_dict["stations"] = 6
                        experimental_params_dict.append(params_dict)
    """

    """
    # set WIP paramters
    adj_CONWIP_WIP_target = [*range(36, 51), 52, 55, 50, 100]
    cost_ratio = ['moderate', 'low', 'high']
    dd_setting = 'main'
    m_complexity = 'single'
    mat_all = 'NHB'
    mat_repl = 'ExHed'

    # CONWIP
    for T in adj_CONWIP_WIP_target:
        for cr in cost_ratio:
            params_dict = dict()
            params_dict["name"] = "WIPsetting"
            params_dict["release_technique"] = "CONWIP"
            params_dict["material_complexity"] = m_complexity
            params_dict["material_complexity_dict"] = material_complexity_dict[m_complexity]
            params_dict["material_allocation"] = mat_all
            params_dict["material_replenishment"] = mat_repl
            params_dict["release_target"] = T
            params_dict["dd_setting"] = dd_setting
            params_dict["v_min"] = due_date_dict[dd_setting]["v_min"]
            params_dict["v_max"] = due_date_dict[dd_setting]["v_max"]
            params_dict["cost_ratio"] = cr
            params_dict["holding_cost"] = cost_ratios_dict[cr]["holding_cost"]
            params_dict["WIP_cost"] = cost_ratios_dict[cr]["WIP_cost"]
            params_dict["earliness_cost"] = cost_ratios_dict[cr]["earliness_cost"]
            params_dict["tardiness_cost"] = cost_ratios_dict[cr]["tardiness_cost"]
            params_dict["utilization"] = 0.9
            params_dict["stations"] = 6
            experimental_params_dict.append(params_dict)

    # DRACO
    adj_DRACO_WIP_target = [*range(12, 41, 2), 50]
    for T in adj_DRACO_WIP_target:
        for cr in cost_ratio:
            params_dict = dict()
            params_dict["name"] = "WIPsetting"
            params_dict["release_technique"] = "DRACO"
            params_dict["material_complexity"] = m_complexity
            params_dict["material_complexity_dict"] = material_complexity_dict[m_complexity]
            params_dict["material_allocation"] = mat_all
            params_dict["material_replenishment"] = mat_repl
            params_dict["release_target"] = T
            params_dict["dd_setting"] = dd_setting
            params_dict["v_min"] = due_date_dict[dd_setting]["v_min"]
            params_dict["v_max"] = due_date_dict[dd_setting]["v_max"]
            params_dict["cost_ratio"] = cr
            params_dict["holding_cost"] = cost_ratios_dict[cr]["holding_cost"]
            params_dict["WIP_cost"] = cost_ratios_dict[cr]["WIP_cost"]
            params_dict["earliness_cost"] = cost_ratios_dict[cr]["earliness_cost"]
            params_dict["tardiness_cost"] = cost_ratios_dict[cr]["tardiness_cost"]
            params_dict["utilization"] = 0.9
            params_dict["stations"] = 6
            experimental_params_dict.append(params_dict)
    """
    """
    # testing variants
    dd_setting = 'main'
    cost_ratio = 'moderate'
    # hierarchical push
    adj_CONWIP_WIP_target = [*range(34, 51), 52, 55, 50, 100]
    for T in adj_CONWIP_WIP_target:
        params_dict = dict()
        params_dict["name"] = "testvariants"
        params_dict["release_technique"] = "CONWIP"
        params_dict["material_complexity"] = "multiple"
        params_dict["material_complexity_dict"] = material_complexity_dict["multiple"]
        params_dict["material_allocation"] = "HB"
        params_dict["material_replenishment"] = 'ExHed'
        params_dict["release_target"] = T
        params_dict["dd_setting"] = dd_setting
        params_dict["v_min"] = due_date_dict[dd_setting]["v_min"]
        params_dict["v_max"] = due_date_dict[dd_setting]["v_max"]
        params_dict["cost_ratio"] = cost_ratio
        params_dict["holding_cost"] = cost_ratios_dict[cost_ratio]["holding_cost"]
        params_dict["WIP_cost"] = cost_ratios_dict[cost_ratio]["WIP_cost"]
        params_dict["earliness_cost"] = cost_ratios_dict[cost_ratio]["earliness_cost"]
        params_dict["tardiness_cost"] = cost_ratios_dict[cost_ratio]["tardiness_cost"]
        params_dict["utilization"] = 0.9
        params_dict["stations"] = 6
        experimental_params_dict.append(params_dict)

    adj_CONWIP_WIP_target = [*range(94, 130, 2), 135, 140, 150, 200]
    for T in adj_CONWIP_WIP_target:
        params_dict = dict()
        params_dict["name"] = "testvariants"
        params_dict["release_technique"] = "CONWL"
        params_dict["material_complexity"] = "multiple"
        params_dict["material_complexity_dict"] = material_complexity_dict["multiple"]
        params_dict["material_allocation"] = "HB"
        params_dict["material_replenishment"] = 'ExHed'
        params_dict["release_target"] = T
        params_dict["dd_setting"] = dd_setting
        params_dict["v_min"] = due_date_dict[dd_setting]["v_min"]
        params_dict["v_max"] = due_date_dict[dd_setting]["v_max"]
        params_dict["cost_ratio"] = cost_ratio
        params_dict["holding_cost"] = cost_ratios_dict[cost_ratio]["holding_cost"]
        params_dict["WIP_cost"] = cost_ratios_dict[cost_ratio]["WIP_cost"]
        params_dict["earliness_cost"] = cost_ratios_dict[cost_ratio]["earliness_cost"]
        params_dict["tardiness_cost"] = cost_ratios_dict[cost_ratio]["tardiness_cost"]
        params_dict["utilization"] = 0.9
        params_dict["stations"] = 6
        experimental_params_dict.append(params_dict)

    adj_CONWIP_WIP_target = [*range(94, 130, 2), 135, 140, 150, 200]
    for T in adj_CONWIP_WIP_target:
        params_dict = dict()
        params_dict["name"] = "testvariants"
        params_dict["release_technique"] = "CONRL"
        params_dict["material_complexity"] = "multiple"
        params_dict["material_complexity_dict"] = material_complexity_dict["multiple"]
        params_dict["material_allocation"] = "HB"
        params_dict["material_replenishment"] = 'ExHed'
        params_dict["release_target"] = T
        params_dict["dd_setting"] = dd_setting
        params_dict["v_min"] = due_date_dict[dd_setting]["v_min"]
        params_dict["v_max"] = due_date_dict[dd_setting]["v_max"]
        params_dict["cost_ratio"] = cost_ratio
        params_dict["holding_cost"] = cost_ratios_dict[cost_ratio]["holding_cost"]
        params_dict["WIP_cost"] = cost_ratios_dict[cost_ratio]["WIP_cost"]
        params_dict["earliness_cost"] = cost_ratios_dict[cost_ratio]["earliness_cost"]
        params_dict["tardiness_cost"] = cost_ratios_dict[cost_ratio]["tardiness_cost"]
        params_dict["utilization"] = 0.9
        params_dict["stations"] = 6
        experimental_params_dict.append(params_dict)
    """
    #"""
    # collect order data
    dd_setting = 'main'
    cost_ratio = 'moderate'
    # hierarchical push
    params_dict = dict()
    params_dict["name"] = "orderdata"
    params_dict["release_technique"] = "BIL"
    params_dict["material_complexity"] = "multiple"
    params_dict["material_complexity_dict"] = material_complexity_dict["multiple"]
    params_dict["material_allocation"] = "HB"
    params_dict["material_replenishment"] = 'ExHed'
    params_dict["release_target"] = None
    params_dict["dd_setting"] = dd_setting
    params_dict["v_min"] = due_date_dict[dd_setting]["v_min"]
    params_dict["v_max"] = due_date_dict[dd_setting]["v_max"]
    params_dict["cost_ratio"] = cost_ratio
    params_dict["holding_cost"] = cost_ratios_dict[cost_ratio]["holding_cost"]
    params_dict["WIP_cost"] = cost_ratios_dict[cost_ratio]["WIP_cost"]
    params_dict["earliness_cost"] = cost_ratios_dict[cost_ratio]["earliness_cost"]
    params_dict["tardiness_cost"] = cost_ratios_dict[cost_ratio]["tardiness_cost"]
    params_dict["utilization"] = 0.9
    params_dict["stations"] = 6
    experimental_params_dict.append(params_dict)

    # hierarchical pull
    params_dict = dict()
    params_dict["name"] = "orderdata"
    params_dict["release_technique"] = "CONWIP"
    params_dict["material_complexity"] = "multiple"
    params_dict["material_complexity_dict"] = material_complexity_dict["multiple"]
    params_dict["material_allocation"] = "HB"
    params_dict["material_replenishment"] = 'ExHed'
    params_dict["release_target"] = 50
    params_dict["dd_setting"] = dd_setting
    params_dict["v_min"] = due_date_dict[dd_setting]["v_min"]
    params_dict["v_max"] = due_date_dict[dd_setting]["v_max"]
    params_dict["cost_ratio"] = cost_ratio
    params_dict["holding_cost"] = cost_ratios_dict[cost_ratio]["holding_cost"]
    params_dict["WIP_cost"] = cost_ratios_dict[cost_ratio]["WIP_cost"]
    params_dict["earliness_cost"] = cost_ratios_dict[cost_ratio]["earliness_cost"]
    params_dict["tardiness_cost"] = cost_ratios_dict[cost_ratio]["tardiness_cost"]
    params_dict["utilization"] = 0.9
    params_dict["stations"] = 6
    experimental_params_dict.append(params_dict)

    # centralised integration
    params_dict = dict()
    params_dict["name"] = "orderdata"
    params_dict["release_technique"] = "BIL"
    params_dict["material_complexity"] = "multiple"
    params_dict["material_complexity_dict"] = material_complexity_dict["multiple"]
    params_dict["material_allocation"] = "HB"
    params_dict["material_replenishment"] = 'PoHed'
    params_dict["release_target"] = None
    params_dict["dd_setting"] = dd_setting
    params_dict["v_min"] = due_date_dict[dd_setting]["v_min"]
    params_dict["v_max"] = due_date_dict[dd_setting]["v_max"]
    params_dict["cost_ratio"] = cost_ratio
    params_dict["holding_cost"] = cost_ratios_dict[cost_ratio]["holding_cost"]
    params_dict["WIP_cost"] = cost_ratios_dict[cost_ratio]["WIP_cost"]
    params_dict["earliness_cost"] = cost_ratios_dict[cost_ratio]["earliness_cost"]
    params_dict["tardiness_cost"] = cost_ratios_dict[cost_ratio]["tardiness_cost"]
    params_dict["utilization"] = 0.9
    params_dict["stations"] = 6
    experimental_params_dict.append(params_dict)

    # decentralised integration
    params_dict = dict()
    params_dict["name"] = "orderdata"
    params_dict["release_technique"] = "DRACO"
    params_dict["material_complexity"] = "multiple"
    params_dict["material_complexity_dict"] = material_complexity_dict["multiple"]
    params_dict["material_allocation"] = "NHB"
    params_dict["material_replenishment"] = 'PoHed'
    params_dict["release_target"] = 25
    params_dict["dd_setting"] = dd_setting
    params_dict["v_min"] = due_date_dict[dd_setting]["v_min"]
    params_dict["v_max"] = due_date_dict[dd_setting]["v_max"]
    params_dict["cost_ratio"] = cost_ratio
    params_dict["holding_cost"] = cost_ratios_dict[cost_ratio]["holding_cost"]
    params_dict["WIP_cost"] = cost_ratios_dict[cost_ratio]["WIP_cost"]
    params_dict["earliness_cost"] = cost_ratios_dict[cost_ratio]["earliness_cost"]
    params_dict["tardiness_cost"] = cost_ratios_dict[cost_ratio]["tardiness_cost"]
    params_dict["utilization"] = 0.9
    params_dict["stations"] = 6
    experimental_params_dict.append(params_dict)
    #"""
    """
    # collect order data
    dd_setting = 'main'
    cost_ratio = 'moderate'
    utilization = [0.80, 0.85, 0.9, 0.92]
    stations = [5, 6, 7]
    for until in utilization:
        for m in stations:
            # hierarchical push
            params_dict = dict()
            params_dict["name"] = "UNTILSTATION"
            params_dict["release_technique"] = "BIL"
            params_dict["material_complexity"] = "multiple"
            params_dict["material_complexity_dict"] = material_complexity_dict["multiple"]
            params_dict["material_allocation"] = "HB"
            params_dict["material_replenishment"] = 'ExHed'
            params_dict["release_target"] = None
            params_dict["dd_setting"] = dd_setting
            params_dict["v_min"] = due_date_dict[dd_setting]["v_min"]
            params_dict["v_max"] = due_date_dict[dd_setting]["v_max"]
            params_dict["cost_ratio"] = cost_ratio
            params_dict["holding_cost"] = cost_ratios_dict[cost_ratio]["holding_cost"]
            params_dict["WIP_cost"] = cost_ratios_dict[cost_ratio]["WIP_cost"]
            params_dict["earliness_cost"] = cost_ratios_dict[cost_ratio]["earliness_cost"]
            params_dict["tardiness_cost"] = cost_ratios_dict[cost_ratio]["tardiness_cost"]
            params_dict["utilization"] = until
            params_dict["stations"] = m
            experimental_params_dict.append(params_dict)

            # hierarchical pull
            params_dict = dict()
            params_dict["name"] = "UNTILSTATION"
            params_dict["release_technique"] = "CONWIP"
            params_dict["material_complexity"] = "multiple"
            params_dict["material_complexity_dict"] = material_complexity_dict["multiple"]
            params_dict["material_allocation"] = "HB"
            params_dict["material_replenishment"] = 'ExHed'
            params_dict["release_target"] = 50
            params_dict["dd_setting"] = dd_setting
            params_dict["v_min"] = due_date_dict[dd_setting]["v_min"]
            params_dict["v_max"] = due_date_dict[dd_setting]["v_max"]
            params_dict["cost_ratio"] = cost_ratio
            params_dict["holding_cost"] = cost_ratios_dict[cost_ratio]["holding_cost"]
            params_dict["WIP_cost"] = cost_ratios_dict[cost_ratio]["WIP_cost"]
            params_dict["earliness_cost"] = cost_ratios_dict[cost_ratio]["earliness_cost"]
            params_dict["tardiness_cost"] = cost_ratios_dict[cost_ratio]["tardiness_cost"]
            params_dict["utilization"] = until
            params_dict["stations"] = m
            experimental_params_dict.append(params_dict)

            # centralised integration
            params_dict = dict()
            params_dict["name"] = "UNTILSTATION"
            params_dict["release_technique"] = "BIL"
            params_dict["material_complexity"] = "multiple"
            params_dict["material_complexity_dict"] = material_complexity_dict["multiple"]
            params_dict["material_allocation"] = "HB"
            params_dict["material_replenishment"] = 'PoHed'
            params_dict["release_target"] = None
            params_dict["dd_setting"] = dd_setting
            params_dict["v_min"] = due_date_dict[dd_setting]["v_min"]
            params_dict["v_max"] = due_date_dict[dd_setting]["v_max"]
            params_dict["cost_ratio"] = cost_ratio
            params_dict["holding_cost"] = cost_ratios_dict[cost_ratio]["holding_cost"]
            params_dict["WIP_cost"] = cost_ratios_dict[cost_ratio]["WIP_cost"]
            params_dict["earliness_cost"] = cost_ratios_dict[cost_ratio]["earliness_cost"]
            params_dict["tardiness_cost"] = cost_ratios_dict[cost_ratio]["tardiness_cost"]
            params_dict["utilization"] = until
            params_dict["stations"] = m
            experimental_params_dict.append(params_dict)

            # decentralised integration
            params_dict = dict()
            params_dict["name"] = "UNTILSTATION"
            params_dict["release_technique"] = "DRACO"
            params_dict["material_complexity"] = "multiple"
            params_dict["material_complexity_dict"] = material_complexity_dict["multiple"]
            params_dict["material_allocation"] = "NHB"
            params_dict["material_replenishment"] = 'PoHed'
            params_dict["release_target"] = 25
            params_dict["dd_setting"] = dd_setting
            params_dict["v_min"] = due_date_dict[dd_setting]["v_min"]
            params_dict["v_max"] = due_date_dict[dd_setting]["v_max"]
            params_dict["cost_ratio"] = cost_ratio
            params_dict["holding_cost"] = cost_ratios_dict[cost_ratio]["holding_cost"]
            params_dict["WIP_cost"] = cost_ratios_dict[cost_ratio]["WIP_cost"]
            params_dict["earliness_cost"] = cost_ratios_dict[cost_ratio]["earliness_cost"]
            params_dict["tardiness_cost"] = cost_ratios_dict[cost_ratio]["tardiness_cost"]
            params_dict["utilization"] = until
            params_dict["stations"] = m
            experimental_params_dict.append(params_dict)
    """
    print(len(experimental_params_dict))
    return experimental_params_dict


# activate the code
if __name__ == '__main__':
    experimental_params_dict = get_interactions()
