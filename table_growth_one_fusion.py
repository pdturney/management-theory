#
# Table Growth One Fusion
#
# Peter Turney, February 27, 2021
#
# Read a fusion pickle file (fusion_storage.bin) and
# select one of the fusions. Show a movie of how the
# fusion changes with each time step.
#
# Also generate a TSV (tab separated values) file
# with the growth of the four colours in each time
# step. The file will be stored in the same directory
# as the fusion pickle file. Each row in the TSV file
# will have the following format:
#
# <time step> \t <red growth> \t <blue growth> 
# \t <orange growth> \t <green growth> \n
#
# TSV file suffix:
#
tsv_file_suffix = "four-colour-growth.tsv"
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
# Number of steps to run the Management Rule.
#
num_steps = 1000
#
# Ask the user to select the desired fusion pickle file.
#
fusion_path = g.opendialog("Choose a fusion pickle file",
              "fusion*.bin", g.getdir("app"))
#
g.note("Verify Selection\n\n" + \
       "Fusion pickle file:\n\n" + \
       fusion_path + "\n\n" + \
       "Exit now if this is incorrect.")
#
# Open the fusion pickle file -- "ab+" opens a file for 
# both appending and reading in binary mode.
#
fusion_handle = open(fusion_path, "ab+")
fusion_handle.seek(0) # start at the beginning of the file
#
# Read the fusion pickle file into a list.
#
fusion_list = []
#
while True:
  try:
    part = pickle.load(fusion_handle)
    fusion_list.append(part)
  except (EOFError, pickle.UnpicklingError):
    break
#
fusion_handle.close()
#
# Make a list of the birth numbers of all of the fusions
# in fusion_list and ask the user to select one of the fusions
# for a movie.
#
birth_num_list = []
# extract all "n" from fusion_list
for (s2, s3, s4, n) in zip(*[iter(fusion_list)] * 4):
  birth_num_list.append(n)
# break birth_num_list into chunks and convert it to a string
chars_per_line = 0
max_chars_per_line = 50
choice_string = ""
for i in range(len(birth_num_list)):
  if ((i + 1) == len(birth_num_list)):
    # last number, so don't add comma
    current_item = str(birth_num_list[i])
    if (chars_per_line < max_chars_per_line):
      # add last number to current line
      choice_string += current_item
    else:
      # add last number to new line
      choice_string += "\n" + current_item
  elif (chars_per_line < max_chars_per_line):
    # not at character limit yet, so add comma
    current_item = str(birth_num_list[i]) + ", "
    choice_string += current_item
    # update character count
    chars_per_line += len(current_item)
  else:
    # end of line, so add new line character
    choice_string += str(birth_num_list[i]) + ",\n"
    # reset character count for the next line
    chars_per_line = 0
# show instructions to the user
user_response = g.getstring(
  "Here is a list of the birth numbers of fusion seeds in\n" +
  "your chosen run of Model-S:\n\n" + \
  choice_string + "\n\n" + \
  "Enter one of the birth numbers and your desired speed\n" + \
  "in seconds per step, separated by a space.\n\n" + \
  "For example: 1823 0.5", "", "Choose a seed and a speed")
#
# Check for errors in user_response.
#
match = re.match("(\d+)\s+([\d\.]+)", user_response)
if match:
  birth_num = int(match[1])
  speed = float(match[2])
  if (speed < 0.0):
    speed = 0.0
else:
  g.note("Your input (" + user_response + \
         ") was not in the requested format.")
  quit()
# need to verify that birth_num is in birth_num_list
if (birth_num in birth_num_list):
  g.note("Your input (" + user_response + ") was accepted.")
else:
  g.note("Your requested birth number (" + str(birth_num) + \
         ") is not in the list.\nPlease try again.")
  quit()
#
# Create the full path for the TSV file and open a
# handle for writing.
#
# format:  <leaf directory>-<birth n>-four-colour-growth.tsv
# example: "run1-birth29-four-colour-growth.tsv
#
# extract the target directory from fusion_path -- we assume that the 
# the fusion pickle file is given by fusion_path and we assume that
# the TSV file will be stored in the same directory as the pickle file
run_directory = os.path.dirname(fusion_path)
# extract leaf directory from run_directory (so we know where it came from, 
# in case it gets moved)
leaf_dir = os.path.basename(os.path.normpath(run_directory))
tsv_dir = os.path.dirname(os.path.abspath(fusion_path))
tsv_file_name = leaf_dir + "-birth" + str(birth_num) + "-" + tsv_file_suffix
tsv_full_path = os.path.join(tsv_dir, tsv_file_name)
tsv_handle = open(tsv_full_path, "w")
#
# Extract the seeds for the given birth number.
#
for (s2, s3, s4, n) in zip(*[iter(fusion_list)] * 4):
  if (n == birth_num):
    part1 = s2
    part2 = s3
    break
#
# Run the Management rule with part1 and part2.
#
# initialize Golly
rule_name = "Management"
g.setalgo("QuickLife") # use "HashLife" or "QuickLife"
g.autoupdate(False) # do not update the view unless requested
g.new(rule_name) # initialize cells to state 0
g.setrule(rule_name) # make an infinite plane
# part1 and part2 (s2 and s3) are both using live state 1 (red),
# so we need to convert part2 to live state 2 (blue)
part2 = mfunc.change_live_state(part2, 2)
# join the parts
whole = mfunc.join_seeds(part1, part2)
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
# write the initial growth to the TSV file: it will be all zero:
# <time step> \t <red growth> \t <blue growth> 
# \t <orange growth> \t <green growth> \n
tsv_handle.write("0\t0\t0\t0\t0\n")
# loop through each step slowly so the user can see what's happening 
# -- to reduce jitter, only adjust fit() once every few seconds
# -- add a little extra when time_since_last_update is updated, in
# case speed is set to zero
time_since_last_update = 0.0
update_interval = 2.5
little_extra = 0.02
g.fit()
for i in range(num_steps):
  time.sleep(speed)
  time_since_last_update += speed + little_extra
  g.run(1)
  if (time_since_last_update > update_interval):
    g.fit()
    time_since_last_update = 0.0
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
  # calculate the growth
  time_step = i + 1
  red_growth = end_size[1] - start_size[1]
  blue_growth = end_size[2] - start_size[2]
  orange_growth = end_size[3] - start_size[3]
  green_growth = end_size[4] - start_size[4]
  # write to the file
  tsv_handle.write("{}\t{}\t{}\t{}\t{}\n".format(time_step,
    red_growth, blue_growth, orange_growth, green_growth))
  #
#
# close file handle
#
tsv_handle.close()
#
#