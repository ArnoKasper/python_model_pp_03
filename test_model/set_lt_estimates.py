""""
Made by: Arno Kasper
Version 2.1
Date 01/11/2020

Current model
- All basic elements added
- Model is validated and cleaned
"""
# set code and import libraries
import simpy
import random
import pandas as pd
from operator import itemgetter
import socket
import warnings
import os
import time
import math
import set_lt_est_exp_paramaters as parameters


class ControlPanel(object):
    def __init__(self, simulation, exp_number):
        """
        class that contains all the settings for the simulation model.
        """
        # general params
        self.experiment_number = exp_number
        self.sim = simulation
        experimental_params_dict = parameters.get_interactions()
        self.params_dict = experimental_params_dict[self.experiment_number]
        self.print_info = False
        self.print_final_info = True

        # set experiment name
        self.names_variables = ["utilization",
                                'm_machines'
                                ]
        self.indexes = self.names_variables.copy()
        self.experiment_name: str = f"lt_est_test_"
        for i in self.indexes:
            self.experiment_name += str(self.params_dict[i]) + "_"

        # experiment variables
        self.warmup_period = 3000
        self.run_time = 10000
        self.number_of_runs = 100

        # shop layout
        self.order_pool = simpy.FilterStore(self.sim.env)
        self.manufacturing_process_layout = []
        self.m = self.params_dict["m_machines"]
        for i in range(1, self.m+1):
            self.manufacturing_process_layout.append(f'WC{i}')
        self.manufacturing_process = dict()
        for _, work_centre in enumerate(self.manufacturing_process_layout):
            self.manufacturing_process[work_centre] = simpy.PriorityResource(self.sim.env, capacity=1)

        # customer enquiry management - Due Date determination
        self.min_max_random_dd = [45, 75]  # Due Dates intervals

        # release control (immediate release is LUMS COR = False)
        self.LUMS_COR = False
        self.workload_norm = 5.8
        self.periodic_release_period = 4.0

        # pool rules
        self.pool_rule = "PRD"
        self.periodic_release_date_factor_k = 4

        # workload params
        self.processed_workload = dict()
        self.released_workload = dict()

        # make dict
        for _, work_centre in enumerate(self.manufacturing_process_layout):
            self.processed_workload[work_centre] = 0
            self.released_workload[work_centre] = 0

        # order arrival params
        self.mean_process_time = 1
        self.aimed_utilization = self.params_dict["utilization"]
        mean_r = ((len(self.manufacturing_process_layout) + 1) / 2)
        m = len(self.manufacturing_process_layout)
        inter_arrival_time = (mean_r / m) * (1 / self.aimed_utilization)
        self.mean_time_between_arrival = round(inter_arrival_time, 5)
        # print(self.mean_time_between_arrival)
        self.process_time_distribution = '2_erlang' #'exponential' #
        self.general_flow_shop = True  # False is pure job shop

        # dispatching
        """
        options available
            - FCFS: First Come First Serve
            - SPT: Shortest Process time 
            - ODD: Operational Due Date (following Land et al., 2014) 
        """
        self.dispatching_rule = "FCFS"


