import pandas as pd


class DataCollection(object):
    def __init__(self, simulation):
        self.sim = simulation

        # order params
        self.order_output_counter = 0
        self.order_input_counter = 0
        self.accumulated_process_time = 0

        self.experiment_database = None
        self.order_list = list()

        # columns names
        self.columns_names_run = [
                            'identifier',
                            'product_name',
                            'throughput_time',
                            'pool_time',
                            'shop_throughput_time',
                            'lateness',
                            'tardiness',
                            'tardy',
                            'material_waiting_time',
                            'material_replenishment_time',
                            'inventory_time',
                            'material_present',
                            'routing_length',
                            'number_of_materials'
                                ]
        return

    def append_run_list(self, result_list):
        """
        append the result of an order to the already existing order list
        :param result_list:
        :return: void
        """
        self.order_list.append(result_list)
        return

    def run_update(self, warmup):
        """
        function that update's the database of the experiment for each run
        :param warmup:
        :return: void
        """
        if not warmup:
            # update database
            self.store_run_data()

        # data processing finished. Update database new run
        self.order_list = list()
        self.accumulated_process_time = 0
        return

    def store_run_data(self):
        # put all data into dataframe
        df_run = pd.DataFrame(self.order_list)
        df_run.columns = self.columns_names_run

        # dataframe for each run
        df = pd.DataFrame(
            [(int(self.sim.env.now / (self.sim.model_panel.WARM_UP_PERIOD + self.sim.model_panel.RUN_TIME)))],
            columns=['run'])

        # generic measures
        number_of_machines_in_process = (len(self.sim.model_panel.MANUFACTURING_FLOOR_LAYOUT))
        df[f"utilization"] = ((self.accumulated_process_time * 100 / number_of_machines_in_process)
                             / self.sim.model_panel.RUN_TIME)
        # order information
        df[f"mean_ttt"] = df_run.loc[:, "throughput_time"].mean()
        df[f"mean_ptt"] = df_run.loc[:, "pool_time"].mean()
        df[f"mean_sttt"] = df_run.loc[:, "shop_throughput_time"].mean()

        # material information
        # df[f"mean_mat_avail_t"] = df_run.loc[:, "material_waiting_time"].mean()
        # df[f'mean_mat_reple_t'] = df_run.loc[:, "material_replenishment_time"].mean()
        df[f'mean_mat_inv_t'] = df_run.loc[:, "inventory_time"].mean()
        df[f'fill_rate'] = df_run.loc[:, "material_present"].mean()

        # due date
        df["mean_lateness"] = df_run.loc[:, "lateness"].mean()
        df["std_lateness"] = df_run.loc[:, "lateness"].std()
        df["mean_tardiness"] = df_run.loc[:, "tardiness"].mean()
        df["mean_squared_tardiness"] = (df_run.loc[:, "tardiness"] ** 2).mean()
        df["percentage_tardy"] = df_run.loc[:, "tardy"].sum() / df_run.shape[0]

        df_exp_interactions = self.add_experiment_variables()
        df = pd.concat([df, df_exp_interactions], axis=1)

        # save data from the run
        if self.experiment_database is None:
            self.experiment_database = df
            # self.experiment_database = df_run
        else:
            self.experiment_database = pd.concat([self.experiment_database, df], ignore_index=True)
        return

    def add_experiment_variables(self):
        df_exp_interaction = pd.DataFrame()
        for i, index in enumerate(self.sim.model_panel.names_variables):
            df_exp_interaction[f"{self.sim.model_panel.names_variables[i]}"] = [self.sim.model_panel.params_dict[index]]
        return df_exp_interaction