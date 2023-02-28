"""
Project: pp_03
Made By: Arno Kasper
Version: 1.1.0
"""


DRACO_WIP_target = [20, 25]
CONWIP_WIP_target = [42, 47]
material_replenishment = ['hierarchical', 'intergral']
material_allocation = ['NHB', 'HB']
release_technique = ["DRACO", 'CONWIP', "IMM"]
material_complexity = ['low', 'moderate', 'high']
cost_ratio = ['base', 'low_low', 'high_low', 'low_high', 'high_high']

material_complexity_dict = {'low': {'material_quantity': 1, "material_request": "constant"},
                            'moderate': {'material_quantity': 3, "material_request": "constant"},
                            'high': {'material_quantity': 3, "material_request": "variable"}}

cost_ratios_dict = {'base': {'holding_cost': 0.5, 'WIP_cost': 3, 'earliness_cost': 0.75,'tardiness_cost': 4},
                    'low_low': {'holding_cost': 0.5, 'WIP_cost': 2, 'earliness_cost': 0.75,'tardiness_cost': 3},
                    'high_low': {'holding_cost': 0.5, 'WIP_cost': 4, 'earliness_cost': 0.75,'tardiness_cost': 3},
                    'low_high': {'holding_cost': 0.5, 'WIP_cost': 2, 'earliness_cost': 0.75,'tardiness_cost': 5},
                    'high_high': {'holding_cost': 0.5, 'WIP_cost': 4, 'earliness_cost': 0.75,'tardiness_cost': 5}
                    }

experimental_params_dict = []