class DataControl(object):
    def __init__(self, simulation):
        """
        object having all the databases and all functionality for data manipulation
        :param simulation: simulation object stored in simulation_model.py
        :return: void
        """
        self.sim = simulation
        self.experiment_database = None
        self.order_list = list()
        self.columns_names_run = [
            "identifier",
            "throughput_time",
            "pool_time",
            "process_throughput_time",
            "lateness",
            "tardiness",
            "tardy",
            'operation_ttt'
        ]

        # other
        self.accumulated_process_time = 0
        self.continous_trigger = 0

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
        self.sim.data.continous_trigger = 0
        return

    def store_run_data(self):
        """
        function that computes all performance metrics of the model
        :return: void
        """
        # put all data into dataframe
        df_run = pd.DataFrame(self.order_list)
        df_run.columns = self.columns_names_run

        # dataframe for each run
        df = pd.DataFrame(
            [(int(self.sim.env.now / (self.sim.control_panel.warmup_period + self.sim.control_panel.run_time)))],
            columns=['run'])

        df["nr_flow_items"] = df_run.shape[0]
        number_of_machines_in_process = len(self.sim.control_panel.manufacturing_process_layout)
        df["utilization"] = ((self.accumulated_process_time * 100 / number_of_machines_in_process)
                             / self.sim.control_panel.run_time)
        df["mean_lt"] = df_run.loc[:, "throughput_time"].mean()
        df["std_lt"] = df_run.loc[:, "throughput_time"].std()

        est_mean = self.sim.general_functions.get_mean_manufacturing_lead_time()
        est_stddev_mm1 = self.sim.general_functions.get_std_dev_manufacturing_lead_time_mm1()
        est_stddev_mg1 = self.sim.general_functions.get_std_dev_manufacturing_lead_time_mg1()
        df["est_mean_lt"] = est_mean
        df["est_std_lt_mm1"] = est_stddev_mm1
        df["est_std_lt_mg1"] = est_stddev_mg1

        df["gap_mean_lt"] = (df_run.loc[:, "throughput_time"].mean() - est_mean) / df_run.loc[:, "throughput_time"].mean()
        df["gap_std_lt_mm1"] = (df_run.loc[:, "throughput_time"].std() - est_stddev_mm1) / df_run.loc[:, "throughput_time"].std()
        df["gap_std_lt_mg1"] = (df_run.loc[:, "throughput_time"].std() - est_stddev_mg1) / df_run.loc[:, "throughput_time"].std()

        df["mean_operation_ttt"] = df_run.loc[:, "operation_ttt"].mean()
        df["std_operation_ttt"] = df_run.loc[:, "operation_ttt"].std()

        df["aimed_utilization"] = self.sim.control_panel.aimed_utilization
        df["machines_m"] = self.sim.control_panel.m

        # df["mean_pool_time"] = df_run.loc[:, "pool_time"].mean()
        #df["std_pool_time"] = df_run.loc[:, "pool_time"].std()
        #df["mean_process_throughput_time"] = df_run.loc[:, "process_throughput_time"].mean()
        #df["std_process_throughput_time"] = df_run.loc[:, "process_throughput_time"].std()
        #df["mean_lateness"] = df_run.loc[:, "lateness"].mean()
        #df["std_lateness"] = df_run.loc[:, "lateness"].std()
        #df["mean_tardiness"] = df_run.loc[:, "tardiness"].mean()
        #df["std_tardiness"] = df_run.loc[:, "tardiness"].std()
        #df["mean_squared_tardiness"] = (df_run.loc[:, "tardiness"] ** 2).mean()
        #df["percentage_tardy"] = df_run.loc[:, "tardy"].sum() / df_run.shape[0]
        #df["LC_triggers"] = self.sim.data.continous_trigger


        # save data from the run to experiment dataframe
        if self.experiment_database is None:
            self.experiment_database = df
        else:
            self.experiment_database = pd.concat([self.experiment_database, df], ignore_index=True)
        return

    def save_dataset(self):
        """
        function that saves the database of the experiment
        :return: void
        """
        file = self._get_directory() + self.sim.control_panel.experiment_name + '.csv'
        self.experiment_database.to_csv(file, index=False)
        if self.sim.control_panel.print_info:
            print("\n")
            print(f"data saved at: {file}")
        return

    def _get_directory(self):
        # define different path options
        machine_name = socket.gethostname()
        path = ""
        # find path for specific machine
        #   arno's PC
        if machine_name == "LAPTOP-HN4N26LU":
            path = "C:/Users/Arno_ZenBook/Dropbox/Professioneel/Research/Results/test/"
        #   peregrine
        elif machine_name[0:7] == "pg-node":
            path = "/data/s3178471/"
        elif machine_name == "WKS052605":
            path = "C:/Users/P288125/Dropbox/Professioneel/Research/pp_03_entropy_balance/data/estimates/experiments_1/"
        else:
            warnings.warn(f"{machine_name} is an unknown CPU name ", Warning)
            path = os.path.abspath(os.getcwd())
            print(f"files are saved in {path}")
        return path


