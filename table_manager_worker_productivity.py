#
# Table Manager Worker Productivity
#
# Peter Turney, February 28, 2021
#
# Run all 844 fusion seeds and store the results internally in
# a numpy tensor:
#
# tensor = 844 fusions x 1001 time steps x 5 colours
#
# - 844 fusion events from 18 fusion_storage.bin files
# - 1001 times steps in the Management game
# - 5 colours (white, red, orange, blue, green)
#
# - value in tensor cell = count of live cells for given triple
#   [fusion_num, step_num, colour_num]
#
# After this tensor has been filled with values, generate
# a table of the form:
#
# <step number> <avg live cells manager-manager> 
# <avg live cells manager-worker> <avg live cells worker-worker>
#
import golly as g
import model_classes as mclass
import model_functions as mfunc
import model_parameters as mparam
import numpy as np
import time
import pickle
import os
import re
import sys
#
# Parameter values for making the table.
#
num_steps = 1001 # number of time steps in the game
num_fusions = 844 # fusions contained in 18 fusion pickles
num_colours = 5 # 5 colours [white, red, blue, orange, green]
num_types = 3 # manager-manager, manager-worker, worker-worker
num_files = 18 # 18 fusion pickles
#
# Location of fusion_storage.bin files -- the input pickles.
#
fusion_dir = "C:/Users/peter/Peter's Projects" + \
             "/management-theory/Experiments/exper1"
#
fusion_files = [] # list of pickles
#
for i in range(num_files):
  fusion_files.append(fusion_dir + "/run" + str(i + 1) + \
    "/fusion_storage.bin")
#
# TSV (tab separated values) file for storing the table.
#
table_file = fusion_dir + "/table_manager_worker_productivity.tsv"
table_handle = open(table_file, "w")
table_handle.write("step num\tmanager-manager\tmanager-worker" + \
                   "\tworker-worker\n")
#
# Initialize the tensor.
#
tensor = np.zeros([num_fusions, num_steps, num_colours])
#
# Read and process each fusion file one-by-one. Each fusion 
# file contains several fusion seeds.
#
fusion_num = 0 # fusion_num ranges from 0 to 843
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
    part1 = s2
    part2 = s3
    # part1 and part2 (s2 and s3) are both using live state 1 (red),
    # so we need to convert part2 to live state 2 (blue)
    # -- mfunc.change_live_state() makes a copy, so the original is
    # not changed
    part2 = mfunc.change_live_state(part2, 2)
    # join the parts
    whole = mfunc.join_seeds(part1, part2)
    # initialize Golly
    rule_name = "Management"
    g.setalgo("QuickLife") # use "HashLife" or "QuickLife"
    g.autoupdate(False) # do not update the view unless requested
    g.new(rule_name) # initialize cells to state 0
    g.setrule(rule_name) # make an infinite plane
    # initialize the counts for the five states:
    # [white, red, blue, orange, green]
    start_size = [0, 0, 0, 0, 0] 
    end_size = [0, 0, 0, 0, 0]
    # copy whole into Golly 
    for x in range(whole.xspan):
      for y in range(whole.yspan):
        state = whole.cells[x][y]
        g.setcell(x, y, state)
        # update start_size and end_size
        start_size[state] += 1
        end_size[state] += 1
    # record the initial growth (time step 0) in the tensor
    # -- the intitial growth is necessarily zero for all colours
    step_num = 0
    for colour_num in range(num_colours):
      tensor[fusion_num, step_num, colour_num] = 0
    # iterate over the number of time steps
    for step_num in range(1, num_steps):
      g.run(1)
      g.update()
      # update end_size
      boundary = g.getrect()
      if (len(boundary) == 0): # if no live cells ...
        end_size = [0, 0, 0, 0, 0]
      else:
        cell_list = g.getcells(boundary)
        # if cell_list ends in 0, then delete the 0 -- note that stateN
        # will never be zero, since dead cells (state 0) are not included
        # in cell_list
        if (cell_list[-1] == 0):
          cell_list.pop()
        # end_size = [white, red, blue, orange, green]
        end_size = [0, 0, 0, 0, 0] # initialize
        for (x, y, state) in zip(*[iter(cell_list)] * 3):
          end_size[state] += 1 # update count
      # update the tensor
      for colour_num in range(num_colours):
        tensor[fusion_num, step_num, colour_num] = \
          end_size[colour_num] - start_size[colour_num]
      #       
    # increment fusion number
    fusion_num += 1
  #
#
# Now that we have filled the tensor, we can generate the table:
#
# <step number> <avg live cells manager-manager> 
# <avg live cells manager-worker> <avg live cells worker-worker>
#
for step_num in range(num_steps):
  #
  mm_count = 0 # manager-manager count (sample size)
  mw_count = 0 # manager-worker count (sample size)
  ww_count = 0 # worker-worker count (sample size)
  #
  mm_growth = 0 # manager-manager growth (sum of live cells)
  mw_growth = 0 # manager-worker growth (sum of live cells)
  ww_growth = 0 # worker-worker growth (sum of live cells)
  #
  for fusion_num in range(num_fusions):
    # 
    red    = tensor[fusion_num, step_num, 1]
    blue   = tensor[fusion_num, step_num, 2]
    orange = tensor[fusion_num, step_num, 3]
    green  = tensor[fusion_num, step_num, 4]
    #
    # red is a manager  = green > red + orange
    # red is a worker   = green <= red + orange
    #
    # blue is a manager = orange > blue + green
    # blue is a worker  = orange <= blue + green
    #
    # manager-manager relation = red and blue are both managers
    # manager-worker relation  = one is a manager and the other is a worker
    # worker-worker relation   = red and blue are both workers
    #
    red_manager  = (green > (red + orange))
    blue_manager = (orange > (blue + green))
    #
    growth = red + blue + orange + green
    #
    if (red_manager and blue_manager):
      mm_count  += 1
      mm_growth += growth
    elif (red_manager and not blue_manager):
      mw_count  += 1
      mw_growth += growth
    elif (blue_manager and not red_manager):
      mw_count  += 1
      mw_growth += growth
    else:
      ww_count  += 1
      ww_growth += growth
    #
  #
  assert mm_count + mw_count + ww_count == num_fusions
  #
  if (mm_count > 0):
    mm_avg_growth = mm_growth / mm_count
  else:
    mm_avg_growth = 0
  #
  if (mw_count > 0):
    mw_avg_growth = mw_growth / mw_count
  else:
    mw_avg_growth = 0
  #
  if (ww_count > 0):
    ww_avg_growth = ww_growth / ww_count
  else:
    ww_avg_growth = 0
  #
  table_handle.write("{}\t{:.3f}\t{:.3f}\t{:.3f}\n".format(step_num,
    mm_avg_growth, mw_avg_growth, ww_avg_growth))
  #
#
table_handle.close()
#
#