def get_interactions():
    #"""
    # IMM
    for m_complexity in material_complexity:
        for mat_all in material_allocation:
            for mat_repl in material_replenishment:
                for cr in cost_ratio:
                    params_dict = dict()
                    params_dict["name"] = "MAR"
                    params_dict["release_technique"] = "immediate"
                    params_dict["material_complexity"] = m_complexity
                    params_dict["material_complexity_dict"] = material_complexity_dict[m_complexity]
                    params_dict["material_allocation"] = mat_all
                    params_dict["material_replenishment"] = mat_repl
                    params_dict["release_target"] = None
                    params_dict["cost_ratio"] = cr
                    params_dict["holding_cost"] = cost_ratios_dict[cr]["holding_cost"]
                    params_dict["WIP_cost"] = cost_ratios_dict[cr]["WIP_cost"]
                    params_dict["earliness_cost"] = cost_ratios_dict[cr]["earliness_cost"]
                    params_dict["tardiness_cost"] = cost_ratios_dict[cr]["tardiness_cost"]
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
                        params_dict["cost_ratio"] = cr
                        params_dict["holding_cost"] = cost_ratios_dict[cr]["holding_cost"]
                        params_dict["WIP_cost"] = cost_ratios_dict[cr]["WIP_cost"]
                        params_dict["earliness_cost"] = cost_ratios_dict[cr]["earliness_cost"]
                        params_dict["tardiness_cost"] = cost_ratios_dict[cr]["tardiness_cost"]
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
                        params_dict["cost_ratio"] = cr
                        params_dict["holding_cost"] = cost_ratios_dict[cr]["holding_cost"]
                        params_dict["WIP_cost"] = cost_ratios_dict[cr]["WIP_cost"]
                        params_dict["earliness_cost"] = cost_ratios_dict[cr]["earliness_cost"]
                        params_dict["tardiness_cost"] = cost_ratios_dict[cr]["tardiness_cost"]
                        experimental_params_dict.append(params_dict)
    #"""
    """
    # test periodic values
    cr = 'low_low' # 'base' #
    params_dict = dict()
    params_dict["name"] = "MAR"
    params_dict["release_technique"] = "immediate"
    params_dict["material_complexity"] = "moderate"
    params_dict["material_complexity_dict"] = material_complexity_dict["moderate"]
    params_dict["material_allocation"] = "HB"
    params_dict["material_replenishment"] = 'hierarchical'
    params_dict["release_target"] = None
    params_dict["cost_ratio"] = cr
    params_dict["holding_cost"] = cost_ratios_dict[cr]["holding_cost"]
    params_dict["WIP_cost"] = cost_ratios_dict[cr]["WIP_cost"]
    params_dict["earliness_cost"] = cost_ratios_dict[cr]["earliness_cost"]
    params_dict["tardiness_cost"] = cost_ratios_dict[cr]["tardiness_cost"]
    experimental_params_dict.append(params_dict)

    params_dict = dict()
    params_dict["name"] = "CONWIP"
    params_dict["release_technique"] = "CONWIP"
    params_dict["material_complexity"] = "moderate"
    params_dict["material_complexity_dict"] = material_complexity_dict["moderate"]
    params_dict["material_allocation"] = "HB"
    params_dict["material_replenishment"] = 'hierarchical'
    params_dict["release_target"] = 47
    params_dict["cost_ratio"] = cr
    params_dict["holding_cost"] = cost_ratios_dict[cr]["holding_cost"]
    params_dict["WIP_cost"] = cost_ratios_dict[cr]["WIP_cost"]
    params_dict["earliness_cost"] = cost_ratios_dict[cr]["earliness_cost"]
    params_dict["tardiness_cost"] = cost_ratios_dict[cr]["tardiness_cost"]
    experimental_params_dict.append(params_dict)

    # cr = 'base'
    params_dict = dict()
    params_dict["name"] = "DRACO"
    params_dict["release_technique"] = "DRACO"
    params_dict["material_complexity"] = "moderate"
    params_dict["material_complexity_dict"] = material_complexity_dict["moderate"]
    params_dict["material_allocation"] = "NHB"
    params_dict["material_replenishment"] = 'intergral'
    params_dict["release_target"] = 25
    params_dict["cost_ratio"] = cr
    params_dict["holding_cost"] = cost_ratios_dict[cr]["holding_cost"]
    params_dict["WIP_cost"] = cost_ratios_dict[cr]["WIP_cost"]
    params_dict["earliness_cost"] = cost_ratios_dict[cr]["earliness_cost"]
    params_dict["tardiness_cost"] = cost_ratios_dict[cr]["tardiness_cost"]
    experimental_params_dict.append(params_dict)

    #"""
    """
    # sensitivity
    # IMM
    m_complexity = "moderate"
    cr = 'base'
    for mat_all in material_allocation:
        for mat_repl in material_replenishment:
            params_dict = dict()
            params_dict["name"] = "MAR"
            params_dict["release_technique"] = "immediate"
            params_dict["material_complexity"] = m_complexity
            params_dict["material_complexity_dict"] = material_complexity_dict[m_complexity]
            params_dict["material_allocation"] = mat_all
            params_dict["material_replenishment"] = mat_repl
            params_dict["release_target"] = None
            params_dict["cost_ratio"] = cr
            params_dict["holding_cost"] = cost_ratios_dict[cr]["holding_cost"]
            params_dict["WIP_cost"] = cost_ratios_dict[cr]["WIP_cost"]
            params_dict["earliness_cost"] = cost_ratios_dict[cr]["earliness_cost"]
            params_dict["tardiness_cost"] = cost_ratios_dict[cr]["tardiness_cost"]
            experimental_params_dict.append(params_dict)

    # CONWIP
    for mat_all in material_allocation:
        for mat_repl in material_replenishment:
            params_dict = dict()
            params_dict["name"] = "CONWIP"
            params_dict["release_technique"] = "CONWIP"
            params_dict["material_complexity"] = m_complexity
            params_dict["material_complexity_dict"] = material_complexity_dict[m_complexity]
            params_dict["material_allocation"] = mat_all
            params_dict["material_replenishment"] = mat_repl
            params_dict["release_target"] = 47
            params_dict["cost_ratio"] = cr
            params_dict["holding_cost"] = cost_ratios_dict[cr]["holding_cost"]
            params_dict["WIP_cost"] = cost_ratios_dict[cr]["WIP_cost"]
            params_dict["earliness_cost"] = cost_ratios_dict[cr]["earliness_cost"]
            params_dict["tardiness_cost"] = cost_ratios_dict[cr]["tardiness_cost"]
            experimental_params_dict.append(params_dict)

    # DRACO
    for mat_all in material_allocation:
        for mat_repl in material_replenishment:
            params_dict = dict()
            params_dict["name"] = "DRACO"
            params_dict["release_technique"] = "DRACO"
            params_dict["material_complexity"] = m_complexity
            params_dict["material_complexity_dict"] = material_complexity_dict[m_complexity]
            params_dict["material_allocation"] = mat_all
            params_dict["material_replenishment"] = mat_repl
            params_dict["release_target"] = 25
            params_dict["cost_ratio"] = cr
            params_dict["holding_cost"] = cost_ratios_dict[cr]["holding_cost"]
            params_dict["WIP_cost"] = cost_ratios_dict[cr]["WIP_cost"]
            params_dict["earliness_cost"] = cost_ratios_dict[cr]["earliness_cost"]
            params_dict["tardiness_cost"] = cost_ratios_dict[cr]["tardiness_cost"]
            experimental_params_dict.append(params_dict)
    """
    print(len(experimental_params_dict))
    return experimental_params_dict


# activate the code
if __name__ == '__main__':
    experimental_params_dict = get_interactions()
