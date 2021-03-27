#
# Photo Fusion
#
# Peter Turney, February 8, 2021
#
# Read a fusion pickle file (fusion_storage.bin) and
# make photos of the fusion events.
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
# Number of steps to run Game of Life or Immigration Rule or
# Management Rule.
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
# The list fusion_list is a repeating sequence of four items:
#
# [s2, s3, s4, n, ..., s2, s3, s4, n]
#
# - s2 is part of s4 (after rotation)
# - s3 is part of s4 (after rotation)
# - s4 is the fusion of s2 and s3
# - s4 is the n-th child born
#
# For each [s2, s3, s4, n] tuple, we will create X photos:
#
# (1) a photo of the red seed s2 in its initial state (left part = red = state 1)
# (2) a photo of the red seed s2 in its final state
# (3) a photo of the blue seed s3 in its initial state (right part = blue = state 2)
# (4) a photo of the blue seed s3 in its final state
# (5) a photo of the fused seed s4 in its initial state (left/red & right/blue)
# (6) a photo of the fused seed s4 in its final state using the Immigration Rule
# (7) a photo of the fused seed s4 in its final state using the Management Rule
#
# The seven files will be assigned names of the following form:
#
# format:  <leaf directory>-<birth n>-<photo type: 1 to 7>.<file type: png>
# example: "run1-birth29-photo1.png
#
# extract the target directory from fusion_path -- we assume that the 
# the fusion pickle file is given by fusion_path and we assume that
# the photos will be stored in the same directory as the pickle file
photo_directory = os.path.dirname(fusion_path)
# extract leaf directory from photo_directory (so we know where it came from, 
# in case it gets moved)
leaf_dir = os.path.basename(os.path.normpath(photo_directory))
# allow time for Golly image to stabilize before entering loop below
time.sleep(2)
# pause between images, in seconds
pause = 0.1
#
# read four items at a time
for (s2, s3, s4, n) in zip(*[iter(fusion_list)] * 4):
  # file 1: a photo of the red seed s2 in its initial state 
  # (left part = red = state 1)
  file_path = photo_directory + "/" + leaf_dir + "-birth" + \
              str(n) + "-photo1.png"
  rule_name = "Immigration"
  seed_list = [s2]
  live_states = [1]
  steps = 0 # initial state
  description = "child number " + str(n) + ", left part, red, " + \
                "initial state, Immigration"
  mfunc.snap_photo(g, file_path, rule_name, seed_list, live_states, \
                   steps, description, pause)
  # file 2: a photo of the red seed s2 in its final state 
  # (left part = red = state 1)
  file_path = photo_directory + "/" + leaf_dir + "-birth" + \
              str(n) + "-photo2.png"
  rule_name = "Immigration"
  seed_list = [s2]
  live_states = [1]
  steps = num_steps # final state
  description = "child number " + str(n) + ", left part, red, " + \
                "final state, Immigration"
  mfunc.snap_photo(g, file_path, rule_name, seed_list, live_states, \
                   steps, description, pause)
  # file 3: a photo of the blue seed s3 in its initial state 
  # (right part = blue = state 2)
  file_path = photo_directory + "/" + leaf_dir + "-birth" + \
              str(n) + "-photo3.png"
  rule_name = "Immigration"
  seed_list = [s3]
  live_states = [2]
  steps = 0 # initial state
  description = "child number " + str(n) + ", right part, blue, " + \
                "initial state, Immigration"
  mfunc.snap_photo(g, file_path, rule_name, seed_list, live_states, \
                   steps, description, pause)
  # file 4: a photo of the red seed s3 in its final state 
  # (right part = blue = state 2)
  file_path = photo_directory + "/" + leaf_dir + "-birth" + \
              str(n) + "-photo4.png"
  rule_name = "Immigration"
  seed_list = [s3]
  live_states = [2]
  steps = num_steps # final state
  description = "child number " + str(n) + ", right part, blue, " + \
                "final state, Immigration"
  mfunc.snap_photo(g, file_path, rule_name, seed_list, live_states, \
                   steps, description, pause)
  # file 5: a photo of the fused seed s4 in its initial state 
  # (left/red & right/blue)
  file_path = photo_directory + "/" + leaf_dir + "-birth" + \
              str(n) + "-photo5.png"
  rule_name = "Immigration"
  seed_list = [s2, s3]
  live_states = [1, 2]
  steps = 0 # initial state
  description = "child number " + str(n) + ", right red, left blue, " + \
                "initial state, Immigration"
  mfunc.snap_photo(g, file_path, rule_name, seed_list, live_states, \
                   steps, description, pause)
  # file 6: a photo of the fused seed s4 in its final state 
  # (red, blue)
  file_path = photo_directory + "/" + leaf_dir + "-birth" + \
              str(n) + "-photo6.png"
  rule_name = "Immigration"
  seed_list = [s2, s3]
  live_states = [1, 2]
  steps = num_steps # final state
  description = "child number " + str(n) + ", right red, left blue, " + \
                "final state, Immigration"
  mfunc.snap_photo(g, file_path, rule_name, seed_list, live_states, \
                   steps, description, pause)
  # file 7: a photo of the fused seed s4 in its final state 
  # (red, blue, orange, green)
  file_path = photo_directory + "/" + leaf_dir + "-birth" + \
              str(n) + "-photo7.png"
  rule_name = "Management"
  seed_list = [s2, s3]
  live_states = [1, 2]
  steps = num_steps # final state
  description = "child number " + str(n) + ", right red, left blue, " + \
                "final state, Management"
  mfunc.snap_photo(g, file_path, rule_name, seed_list, live_states, \
                   steps, description, pause)
#
#