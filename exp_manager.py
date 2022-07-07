"""
Project: ProcessSim
Made By: Arno Kasper
Version: 1.0.0
"""
import pandas as pd
import socket
import random
import warnings
import os
import simulationmodel as sim


class Experiment_Manager(object):

    # Creat a batch of experiments with a upper an lower limit
    def __init__(self, lower, upper):
        """
        initialize experiments integers
        :param lower: lower boundary of the exp number
        :param upper: upper boundary of the exp number
        """
        self.lower = lower
        self.upper = upper

        if self.lower > self.upper:
            raise Exception("lower exp number higher than upper exp number")

        self.count_experiment = 0
        self.exp_manager()

    def exp_manager(self):
        """
        define the experiment manager who controls the simulation model
        :return: void
        """
        # use a loop to illiterate multiple experiments from the exp_dat list
        for i in range(self.lower, (self.upper + 1)):
            # import simulation model and run
            self.sim = sim.SimulationModel(exp_number=i)
            self.sim.sim_function()

            # save the experiment
            self.saving_exp()

    def saving_exp(self):
        """
        save all the experiment data versions
        :return: void
        """
        # initialize params
        df = self.sim.data.experiment_database
        file_version = ".csv"  # ".xlsx"#".csv"#

        # get file directory
        path = self.get_directory()

        # create the experimental name
        exp_name = self.sim.model_panel.experiment_name

        # save file
        file = path + exp_name + file_version
        try:
            # save as csv file
            if file_version == ".csv":
                self.save_database_csv(file=file, database=df)

            # save as excel file
            elif file_version == ".xlsx":
                self.save_database_xlsx(file=file, database=df)

        except PermissionError:
            # failed to save, make a random addition to the name to save anyway
            from string import ascii_lowercase, digits
            random_genetator = random.Random()
            random_name = "random_"
            strings = []
            strings[:0] = ascii_lowercase + digits
            name_lenght = random_genetator.randint(1, len(strings) + 1)

            # build the name
            for j in range(0, name_lenght):
                random_genetator.shuffle(strings)
                random_name += strings[j]

            # change original name
            file = path + random_name + exp_name + file_version

            # save as csv file
            if file_version == ".csv":
                self.save_database_csv(file=file, database=df)

            # save as excel file
            elif file_version == ".xlsx":
                self.save_database_xlsx(file=file, database=df)

            # notify the user
            warnings.warn(f"Permission Error, saved with name {random_name + exp_name}", Warning)

        # add the experiment number for the next experiment
        self.count_experiment += 1

        if self.sim.model_panel.print_results:
            try:
                print(f"\nresults of experiment {exp_name}:")
                print(df.describe().loc[['mean']].to_string(index=False))
                print("\n")
            except (KeyError, IndexError):
                print("could not print simulation results")
                print(df.describe().loc[['mean']].to_string(index=False))

        print(f"simulation data saved with name:    {exp_name}")
        if self.sim.print_info:
            print(f"\tinput this experiment:      {self.sim.data.order_input_counter}")
            print(f"\toutput this experiment:     {self.sim.data.order_output_counter}")

    def save_database_csv(self, file, database):
        database.to_csv(file, index=False)

    def save_database_xlsx(self, file, database):
        writer = pd.ExcelWriter(file, engine='xlsxwriter')
        database.to_excel(writer, sheet_name='name', index=False)
        writer.save()

    def get_directory(self):
        # define different path options
        machine_name = socket.gethostname()
        path = ""
        # find path for specific machine
        if machine_name == "LAPTOP-HN4N26LU":
            path = "C:/Users/Arno_ZenBook/Dropbox/Professioneel/Research/Results/test/"
        elif machine_name[0:7] == "pg-node":
            path = "/data/p288125/"
        elif machine_name in ["WKS033389", "WKS052605"]:
            path = "C:/Users/P288125/Dropbox/Professioneel/Research/Results/test/"
        else:
            warnings.warn(f"{machine_name} is an unknown machine name ", Warning)
            path = os.path.abspath(os.getcwd())
            print(f"files are saved in {path}")
        return path
