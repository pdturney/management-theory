#
# Compare Random
#
# Peter Turney, January 22, 2021
#
# Compare an algorithm to a baseline, where each seed produced
# by the algorithm is compared to a random seed of the same
# dimensions and same density.
#
import golly as g
import model_classes as mclass
import model_functions as mfunc
import model_parameters as mparam
import numpy as np
import pickle
import os
import sys
#
# -----------------------------
# Get some input from the user.
# -----------------------------
#
[pickle_dir, analysis_dir, sorted_pickle_names, \
  smallest_pickle_size] = mfunc.choose_pickles(g)
#
# -----------------------------------------------------------------
# Initialize some variables and print them to the output.
# -----------------------------------------------------------------
#
# pickles
#
num_runs = len(sorted_pickle_names)
final_num = smallest_pickle_size
step_size = 1
#
# stats analysis file
#
basename = os.path.basename(os.path.normpath(analysis_dir))
analysis_path = analysis_dir + "/compare-random-" + \
  basename + ".tsv"
analysis_handle = open(analysis_path, "w") 
#
# parameters from model_parameters.py
#
width_factor = mparam.width_factor
height_factor = mparam.height_factor
time_factor = mparam.time_factor
num_trials = mparam.num_trials
#
mfunc.show_message(g, analysis_handle, "\n\nCompare Random\n\n")
#
for i in range(num_runs):
  message = sorted_pickle_names[i] + "\n"
  mfunc.show_message(g, analysis_handle, message)
#
mfunc.show_message(g, analysis_handle, "\n")
#
mfunc.show_message(g, analysis_handle, "\nwidth_factor = " + \
  str(width_factor) + "\n")
mfunc.show_message(g, analysis_handle, "height_factor = " + \
  str(height_factor) + "\n")
mfunc.show_message(g, analysis_handle, "time_factor = " + \
  str(time_factor) + "\n")
mfunc.show_message(g, analysis_handle, "num_trials = " + \
  str(num_trials) + "\n\n")
mfunc.show_message(g, analysis_handle, "path = " + \
  str(pickle_dir) + "\n\n")
#
mfunc.show_message(g, analysis_handle, \
  "Note that the numbers will change slightly each time this \n" + \
  "runs.\n\n")
#
# The TSV (tab separated value) file has the format:
#
# <generation number> <tab> <average fitness of algorithm vs baseline>
#
# If tha algorithm is more fit than the baseline for the given generation,
# then the average fitness will be greater than 0.5; otherwise it will
# be less than 0.5.
#
# -----------------------------------------------------------------
# For each generation, compare the algorithm to the baseline.
# -----------------------------------------------------------------
#
pop_size = mparam.pop_size
elite_size = mparam.elite_size
#
for i in range(0, final_num + 1, step_size):
  # for each run in generation i ...
  avg_fitnesses = []
  for run in range(num_runs):
    pickle_name = sorted_pickle_names[run] # log-2018-11-19-15h-40m-05s
    # read in X
    x_name = pickle_name + "-pickle-" + str(i) + ".bin"
    x_path = pickle_dir + x_name
    x_handle = open(x_path, "rb") # rb = read binary
    x_sample = pickle.load(x_handle)
    x_handle.close()
    # match each seed in x_sample with a random baseline seed
    # of the same dimensions -- the size of x_sample is
    # elite_size, the number of seeds in the elite pickles
    total_fitness = 0
    total_sample_size = 0
    for evolved_seed in x_sample:
      # so that the noise level here is comparable to the noise level
      # in compare_generations.py, generate the same number of random
      # seeds as there are seeds in the elite pickles
      for sample in range(num_runs * elite_size):
        # make a copy of evolved_seed and randomly shuffle the cells
        # in the new seed, so that the new randomized seed has the
        # same dimensions and the same density as evolved_seed
        random_seed = evolved_seed.shuffle()
        # compare the evolved seed to the random seed
        [random_score, evolved_score] = mfunc.score_pair(g, random_seed, \
          evolved_seed, width_factor, height_factor, time_factor, num_trials)
        total_fitness = total_fitness + evolved_score
        total_sample_size = total_sample_size + 1
    # calculate average fitness for the run
    avg_fitness = total_fitness / total_sample_size
    # convert to formatted string
    avg_fitnesses.append("{:.4f}".format(avg_fitness)) 
  # write out the fitness
  tab = "\t"
  mfunc.show_message(g, analysis_handle, \
    str(i) + tab + tab.join(avg_fitnesses) + "\n")
#
# Final message.
#
mfunc.show_message(g, analysis_handle, "\nAnalysis complete.\n")
analysis_handle.close()
#
#