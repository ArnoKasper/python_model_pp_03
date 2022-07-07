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


class ControlPanel(object):
    def __init__(self, simulation):
        """
        class that contains all the settings for the simulation model.
        """
        # general params
        self.sim = simulation
        self.print_info = True
        self.experiment_name = "compact_model"

        # experiment variables
        self.warmup_period = 3000
        self.run_time = 10000
        self.number_of_runs = 100

        # shop layout
        self.order_pool = simpy.FilterStore(self.sim.env)
        self.manufacturing_process_layout = ['WC1', 'WC2', 'WC3', 'WC4', 'WC5', 'WC6']
        self.manufacturing_process = dict()
        for _, work_centre in enumerate(self.manufacturing_process_layout):
            self.manufacturing_process[work_centre] = simpy.PriorityResource(self.sim.env, capacity=1)

        # customer enquiry management - Due Date determination
        self.min_max_random_dd = [30, 45]  # Due Dates intervals

        # release control (immediate release is LUMS COR = False)
        self.LUMS_COR = True
        self.workload_norm = 5
        self.periodic_release_period = 4.0

        # pool rules
        self.pool_rule = "PRD"
        self.periodic_release_date_factor_k = 3

        # workload params
        self.processed_workload = dict()
        self.released_workload = dict()

        # make dict
        for _, work_centre in enumerate(self.manufacturing_process_layout):
            self.processed_workload[work_centre] = 0
            self.released_workload[work_centre] = 0

        # order arrival params
        self.mean_time_between_arrival = 0.648
        self.mean_process_time = 1
        self.truncation_level = 4
        self.general_flow_shop = True  # False is pure job shop

        # dispatching
        """
        options available
            - FCFS: First Come First Serve
            - SPT: Shortest Process time 
            - ODD: Operational Due Date (following Land et al., 2014) 
        """
        self.dispatching_rule = "ODD"


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
            "tardy"
        ]

        # other
        self.accumulated_process_time = 0

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
        df["mean_throughput_time"] = df_run.loc[:, "throughput_time"].mean()
        df["std_throughput_time"] = df_run.loc[:, "throughput_time"].std()
        df["mean_pool_time"] = df_run.loc[:, "pool_time"].mean()
        df["std_pool_time"] = df_run.loc[:, "pool_time"].std()
        df["mean_process_throughput_time"] = df_run.loc[:, "process_throughput_time"].mean()
        df["std_process_throughput_time"] = df_run.loc[:, "process_throughput_time"].std()
        df["mean_lateness"] = df_run.loc[:, "lateness"].mean()
        df["std_lateness"] = df_run.loc[:, "lateness"].std()
        df["mean_tardiness"] = df_run.loc[:, "tardiness"].mean()
        df["std_tardiness"] = df_run.loc[:, "tardiness"].std()
        df["mean_squared_tardiness"] = (df_run.loc[:, "tardiness"] ** 2).mean()
        df["percentage_tardy"] = df_run.loc[:, "tardy"].sum() / df_run.shape[0]

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

    def random_due_date(self):
        """
        random due date assignment
        :return: value
        """
        return self.sim.env.now + self.random_generator.uniform(self.sim.control_panel.min_max_random_dd[0],
                                                                self.sim.control_panel.min_max_random_dd[1]
                                                                )


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
        self.routing_sequence = random.sample(self.sim.control_panel.manufacturing_process_layout, random.randint(1, 6))
        if self.sim.control_panel.general_flow_shop:
            self.routing_sequence.sort()  # GFS

        self.process_time = {}
        for work_centre in self.routing_sequence:
            self.process_time[work_centre] = \
                self.sim.general_functions.two_erlang_truncated(
                    mean_process_time=self.sim.control_panel.mean_process_time,
                    truncation=self.sim.control_panel.truncation_level
                    )
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
            self.sim.release_control.order_pool(order=order)
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
        order.pool_time = order.release_time - order.entry_time

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
                order.priority = order.identifier
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
            # Provide feedback for the continuous release mechanism of LUMS COR
            self.sim.release_control.finished_load(order=order, work_center=work_centre)
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

        # save list
        self.sim.data.append_run_list(result_list=df_list)
        return

    def _heavenside(self, x):
        if x > 0:
            return 1
        return -1


