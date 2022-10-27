"""
Project: pp_03
Made By: Arno Kasper
Version: 1.1.0
"""
import numpy as np


material_complexity = ['low', 'moderate']
shop_complexity = ['low', 'moderate']
DRACO_WIP_target = [18, 36]
CONWIP_WIP_target = [35, 40, 45]
reorder_moment = ['release']
pool_rule = ['CPRD', 'MPRD', 'IPRD']
release_technique = ["DRACO", 'CONWIP', "IMM"]

reorder_levels = [23, 24, 27]
lead_time_levels = [33, 37, 41]


shop_complexity_dict = { 'base_line': {'work_centres': 3, "routing_configuration": "PFS"},
                         'low': {'work_centres': 5, "routing_configuration": "GFS"},
                         'moderate': {'work_centres': 5, "routing_configuration": "PJS"},
                         'high': {'work_centres': 5, "routing_configuration": "PJSR"}}

material_complexity_dict = { 'base_line': {'material_quantity': 1, "material_request": "constant"},
                             'low': {'material_quantity': 3, "material_request": "constant"},
                             'moderate': {'material_quantity': 3, "material_request": "variable"},
                             'high': {'material_quantity': 3, "material_request": "variable_replace"}}
experimental_params_dict = []


def get_interactions():
    """
    # IMM
    for m_complexity in material_complexity:
        for s_complexity in shop_complexity:
            for reorder_lvl in reorder_levels:
                for lead_time_lvl in lead_time_levels:
                    for reorder_mom in reorder_moment:
                        params_dict = dict()
                        params_dict["name"] = "IMM"
                        params_dict["release_technique"] = "immediate"
                        params_dict["material_allocation"] = "availability"
                        params_dict["material_complexity"] = m_complexity
                        params_dict["material_complexity_dict"] = material_complexity_dict[m_complexity]
                        params_dict["shop_complexity"] = s_complexity
                        params_dict["shop_complexity_dict"] = shop_complexity_dict[s_complexity]
                        params_dict["reorder_level"] = reorder_lvl
                        params_dict["lead_time_level"] = lead_time_lvl
                        params_dict["reorder_moment"] = reorder_mom
                        params_dict["release_target"] = None
                        experimental_params_dict.append(params_dict)

    # CONWIP
    for m_complexity in material_complexity:
        for s_complexity in shop_complexity:
            for reorder_lvl in reorder_levels:
                for lead_time_lvl in lead_time_levels:
                    for reorder_mom in reorder_moment:
                        for T in CONWIP_WIP_target:
                            params_dict = dict()
                            params_dict["name"] = "CONWIP"
                            params_dict["release_technique"] = "CONWIP"
                            params_dict["material_allocation"] = "availability"
                            params_dict["material_complexity"] = m_complexity
                            params_dict["material_complexity_dict"] = material_complexity_dict[m_complexity]
                            params_dict["shop_complexity"] = s_complexity
                            params_dict["shop_complexity_dict"] = shop_complexity_dict[s_complexity]
                            params_dict["reorder_level"] = reorder_lvl
                            params_dict["lead_time_level"] = lead_time_lvl
                            params_dict["reorder_moment"] = reorder_mom
                            params_dict["release_target"] = T
                            experimental_params_dict.append(params_dict)

    # DRACO
    for m_complexity in material_complexity:
        for s_complexity in shop_complexity:
            for reorder_lvl in reorder_levels:
                for lead_time_lvl in lead_time_levels:
                    for reorder_mom in reorder_moment:
                        for T in DRACO_WIP_target:
                            params_dict = dict()
                            params_dict["name"] = "COR"
                            params_dict["release_technique"] = "DRACO"
                            params_dict["material_allocation"] = "availability"
                            params_dict["material_complexity"] = m_complexity
                            params_dict["material_complexity_dict"] = material_complexity_dict[m_complexity]
                            params_dict["shop_complexity"] = s_complexity
                            params_dict["shop_complexity_dict"] = shop_complexity_dict[s_complexity]
                            params_dict["reorder_level"] = reorder_lvl
                            params_dict["lead_time_level"] = lead_time_lvl
                            params_dict["reorder_moment"] = reorder_mom
                            params_dict["release_target"] = T
                            experimental_params_dict.append(params_dict)
    """
    params_dict = dict()
    params_dict["name"] = "DRACO"
    params_dict["release_technique"] = "DRACO"
    params_dict["material_allocation"] = "availability"
    params_dict["material_complexity"] = "low"
    params_dict["material_complexity_dict"] = material_complexity_dict["low"]
    params_dict["shop_complexity"] = "low"
    params_dict["shop_complexity_dict"] = shop_complexity_dict["low"]
    params_dict["reorder_level"] = 23
    params_dict["lead_time_level"] = 42
    params_dict["reorder_moment"] = "arrival"
    params_dict["release_target"] = 20
    params_dict["pool_rule"] = "EDD"
    experimental_params_dict.append(params_dict)

    print(len(experimental_params_dict))
    return experimental_params_dict


# activate the code
if __name__ == '__main__':
    experimental_params_dict = get_interactions()
