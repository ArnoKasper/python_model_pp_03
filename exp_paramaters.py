"""
Project: pp_03
Made By: Arno Kasper
Version: 1.1.0
"""
import numpy as np


material_complexity = ['low', 'medium', 'high']
shop_complexity = ['low', 'medium', 'high']
WIP_target = [18, 36]
reorder_moment = ['arrival', 'release']
release_technique = ["DRACO", "IMM"]

reorder_levels = [22, 24, 27]
lead_time_levels = [33, 37, 41]


shop_complexity_dict = {'low': {'work_centres': 5, "routing_configuration": "GFS"},
                         'medium': {'work_centres': 5, "routing_configuration": "PJS"},
                         'high': {'work_centres': 5, "routing_configuration": "PJSR"}}

material_complexity_dict = {'low': {'material_quantity': 3, "material_request": "constant"},
                             'medium': {'material_quantity': 3, "material_request": "variable"},
                             'high': {'material_quantity': 3, "material_request": "variable_replace"}}
experimental_params_dict = []


def get_interactions():
    # MOR
    for m_complexity in material_complexity:
        for s_complexity in shop_complexity:
            for reorder_lvl in reorder_levels:
                for lead_time_lvl in lead_time_levels:
                    for reorder_mom in reorder_moment:
                        params_dict = dict()
                        params_dict["name"] = "MOR"
                        params_dict["release_technique"] = "immediate"
                        params_dict["material_allocation"] = "rationing"
                        params_dict["material_complexity"] = m_complexity
                        params_dict["material_complexity_dict"] = material_complexity_dict[m_complexity]
                        params_dict["shop_complexity"] = s_complexity
                        params_dict["shop_complexity_dict"] = shop_complexity_dict[s_complexity]
                        params_dict["reorder_level"] = reorder_lvl
                        params_dict["lead_time_level"] = lead_time_lvl
                        params_dict["reorder_moment"] = reorder_mom
                        params_dict["release_target"] = None
                        experimental_params_dict.append(params_dict)
    # COR
    for m_complexity in material_complexity:
        for s_complexity in shop_complexity:
            for reorder_lvl in reorder_levels:
                for lead_time_lvl in lead_time_levels:
                    for reorder_mom in reorder_moment:
                        for T in WIP_target:
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
    print(len(experimental_params_dict))
    return experimental_params_dict


# activate the code
if __name__ == '__main__':
    experimental_params_dict = get_interactions()