class GeneralFunctions(object):
    def __init__(self, simulation):
        """
        object having all attributes the general functions class. The general functions class has a variety of tools
        that can be used by any module anywhere in the simulation.
        :param simulation: simulation object stored in simulation_model.py
        :return: void
        """
        self.sim = simulation

        # set seeds for common random numbers
        self.random_generator = random.Random()
        self.random_generator.seed(999999)

    def two_erlang_truncated(self, mean_process_time, truncation):
        """
        two erlang distribution
        :param mean_process_time:
        :param truncation:
        :return: value
        """
        # adjust mean to ensure a correct mean after truncation
        if truncation == 4 and mean_process_time == 1:
            mean_process_time_adj = 1.975
        else:
            raise Exception("for this truncation level and mean no adjusted mean available")
        value = truncation + 1
        while value > truncation:
            value = self.random_generator.expovariate(mean_process_time_adj) + \
                    self.random_generator.expovariate(mean_process_time_adj)
        return value

    def two_erlang(self, mean):
        """
        two erlang distribution
        :param mean_process_time:
        :return: value
        """
        return self.random_generator.expovariate(mean*2) + self.random_generator.expovariate(mean*2)

    def exponential(self, mean):
        """
        two erlang distribution
        :param mean_process_time:
        :return: value
        """
        return self.random_generator.expovariate(mean)

    def random_due_date(self):
        """
        random due date assignment
        :return: value
        """
        return self.sim.env.now + self.random_generator.uniform(self.sim.control_panel.min_max_random_dd[0],
                                                                self.sim.control_panel.min_max_random_dd[1]
                                                                )

    def get_mean_q(self):
        mean_p = self.sim.control_panel.mean_process_time
        rho = self.sim.control_panel.aimed_utilization
        cv_a = 1
        if self.sim.control_panel.process_time_distribution == '2_erlang':
            cv_p = 0.5
        elif self.sim.control_panel.process_time_distribution == 'exponential':
            cv_p = 1
        else:
            raise Exception('cannot set queue for the given process time distribution')
        return mean_p * rho / (1 - rho) * (cv_a ** 2 + cv_p ** 2) / 2

    def get_mean_manufacturing_lead_time(self):
        mean_r = (len(self.sim.control_panel.manufacturing_process_layout) + 1) / 2
        mean_p = self.sim.control_panel.mean_process_time
        mean_q = self.get_mean_q()
        return mean_r * (mean_p + mean_q)

    def get_std_dev_manufacturing_lead_time_mm1(self):
        mean_p = self.sim.control_panel.mean_process_time
        rho = self.sim.control_panel.aimed_utilization
        mean_a = mean_p / rho
        # compute variance mm1 queue
        v_mm1 = 1/(mean_p - mean_a)**2

        # routing distribution params
        nr_of_routing = len(self.sim.control_panel.manufacturing_process_layout)
        prob_routing_j = 1 / nr_of_routing

        # assume independent variances
        result = 0
        for j, _ in enumerate(self.sim.control_panel.manufacturing_process_layout):
            result += (j + 1) * v_mm1
        return math.sqrt(prob_routing_j * result)

    def get_std_dev_manufacturing_lead_time_mg1(self):
        mean_p = self.sim.control_panel.mean_process_time
        rho = self.sim.control_panel.aimed_utilization
        mean_a = mean_p / rho
        mean_q = self.get_mean_q()
        # compute variance mm1 queue
        v_mg1 = mean_q**2 + (mean_a * (2/math.sqrt(2)))/(3*(1-rho))
        v = 0.5 ** 2 + v_mg1
        # routing distribution params
        nr_of_routing = len(self.sim.control_panel.manufacturing_process_layout)
        prob_routing_j = 1 / nr_of_routing
        # assume independent variances
        result = 0
        for j, _ in enumerate(self.sim.control_panel.manufacturing_process_layout):
            result += (j + 1) * math.sqrt(nr_of_routing) * v
        return math.sqrt(prob_routing_j * result)


class Order(object):
    def __init__(self, simulation):
        """
        object having all attributes of the an order
        :param simulation: simulation object stored in simulation_model.py
        :return: void
        """
        # general params
        self.sim = simulation
        self.identifier = 0
        self.name = ""

        # customer enquiry management params
        self.entry_time = self.sim.env.now
        self.due_date = self.sim.general_functions.random_due_date()

        # pool params
        self.released = False
        self.release_time = 0
        self.pool_time = 0
        self.finishing_time = 0

        # process params
        self.routing_sequence = random.sample(self.sim.control_panel.manufacturing_process_layout, random.randint(1, self.sim.control_panel.m))
        if self.sim.control_panel.general_flow_shop:
            self.routing_sequence.sort()  # GFS

        self.process_time = {}
        for work_centre in self.routing_sequence:
            if self.sim.control_panel.process_time_distribution == '2_erlang':
                self.process_time[work_centre] = \
                    self.sim.general_functions.two_erlang(
                        mean=self.sim.control_panel.mean_process_time
                        )
            elif self.sim.control_panel.process_time_distribution == 'exponential':
                self.process_time[work_centre] = \
                    self.sim.general_functions.exponential(
                        mean=self.sim.control_panel.mean_process_time
                        )
            else:
                raise Exception("no valid process time distribution selected")
        if self.sim.control_panel.dispatching_rule == "ODD":
            self.operational_due_dates = {}

        self.periodic_release_date = self.due_date - (len(self.routing_sequence)
                                                      * self.sim.control_panel.periodic_release_date_factor_k)


