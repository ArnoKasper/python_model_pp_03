"""
Project: pp_03
Made By: Arno Kasper
Version: 1.1.0
"""

material_complexity = ['low', 'moderate', 'high']
shop_complexity = ['GFS', 'PJS']
DRACO_WIP_target = [15, 25]
CONWIP_WIP_target = [40, 45]

reorder_moment = ['release', 'arrival']
release_technique = ["DRACO", 'CONWIP', "IMM"]

mean_replenishment_times = [10, 50, 100]

reorder_level_dict = {'10': [23, 24, 27],
                      '50': [103, 105, 110],
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
                for reorder_lvl in reorder_level_dict[f'{mean_replenishment_lvl}']:
                    for reorder_mom in reorder_moment:
                        if m_complexity == "low":
                            corr_reorder_lvl = int(reorder_lvl / 3) + 1
                        else:
                            corr_reorder_lvl = reorder_lvl
                        params_dict = dict()
                        params_dict["name"] = "IMM"
                        params_dict["release_technique"] = "immediate"
                        params_dict["material_complexity"] = m_complexity
                        params_dict["material_complexity_dict"] = material_complexity_dict[m_complexity]
                        params_dict["routing_configuration"] = s_complexity
                        params_dict["reorder_level"] = corr_reorder_lvl
                        params_dict["mean_replenishment_time"] = mean_replenishment_lvl
                        params_dict["reorder_moment"] = reorder_mom
                        params_dict["release_target"] = None
                        experimental_params_dict.append(params_dict)

    # CONWIP
    for m_complexity in material_complexity:
        for s_complexity in shop_complexity:
            for mean_replenishment_lvl in mean_replenishment_times:
                for reorder_lvl in reorder_level_dict[f'{mean_replenishment_lvl}']:
                    for reorder_mom in reorder_moment:
                        for T in CONWIP_WIP_target:
                            if m_complexity == "low":
                                corr_reorder_lvl = int(reorder_lvl / 3) + 1
                            else:
                                corr_reorder_lvl = reorder_lvl
                            params_dict = dict()
                            params_dict["name"] = "CONWIP"
                            params_dict["release_technique"] = "CONWIP"
                            params_dict["material_complexity"] = m_complexity
                            params_dict["material_complexity_dict"] = material_complexity_dict[m_complexity]
                            params_dict["routing_configuration"] = s_complexity
                            params_dict["reorder_level"] = corr_reorder_lvl
                            params_dict["mean_replenishment_time"] = mean_replenishment_lvl
                            params_dict["reorder_moment"] = reorder_mom
                            params_dict["release_target"] = T
                            experimental_params_dict.append(params_dict)

    # DRACO
    for m_complexity in material_complexity:
        for s_complexity in shop_complexity:
            for mean_replenishment_lvl in mean_replenishment_times:
                for reorder_lvl in reorder_level_dict[f'{mean_replenishment_lvl}']:
                    for reorder_mom in reorder_moment:
                        for T in DRACO_WIP_target:
                            # correct reorder level
                            if m_complexity == "low":
                                corr_reorder_lvl = int(reorder_lvl / 3) + 1
                            else:
                                corr_reorder_lvl = reorder_lvl
                            params_dict = dict()
                            params_dict["name"] = "COR"
                            params_dict["release_technique"] = "DRACO"
                            params_dict["material_complexity"] = m_complexity
                            params_dict["material_complexity_dict"] = material_complexity_dict[m_complexity]
                            params_dict["routing_configuration"] = s_complexity
                            params_dict["reorder_level"] = corr_reorder_lvl
                            params_dict["mean_replenishment_time"] = mean_replenishment_lvl
                            params_dict["reorder_moment"] = reorder_mom
                            params_dict["release_target"] = T
                            experimental_params_dict.append(params_dict)
    """
    params_dict = dict()
    params_dict["name"] = "CONWIP"
    params_dict["release_technique"] = "CONWIP"
    params_dict["material_complexity"] = "low"
    params_dict["material_complexity_dict"] = material_complexity_dict["low"]
    params_dict["routing_configuration"] = "GFS"
    params_dict["reorder_level"] = int(25 / 3) + 1
    params_dict["mean_replenishment_time"] = 10
    params_dict["reorder_moment"] = "arrival"
    params_dict["release_target"] = 45
    experimental_params_dict.append(params_dict)
    """
    print(len(experimental_params_dict))
    return experimental_params_dict


# activate the code
if __name__ == '__main__':
    experimental_params_dict = get_interactions()
