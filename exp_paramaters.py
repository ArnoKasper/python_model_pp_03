"""
Project: pp_03
Made By: Arno Kasper
Version: 1.1.0
"""

material_complexity = ['low', 'moderate', 'high']
shop_complexity = ['GFS'] #['GFS', 'PJS']
DRACO_WIP_target = [15, 25]
CONWIP_WIP_target = [42, 47]
disruptions = [True, False]

material_allocation = ['availability', 'rationing']

release_technique = ["DRACO", 'CONWIP', "IMM"]

mean_replenishment_times = [50]

reorder_level_dict = {'10': [23, 24, 27],
                      '50': {'low': [32, 35, 38], 'moderate': [102, 105, 110], 'high': [103, 105, 110]},
                      '100': [200, 210, 220]
                      }

shop_complexity_dict = {'low': {'work_centres': 6, "routing_configuration": "GFS"},
                        'moderate': {'work_centres': 6, "routing_configuration": "PJS"}}

material_complexity_dict = {'low': {'material_quantity': 1, "material_request": "constant"},
                            'moderate': {'material_quantity': 3, "material_request": "constant"},
                            'high': {'material_quantity': 3, "material_request": "variable"}}
experimental_params_dict = []

def get_interactions():
    #"""
    # IMM
    for m_complexity in material_complexity:
        for s_complexity in shop_complexity:
            for mean_replenishment_lvl in mean_replenishment_times:
                for reorder_lvl in reorder_level_dict[f'{mean_replenishment_lvl}'][m_complexity]:
                    for mat_all in material_allocation:
                        for disruption in disruptions:
                            params_dict = dict()
                            params_dict["name"] = "IMM"
                            params_dict["release_technique"] = "immediate"
                            params_dict["material_complexity"] = m_complexity
                            params_dict["material_complexity_dict"] = material_complexity_dict[m_complexity]
                            params_dict["routing_configuration"] = s_complexity
                            params_dict["reorder_level"] = reorder_lvl
                            params_dict["mean_replenishment_time"] = mean_replenishment_lvl
                            params_dict["material_allocation"] = mat_all
                            params_dict["release_target"] = None
                            params_dict["disruption"] = disruption
                            experimental_params_dict.append(params_dict)

    # CONWIP
    for m_complexity in material_complexity:
        for s_complexity in shop_complexity:
            for mean_replenishment_lvl in mean_replenishment_times:
                for reorder_lvl in reorder_level_dict[f'{mean_replenishment_lvl}'][m_complexity]:
                    for mat_all in material_allocation:
                        for T in CONWIP_WIP_target:
                            for disruption in disruptions:
                                params_dict = dict()
                                params_dict["name"] = "CONWIP"
                                params_dict["release_technique"] = "CONWIP"
                                params_dict["material_complexity"] = m_complexity
                                params_dict["material_complexity_dict"] = material_complexity_dict[m_complexity]
                                params_dict["routing_configuration"] = s_complexity
                                params_dict["reorder_level"] = reorder_lvl
                                params_dict["mean_replenishment_time"] = mean_replenishment_lvl
                                params_dict["material_allocation"] = mat_all
                                params_dict["release_target"] = T
                                params_dict["disruption"] = disruption
                                experimental_params_dict.append(params_dict)

    # DRACO
    for m_complexity in material_complexity:
        for s_complexity in shop_complexity:
            for mean_replenishment_lvl in mean_replenishment_times:
                for reorder_lvl in reorder_level_dict[f'{mean_replenishment_lvl}'][m_complexity]:
                    for mat_all in material_allocation:
                        for T in DRACO_WIP_target:
                            for disruption in disruptions:
                                params_dict = dict()
                                params_dict["name"] = "DRACO"
                                params_dict["release_technique"] = "DRACO"
                                params_dict["material_complexity"] = m_complexity
                                params_dict["material_complexity_dict"] = material_complexity_dict[m_complexity]
                                params_dict["routing_configuration"] = s_complexity
                                params_dict["reorder_level"] = reorder_lvl
                                params_dict["mean_replenishment_time"] = mean_replenishment_lvl
                                params_dict["material_allocation"] = mat_all
                                params_dict["release_target"] = T
                                params_dict["disruption"] = disruption
                                experimental_params_dict.append(params_dict)
    """
    params_dict = dict()
    params_dict["name"] = "IMM"
    params_dict["release_technique"] = "immediate"
    params_dict["material_complexity"] = "high"
    params_dict["material_complexity_dict"] = material_complexity_dict["high"]
    params_dict["routing_configuration"] = "GFS"
    params_dict["reorder_level"] = 105
    params_dict["mean_replenishment_time"] = 50
    params_dict["material_allocation"] = "availability" # 'rationing' #
    params_dict["release_target"] = 20
    params_dict["disruption"] = True
    experimental_params_dict.append(params_dict)
    #"""
    print(len(experimental_params_dict))
    return experimental_params_dict


# activate the code
if __name__ == '__main__':
    experimental_params_dict = get_interactions()
