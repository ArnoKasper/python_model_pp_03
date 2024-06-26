"""
Project: ProcessSim
Made By: Arno Kasper
Version: 1.0.0
"""
import sys
from exp_manager import Experiment_Manager
import time

# track run time
start_time = time.time()

experiment_number = int(sys.argv[1])

# activate the simulation (automatic model)
Experiment_Manager(experiment_number, experiment_number)

# provide essential experimental information
t_time = (time.time() - start_time)
t_hours = t_time // 60 // 60
t_min = (t_time - (t_hours * 60 * 60)) // 60
t_seconds = (t_time - (t_min * 60) - (t_hours * 60 * 60))

print(f"\n\nExperiment {experiment_number} is finished"
      f"\nThe total run time"
      f"\n\tHours:      {t_hours}"
      f"\n\tMinutes:    {t_min}"
      f"\n\tSeconds:    {round(t_seconds, 2)}")
