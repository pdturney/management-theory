#
# Table Growth One Pickle
#
# Peter Turney, February 27, 2021
#
# Read a fusion pickle file (fusion_storage.bin) and
# analyze the fusion events. In particular, we are
# interested in mutualism in symbiosis and the
# possibility of manager-worker relationships in 
# mutualist symbiosis.
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
# Note that the fitness of s2 and s3 is their fitness at the time
# when s4 is created, not their fitness at the time when they were
# created. On average, s2 and s3 will be less fit at the time when
# s4 is created than at the time when they were created, since the
# population is expected to become more fit as time passes.
#
# Open the fusion report file for writing.
#
report_path = fusion_path.replace(".bin", ".txt")
report_handle = open(report_path, "w")
#
# write table header
report_handle.write(
  "whole seed birth number\t" + \
  "left seed relative fitness\t" + \
  "right seed relative fitness\t" + \
  "whole seed relative fitness\t" + \
  "max left and right seed relative fitness\t" + \
  "whole relative fitness > max part relative fitness\t" + \
  "left seed growth\t" + \
  "right seed growth\t" + \
  "whole seed growth\t" + \
  "left seed growth + right seed growth\t" + \
  "whole seed growth > sum parts growth\t" + \
  "left seed absolute fitness\t" + \
  "right seed absolute fitness\t" + \
  "whole seed absolute fitness\t" + \
  "max left and right seed absolute fitness\t" + \
  "whole absolute fitness > max part absolute fitness\t" + \
  "red cells growth\t" + \
  "blue cells growth\t" + \
  "orange cells growth\t" + \
  "green cells growth\t" + \
  "red-orange growth increase with blue-green help\t" + \
  "blue-green growth increase with red-orange help\t" + \
  "growth increase with cooperation\t" + \
  "red-orange is less productive but makes net productivity increase\t" + \
  "blue-green is less productive but makes net productivity increase\t" + \
  "manager-worker relation exists\t" + \
  "two good cooperative workers with no manager\t" + \
  "two workers better off working alone\n")