class ReleaseControl(object):
    def __init__(self, simulation):
        self.sim = simulation

        # set seeds for common random numbers
        self.random_generator = random.Random()
        self.random_generator.seed(999999)

    def order_pool(self, order):
        """
        the the pool with flow items before the process
        :param order: order object found in order.py
        :return: void
        """
        seq_priority = order.periodic_release_date
        # put each job in the pool
        job = [order, seq_priority, 1]
        self.sim.control_panel.order_pool.put(job)
        # release mechanisms
        if self.sim.control_panel.LUMS_COR:
            # feedback mechanism for continuous release
            work_center = order.routing_sequence[0]
            if self.control_work_centre_empty(work_center=work_center):
                order.process = self.sim.env.process(
                    self.sim.release_control.continuous_trigger(work_center=work_center))
        else:
            # immediate release method
            self.sim.env.process(self.sim.process.manufacturing_process(order=order))
        return

    def control_work_centre_empty(self, work_center):
        """
        controls if the queue is empty
        :param: work_center:
        :return: bool
        """
        in_the_workcentre = len(self.sim.control_panel.manufacturing_process[work_center].queue) + \
                            len(self.sim.control_panel.manufacturing_process[work_center].users)
        return in_the_workcentre == 0

    def remove_from_pool(self, release_now):
        """
        remove flow item from the pool
        :param release_now: list with parameters of the flow item
        :return: void
        """
        # create a variable that is equal to a item that is removed from the pool
        release_now[2] = 0
        # sort the queue
        self.sim.control_panel.order_pool.items.sort(key=itemgetter(2))
        # remove flow item from pool
        self.sim.control_panel.order_pool.get()

    def periodic_release(self):
        """
        Workload Control Periodic release using aggregate load. See workings in Land 2004.
        :return: void
        """
        periodic_interval = self.sim.control_panel.periodic_release_period
        while True:
            yield self.sim.env.timeout(periodic_interval)
            # reset the list of released orders
            release_now = []
            # sequence the orders currently in the pool
            self.sim.control_panel.order_pool.items.sort(key=itemgetter(1))
            # contribute the load from each item in the pool
            for _, order_list in enumerate(self.sim.control_panel.order_pool.items):
                order = order_list[0]
                # contribute the corrected aggregate load from for each workstation (Oosterman et al., 2000)
                for WC in order.routing_sequence:
                    self.sim.control_panel.released_workload[WC] += order.process_time[WC] / (
                                order.routing_sequence.index(WC) + 1)
                order.release = True
                # the new load situation is compared to the norm
                for WC in order.routing_sequence:
                    if self.sim.control_panel.released_workload[WC] - self.sim.control_panel.processed_workload[WC] \
                            > self.sim.control_panel.workload_norm:
                        order.release = False
                # if a norm has been violated the job is not released and the contributed load set back
                if not order.release:
                    for WC in order.routing_sequence:
                        self.sim.control_panel.released_workload[WC] -= order.process_time[WC] / (
                                order.routing_sequence.index(WC) + 1)
                # the released orders are collected into a list for release
                if order.release:
                    # orders for released are collected into a list
                    release_now.append(order_list)
                    # the orders are send to the process
                    self.sim.env.process(self.sim.process.manufacturing_process(order=order))
            # the released orders are removed from the pool using the remove from pool method
            for _, jobs in enumerate(release_now):
                self.sim.release_control.remove_from_pool(release_now=jobs)

    def continuous_trigger(self, work_center):
        """
        Workload Control: continuous release using aggregate load. See workings in Thürer et al, 2012.
        Part of LUMS COR
        :return: void
        """
        while True:
            # empty the release list
            trigger = 1
            # sort orders in the pool
            self.sim.control_panel.order_pool.items.sort(key=itemgetter(1))
            # control if there is any order available for the starving work centre from all items in the pool
            for _, order_list in enumerate(self.sim.control_panel.order_pool.items):
                order = order_list[0]
                # if there is an order available, than it can be released
                if order.routing_sequence[0] == work_center and trigger == 1:
                    trigger += 1
                    # contribute the load to the workload measures
                    for WC in order.routing_sequence:
                        self.sim.control_panel.released_workload[WC] += order.process_time[WC] / (
                                order.routing_sequence.index(WC) + 1)
                        order.release = True
                        # if an order turned out to be released, it is send to be removed from the pool
                    if order.release:
                        # send the order to the starting work centre
                        self.sim.env.process(self.sim.process.manufacturing_process(order=order))
                        # release order from the pool
                        self.sim.release_control.remove_from_pool(release_now=order_list)
            return
            yield

    def continuous_trigger_activation(self, work_center):
        """
        feedback mechanism for continuous release
        :param work_center
        :return: void
        """
        # control the if the the amount of orders in or before the work centre is equal or less than one
        if self.control_work_centre_empty(work_center=work_center):
            self.sim.env.process(self.sim.release_control.continuous_trigger(work_center=work_center))

    def finished_load(self, order, work_center):
        """
        add the processed load and trigger continuous release if required.
        :param order:
        :param work_center:
        :return: void
        """
        if self.sim.control_panel.LUMS_COR:
            self.sim.control_panel.processed_workload[work_center] += order.process_time[work_center] / (
                    order.routing_sequence.index(work_center) + 1)
            self.sim.release_control.continuous_trigger_activation(work_center=work_center)
        return