class Process(object):
    def __init__(self, simulation):
        # general params
        self.sim = simulation

        # set seeds for common random numbers
        self.random_generator = random.Random()
        self.random_generator.seed(999999)

        # import fixed variables
        self.mean_time_between_arrivals = self.sim.control_panel.mean_time_between_arrival
        self.warmup_period = self.sim.control_panel.warmup_period
        self.run_time = self.sim.control_panel.run_time
        self.number_of_runs = self.sim.control_panel.number_of_runs

    def generate_random_arrivals(self):
        """
        function that controls random order arrival. Finds next arrival time and initializes an order object.
        :return: void
        """
        i = 1
        while True:
            # new arrival, get order
            order = Order(simulation=self.sim)
            order.identifier = i
            order.name = ('Job%07d' % i)
            # send order to release process
            self.sim.env.process(self.sim.process.manufacturing_process(order=order))
            # get next arrival time and wait
            t = self.random_generator.expovariate(1 / self.mean_time_between_arrivals)
            yield self.sim.env.timeout(t)
            i += 1
            # break statement to stop simulation
            if self.sim.env.now >= (self.warmup_period + self.run_time) * self.number_of_runs:
                break

    def manufacturing_process(self, order):
        """
        the manufacturing process where orders follow a specific routing through the manufacturing process. (Closed
        queue variant)
        :param order: Order object
        :return: void
        """
        # order is released, collect data
        order.release_time = self.sim.env.now

        # adjust ODD according to Land et al., (2014)
        if self.sim.control_panel.dispatching_rule == "ODD":
            slack = order.due_date - self.sim.env.now
            if slack >= 0:
                for WC in order.routing_sequence:
                    order.operational_due_dates[WC] = self.sim.env.now + (order.routing_sequence.index(WC) + 1) * (
                                slack / len(order.routing_sequence))
            else:
                for WC in order.routing_sequence:
                    order.operational_due_dates[WC] = self.sim.env.now

        # loop to visit each work centre in routing
        for work_centre in order.routing_sequence:
            # request the aimed work centre for processing
            order.requested_work_centre = self.sim.control_panel.manufacturing_process[work_centre]
            # request with a certain level of priority
            if self.sim.control_panel.dispatching_rule == "FCFS":
                order.priority = self.sim.env.now
            elif self.sim.control_panel.dispatching_rule == "SPT":
                order.priority = order.process_time[work_centre]
            elif self.sim.control_panel.dispatching_rule == "ODD":
                order.priority = order.operational_due_dates[work_centre]
            else:
                raise Exception('Unknown dispatching rule defined')

            # make request
            req = order.requested_work_centre.request(priority=order.priority)
            # yield a request
            yield req
            # order in queue ---> wait for capacity
            # start processing
            yield self.sim.env.timeout(order.process_time[work_centre])
            # order is finished, start processing
            order.requested_work_centre.release(req)
            self.sim.data.accumulated_process_time += order.process_time[work_centre]
            # loop to next work centre or end processing

        # order finished processing, collect data
        self.data_collection_final(order=order)

        return

    def data_collection_final(self, order):
        """
        Collect data from finished order
        :param order: order object
        :return: void

        key list
            0: identifier
            1: throughput_time
            2: pool_time
            3: process_throughput_time
            4: lateness
            5: tardiness
            6: tardy
            7 - inf: else
        """
        # the finishing time
        order.finishing_time = self.sim.env.now

        # setup list
        df_list = list()

        # put all the order performance metrics into list
        df_list.append(order.identifier)
        df_list.append(order.finishing_time - order.entry_time)
        df_list.append(order.pool_time)
        df_list.append(order.finishing_time - order.release_time)
        df_list.append(order.finishing_time - order.due_date)
        df_list.append(max(0, (order.finishing_time - order.due_date)))
        df_list.append(max(0, self._heavenside(x=(order.finishing_time - order.due_date))))
        df_list.append((order.finishing_time - order.entry_time)/len(order.routing_sequence))

        # save list
        self.sim.data.append_run_list(result_list=df_list)
        return

    def _heavenside(self, x):
        if x > 0:
            return 1
        return -1