# read four items at a time
for (s2, s3, s4, n) in zip(*[iter(fusion_list)] * 4):
  # make a clean, empty hash table for storing statistics,
  # so we start over fresh each time through this loop
  stats_hash = {}
  stats_hash["whole seed birth number"] = n
  stats_hash["left seed relative fitness"] = s2.fitness()
  stats_hash["right seed relative fitness"] = s3.fitness()
  stats_hash["whole seed relative fitness"] = s4.fitness()
  stats_hash["max left and right seed relative fitness"] = \
    max(stats_hash["left seed relative fitness"],
    stats_hash["right seed relative fitness"])
  # whole relative fitness > max part relative fitness
  stats_hash["whole relative fitness > max part relative fitness"] = \
    stats_hash["whole seed relative fitness"] > \
    max(stats_hash["left seed relative fitness"],
    stats_hash["right seed relative fitness"])
  # growth of left seed, right seed, and whole fused seed
  mfunc.mono_growth(g, num_steps, s2, "left seed", stats_hash)
  mfunc.mono_growth(g, num_steps, s3, "right seed", stats_hash)
  mfunc.mono_growth(g, num_steps, s4, "whole seed", stats_hash)
  stats_hash["left seed growth + right seed growth"] = \
    stats_hash["left seed growth"] + \
    stats_hash["right seed growth"]
  # difference between parts and whole
  stats_hash["whole seed growth > sum parts growth"] = \
    stats_hash["whole seed growth"] > \
    (stats_hash["left seed growth"] + \
    stats_hash["right seed growth"])
  # fitness compared with absolute versions of the given seed
  mfunc.compare_random(g, s2, "left seed", stats_hash)
  mfunc.compare_random(g, s3, "right seed", stats_hash)
  mfunc.compare_random(g, s4, "whole seed", stats_hash)
  stats_hash["max left and right seed absolute fitness"] = \
    max(stats_hash["left seed absolute fitness"], \
    stats_hash["right seed absolute fitness"])
  # whole absolute fitness > max part absolute fitness
  stats_hash["whole absolute fitness > max part absolute fitness"] = \
    stats_hash["whole seed absolute fitness"] > \
    max(stats_hash["left seed absolute fitness"], \
    stats_hash["right seed absolute fitness"])
  # growth of red, blue, orange, green
  mfunc.quad_growth(g, num_steps, s2, s3, stats_hash)
  # cooperation
  stats_hash["red-orange growth increase with blue-green help"] = \
    stats_hash["red cells growth"] + \
    stats_hash["orange cells growth"] - \
    stats_hash["left seed growth"]
  stats_hash["blue-green growth increase with red-orange help"] = \
    stats_hash["blue cells growth"] + \
    stats_hash["green cells growth"] - \
    stats_hash["right seed growth"]
  stats_hash["growth increase with cooperation"] = \
    stats_hash["red-orange growth increase with blue-green help"] + \
    stats_hash["blue-green growth increase with red-orange help"]
  # productivity
  stats_hash["red-orange is less productive but makes net productivity increase"] = \
    (stats_hash["red-orange growth increase with blue-green help"] < 0) \
    and (stats_hash["growth increase with cooperation"] > 0)
  stats_hash["blue-green is less productive but makes net productivity increase"] = \
    (stats_hash["blue-green growth increase with red-orange help"] < 0) \
    and (stats_hash["growth increase with cooperation"] > 0)
  # manager-worker relations
  stats_hash["manager-worker relation exists"] = \
    stats_hash["red-orange is less productive but makes net productivity increase"] \
    or stats_hash["blue-green is less productive but makes net productivity increase"]
  stats_hash["two good cooperative workers with no manager"] = \
    (stats_hash["red-orange growth increase with blue-green help"] > 0) \
    and (stats_hash["blue-green growth increase with red-orange help"] > 0)
  stats_hash["two workers better off working alone"] = \
    stats_hash["growth increase with cooperation"] < 0
  # table row
  report_handle.write(
    "{}\t".format(stats_hash["whole seed birth number"]) + \
    "{:.3f}\t".format(stats_hash["left seed relative fitness"]) + \
    "{:.3f}\t".format(stats_hash["right seed relative fitness"]) + \
    "{:.3f}\t".format(stats_hash["whole seed relative fitness"]) + \
    "{:.3f}\t".format(stats_hash["max left and right seed relative fitness"]) + \
    "{}\t".format(stats_hash["whole relative fitness > max part relative fitness"]) + \
    "{}\t".format(stats_hash["left seed growth"]) + \
    "{}\t".format(stats_hash["right seed growth"]) + \
    "{}\t".format(stats_hash["whole seed growth"]) + \
    "{}\t".format(stats_hash["left seed growth + right seed growth"]) + \
    "{}\t".format(stats_hash["whole seed growth > sum parts growth"]) + \
    "{:.3f}\t".format(stats_hash["left seed absolute fitness"]) + \
    "{:.3f}\t".format(stats_hash["right seed absolute fitness"]) + \
    "{:.3f}\t".format(stats_hash["whole seed absolute fitness"]) + \
    "{:.3f}\t".format(stats_hash["max left and right seed absolute fitness"]) + \
    "{}\t".format(stats_hash["whole absolute fitness > max part absolute fitness"]) + \
    "{}\t".format(stats_hash["red cells growth"]) + \
    "{}\t".format(stats_hash["blue cells growth"]) + \
    "{}\t".format(stats_hash["orange cells growth"]) + \
    "{}\t".format(stats_hash["green cells growth"]) + \
    "{}\t".format(stats_hash["red-orange growth increase with blue-green help"]) + \
    "{}\t".format(stats_hash["blue-green growth increase with red-orange help"]) + \
    "{}\t".format(stats_hash["growth increase with cooperation"]) + \
    "{}\t".format(stats_hash["red-orange is less productive but makes net productivity increase"]) + \
    "{}\t".format(stats_hash["blue-green is less productive but makes net productivity increase"]) + \
    "{}\t".format(stats_hash["manager-worker relation exists"]) + \
    "{}\t".format(stats_hash["two good cooperative workers with no manager"]) + \
    "{}\n".format(stats_hash["two workers better off working alone"]))
  # end of for loop
#
# Close the fusion report file.
#
report_handle.close()
#
#