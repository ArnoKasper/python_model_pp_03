from simpy import Environment, Event
from random import Random
import numpy as np
from scipy import stats
import socket
import warnings
import os
from string import ascii_lowercase, digits
from typing import Generator

from controlpanel import ModelPanel, PolicyPanel
from data_collection_and_storage import DataCollection
from generalfunctions import GeneralFunctions
from simsource import Demand
from generate import Generation
from process import Process
from release import Release
from inventory import Inventory
from supply import Supply
from systemstatedispatching import SystemStateDispatching


class SimulationModel(object):
    """
    class containing the simulation model function
    the simulation instance (i.e. self) is passed in the other function outside this class as sim
    """

    def __init__(self, exp_number: int = 1, print_info=True) -> None:
        # setup general params
        self.exp_number: int = exp_number
        self.warm_up: bool = True

        # Set seed for specifically process times and other random generators
        """
        various common random number streams are used
        - from the module Random(), this is used for orders, and the shop floor
        - from the module Numpy, this is for the inventory process
        - from the module 
        """
        # order random number stream
        self.random_generator: Random = Random()
        self.random_generator.seed(999999)

        # numpy common random number streams
        self.NP_random_generator = {}
        streams_for = ['inventory', 'supply']
        self.seed_sequence = np.random.SeedSequence(12345)
        self.child_seeds = self.seed_sequence.spawn(len(streams_for))
        streams = [np.random.default_rng(s) for s in self.child_seeds]
        for s, stream in enumerate(streams):
            self.NP_random_generator[streams_for[s]] = stream

        # import the Simpy environment
        self.env: Environment = Environment()

        # add general functionality to the model
        self.general_functions: GeneralFunctions = GeneralFunctions(
            simulation=self)

        # get the model and policy control panel
        self.model_panel: ModelPanel = ModelPanel(
            experiment_number=self.exp_number, simulation=self)
        self.policy_panel: PolicyPanel = PolicyPanel(
            experiment_number=self.exp_number, simulation=self)
        self.print_info: bool = print_info

        # get the data storage objects
        self.data: DataCollection = DataCollection(simulation=self)

        # import PPC
        self.release: Release = Release(simulation=self)
        self.inventory: Inventory = Inventory(simulation=self)
        self.system_state_dispatching: SystemStateDispatching = SystemStateDispatching(simulation=self)

        # import process
        self.supplier: Supply = Supply(simulation=self)
        self.process: Process = Process(simulation=self)

        # initialize demand
        self.demand: Demand = Demand(simulation=self)
        self.demand_process = None

        # initialize generation
        self.generation_process = {}
        self.generation: Generation = Generation(simulation=self)

        # activate data collection methods
        self.run_manager = self.env.process(SimulationModel.run_manager(self))

    def sim_function(self) -> None:
        """
        initialling and timing of the generator functions
        :return: void
        """
        # set the the length of the simulation (add one extra time unit to save result last run)
        if self.print_info:
            self.print_start_info()
        # start the generators
        self.generation.initialize_generation()

        self.demand_process = self.env.process(self.demand.generate_random_arrival_exp())

        # start simulation
        sim_time = (self.model_panel.WARM_UP_PERIOD +
                    self.model_panel.RUN_TIME) * self.model_panel.NUMBER_OF_RUNS + 0.001
        self.env.run(until=sim_time)
        # simulation finished, print final info
        if self.print_info:
            self.print_end_info()

    def run_manager(self) -> Generator[Event, None, None]:
        """
        The run manager managing processes during the simulation. Can perform the same actions in through cyclic
        manner. Currently, the run_manager managers printing information and the saving and processing of information.
        :return: void
        """
        while self.env.now < (
                self.model_panel.WARM_UP_PERIOD + self.model_panel.RUN_TIME) * self.model_panel.NUMBER_OF_RUNS:
            yield self.env.timeout(self.model_panel.WARM_UP_PERIOD)
            # chance the warm_up status
            self.warm_up = True
            # update data
            self.data.run_update(warmup=self.warm_up)
            yield self.env.timeout(self.model_panel.RUN_TIME)
            # chance the warm_up status
            self.warm_up = False
            # update data
            self.data.run_update(warmup=self.warm_up)
            # print run info if required
            if self.print_info:
                self.print_run_info()
        return

    def print_run_info(self):
        # vital simulation results are given
        run_number = int(self.env.now / (self.model_panel.WARM_UP_PERIOD + self.model_panel.RUN_TIME))
        index = run_number - 1
        # statistics
        try:
            statistics = self.replication_confidence_interval(run_number=run_number, criteria='mean_ttt')
        except (NameError, KeyError):
            statistics = 'could not compute statistics'
        # print info
        try:
            if index == 0:
                print(self.data.experiment_database.iloc[index:, ].to_string(
                    index=False), end=' ')
                print(statistics)
            else:
                print('\n'.join(self.data.experiment_database.iloc[index:, ].to_string(
                    index=False).split('\n')[1:]), end=' ')
                print(statistics)
        except (KeyError, IndexError):
            print("could not print simulation results")
        return

    def replication_confidence_interval(self, run_number, criteria):
        running_mean = self.data.experiment_database.loc[:, criteria].mean()
        current_std_dev = self.data.experiment_database.loc[:, criteria].std()
        confidence_int = stats.t.ppf(
            1 - 0.025, df=self.data.experiment_database.shape[0] - 1)
        confidence_int = confidence_int * \
                         (current_std_dev / np.sqrt(run_number))
        lower_confidence = round(running_mean - confidence_int, 4)
        upper_confidence = '%.4f' % round(running_mean + confidence_int, 4)
        deviation = '%.4f' % round(
            ((running_mean - lower_confidence) / running_mean) * 100, 4)
        lower_confidence = '%.4f' % lower_confidence
        running_mean = '%.4f' % round(running_mean, 4)
        return [running_mean, lower_confidence, upper_confidence, deviation]

    def saving_exp(self):
        """
        save all the experiment data versions
        :return: void
        """
        # initialize params
        df = self.data.experiment_database
        file_version = ".csv"

        # get file directory
        path = self.get_directory()

        # create the experimental name
        exp_name = self.model_panel.experiment_name

        # save file
        try:
            self.save_database_csv(file=path + exp_name + file_version,
                                   database=df
                                   )
        except PermissionError:
            # failed to save, make a random addition to the name to save anyway
            random_name = "random_"
            strings = []
            strings[:0] = ascii_lowercase + digits
            name_length = self.random_generator.randint(1, len(strings) + 1)
            # build the name
            for j in range(0, name_length):
                self.random_generator.shuffle(strings)
                random_name += strings[j]
            # try to save it again
            self.save_database_csv(file=path + random_name + exp_name + file_version,
                                   database=df
                                   )
            # notify the user
            warnings.warn(
                f"Permission Error, saved with name {random_name + exp_name}", Warning)
        # print info to the user
        if self.model_panel.print_results:
            try:
                print(f"\nresults of experiment {exp_name}:")
                df_print = df.describe().loc[['mean']].T
                df_print.insert(0, 'column', df.columns)
                print(df_print.to_string(index=False))
                print("\n")
            except (KeyError, IndexError):
                print("could not print simulation results")

        print(f"simulation data saved with name:    {exp_name}")
        if self.print_info:
            print(
                f"\tinput this experiment:      {self.data.order_input_counter}")
            print(
                f"\toutput this experiment:     {self.data.order_output_counter}")

    @staticmethod
    def save_database_csv(file, database):
        database.to_csv(file, index=False)
        return

    @staticmethod
    def get_directory():
        # define different path options
        machine_name = socket.gethostname()
        # find path for specific machine
        if machine_name == "LAPTOP-HN4N26LU":
            path = "C:/Users/Arno_ZenBook/Dropbox/Professioneel/Research/Results/test/"
        elif machine_name[0:7] == "pg-node":
            path = "/data/p288125/"
        elif machine_name in ["WKS033389", "WKS052605"]:
            path = "C:/Users/P288125/Dropbox/Professioneel/Research/Results/test/"
        else:
            warnings.warn(
                f"{machine_name} is an unknown machine name ", Warning)
            path = os.path.abspath(os.getcwd())
            print(f"files are saved in {path}")
        return path

    def print_start_info(self) -> None:
        print(
            f"Simulation starts with experiment: {self.model_panel.experiment_name}")
        print(
            f"Mean time between arrival: {self.model_panel.MEAN_TIME_BETWEEN_ARRIVAL}")
        return

    @staticmethod
    def print_end_info() -> None:
        print("Simulation ends")
        return

    @staticmethod
    def print_warmup_info() -> None:
        return print('Warm-up period finished')


if __name__ == "__main__":
    # import simulation model
    sim = SimulationModel()

    # run the simulation model until completion
    sim.sim_function()
    # sim.env.step() # go to one step
    # save database
    sim.saving_exp()