class SimulationModel(object):
    """
    Class containing the simulation model function the simulation instance (i.e. self) is passed in the other
    function outside this class as sim. This class uses all other object to run the model. More specifically:
        ControlPanel:       Contains all the settings for the simulation model.
        Environment:        Class from Simpy which allows to control the simulation generator functions.
        GeneralFunctions:   Class with various functions, i.e. a toolbox.
        Data:               Class with all the methods required to transform, store and manipulate all data
        Process:            Class with the simulation source and the manufacturing process.
    """

    def __init__(self, exp_number=1):
        """
        load all required classes to complete the model and the settings
        """
        # setup general params
        self.warm_up = True
        self.exp_number = exp_number

        # set seed for common random numbers
        self.random_generator = random.Random()
        self.random_generator.seed(999999)

        # import the Simpy environment
        self.env = simpy.Environment()

        # add general functionality to the model
        self.general_functions = GeneralFunctions(simulation=self)

        # get the model and policy control panel
        self.control_panel = ControlPanel(simulation=self, exp_number=exp_number)
        self.print_info = self.control_panel.print_info

        # get the data storage variables
        self.data = DataControl(simulation=self)

        # import process
        self.process: Process = Process(simulation=self)

        # declare variables
        self.source_process = None
        self.run_manager = None

    # the actual simulation function with all required SimPy settings---------------------------------------------------
    def sim_function(self):
        """
        initialling and timing of the generator functions
        :return: void
        """

        # initialize processes
        self.source_process = self.env.process(self.process.generate_random_arrivals())

        # activate data collection methods
        self.run_manager = self.env.process(SimulationModel.run_manager(self))

        # start simulation
        sim_time = (self.control_panel.warmup_period + self.control_panel.run_time) * \
                   self.control_panel.number_of_runs + 0.001
        self.env.run(until=sim_time)

        # simulation finished: save database and print final info
        self.data.save_dataset()

        if self.control_panel.print_final_info:
            #print(f"\nMean results of experiment:")
            print(self.data.experiment_database.describe().loc[['mean']].to_string(index=False))
            #print("\n")

    def run_manager(self):
        """
        The run manager managing processes during the simulation. Can perform the same actions in through cyclic
        manner. Currently, the run_manager managers printing information and the saving and processing of information.
        :return: void
        """
        while self.env.now < (
                self.control_panel.warmup_period + self.control_panel.run_time) * self.control_panel.number_of_runs:
            yield self.env.timeout(self.control_panel.warmup_period)
            # chance the warm_up status
            self.warm_up = True

            # update data
            self.data.run_update(warmup=self.warm_up)

            yield self.env.timeout(self.control_panel.run_time)
            # chance the warm_up status
            self.warm_up = False

            # update data
            self.data.run_update(warmup=self.warm_up)

            # print run info if required
            if self.print_info:
                self._print_run_info()

    def _print_run_info(self):
        # vital simulation results are given
        run_number = int(self.env.now / (self.control_panel.warmup_period + self.control_panel.run_time))
        index = run_number - 1
        # print info
        try:
            if index == 0:
                print(self.data.experiment_database.iloc[index:, ].to_string(index=False), end='\n')
            else:
                print('\n'.join(self.data.experiment_database.iloc[index:, ].to_string(index=False).split('\n')[1:]), end='\n')
        except (KeyError, IndexError):
            print("could not print simulation results")
        return


# activate the code
if __name__ == '__main__':
    # track run time
    start_time = time.time()

    # import simulation model and run simulation
    simulation = SimulationModel()
    simulation.sim_function()

    # compute run time
    t_time = (time.time() - start_time)
    t_hours = t_time // 60 // 60
    t_min = (t_time - (t_hours * 60 * 60)) // 60
    t_seconds = (t_time - (t_min * 60) - (t_hours * 60 * 60))

    print(f"\n\nExperiment finished"
          f"\nThe total run time"
          f"\n\tHours:      {t_hours}"
          f"\n\tMinutes:    {t_min}"
          f"\n\tSeconds:    {round(t_seconds, 2)}")
