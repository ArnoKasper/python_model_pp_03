"""
Project: pp_05
Made By: Arno Kasper
Version: 1.0.0
"""
import numpy as np


material_complexity = ['low', 'medium', 'high']
shop_complexity = ['low', 'medium', 'high']
WIP_target = [18, 36, 48]
reorder_moment = ['arrival', 'release']
release_technique = ["DRACO", "IMM"]

reorder_levels = {'low': [6, 7, 8, 9],
                  'medium': [22, 23, 25, 27],
                  'high': [22, 23, 25, 27]
                  }
index_reorder_level = len(reorder_levels['low'])


shop_complexity_dict = {'low': {'work_centres': 3, "routing_configuration": "PFS"},
                         'medium': {'work_centres': 5, "routing_configuration": "GFS"},
                         'high': {'work_centres': 5, "routing_configuration": "PJS"}}

material_complexity_dict = {'low': {'material_quantity': 1, "material_request": "constant"},
                             'medium': {'material_quantity': 3, "material_request": "constant"},
                             'high': {'material_quantity': 3, "material_request": "variable"}}
experimental_params_dict = []


def get_interactions():
    # MOR
    for m_complexity in material_complexity:
        for s_complexity in shop_complexity:
            for reorder_lvl in range(0, index_reorder_level):
                for reorder_mom in reorder_moment:
                    params_dict = dict()
                    params_dict["name"] = "MOR"
                    params_dict["release_technique"] = "immediate"
                    params_dict["material_complexity"] = m_complexity
                    params_dict["material_complexity_dict"] = material_complexity_dict[m_complexity]
                    params_dict["shop_complexity"] = s_complexity
                    params_dict["shop_complexity_dict"] = shop_complexity_dict[s_complexity]
                    params_dict["reorder_level"] = reorder_levels[m_complexity][reorder_lvl]
                    params_dict["reorder_moment"] = reorder_mom
                    params_dict["release_target"] = None
                    experimental_params_dict.append(params_dict)
    # COR
    for m_complexity in material_complexity:
        for s_complexity in shop_complexity:
            for reorder_lvl in range(0, index_reorder_level):
                for reorder_mom in reorder_moment:
                    for T in WIP_target:
                        params_dict = dict()
                        params_dict["name"] = "COR"
                        params_dict["release_technique"] = "DRACO"
                        params_dict["material_complexity"] = m_complexity
                        params_dict["material_complexity_dict"] = material_complexity_dict[m_complexity]
                        params_dict["shop_complexity"] = s_complexity
                        params_dict["shop_complexity_dict"] = shop_complexity_dict[s_complexity]
                        params_dict["reorder_level"] = reorder_levels[m_complexity][reorder_lvl]
                        params_dict["reorder_moment"] = reorder_mom
                        params_dict["release_target"] = T
                        experimental_params_dict.append(params_dict)

    print(len(experimental_params_dict))
    return experimental_params_dict


# activate the code
if __name__ == '__main__':
    experimental_params_dict = get_interactions()
