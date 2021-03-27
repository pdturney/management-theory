#
# Table Growth All Pickles
#
# Peter Turney, March 1, 2021
#
# Read all fusion pickle files (fusion_storage.bin)
# and analyze all fusion events. 
#
import golly as g
import model_classes as mclass
import model_functions as mfunc
import model_parameters as mparam
import numpy as np
import pickle
import os
import re
import sys
#
# Number of steps to run Game of Life in order to estimate
# growth rates of fused seeds and parts of fused seeds. This
# is a dynamic variable in model_functions.py, calculated by
# the function dimensions(), but here it is a constant, so
# that all fused seeds are evaluated by the same standard.
# Also, score_pair() in model_functions.py uses a toroid,
# but we will use an infinite plane here.
#
num_steps = 1000
#
# Location of fusion_storage.bin files -- the input pickles.
#
fusion_dir = "C:/Users/peter/Peter's Projects" + \
             "/management-theory/Experiments/exper1"
#
fusion_files = [] # list of pickles
num_files = 18 # 18 fusion pickles
#
for i in range(num_files):
  fusion_files.append(fusion_dir + "/run" + str(i + 1) + \
    "/fusion_storage.bin")
#
# Open the fusion report file for writing.
#
report_path = "C:/Users/peter/Peter's Projects/management-theory" + \
              "/Experiments/exper1/table_growth_all_pickles.tsv"
report_handle = open(report_path, "w")
#
# Write table header.
#
report_handle.write(
  "run number\t" + \
  "fusion number\t" + \
  "whole seed birth number\t" + \
  "left seed growth\t" + \
  "right seed growth\t" + \
  "whole seed growth\t" + \
  "sum parts growth\t" + \
  "max parts growth\t" + \
  "whole seed growth > sum parts growth\t" + \
  "whole seed growth > max parts growth\t" + \
  "red cells growth\t" + \
  "blue cells growth\t" + \
  "orange cells growth\t" + \
  "green cells growth\t" + \
  "red manager\t" + \
  "blue manager\t" + \
  "manager-manager relation\t" + \
  "manager-worker relation\t" + \
  "worker-worker relation\n")
#
# Read and process each fusion file one-by-one. Each fusion 
# file contains several fusion seeds.
#
run_num = 1 # run_num ranges from 1 to 18
fusion_num = 1 # fusion_num ranges from 1 to 844
#
for fusion_file in fusion_files:
  fusion_handle = open(fusion_file, "ab+")
  fusion_handle.seek(0) # start at the beginning of the file
  fusion_list = []
  # read the pickle file into fusion_list
  while True:
    try:
      part = pickle.load(fusion_handle)
      fusion_list.append(part)
    except (EOFError, pickle.UnpicklingError):
      break
  fusion_handle.close()
  # iterate through the fusion events in the current fusion file
  # -- read four items at a time
  for (s2, s3, s4, n) in zip(*[iter(fusion_list)] * 4):
    # make a clean, empty hash table for storing statistics,
    # so we start over fresh each time through this loop
    stats_hash = {}
    stats_hash["run number"] = run_num
    stats_hash["fusion number"] = fusion_num
    stats_hash["whole seed birth number"] = n
    # growth of left seed, right seed, and whole fused seed
    mfunc.mono_growth(g, num_steps, s2, "left seed", stats_hash)
    mfunc.mono_growth(g, num_steps, s3, "right seed", stats_hash)
    mfunc.mono_growth(g, num_steps, s4, "whole seed", stats_hash)
    stats_hash["sum parts growth"] = \
      stats_hash["left seed growth"] + \
      stats_hash["right seed growth"]
    stats_hash["max parts growth"] = \
      max(stats_hash["left seed growth"], \
      stats_hash["right seed growth"])
    # difference between parts and whole
    stats_hash["whole seed growth > sum parts growth"] = \
      stats_hash["whole seed growth"] > stats_hash["sum parts growth"]
    stats_hash["whole seed growth > max parts growth"] = \
      stats_hash["whole seed growth"] > stats_hash["max parts growth"]
    # growth of red, blue, orange, green
    mfunc.quad_growth(g, num_steps, s2, s3, stats_hash)
    # manager-worker relations
    stats_hash["red manager"] = stats_hash["green cells growth"] > \
      (stats_hash["red cells growth"] + stats_hash["orange cells growth"])
    stats_hash["blue manager"] = stats_hash["orange cells growth"] > \
      (stats_hash["blue cells growth"] + stats_hash["green cells growth"])
    # note that we're adding Boolean values here, treating False as 0
    # and True as 1
    stats_hash["manager-manager relation"] = \
      ((stats_hash["red manager"] + stats_hash["blue manager"]) == 2)
    stats_hash["manager-worker relation"] = \
      ((stats_hash["red manager"] + stats_hash["blue manager"]) == 1)
    stats_hash["worker-worker relation"] = \
      ((stats_hash["red manager"]) + (stats_hash["blue manager"]) == 0)
    # table row
    report_handle.write(
      "{}\t".format(stats_hash["run number"]) + \
      "{}\t".format(stats_hash["fusion number"]) + \
      "{}\t".format(stats_hash["whole seed birth number"]) + \
      "{}\t".format(stats_hash["left seed growth"]) + \
      "{}\t".format(stats_hash["right seed growth"]) + \
      "{}\t".format(stats_hash["whole seed growth"]) + \
      "{}\t".format(stats_hash["sum parts growth"]) + \
      "{}\t".format(stats_hash["max parts growth"]) + \
      "{}\t".format(stats_hash["whole seed growth > sum parts growth"]) + \
      "{}\t".format(stats_hash["whole seed growth > max parts growth"]) + \
      "{}\t".format(stats_hash["red cells growth"]) + \
      "{}\t".format(stats_hash["blue cells growth"]) + \
      "{}\t".format(stats_hash["orange cells growth"]) + \
      "{}\t".format(stats_hash["green cells growth"]) + \
      "{}\t".format(stats_hash["red manager"]) + \
      "{}\t".format(stats_hash["blue manager"]) + \
      "{}\t".format(stats_hash["manager-manager relation"]) + \
      "{}\t".format(stats_hash["manager-worker relation"]) + \
      "{}\n".format(stats_hash["worker-worker relation"]))
    # 
    fusion_num += 1
  #
  run_num += 1
#
# Close the fusion report file.
#
report_handle.close()
#
#