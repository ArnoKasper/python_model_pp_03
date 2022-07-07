"""
Project: pp_05
Made By: Arno Kasper
Version: 1.0.0
"""
import numpy as np

WLC_norms = [4.5, 4.9, 5.8, 6.7, 7.6, 8.5, 10]
WIP_target = [1, 6, 12, 14, 18, 24, 36, 84]
WIP_loop_target = [1, 2, 3, 4, 8, 10]
POLCA_cards = [3, 4, 5, 8, 12, 5000]
due_date_type = ["total_work_content", "constant"]
due_date_tightness = ["tight", "loose"]

dd_dict = {"loose": {"total_work_content": 12,
                     "random": [30, 54],
                     "constant": 42
                     },
           "tight": {"total_work_content": 9,
                     "random": [28, 35],
                     "constant": 31.5
                     }
           }

experimental_params_dict = []


def get_interactions():
    """
    # FOCUS
    for dd_type in due_date_type:
        for tightness in due_date_tightness:
            params_dict = dict()
            params_dict["name"] = "FOCUS"
            params_dict["hierarchical_order_release"] = False
            params_dict["hierarchical_order_authorization"] = False
            params_dict["dispatching_mode"] = "system_state_dispatching"
            params_dict["dispatching_rule"] = "FOCUS"
            params_dict["ssd_order_release"] = False
            params_dict["ssd_order_authorization"] = False
            params_dict["release_target"] = None
            params_dict["authorization_target"] = None
            params_dict["dd_type"] = dd_type
            params_dict["dd_tightness"] = tightness
            params_dict["dd_value"] = dd_dict[tightness][dd_type]
            experimental_params_dict.append(params_dict)

    # "DRACO"
    WIP_target = [6, 12, 14, 18, 24, 36, 84]
    for T in WIP_target:
        for dd_type in due_date_type:
            for tightness in due_date_tightness:
                target = int(T / 6)
                params_dict = dict()
                params_dict["name"] = "DRACO"
                params_dict["hierarchical_order_release"] = False
                params_dict["hierarchical_order_authorization"] = False
                params_dict["dispatching_mode"] = "system_state_dispatching"
                params_dict["dispatching_rule"] = "DRACO"
                params_dict["ssd_order_release"] = True
                params_dict["ssd_order_authorization"] = True
                params_dict["release_target"] = T
                params_dict["authorization_target"] = target
                params_dict["dd_type"] = dd_type
                params_dict["dd_tightness"] = tightness
                params_dict["dd_value"] = dd_dict[tightness][dd_type]
                experimental_params_dict.append(params_dict)

    # "DRACO (D)"
    for dd_type in due_date_type:
        for tightness in due_date_tightness:
            params_dict = dict()
            params_dict["name"] = "DRACO (D)"
            params_dict["hierarchical_order_release"] = False
            params_dict["hierarchical_order_authorization"] = False
            params_dict["dispatching_mode"] = "system_state_dispatching"
            params_dict["dispatching_rule"] = "DRACO"
            params_dict["ssd_order_release"] = False
            params_dict["ssd_order_authorization"] = False
            params_dict["release_target"] = None
            params_dict["authorization_target"] = None
            params_dict["dd_type"] = dd_type
            params_dict["dd_tightness"] = tightness
            params_dict["dd_value"] = dd_dict[tightness][dd_type]
            experimental_params_dict.append(params_dict)

    # "DRACO (R + D)"
    WIP_target = [1, 6, 12, 14, 18, 24, 36, 84]
    for T in WIP_target:
        for dd_type in due_date_type:
            for tightness in due_date_tightness:
                params_dict = dict()
                params_dict["name"] = "DRACO (R + D)"
                params_dict["hierarchical_order_release"] = False
                params_dict["hierarchical_order_authorization"] = False
                params_dict["dispatching_mode"] = "system_state_dispatching"
                params_dict["dispatching_rule"] = "DRACO"
                params_dict["ssd_order_release"] = True
                params_dict["ssd_order_authorization"] = False
                params_dict["release_target"] = T
                params_dict["authorization_target"] = None
                params_dict["dd_type"] = dd_type
                params_dict["dd_tightness"] = tightness
                params_dict["dd_value"] = dd_dict[tightness][dd_type]
                experimental_params_dict.append(params_dict)

    # "DRACO (A + D)"
    for C_jk in WIP_loop_target:
        for dd_type in due_date_type:
            for tightness in due_date_tightness:
                params_dict = dict()
                params_dict["name"] = "DRACO (A + D)"
                params_dict["hierarchical_order_release"] = False
                params_dict["hierarchical_order_authorization"] = False
                params_dict["dispatching_mode"] = "system_state_dispatching"
                params_dict["dispatching_rule"] = "DRACO"
                params_dict["ssd_order_release"] = False
                params_dict["ssd_order_authorization"] = True
                params_dict["release_target"] = None
                params_dict["authorization_target"] = C_jk
                params_dict["dd_type"] = dd_type
                params_dict["dd_tightness"] = tightness
                params_dict["dd_value"] = dd_dict[tightness][dd_type]
                experimental_params_dict.append(params_dict)

    # LUMS COR
    for norm in WLC_norms:
        for dd_type in due_date_type:
            for tightness in due_date_tightness:
                params_dict = dict()
                params_dict["name"] = "LUMS COR"
                params_dict["hierarchical_order_release"] = True
                params_dict["hierarchical_order_authorization"] = False
                params_dict["dispatching_mode"] = "priority_rule"
                params_dict["dispatching_rule"] = "ODD_land"
                params_dict["ssd_order_release"] = False
                params_dict["ssd_order_authorization"] = False
                params_dict["release_target"] = norm
                params_dict["authorization_target"] = None
                params_dict["dd_type"] = dd_type
                params_dict["dd_tightness"] = tightness
                params_dict["dd_value"] = dd_dict[tightness][dd_type]
                experimental_params_dict.append(params_dict)

    # POLCA
    for cards in POLCA_cards:
        for dd_type in due_date_type:
            for tightness in due_date_tightness:
                params_dict = dict()
                params_dict["name"] = "POLCA"
                params_dict["hierarchical_order_release"] = False
                params_dict["hierarchical_order_authorization"] = True
                params_dict["dispatching_mode"] = "priority_rule"
                params_dict["dispatching_rule"] = "ODD_land"
                params_dict["ssd_order_release"] = False
                params_dict["ssd_order_authorization"] = False
                params_dict["release_target"] = None
                params_dict["authorization_target"] = cards
                params_dict["dd_type"] = dd_type
                params_dict["dd_tightness"] = tightness
                params_dict["dd_value"] = dd_dict[tightness][dd_type]
                experimental_params_dict.append(params_dict)

    # LC-POLCA
    for norm in WLC_norms:
        for dd_type in due_date_type:
            for tightness in due_date_tightness:
                params_dict = dict()
                params_dict["name"] = "LC-POLCA"
                params_dict["hierarchical_order_release"] = True
                params_dict["hierarchical_order_authorization"] = True
                params_dict["dispatching_mode"] = "priority_rule"
                params_dict["dispatching_rule"] = "ODD_land"
                params_dict["ssd_order_release"] = False
                params_dict["ssd_order_authorization"] = False
                params_dict["release_target"] = norm
                params_dict["authorization_target"] = 3
                params_dict["dd_type"] = dd_type
                params_dict["dd_tightness"] = tightness
                params_dict["dd_value"] = dd_dict[tightness][dd_type]
                experimental_params_dict.append(params_dict)

    # ODD
    for dd_type in due_date_type:
        for tightness in due_date_tightness:
            params_dict = dict()
            params_dict["name"] = "ODD"
            params_dict["hierarchical_order_release"] = False
            params_dict["hierarchical_order_authorization"] = False
            params_dict["dispatching_mode"] = "priority_rule"
            params_dict["dispatching_rule"] = "ODD_land"
            params_dict["ssd_order_release"] = False
            params_dict["ssd_order_authorization"] = False
            params_dict["release_target"] = None
            params_dict["authorization_target"] = None
            params_dict["dd_type"] = dd_type
            params_dict["dd_tightness"] = tightness
            params_dict["dd_value"] = dd_dict[tightness][dd_type]
            experimental_params_dict.append(params_dict)

    # LC-POLCA (with FOCUS)
    for norm in WLC_norms:
        for dd_type in due_date_type:
            for tightness in due_date_tightness:
                params_dict = dict()
                params_dict["name"] = "LC-POLCA"
                params_dict["hierarchical_order_release"] = True
                params_dict["hierarchical_order_authorization"] = True
                params_dict["dispatching_mode"] = "system_state_dispatching"
                params_dict["dispatching_rule"] = "FOCUS"
                params_dict["ssd_order_release"] = False
                params_dict["ssd_order_authorization"] = False
                params_dict["release_target"] = norm
                params_dict["authorization_target"] = 3
                params_dict["dd_type"] = dd_type
                params_dict["dd_tightness"] = tightness
                params_dict["dd_value"] = dd_dict[tightness][dd_type]
                experimental_params_dict.append(params_dict)
    """
    # LUMS COR
    for norm in WLC_norms:
        params_dict = dict()
        params_dict["name"] = "LUMS COR"
        params_dict["hierarchical_order_release"] = True
        params_dict["hierarchical_order_authorization"] = False
        params_dict["dispatching_mode"] = "priority_rule"
        params_dict["dispatching_rule"] = "ODD_land"
        params_dict["ssd_order_release"] = False
        params_dict["ssd_order_authorization"] = False
        params_dict["release_target"] = norm
        params_dict["authorization_target"] = None
        params_dict["dd_type"] = "constant"
        params_dict["dd_tightness"] = "tight"  # "loose"
        params_dict["dd_value"] = dd_dict["tight"]["constant"]
        experimental_params_dict.append(params_dict)
    """
    params_dict = dict()
    params_dict["name"] = "IMM"
    params_dict["hierarchical_order_release"] = False
    params_dict["hierarchical_order_authorization"] = False
    params_dict["dispatching_mode"] = "priority_rule"
    params_dict["dispatching_rule"] = "FCFS"
    params_dict["ssd_order_release"] = False
    params_dict["ssd_order_authorization"] = False
    params_dict["release_target"] = 4.5
    params_dict["authorization_target"] = 3
    params_dict["dd_type"] = "constant"
    params_dict["dd_tightness"] = "tight" # "loose"
    params_dict["dd_value"] = dd_dict["tight"]["constant"]
    experimental_params_dict.append(params_dict)

    params_dict = dict()
    params_dict["name"] = "LUMS_COR"
    params_dict["hierarchical_order_release"] = True
    params_dict["hierarchical_order_authorization"] = False
    params_dict["dispatching_mode"] = "priority_rule"
    params_dict["dispatching_rule"] = "ODD_land"
    params_dict["ssd_order_release"] = False
    params_dict["ssd_order_authorization"] = False
    params_dict["release_target"] = 20
    params_dict["authorization_target"] = None
    params_dict["dd_type"] = "constant"
    params_dict["dd_tightness"] = "tight" # "loose"
    params_dict["dd_value"] = dd_dict["tight"]["constant"]
    experimental_params_dict.append(params_dict)

    T = 36
    params_dict = dict()
    params_dict["name"] = "DRACO"
    params_dict["hierarchical_order_release"] = False
    params_dict["hierarchical_order_authorization"] = False
    params_dict["dispatching_mode"] = "system_state_dispatching"
    params_dict["dispatching_rule"] = "DRACO"
    params_dict["ssd_order_release"] = True
    params_dict["ssd_order_authorization"] = True
    params_dict["release_target"] = T
    params_dict["authorization_target"] = int(T / 6)
    params_dict["dd_type"] = "constant"
    params_dict["dd_tightness"] = "tight" # "loose"
    params_dict["dd_value"] = dd_dict["tight"]["constant"]
    experimental_params_dict.append(params_dict)
    
    params_dict = dict()
    params_dict["name"] = "DRACO (D)"
    params_dict["hierarchical_order_release"] = False
    params_dict["hierarchical_order_authorization"] = False
    params_dict["dispatching_mode"] = "system_state_dispatching"
    params_dict["dispatching_rule"] = "DRACO"
    params_dict["ssd_order_release"] = False
    params_dict["ssd_order_authorization"] = False
    params_dict["release_target"] = None
    params_dict["authorization_target"] = None
    params_dict["dd_type"] = "constant"
    params_dict["dd_tightness"] = "loose"
    params_dict["dd_value"] = dd_dict["loose"]["constant"]
    experimental_params_dict.append(params_dict)
    """

    print(len(experimental_params_dict))
    return experimental_params_dict


# activate the code
if __name__ == '__main__':
    experimental_params_dict = get_interactions()