class SimulationModel(object):
    """
    Class containing the simulation model function the simulation instance (i.e. self) is passed in the other
    function outside this class as sim. This class uses all other object to run the model. More specifically:
        ControlPanel:       Contains all the settings for the simulation model.
        Environment:        Class from Simpy which allows to control the simulation generator functions.
        GeneralFunctions:   Class with various functions, i.e. a toolbox.
        Data:               Class with all the methods required to transform, store and manipulate all data
        ReleaseControl:     Class with all the tools needed to perform release control. Currently only periodic
                            and LUMS COR.
        Process:            Class with the simulation source and the manufacturing process.
    """

    def __init__(self):
        """
        load all required classes to complete the model and the settings
        """
        # setup general params
        self.warm_up = True

        # set seed for common random numbers
        self.random_generator = random.Random()
        self.random_generator.seed(999999)

        # import the Simpy environment
        self.env = simpy.Environment()

        # add general functionality to the model
        self.general_functions = GeneralFunctions(simulation=self)

        # get the model and policy control panel
        self.control_panel = ControlPanel(simulation=self)
        self.print_info = self.control_panel.print_info

        # get the data storage variables
        self.data = DataControl(simulation=self)

        # import release control
        self.release_control = ReleaseControl(simulation=self)

        # import process
        self.process: Process = Process(simulation=self)

        # declare variables
        self.release_periodic = "to_declare"
        self.source_process = "to_declare"
        self.run_manager = "to_declare"

    # the actual simulation function with all required SimPy settings---------------------------------------------------
    def sim_function(self):
        """
        initialling and timing of the generator functions
        :return: void
        """
        # activate release control
        if self.control_panel.LUMS_COR:
            self.release_periodic = self.env.process(self.release_control.periodic_release())

        # initialize processes
        self.source_process = self.env.process(self.process.generate_random_arrivals())

        # activate data collection methods
        self.run_manager = self.env.process(SimulationModel.run_manager(self))

        # set the the length of the simulation (add one extra time unit to save result last run)
        if self.print_info:
            self._print_start_info()

        # start simulation
        sim_time = (self.control_panel.warmup_period + self.control_panel.run_time) * \
                   self.control_panel.number_of_runs + 0.001
        self.env.run(until=sim_time)

        # simulation finished: save database and print final info
        self.data.save_dataset()

        if self.print_info:
            print(f"\nMean results of experiment:")
            print(self.data.experiment_database.describe().loc[['mean']].to_string(index=False))
            print("\n")
            self._print_end_info()

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

            # print run info if required
            if self.print_info:
                self._print_warmup_info()

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

    def _print_start_info(self):
        print("Simulation starts")
        return


    def _print_warmup_info(self):
        return print('Warm-up period finished')

    def _print_run_info(self):
        # vital simulation results are given
        run_number = int(self.env.now / (self.control_panel.warmup_period + self.control_panel.run_time))
        index = run_number - 1

        # make progress bar
        delta = 100
        progress = "["
        step = delta / self.control_panel.number_of_runs

        for i in range(1, 101):
            if run_number * step > i:
                progress = progress + "="
            elif run_number * step == i:
                progress = progress + ">"
            else:
                progress = progress + "."
        progress = progress + f"] {round(run_number / self.control_panel.number_of_runs * 100, 2)}%"
        print(f"run number {run_number}", progress)
        # print info
        print(self.data.experiment_database.iloc[index:, ].to_string(index=False))
        return

    def _print_end_info(self):
        print("Simulation ends")
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
