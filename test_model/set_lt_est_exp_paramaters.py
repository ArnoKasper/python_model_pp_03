
util = [*range(50, 100)]
utilization_levels = [x/100 for x in util]
m_levels = [*range(1, 13)]

def get_interactions():
    experimental_params_dict = []
    for m in m_levels:
        for u in utilization_levels:
            params_dict = dict()
            params_dict["utilization"] = u
            params_dict["m_machines"] = m
            experimental_params_dict.append(params_dict)
    print(len(experimental_params_dict))
    return experimental_params_dict