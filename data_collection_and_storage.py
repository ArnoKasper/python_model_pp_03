import pandas as pd


class DataCollection(object):
    def __init__(self, simulation):
        self.sim = simulation

        # order params
        self.order_output_counter = {}
        self.order_input_counter = {}
        self.accumulated_process_time = {}
        for line in self.sim.model_panel.LINE_STRUCTURE.keys():
            self.order_output_counter[line] = 0
            self.order_input_counter[line] = 0
            self.accumulated_process_time[line] = 0

        self.experiment_database = None
        self.order_list = list()

        # demand params
        self.demanded_items_counter = 0
        self.demanded_items_fulfilled = 0

        # columns names
        self.columns_names_run = [
                            'line',
                            'identifier',
                            'product_name',
                            'throughput_time',
                            'inventory_time',
                            'material_waiting_time',
                            'shop_throughput_time',
                            'lateness',
                            'tardiness',
                            'tardy'
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
        for line in self.sim.model_panel.LINE_STRUCTURE.keys():
            self.accumulated_process_time[line] = 0

        self.demanded_items_counter = 0
        self.demanded_items_fulfilled = 0
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
        # df['service_level'] = self.demanded_items_fulfilled / self.demanded_items_counter

        # line specific measures
        for line in self.sim.model_panel.LINE_STRUCTURE.keys():
            df_run_line = df_run.loc[df_run['line'] == line]
            # df[f"nr_flow_items_{line}"] = df_run_line.shape[0]
            number_of_machines_in_process = (len(self.sim.model_panel.MANUFACTURING_FLOOR_LAYOUT[line]))
            df[f"util_{line}"] = ((self.accumulated_process_time[line] * 100 / number_of_machines_in_process)
                                 / self.sim.model_panel.RUN_TIME)
            df[f"mean_ttt_{line}"] = df_run_line.loc[:, "throughput_time"].mean()
            df[f"mean_mwt_{line}"] = df_run_line.loc[:, "material_waiting_time"].mean()
            df[f"mean_sttt_{line}"] = df_run_line.loc[:, "shop_throughput_time"].mean()
            df[f"FGI_{line}"] = df_run_line.loc[:, "inventory_time"].mean() / self.sim.model_panel.DEMAND_RATE

        # due date
        df_run_line = df_run.loc[df_run['line'] == 'line_1']
        df["mean_lateness"] = df_run_line.loc[:, "lateness"].mean()
        df["mean_tardiness"] = df_run_line.loc[:, "tardiness"].mean()
        df["mean_squared_tardiness"] = (df_run_line.loc[:, "tardiness"] ** 2).mean()
        df["percentage_tardy"] = df_run_line.loc[:, "tardy"].sum() / df_run.shape[0]

        # save data from the run
        if self.experiment_database is None:
            self.experiment_database = df
        else:
            self.experiment_database = pd.concat([self.experiment_database, df], ignore_index=True)
        return
