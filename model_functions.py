"""
Model Functions

Peter Turney, February 9, 2021
"""
import golly as g
import model_classes as mclass
import model_parameters as mparam
import random as rand
import numpy as np
import copy
import time
import pickle
import os
import re
import sys
import pyautogui # tool for taking photos of the screen
"""
Various functions for working with Golly
"""
#
# show_message(g, log_handle, message) -- returns NULL
#
def show_message(g, log_handle, message):
  """
  A function for writing a message to both the Golly window
  and the log file.
  """
  log_handle.write(message)
  g.show(message)
#
# set_mag(g) -- returns mag
#
def set_mag(g):
  """
  A function for setting the Golly screen magnification
  """
  # the maximum of the X span and the Y span
  g_maxspan = np.amax([g.getwidth(), g.getheight()])
  # the Golly magnification ratio is 2 to the power of mag
  if (g_maxspan < 80):
    mag = 5 # 2^5 = 32
  elif (g_maxspan < 160):
    mag = 4 # 2^4 = 16
  elif (g_maxspan < 320):
    mag = 3 # 2^3 = 8
  elif (g_maxspan < 640):
    mag = 2 # 2^2 = 4
  elif (g_maxspan < 1280):
    mag = 1 # 2^1 = 2
  else:
    mag = 0 # 2^0 = 1
  return mag
#
# show_parameters() -- returns a list of parameters and values
#
def show_parameters():
  """
  Make a list of the parameters in mparam and show
  the value of each parameter.
  """
  parameter_names = sorted(dir(mparam))
  display_list = []
  for name in parameter_names:
    # skip over system names
    # - system names have the form "__file__"
    if (name[0] != "_"): 
      value = str(getattr(mparam, name))
      display_list.append(name + " = " + value)
  return display_list
#
# get_minmax(g) -- returns [g_xmin, g_xmax, g_ymin, g_ymax]
#
def get_minmax(g):
  """
  Calculate the min and max of the Golly toroid coordinates
  """
  # get height and width
  g_xspan = g.getwidth()
  g_yspan = g.getheight()
  # calculate min and max
  g_xmin = - int(g_xspan / 2)
  g_xmax = g_xspan + g_xmin
  g_ymin = - int(g_yspan / 2)
  g_ymax = g_yspan + g_ymin
  #
  return [g_xmin, g_xmax, g_ymin, g_ymax]
#
# count_pops(g) -- returns [count1, count2]
#
def count_pops(g):
  """
  Count the populations of state 1 (red) and state 2 (blue)
  """
  # find the min and max of the Golly toroid coordinates
  [g_xmin, g_xmax, g_ymin, g_ymax] = get_minmax(g)
  #
  count1 = 0
  count2 = 0
  #
  for x in range(g_xmin, g_xmax):
    for y in range(g_ymin, g_ymax):
      a = g.getcell(x, y)
      if (a == 1):
        count1 = count1 + 1
      if (a == 2):
        count2 = count2 + 1
  #
  return [count1, count2]
#
# initialize_population(pop_size, s_xspan, s_yspan, seed_density)
# -- returns population
#
def initialize_population(pop_size, s_xspan, s_yspan, seed_density):
  """
  Randomly initialize the population of seeds.
  """
  #
  # Initialize the population: a list of seeds.
  #
  # Here a seed is an initial Game of Life pattern (it is
  # not a random number seed).
  #
  population = []
  #
  for i in range(pop_size):
    # Make an empty seed (all zeros). 
    seed = mclass.Seed(s_xspan, s_yspan, pop_size) 
    # Randomly set some cells to state 1 (red).
    seed.randomize(seed_density)  
    # Set the count of living cells.
    seed.num_living = seed.count_ones()
    # Set the position of the new seed in the population array.
    seed.address = i 
    # Add the seed to the population.
    population.append(seed) 
    #
  return population
#
# dimensions(s1, s2, width_factor, height_factor, time_factor)
# -- returns [g_width, g_height, g_time]
#
def dimensions(s1, s2, width_factor, height_factor, time_factor):
  """
  Define the dimensions of the Golly universe, based on the
  sizes of the two seeds and various multiplicative factors.
  """
  #
  # Suggested values:
  #
  #   width_factor  = 6.0
  #   height_factor = 3.0
  #   time_factor   = 6.0
  #
  assert width_factor > 2.0 # need space for two seeds, left and right
  assert height_factor > 1.0 # need space for tallest seed
  assert time_factor > 1.0 # time should increase with increased space
  #
  # Find the maximum of the dimensions of the two seeds.
  #
  max_size = np.amax([s1.xspan, s1.yspan, s2.xspan, s2.yspan])
  #
  # Apply the various factors.
  #
  g_width = int(max_size * width_factor)
  g_height = int(max_size * height_factor)
  g_time = int((g_width + g_height) * time_factor)
  #
  return [g_width, g_height, g_time]
#
# score_pair(g, seed1, seed2, width_factor, height_factor, \
#   time_factor, num_trials) -- returns [score1, score2]
#
def score_pair(g, seed1, seed2, width_factor, height_factor, \
  time_factor, num_trials):
  """
  Put seed1 and seed2 into the Immigration Game g and see which 
  one wins and which one loses. Note that this function does
  not update the histories of the seeds. For updating histories,
  use update_history().
  """
  #
  # Make copies of the original two seeds, so that the following
  # manipulations do not change the originals.
  #
  s1 = copy.deepcopy(seed1)
  s2 = copy.deepcopy(seed2)
  #
  # Check the number of living cells in the seeds. If the number
  # is zero, it is probably a mistake. The number is initially
  # set to zero and it should be updated when the seed is filled
  # with living cells. We could use s1.count_ones() here, but
  # we're trying to be efficient by counting only once and 
  # storing the count.
  #
  assert s1.num_living > 0
  assert s2.num_living > 0
  #
  # Initialize scores
  #
  score1 = 0.0
  score2 = 0.0
  #
  # Run several trials with different rotations and locations.
  #
  for trial in range(num_trials):
    #
    # Randomly rotate and flip s1 and s2
    #
    s1 = s1.random_rotate()
    s2 = s2.random_rotate()
    #
    # Switch cells in the second seed (s2) from state 1 (red) to state 2 (blue)
    #
    s2.red2blue()
    #
    # Rule file
    #
    rule_name = "Immigration"
    #
    # Set toroidal universe of height yspan and width xspan
    # Base the s1ze of the universe on the s1zes of the seeds
    #
    # g = the Golly universe
    #
    [g_width, g_height, g_time] = dimensions(s1, s2, \
      width_factor, height_factor, time_factor)
    #
    # set algorithm -- "HashLife" or "QuickLife"
    #
    g.setalgo("QuickLife") # use "HashLife" or "QuickLife"
    g.autoupdate(False) # do not update the view unless requested
    g.new(rule_name) # initialize cells to state 0
    g.setrule(rule_name + ":T" + str(g_width) + "," + str(g_height)) # make a toroid
    #
    # Find the min and max of the Golly toroid coordinates
    #
    [g_xmin, g_xmax, g_ymin, g_ymax] = get_minmax(g)
    #
    # Set magnification for Golly viewer
    #
    g.setmag(set_mag(g))
    #
    # Randomly place seed s1 somewhere in the left s1de of the toroid
    #
    s1.insert(g, g_xmin, -1, g_ymin, g_ymax)
    #
    # Randomly place seed s2 somewhere in the right s1de of the toroid
    #
    s2.insert(g, +1, g_xmax, g_ymin, g_ymax)
    #
    # Run for a fixed number of generations.
    # Base the number of generations on the sizes of the seeds.
    # Note that these are generations ins1de one Game of Life, not
    # generations in an evolutionary sense. Generations in the 
    # Game of Life correspond to growth and decay of a phenotype,
    # whereas generations in evolution correspond to the reproduction
    # of a genotype.
    #
    g.run(g_time) # run the Game of Life for g_time time steps
    g.update() # need to update Golly to get counts
    #
    # Count the populations of the two colours. State 1 = red = seed1.
    # State 2 = blue = seed2.
    #
    [count1, count2] = count_pops(g)
    #
    # We need to make an adjustment to these counts. We don't want to 
    # use the total count of living cells; instead we want to use
    # the increase in the number of living cells over the course of
    # the contest between the two organisms. The idea here is that
    # we want to reward seeds according to their growth during the
    # contest, not according to their initial states. This should
    # avoid an evolutionary bias towards larger seeds simply due
    # to size rather than due to functional properties. It should
    # also encourage efficient use of living cells, as opposed to
    # simply ignoring useless living cells.
    #
    # s1.num_living = initial number of living cells in s1
    # s2.num_living = initial number of living cells in s2
    #
    if (s1.num_living < count1):
      count1 = count1 - s1.num_living
    else:
      count1 = 0
    #
    if (s2.num_living < count2):
      count2 = count2 - s2.num_living
    else:
      count2 = 0
    #
    # Now we are ready to determine the winner.
    #
    if (count1 > count2):
      score1 = score1 + 1.0
    elif (count2 > count1):
      score2 = score2 + 1.0
    else:
      score1 = score1 + 0.5
      score2 = score2 + 0.5
    #
  #
  # Normalize the scores
  #
  score1 = score1 / num_trials
  score2 = score2 / num_trials
  #
  return [score1, score2]
#
# update_history(g, pop, i, j, width_factor, height_factor, \
#   time_factor, num_trials) -- returns NULL
#
def update_history(g, pop, i, j, width_factor, height_factor, \
  time_factor, num_trials):
  """
  Put the i-th and j-th seeds into the Immigration Game g and
  see which one wins and which one loses. The history of the 
  seeds will be updated in pop.
  """
  #
  # If i == j, let's just call it a tie.
  #
  if (i == j):
    pop[i].history[i] = 0.5
    return
  #
  # Call score_pair()
  #
  [scorei, scorej] = score_pair(g, pop[i], pop[j], width_factor, \
    height_factor, time_factor, num_trials)
  #
  # Update pop[i] and pop[j] with the new scores. 
  #
  pop[i].history[j] = scorei
  pop[j].history[i] = scorej
  # 
  # returns NULL
  # 
#
# update_similarity(pop, i, j) -- returns NULL
#
def update_similarity(pop, i, j):
  """
  Calculate the similarity between the two given seeds and 
  update their internal records with the result.
  """
  #
  # If i == j, the similarity score is the maximum.
  #
  if (i == j):
    pop[i].similarities[i] = 1.0
    return
  #
  # Calculate the similarity and update the population record.
  #
  sim = similarity(pop[i], pop[j])
  pop[i].similarities[j] = sim
  pop[j].similarities[i] = sim
  # 
  # returns NULL
  # 
#
# find_top_seeds(population, sample_size) -- returns sample_pop
#
def find_top_seeds(population, sample_size):
  """
  Find the best (fittest) sample_size seeds in the population.
  """
  pop_size = len(population)
  assert pop_size > sample_size
  assert sample_size > 0
  # calculate fitness for each seed in the population, from their history
  scored_pop = []
  for i in range(pop_size):
    item = [population[i].fitness(), population[i]]
    scored_pop.append(item)
  # sort population in order of decreasing fitness (reverse=True)
  scored_pop.sort(key = lambda x: x[0], reverse=True) # sort by fitness
  # take the top sample_size items from scored_pop and
  # remove their attached fitness numbers
  sample_pop = []
  for i in range(sample_size):
    sample_pop.append(scored_pop[i][1]) # drop fitness number
  # return the cleaned-up list of sample_size seeds
  return sample_pop
#
# random_sample(population, sample_size) -- returns sample_pop
#
def random_sample(population, sample_size):
  """
  Get a random sample of sample_size seeds from the population.
  """
  #
  # To avoid duplicates in the sample, randomize the order of the
  # population and then take the first sample_size seeds
  # from the randomized list.
  #
  pop_size = len(population)
  assert pop_size > sample_size
  assert sample_size > 0
  # attach a random number to each seed in the population
  randomized_pop = []
  for i in range(pop_size):
    # item = [random real number between 0 and 1, the i-th seed]
    item = [rand.uniform(0, 1), population[i]]
    randomized_pop.append(item)
  # sort randomized_pop in order of the attached random numbers
  randomized_pop.sort(key = lambda x: x[0]) # sort by random number
  # take the top sample_size items from randomized_pop and
  # remove their attached random numbers
  sample_pop = []
  for i in range(sample_size):
    sample_pop.append(randomized_pop[i][1]) # drop random number
  # return the cleaned-up list of sample_size seeds
  return sample_pop
#
# find_best_seed(sample) -- returns best_seed
#
def find_best_seed(sample):
  """
  In the list of seeds in sample, find the seed (not necessarily
  unique) with maximum fitness.
  """
  sample_size = len(sample)
  assert sample_size > 0
  best_seed = sample[0]
  best_score = best_seed.fitness()
  for i in range(len(sample)):
    if (sample[i].fitness() > best_score):
      best_seed = sample[i]
      best_score = best_seed.fitness()
  return best_seed
#
# find_worst_seed(sample) -- returns worst_seed
#
def find_worst_seed(sample):
  """
  In the list of seeds in sample, find the seed (not necessarily
  unique) with minimum fitness.
  """
  sample_size = len(sample)
  assert sample_size > 0
  worst_seed = sample[0]
  worst_score = worst_seed.fitness()
  for i in range(len(sample)):
    if (sample[i].fitness() < worst_score):
      worst_seed = sample[i]
      worst_score = worst_seed.fitness()
  return worst_seed
#
# average_fitness(sample) -- returns average
#
def average_fitness(sample):
  """
  Given a list of sample seeds, return their average fitness,
  relative to the whole population.
  """
  sample_size = len(sample)
  assert sample_size > 0
  total_fitness = 0.0
  for i in range(len(sample)):
    total_fitness = total_fitness + sample[i].fitness()
  average = total_fitness / sample_size
  return average
#
# archive_elite(population, elite_size, log_directory, log_name, run_id_number) 
# -- returns NULL
#
def archive_elite(population, elite_size, log_directory, log_name, run_id_number):
  """
  Store an archive file of the elite members of the population,
  for future testing. The elite consists of the top elite_size
  most fit seeds in the current population.
  """
  history_sample = find_top_seeds(population, elite_size)
  history_name = log_name + "-pickle-" + str(run_id_number)
  history_path = log_directory + "/" + history_name + ".bin"
  history_handle = open(history_path, "wb") # wb = write binary
  pickle.dump(history_sample, history_handle)
  history_handle.close()
  # 
  # returns NULL
  # 
#
# fusion_storage(s2, s3, s4, n) -- returns NULL
#
def fusion_storage(s2, s3, s4, n):
  """
  After fusion has occurred, store the parts (s2, s3) and their
  fusion (s4) in a binary file for future analysis and inspection.
  The seed s4 is the n-th child born.
  """
  # make a file name for storage
  fusion_path = mparam.log_directory + "/fusion_storage.bin"
  # "ab+" opens a file for both appending and reading in binary mode
  fusion_handle = open(fusion_path, "ab+")
  # store the seeds and the generation number
  pickle.dump(s2, fusion_handle)    # s2 is part of s4 (after rotation)
  pickle.dump(s3, fusion_handle)    # s3 is part of s4 (after rotation)
  pickle.dump(s4, fusion_handle)    # s4 is the fusion of s2 and s3
  pickle.dump(n, fusion_handle)     # s4 is n-th child
  # close handle
  fusion_handle.close()
  # 
  # returns NULL
  #
#
# similarity(seed0, seed1) -- returns similarity
#
def similarity(seed0, seed1):
  """
  Measure the bit-wise similarity of two seeds. If the seeds
  have different sizes, return zero.
  """
  # Make sure the seeds are the same size.
  if (seed0.xspan != seed1.xspan):
    return 0.0
  if (seed0.yspan != seed1.yspan):
    return 0.0
  # Initialize count.
  num_agree = 0.0
  # Count agreements.
  for x in range(seed0.xspan):
    for y in range(seed0.yspan):
      if (seed0.cells[x][y] == seed1.cells[x][y]):
        num_agree = num_agree + 1.0
  # Calculate a similarity score ranging from zero to one.
  similarity = num_agree / (seed0.xspan * seed0.yspan)
  # Return the degree of similarity between the two seeds.
  return similarity
#
# find_similar_seeds(target_seed, pop, min_similarity, max_similarity)
# -- returns similar_seeds
# 
def find_similar_seeds(target_seed, pop, min_similarity, max_similarity):
  """
  Given a target seed, find seeds in the population with similarities
  to the target in the range from min_similarity to max_similarity.
  This function assumes that target_seed is in the population and
  the list target_seed.similarities is up-to-date. 
  """
  similar_seeds = []
  for i in range(len(pop)):
    if ((target_seed.similarities[i] >= min_similarity) and \
      (target_seed.similarities[i] <= max_similarity) and \
      (target_seed.address != i)):
      similar_seeds.append(pop[i])
  # return the seeds that satisfy the conditions
  return similar_seeds
#
# mate(seed0, seed1) -- returns child_seed
#
def mate(seed0, seed1):
  """
  Apply crossover to seed0 and seed1. We only have one crossover point,
  because multiple crossover points would be more disruptive to the
  structure of the seeds.
  """
  # This function is designed with the assumption that the seeds are 
  # the same size.
  assert seed0.xspan == seed1.xspan
  assert seed0.yspan == seed1.yspan
  # Note the spans of seed0 and seed1.
  xspan = seed0.xspan
  yspan = seed0.yspan
  # Randomly swap the seeds. Because s0 is always the top part of
  # a split that cuts across the Y axis and the left part of a split 
  # that cuts across the X axis, we need to swap the seeds in order
  # to add some variety.
  if (rand.uniform(0, 1) < 0.5):
    s0 = seed0
    s1 = seed1
  else:
    s0 = seed1
    s1 = seed0
  # Initialize the child to zero.
  child_seed = mclass.Seed(xspan, yspan, mparam.pop_size) 
  # Randomly choose whether to split on the X axis or
  # the Y axis.
  if (rand.uniform(0, 1) < 0.5):
    # Choose the Y axis split point. There will always be
    # at least one row on either side of the split point.
    assert yspan > 1
    y_split_point = rand.randrange(yspan - 1)
    for x in range(xspan):
      for y in range(yspan):
        if (y <= y_split_point):
          child_seed.cells[x][y] = s0.cells[x][y]
        else:
          child_seed.cells[x][y] = s1.cells[x][y]
  else:
    # Choose the X axis split point. There will always be
    # at least one column on either side of the split point.
    assert xspan > 1
    x_split_point = rand.randrange(xspan - 1)
    for x in range(xspan):
      for y in range(yspan):
        if (x <= x_split_point):
          child_seed.cells[x][y] = s0.cells[x][y]
        else:
          child_seed.cells[x][y] = s1.cells[x][y]
  # Return the resulting child.
  return child_seed
#
# uniform_asexual(candidate_seed, pop, n) -- returns [pop, message]
#
def uniform_asexual(candidate_seed, pop, n):
  """
  Create a new seed by randomly mutating an existing seed. The
  new seed is generated by selecting a parent seed and flipping
  bits in the parent. The size of the seed does not change; it
  is uniform.
  """
  # The most fit member of the tournament.
  s0 = candidate_seed
  # Mutate the best seed to make a new child. The only mutation
  # here is flipping bits.
  mutation_rate = mparam.mutation_rate
  s1 = copy.deepcopy(s0)
  s1.flip_bits(mutation_rate)
  s1.num_living = s1.count_ones() # update count of living cells
  # Find the least fit old seed in the population. It's not a problem
  # if there are ties.
  s2 = find_worst_seed(pop)
  # Now we have:
  #
  # s0 = fit parent seed
  # s1 = the mutated new child
  # s2 = the least fit old seed, which will be replaced by the mutated child
  #
  # Replace the least fit old seed in the population (s2) with the
  # new child (s1).
  i = s2.address # find the position of the old seed (s2)
  s1.address = i # copy the old position of the old seed into s1, the child
  pop[i] = s1 # replace s2 (old seed) in population (pop) with s1 (new child)
  # Build a history for the new seed, by matching it against all seeds
  # in the population.
  width_factor = mparam.width_factor
  height_factor = mparam.height_factor
  time_factor = mparam.time_factor
  num_trials = mparam.num_trials
  pop_size = len(pop)
  for j in range(pop_size):
    update_history(g, pop, i, j, width_factor, height_factor, \
      time_factor, num_trials)
    update_similarity(pop, i, j)
  # Report on the new history of the new seed
  message = "Run: {}".format(n) + \
    "  Parent fitness (s0): {:.3f}".format(s0.fitness()) + \
    "  Child fitness (s1): {:.3f}".format(s1.fitness()) + \
    "  Replaced seed fitness (s2): {:.3f}\n".format(s2.fitness())
  # It is possible that s1 is worse than s2, if there was a bad mutation in s1.
  # Let's not worry about that, since s1 will soon be replaced if it is less
  # fit than the least fit seed (that is, s2).
  return [pop, message]
#
# variable_asexual(candidate_seed, pop, n, max_seed_area) 
# -- returns [pop, message]
#
def variable_asexual(candidate_seed, pop, n, max_seed_area):
  """
  Create a new seed by randomly mutating, growing, and shrinking
  an existing seed. The new seed is generated by selecting a parent 
  seed and randomly flipping bits, removing rows and columns, or
  adding rows and columns. The size of the seed is variable; it 
  may increase or decrease in size.
  """
  # The most fit member of the tournament.
  s0 = candidate_seed
  # Mutate the best seed to make a new child. The mutations here
  # are flipping bits, removing rows and columns (shrinking), and
  # adding rows and columns (growing).
  prob_grow = mparam.prob_grow
  prob_flip = mparam.prob_flip
  prob_shrink = mparam.prob_shrink
  seed_density = mparam.seed_density
  mutation_rate = mparam.mutation_rate
  s1 = copy.deepcopy(s0)
  s1 = s1.mutate(prob_grow, prob_flip, prob_shrink, seed_density, mutation_rate)
  s1.num_living = s1.count_ones() # update count of living cells
  # Make sure the area of the new seed is not greater than the maximum.
  # If it is too big, then default to uniform_asexual reproduction.
  if ((s1.xspan * s1.yspan) > max_seed_area):
    return uniform_asexual(candidate_seed, pop, n)
  # Find the least fit old seed in the population. It's not a problem
  # if there are ties.
  s2 = find_worst_seed(pop)
  # Now we have:
  #
  # s0 = fit parent seed
  # s1 = the mutated new child
  # s2 = the least fit old seed, which will be replaced by the mutated child
  #
  # Replace the least fit old seed in the population (s2) with the
  # new child (s1).
  i = s2.address # find the position of the old seed (s2)
  s1.address = i # copy the old position of the old seed into s1, the child
  pop[i] = s1 # replace s2 (old seed) in population (pop) with s1 (new child)
  # Build a history for the new seed, by matching it against all seeds
  # in the population.
  width_factor = mparam.width_factor
  height_factor = mparam.height_factor
  time_factor = mparam.time_factor
  num_trials = mparam.num_trials
  pop_size = len(pop)
  for j in range(pop_size):
    update_history(g, pop, i, j, width_factor, height_factor, \
      time_factor, num_trials)
    update_similarity(pop, i, j)
  # Report on the new history of the new seed
  message = "Run: {}".format(n) + \
    "  Parent fitness (s0): {:.3f}".format(s0.fitness()) + \
    "  Child fitness (s1): {:.3f}".format(s1.fitness()) + \
    "  Replaced seed fitness (s2): {:.3f}\n".format(s2.fitness())
  # It is possible that s1 is worse than s2, if there was a bad mutation in s1.
  # Let's not worry about that, since s1 will soon be replaced if it is less
  # fit than the least fit seed (that is, s2).
  return [pop, message]
#
# sexual(candidate_seed, pop, n, max_seed_area) -- returns [pop, message]
#
def sexual(candidate_seed, pop, n, max_seed_area):
  """
  Create a new seed either asexually or sexually. First a single parent
  is chosen from the population. If a second parent can be found that
  is sufficiently similar to the first parent, then the child will have
  two parents (sexual reproduction). If no similar second parent can be
  found, then the child will have one parent (asexual reproduction).
  """
  # Let s0 be the most fit member of the tournament.
  s0 = candidate_seed
  # Find similar seeds in the population (members of the same species).
  min_similarity = mparam.min_similarity
  max_similarity = mparam.max_similarity
  similar_seeds = find_similar_seeds(s0, pop, min_similarity, max_similarity)
  num_similar_seeds = len(similar_seeds)
  # If no similar seeds were found, then use variable asexual reproduction.
  if (num_similar_seeds == 0):
    return variable_asexual(candidate_seed, pop, n, max_seed_area)
  # Run a new tournament to select a second seed s1 as a mate for s0.
  tournament_size = mparam.tournament_size
  if (num_similar_seeds <= tournament_size):
    s1 = find_best_seed(similar_seeds)
  else:
    tournament_sample = random_sample(similar_seeds, tournament_size)
    s1 = find_best_seed(tournament_sample)
  # Mate the parents to make a new child.
  s2 = mate(s0, s1)
  # Mutate the child.
  prob_grow = mparam.prob_grow
  prob_flip = mparam.prob_flip
  prob_shrink = mparam.prob_shrink
  seed_density = mparam.seed_density
  mutation_rate = mparam.mutation_rate
  s3 = s2.mutate(prob_grow, prob_flip, prob_shrink, seed_density, mutation_rate)
  s3.num_living = s3.count_ones() # update count of living cells
  # Make sure the area of the new seed is not greater than the maximum.
  # If it is too big, then default to uniform_asexual reproduction.
  if ((s3.xspan * s3.yspan) > max_seed_area):
    return uniform_asexual(candidate_seed, pop, n)
  # Find the least fit old seed in the population. It's not a problem
  # if there are ties.
  s4 = find_worst_seed(pop)
  # Now we have:
  #
  # s0 = parent 0
  # s1 = parent 1
  # s2 = the new child, before mutation
  # s3 = the mutated new child
  # s4 = the least fit old seed, which will be replaced by the mutated child
  #
  # Replace the least fit old seed in the population (s4) with the
  # new child (s3).
  i = s4.address # find the position of the old seed (s4)
  s3.address = i # copy the old position of the old seed into s3, the child
  pop[i] = s3 # replace s4 (old seed) in population (pop) with s3 (new child)
  # Build a history for the new seed, by matching it against all seeds
  # in the population.
  width_factor = mparam.width_factor
  height_factor = mparam.height_factor
  time_factor = mparam.time_factor
  num_trials = mparam.num_trials
  pop_size = len(pop)
  for j in range(pop_size):
    update_history(g, pop, i, j, width_factor, height_factor, \
      time_factor, num_trials)
    update_similarity(pop, i, j)
  # Report on the new history of the new seed
  message = "Run: {}".format(n) + \
    "  Parent 0 fitness (s0): {:.3f}".format(s0.fitness()) + \
    "  Parent 1 fitness (s1): {:.3f}".format(s1.fitness()) + \
    "  Child fitness (s3): {:.3f}".format(s3.fitness()) + \
    "  Replaced seed fitness (s4): {:.3f}\n".format(s4.fitness())
  # It is possible that s3 is worse than s4, if there was a bad mutation in s3.
  # Let's not worry about that, since s3 will soon be replaced if it is less
  # fit than the least fit seed (that is, s4).
  return [pop, message]
#
# fusion(candidate_seed, pop, n, max_seed_area) 
# -- returns [pop, message]
#
def fusion(candidate_seed, pop, n, max_seed_area):
  """
  Fuse two seeds together. Randomly rotate the seeds before
  joining them. Let's put one seed on the left and the other 
  seed on the right. Insert one empty column between the two 
  seeds, as a kind of buffer, so that the two seeds do not 
  immediately interact. This empty column also helps fission
  later on, to split joined seeds at the same point where they
  were initially joined.
  """
  # The most fit member of the tournament.
  s0 = candidate_seed
  # Run another tournament to select a second seed. The second
  # seed might be identical to the first seed. That's OK.
  tournament_size = mparam.tournament_size
  tournament_sample = random_sample(pop, tournament_size)
  s1 = find_best_seed(tournament_sample)
  # If the flag fusion_test_flag is set to 1, then randomize s1
  # by shuffling its cells. This operation is expected to reduce
  # the fitness of the new fusion seed. Usually fusion_test_flag
  # should be set to 0. Note that s1.shuffle() makes a copy, so the
  # original of s1 is not affected by the shuffling.
  if (mparam.fusion_test_flag == 1):
    s1 = s1.shuffle()
  # Randomly rotate the seeds. These rotations (s2 and s3) are copies. 
  # The originals (s0 and s1) are not affected by the rotations.
  s2 = s0.random_rotate()
  s3 = s1.random_rotate()
  # Get dimensions for the new fusion seed.
  pop_size = mparam.pop_size
  xspan = s2.xspan + s3.xspan + 1 # left width + right width + empty gap
  yspan = max(s2.yspan, s3.yspan) # the larger of the two heights
  # Make sure the area of the new seed is not greater than the maximum.
  # If it is too big, then default to sexual reproduction.
  if ((xspan * yspan) > max_seed_area):
    return sexual(candidate_seed, pop, n, max_seed_area)
  # Copy s2 into the left side of s4.
  s4 = mclass.Seed(xspan, yspan, pop_size) # cells initialized to zero
  for x in range(s2.xspan):
    for y in range(s2.yspan):
      s4.cells[x][y] = s2.cells[x][y]
  # Copy s3 into the right side of s4.
  for x in range(s3.xspan):
    for y in range(s3.yspan):
      s4.cells[x + s2.xspan + 1][y] = s3.cells[x][y]
  # Update count of living cells
  s4.num_living = s4.count_ones()
  # Find the least fit old seed in the population. It's not a problem
  # if there are ties.
  s5 = find_worst_seed(pop)
  # Now we have:
  #
  # s0 = seed 0
  # s1 = seed 1
  # s2 = rotated seed 0
  # s3 = rotated seed 1
  # s4 = the fusion of s2 and s3
  # s5 = the least fit old seed, which will be replaced by s4
  #
  # NOTE: we're not applying mutation here, because this is not a form
  # of reproduction. It's a merger of two seeds. 
  #
  # Replace the least fit old seed in the population (s5) with the
  # new fusion seed (s4).
  i = s5.address # find the position of the old seed (s5)
  s4.address = i # copy the old position of the old seed into s4, the new fusion seed
  pop[i] = s4 # replace s5 (old seed) in population (pop) with s4 (new fusion seed)
  # Build a history for the new seed, by matching it against all seeds
  # in the population.
  width_factor = mparam.width_factor
  height_factor = mparam.height_factor
  time_factor = mparam.time_factor
  num_trials = mparam.num_trials
  for j in range(pop_size):
    update_history(g, pop, i, j, width_factor, height_factor, \
      time_factor, num_trials)
    update_similarity(pop, i, j)
  # If the flag immediate_symbiosis_flag is set to "1", then
  # we must test to see whether s4 is more fit than both s1 and s2.
  if (mparam.immediate_symbiosis_flag == 1):
    if ((s0.fitness() >= s4.fitness()) or (s1.fitness() >= s4.fitness)):
      # If either of the parts (s0 or s1) has a fitness greater than
      # or equal to the fitness of s4, then default to sexual reproduction.
      # Symbiosis means that the whole is more fit than the parts.
      # When the flag immediate_symbiosis_flag is set to "1", we
      # insist that symbiosis should happen immediately, rather than
      # hoping that it will happen in some future generation.
      return sexual(candidate_seed, pop, n, max_seed_area)
  # Report on the new history of the new seed.
  message = "Run: {}".format(n) + \
    "  Seed 0 fitness (s0): {:.3f}".format(s0.fitness()) + \
    "  Seed 1 fitness (s1): {:.3f}".format(s1.fitness()) + \
    "  Fusion fitness (s4): {:.3f}".format(s4.fitness()) + \
    "  Replaced seed fitness (s5): {:.3f}\n".format(s5.fitness())
  # Store the new seed (s4) and its parts (s2, s3) for future analysis.
  fusion_storage(s2, s3, s4, n)
  # Return with the updated population and a message.
  return [pop, message]
#
# fission(candidate_seed, pop, n, max_seed_area) 
# -- returns [pop, message]
#
def fission(candidate_seed, pop, n, max_seed_area):
  """
  In fusion, we use the convention of putting one seed on 
  the left and the other seed on the right, before we fuse
  the two seeds. In fission, we assume that fission will 
  split the left part from the right part. Find the most 
  sparse column in the candidate seed and split the seed along 
  this column. If both parts are at least the minimum allowed 
  seed size, randomly choose one of them. If only one part
  is at least the minimum allowed seed size, choose that
  one part. If neither part is at least the minimum allowed 
  seed size, then default to sexual reproduction.
  """
  # The most fit member of the tournament.
  s0 = candidate_seed
  # Minimum xspan. Only xspan is relevant, since we are splitting
  # left and right parts.
  min_s_xspan = mparam.min_s_xspan
  # See whether the seed is big enough to split. If it is too
  # small, then default to sexual reproduction.
  if (s0.xspan <= min_s_xspan):
    return sexual(candidate_seed, pop, n, max_seed_area)
  # Location of the most sparse column. If there are ties, the
  # first sparse column will be chosen.
  sparse_col = np.argmin(np.sum(s0.cells, axis = 0))
  # Left and right parts.
  left_cells = s0.cells[0:sparse_col, :]
  right_cells = s0.cells[(sparse_col + 1):, :]
  # Initialize a seed for the left or right part.
  s1 = copy.deepcopy(s0)
  # If both parts are big enough, randomly choose one of them.
  if ((left_cells.shape[0] >= min_s_xspan) \
    and (right_cells.shape[0] >= min_s_xspan)):
    if (rand.uniform(0, 1) < 0.5):
      s1.cells = left_cells
    else:
      s1.cells = right_cells
  # If only the left part is big enough, use the left part.
  elif (left_cells.shape[0] >= min_s_xspan):
    s1.cells = left_cells
  # If only the right part is big enough, use the right part.
  elif (right_cells.shape[0] >= min_s_xspan):
    s1.cells = right_cells
  # If neither part is big enough, use sexual reproduction
  else: 
    return sexual(candidate_seed, pop, n, max_seed_area)
  # Set the correct dimensions for the new seed
  s1.xspan = s1.cells.shape[0]
  s1.yspan = s1.cells.shape[1]
  # Update count of living cells
  s1.num_living = s1.count_ones()
  # Find the least fit old seed in the population. It's not a problem
  # if there are ties.
  s2 = find_worst_seed(pop)
  # Now we have:
  #
  # s0 = seed 0
  # s1 = left or right side of seed 0
  # s2 = the least fit old seed, which will be replaced by s1
  #
  # Replace the least fit old seed in the population (s2) with the
  # chosen part (s1).
  i = s2.address # find the position of the old seed (s2)
  s1.address = i # copy the old position of the old seed into s1
  pop[i] = s1 # replace s2 (old seed) in population (pop) with s1
  # Build a history for the new seed, by matching it against all seeds
  # in the population.
  width_factor = mparam.width_factor
  height_factor = mparam.height_factor
  time_factor = mparam.time_factor
  num_trials = mparam.num_trials
  pop_size = len(pop)
  for j in range(pop_size):
    update_history(g, pop, i, j, width_factor, height_factor, \
      time_factor, num_trials)
    update_similarity(pop, i, j)
  # Report on the new history of the new seed
  message = "Run: {}".format(n) + \
    "  Whole fitness (s0): {:.3f}".format(s0.fitness()) + \
    "  Fragment fitness (s1): {:.3f}".format(s1.fitness()) + \
    "  Replaced seed fitness (s2): {:.3f}\n".format(s2.fitness())
  # Return with the updated population and a message.
  return [pop, message]
#
# symbiotic(candidate_seed, pop, n, max_seed_area) 
# -- returns [pop, message]
#
def symbiotic(candidate_seed, pop, n, max_seed_area):
  """
  Create a new seed by joining two existing seeds (fusion) or
  by splitting one seed into two seeds (fission). If fission
  is chosen, only one of the two resulting seeds is used.
  If neither fission nor fusion is chosen, we default to 
  sexual reproduction.
  """
  # Decide whether to use fission, fusion, or sexual reproduction.
  # To avoid bias, it makes sense to set these two probabilities to
  # the same value. Because fusion can result in large seeds, which
  # will slow down the simulation, it makes sense to set the
  # probability of fusion relatively low.
  #
  prob_fission = mparam.prob_fission
  prob_fusion = mparam.prob_fusion
  #
  uniform_random = rand.uniform(0, 1)
  #
  if (uniform_random < prob_fission):
    # this will be invoked with a probability of prob_fission
    return fission(candidate_seed, pop, n, max_seed_area)
  elif (uniform_random < (prob_fission + prob_fusion)):
    # this will be invoked with a probability of prob_fusion
    return fusion(candidate_seed, pop, n, max_seed_area)
  else:
    # if neither fission nor fusion, then sexual reproduction
    return sexual(candidate_seed, pop, n, max_seed_area)
#
# hash_pickles(pickle_list) -- returns pickle_hash
#
def hash_pickles(pickle_list):
  """
  Assume we have a list of pickle files of the following general form:
     ------------------------------------------------
     log-2019-02-22-12h-45m-00s-pickle-0.bin,
     log-2019-02-22-12h-45m-00s-pickle-1.bin, 
     ...
     log-2019-02-22-12h-45m-00s-pickle-100.bin,
     log-2019-02-22-12h-45m-12s-pickle-0.bin,
     log-2019-02-22-12h-45m-12s-pickle-1.bin, 
     ...
     log-2019-02-22-12h-45m-12s-pickle-100.bin
     ------------------------------------------------
  We split each pickle name into a base part ("log-2019-02-22-12h-45m-00s")
  and a numerical part ("0", "1", ..., "100") and we return a hash table
  that maps each unique base part to the maximum numerical part for that
  given base part (e.g., in examples above, the maximum is 100).
  """
  # initialize the hash of pickles
  pickle_hash = {}
  # process the items in the pickle list
  for pickle in pickle_list:
    # extract the base part of the pickle
    pickle_base_search = re.search(r'(log-.+\d\ds)-pickle-', pickle)
    assert pickle_base_search, "No pickles were found in the directory."
    pickle_base = pickle_base_search.group(1)
    # extract the numerical part of the pickle
    pickle_num_search = re.search(r'-pickle-(\d+)\.bin', pickle)
    assert pickle_num_search, "No pickles were found in the directory."
    pickle_num = int(pickle_num_search.group(1))
    # use the base part of the pickle as the hash key
    # and set the value to the largest numerical part
    if (pickle_base in pickle_hash):
      current_largest = pickle_hash[pickle_base]
      if (pickle_num > current_largest):
        pickle_hash[pickle_base] = pickle_num
    else:
      pickle_hash[pickle_base] = pickle_num
    #
  return pickle_hash
#
# choose_pickles(g) -- returns [pickle_dir, analysis_dir, 
#                      sorted_pickle_names, smallest_pickle_size]
#
def choose_pickles(g):
  """
  Present a GUI to ask the users which folder of pickles they
  would like to analyze.
  """
  #
  # Open a dialog window and ask the user to select a folder.
  #
  g.note("Analyze Pickles\n\n" + \
         "Select a FOLDER of pickled seeds (not a FILE of seeds).\n" + \
         "The pickles will be analyzed and the results will be\n" + \
         "stored in the same directory as the pickles.\n")
  #
  pickle_dir = g.opendialog("Choose a folder of pickled seeds", \
               "dir", g.getdir("app"))
  #
  analysis_dir = pickle_dir
  #
  g.note("Verify Selection\n\n" + \
         "The folder of pickled seeds:\n\n" + \
         "   " + pickle_dir + "\n\n" + \
         "The folder for the analysis results:\n\n" + \
         "   " + analysis_dir + "\n\n" + \
         "Exit now if this is incorrect.")
  #
  # Make a list of the pickles in pickle_dir.
  #
  pickle_list = []
  for file in os.listdir(pickle_dir):
    if (file.endswith(".bin") and file.startswith("log-")):
      pickle_list.append(file)
  #
  # Verify that there are some ".bin" files in the list.
  #
  if (len(pickle_list) == 0):
    g.note("No pickles were found in the directory:\n\n" + \
           "   " + pickle_dir + "\n\n" + \
           "Exiting now.")
    sys.exit(0)
  #
  # Make a hash table that maps pickle names to the last
  # generation number of the given group of pickles.
  #
  pickle_hash = hash_pickles(pickle_list)
  #
  # Calculate the size of the smallest group of pickles.
  #
  smallest_pickle_size = min(pickle_hash.values())
  #
  # Report the base parts of the pickles and their maximum
  # values
  #
  sorted_pickle_names = sorted(pickle_hash.keys())
  pickle_note = ""
  for pickle_base in sorted_pickle_names:
    pickle_note = pickle_note + \
      pickle_base + " ranges from 0 to " + \
      str(pickle_hash[pickle_base]) + "\n"
  g.note("These pickles were found:\n\n" +
    pickle_note + "\n" + \
    "The analysis will range from 0 to " + \
    str(smallest_pickle_size) + "\n\n" + \
    "Exit now if this is not what you expected.")
  #
  return [pickle_dir, analysis_dir, \
    sorted_pickle_names, smallest_pickle_size]
#
# validate_designed_seed(g, seed_path, max_area) 
# -- returns 0 for bad, 1 for good
#
def validate_designed_seed(g, seed_path, max_area):
  """
  This function checks whether we can convert a human-made pattern file
  into a seed.
  """
  #
  # We only want *.rle or *.lif
  #
  file_base, file_extension = os.path.splitext(seed_path)
  if (file_extension != ".rle") and (file_extension != ".lif"):
    return 0
  #
  # Golly has two kinds of cell lists, one that contains an even number 
  # of members and one that contains an odd number of members. The 
  # former is intended for two states (0 and 1) and the latter is intended 
  # for more than two states. Here we are only interested in patterns designed 
  # for the Game of Life, which only has two states.
  #
  cell_list = g.load(seed_path)
  #
  # Make sure cell_list is not too small
  #
  too_small = 5
  #
  if (len(cell_list) <= too_small):
    return 0
  #
  # We can only handle cell_list if it has an even number of members.
  #
  if (len(cell_list) % 2 != 0):
    return 0
  #
  # See how big this pattern is.
  #
  min_x = cell_list[0]
  max_x = cell_list[0]
  min_y = cell_list[1]
  max_y = cell_list[1]
  #
  for i in range(0, len(cell_list), 2):
    pair = (cell_list[i], cell_list[i + 1])
    (x, y) = pair
    if (x < min_x):
      min_x = x
    if (x > max_x):
      max_x = x
    if (y < min_y):
      min_y = y
    if (y > max_y):
      max_y = y
  #
  # Make sure it's not too big.
  #
  if (max_x * max_y > max_area):
    return 0
  #
  # Make sure it's not too small.
  #
  if (max_x == 0) or (max_y == 0):
    return 0
  #
  # Passed all tests.
  #
  return 1
#
# load_designed_seed(g, seed_path) -- returns seed
#
def load_designed_seed(g, seed_path):
  """
  Given the path to a human-designed Game of Life pattern, load the
  file and convert it to a seed.
  """
  #
  # Golly has two kinds of cell lists, one that contains an even number 
  # of members and one that contains an odd number of members. The 
  # former is intended for two states (0 and 1) and the latter is intended 
  # for more than two states. Here we are only interested in patterns designed 
  # for the Game of Life, which only has two states.
  #
  cell_list = g.load(seed_path)
  #
  # Make sure that cell_list is the type of list that contains an even
  # number of members. Make sure cell_list is not unreasonably small.
  #
  assert len(cell_list) % 2 == 0
  assert len(cell_list) > 10
  #
  # Convert cell_list to a list of (x, y) pairs.
  #
  pair_list = []
  min_x = cell_list[0]
  max_x = cell_list[0]
  min_y = cell_list[1]
  max_y = cell_list[1]
  #
  for i in range(0, len(cell_list), 2):
    pair = (cell_list[i], cell_list[i + 1])
    pair_list.append(pair)
    (x, y) = pair
    if (x < min_x):
      min_x = x
    if (x > max_x):
      max_x = x
    if (y < min_y):
      min_y = y
    if (y > max_y):
      max_y = y
  #
  # Convert pair_list to a seed. Start with a seed full of
  # zeros and set the cells given in pair_list to ones.
  #
  assert min_x == 0
  assert min_y == 0
  assert max_x > 0
  assert max_y > 0
  #
  s_xspan = max_x + 1
  s_yspan = max_y + 1
  #
  seed = mclass.Seed(s_xspan, s_yspan, mparam.pop_size)
  #
  for pair in pair_list:
    (x, y) = pair
    seed.cells[x][y] = 1
  #
  # Count the initial number of living cells in the seed
  # and store the count.
  #
  seed.num_living = seed.count_ones()
  #
  assert seed.num_living > 0
  #
  return seed
#
# mono_growth(g, num_steps, seed, description, stats_hash) 
# -- returns nothing: all the information is stored in the
#    hash table stats_hash
#
def mono_growth(g, num_steps, seed, description, stats_hash):
  """
  Calculate how much one seed with one live colour (mono) grows 
  after num_steps steps of the Game of Life.
  """
  #
  # Initialize the game.
  #
  magnify = 2 # magnification for display: negative = smaller
  pause = 0 # pause for display: measured in seconds
  rule_name = "B3/S23" # the Game of Life
  g.setalgo("QuickLife") # use "HashLife" or "QuickLife"
  g.autoupdate(False) # do not update the view unless requested
  g.new(rule_name) # initialize cells to state 0
  g.setrule(rule_name) # make an infinite plane
  g.setmag(magnify) # magnification: negative = smaller
  g.setcolors([0,255,255,255,1,0,0,0]) # 0 = white, 1 = black
  #
  # Copy the seed into the plane.
  #
  for x in range(seed.xspan):
    for y in range(seed.yspan):
      state = seed.cells[x][y]
      g.setcell(x, y, state)
  #
  # Run the game for num_steps steps.
  #
  start_size = seed.count_ones()
  g.show(description + " start size = " + str(start_size)) # status bar
  g.update() # show the start state
  time.sleep(pause)
  g.run(num_steps) # run the Game of Life for num_steps time steps
  end_size = int(g.getpop())
  g.show(description + " end size = " + str(end_size)) # status bar
  g.update() # show the end state
  time.sleep(pause)
  #
  # Add results to stats_hash.
  #
  stats_hash[description + " start size"] = start_size
  stats_hash[description + " end size"] = end_size
  stats_hash[description + " growth"] = end_size - start_size
  #
  # return nothing -- all the information is stored in the
  # hash table stats_hash
  return
#
# quad_growth(g, num_steps, part1, part2, stats_hash) 
# -- returns nothing: all the information is stored in the
#    hash table stats_hash
#
def quad_growth(g, num_steps, part1, part2, stats_hash):
  """
  The input should be two parts of a fused seed. We will colour
  one part red and the other part blue. We will then run a
  five-state variation of the Game of Life, which can be viewed
  as an extension of the Immigration Game. Let's call it the
  Management Game.
  """
  #
  # five states of cells:
  #
  # 0 = white   (dead)
  # 1 = red     (alive)
  # 2 = blue    (alive)
  # 3 = orange  (alive)
  # 4 = green   (alive)
  #
  # R = red, B = blue, P = orange (red+yellow), A = green (blue+yellow)
  #
  # background colour = not alive = white
  #
  # 1 new red cell   = this cell was created by three red cells
  # 1 new orange cell  = this cell was created with help by blue or green
  #
  # 1 new blue cell  = this cell was created by three blue cells
  # 1 new green cell = this cell was created with help by red or orange
  #
  #
  # Initialize the game.
  #
  magnify = 2 # magnification for display: negative = smaller
  pause = 0 # pause for display: measured in seconds
  rule_name = "Management" # the Management Game
  g.setalgo("QuickLife") # use "HashLife" or "QuickLife"
  g.autoupdate(False) # do not update the view unless requested
  g.new(rule_name) # initialize cells to state 0
  g.setrule(rule_name) # make an infinite plane
  g.setmag(magnify) # magnification: negative = smaller
  #
  # Fuse part1 and part2 to make a new whole, but change part2 
  # from red (state 1) to blue (state 2), so that we can distinguish 
  # the two parts inside the new whole.
  #
  # Get dimensions for the new fusion seed, whole.
  #
  xspan = part1.xspan + part2.xspan + 1 # left width + right width + empty gap
  yspan = max(part1.yspan, part2.yspan) # the larger of the two heights
  whole = mclass.Seed(xspan, yspan, mparam.pop_size) # cells set to zero
  #
  # Copy part1 into the left side of whole.
  #
  for x in range(part1.xspan):
    for y in range(part1.yspan):
      # write states 0 and 1 into whole.cells (white and red)
      whole.cells[x][y] = part1.cells[x][y] 
  #
  # Copy part2 into the right side of whole.
  #
  for x in range(part2.xspan):
    for y in range(part2.yspan):
      # write states 0 and 2 into whole.cells (white and blue)
      whole.cells[x + part1.xspan + 1][y] = part2.cells[x][y] * 2
  #
  # Find the initial counts of red and blue. We know that
  # the intial counts for orange and green are zero. We
  # don't actually care about white, but trying to avoid
  # white may slow down the loop.
  #
  # start_size = [white, red, blue, orange, green]
  start_size = [0, 0, 0, 0, 0]
  for x in range(whole.xspan):
    for y in range(whole.yspan):
      state = whole.cells[x][y]
      # update the counts for each colour
      start_size[state] += 1
      # copy the fused seed into the Game
      g.setcell(x, y, state)
  # add data to hash table
  stats_hash["red cells start size"] = start_size[1]
  stats_hash["blue cells start size"] = start_size[2]
  stats_hash["orange cells start size"] = start_size[3] # should be zero
  stats_hash["green cells start size"] = start_size[4] # should be zero
  #
  # Run the game for num_steps steps.
  #
  g.show("red cells start size = " + str(start_size[1]) + \
         ", blue cells start size = " + str(start_size[2]))
  g.update() # show the starting state
  time.sleep(pause)
  g.run(num_steps) # run the Game for num_steps time steps
  #
  # Find the final counts of the four colours (red, blue, orange, green)
  # and subtract the initial counts to get the growths. Note that the
  # final numbers can be negative.
  #
  # find bounding rectangle (might be empty if no live cells)
  boundary = g.getrect()
  if (len(boundary) == 0): # if no live cells ...
    stats_hash["red cells end size"] = 0
    stats_hash["blue cells end size"] = 0
    stats_hash["orange cells end size"] = 0
    stats_hash["green cells end size"] = 0
    stats_hash["red cells growth"] = - start_size[1]
    stats_hash["blue cells growth"] = - start_size[2]
    stats_hash["orange cells growth"] = - start_size[3]
    stats_hash["green cells growth"] = - start_size[4]
    return
  # a multi-state (multi-colour) cell list has the form:
  #   [ x1, y1, state1, . . . xN, yN, stateN ]     if N is odd
  #   [ x1, y1, state1, . . . xN, yN, stateN, 0 ]  if N is even
  # if boundary is empty, then cell_list will be empty 
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
  # add end size to hash table
  stats_hash["red cells end size"] = end_size[1]
  stats_hash["blue cells end size"] = end_size[2]
  stats_hash["orange cells end size"] = end_size[3]
  stats_hash["green cells end size"] = end_size[4]
  # add growth to hash table
  stats_hash["red cells growth"] = end_size[1] - start_size[1]
  stats_hash["blue cells growth"] = end_size[2] - start_size[2]
  stats_hash["orange cells growth"] = end_size[3] - start_size[3]
  stats_hash["green cells growth"] = end_size[4] - start_size[4]
  # show final sizes for each colour in status bar
  g.show("red cells end size = " + str(end_size[1]) + \
         ", blue cells end size = " + str(end_size[2]) + \
         ", orange cells end size = " + str(end_size[3]) + \
         ", green cells end size = " + str(end_size[4]))
  g.update() # need to update Golly to get counts
  time.sleep(pause) 
  #
  # return nothing -- all the information is stored in the
  # hash table stats_hash
  return
#
# compare_random(g, random_seed, description, stats_hash)
# -- returns nothing: all the information is stored in the
#    hash table stats_hash
#
def compare_random(g, evolved_seed, description, stats_hash):
  """
  Calculate the fitness of evolved_seed by comparing it with randomly
  shuffled versions of itself (random_seed) in the Immigration Game.
  """
  #
  # Get the parameters for competitions in the Immigration Game.
  #
  width_factor = mparam.width_factor # (e.g., 6.0)
  height_factor = mparam.height_factor # (e.g., 3.0)
  time_factor = mparam.time_factor # (e.g., 6.0)
  num_trials = mparam.num_trials # (e.g., 2)
  # so that the noise level here is comparable to the noise level
  # in compare_generations.py, generate the same number of random
  # seeds as there are seeds in the elite pickles (num_runs * elite_size)
  num_runs = mparam.num_generations + 1 # number of pickles (e.g. 101)
  elite_size =  mparam.elite_size # number of seeds per pickle (e.g. 50)
  #
  # Run the competitions.
  #
  total_fitness = 0
  total_sample_size = 0
  for sample in range(num_runs * elite_size): # (e.g. 101 * 50 = 5,050)
    # make a copy of evolved_seed and randomly shuffle the cells
    # in the new seed, so that the new randomized seed has the
    # same dimensions and the same density as evolved_seed
    random_seed = evolved_seed.shuffle()
    # compare the input seed to the random seed -- score_pair()
    # will change the colour of the random seed and run the
    # Immigration Game
    [random_score, evolved_score] = score_pair(g, random_seed, \
      evolved_seed, width_factor, height_factor, time_factor, num_trials)
    total_fitness = total_fitness + evolved_score
    total_sample_size = total_sample_size + 1
  # calculate average fitness for the run
  avg_fitness = total_fitness / total_sample_size
  # add info to stats_hash
  stats_hash[description + " absolute fitness"] = avg_fitness
  #
  # return nothing -- all the information is stored in the
  # hash table stats_hash
  return
#
# change_live_state(seed, new_state) 
# -- return a modified copy of the input seed
#
def change_live_state(seed, new_state):
  """
  Given an input seed with live state 1, copy the seed and
  replace state 1 with new_state.
  """
  # copy the seed so that the original is not changed
  new_seed = copy.deepcopy(seed)
  # change state 1 in the given seed to new_state -- we multiply
  # here instead of using "if X then Y", in the belief that
  # multiplication is faster
  for x in range(new_seed.xspan):
    for y in range(new_seed.yspan):
      # update seed.cells -- state 0 remains state 0
      # and state 1 becomes new_state
      new_seed.cells[x][y] = new_seed.cells[x][y] * new_state
  #
  return new_seed
#
# join_seeds(part1, part2) -- returns whole
#
def join_seeds(part1, part2):
  """
  Given two seeds, part1 and part2, join them together, with
  part1 on the left and part2 on the right. Insert a gap of
  one column between them.
  """
  #
  # Calculate the dimensions of the new seed.
  #
  xspan = part1.xspan + part2.xspan + 1 # left width + right width + empty gap
  yspan = max(part1.yspan, part2.yspan) # the larger of the two heights
  whole = mclass.Seed(xspan, yspan, mparam.pop_size) # cells set to zero
  #
  # Copy part1 into the left side of whole.
  #
  for x in range(part1.xspan):
    for y in range(part1.yspan):
      whole.cells[x][y] = part1.cells[x][y] 
  #
  # Copy part2 into the right side of whole.
  #
  for x in range(part2.xspan):
    for y in range(part2.yspan):
      whole.cells[x + part1.xspan + 1][y] = part2.cells[x][y]
  #
  # Return the new seed.
  #
  return whole
#
# snap_photo(g, file_path, rule_name, seed_list, live_states, 
#            steps, description, pause)
# -- returns nothing: photo is written to specified file_path
#
def snap_photo(g, file_path, rule_name, seed_list, live_states, \
               steps, description, pause):
  """
  Run Golly with the given seed(s) and take a photo of the result.
  The photo will be stored in file_path (*.png).
  """
  #
  # Sanity check: seed_list and live_states should have the same size.
  # The live state in the Nth seed in seed_list in will be the Nth state 
  # in the list live_state.
  #
  assert len(seed_list) == len(live_states)
  #
  # Initialize the game.
  #
  g.setalgo("QuickLife") # use "HashLife" or "QuickLife"
  g.autoupdate(False) # do not update the view unless requested
  g.new(rule_name) # initialize cells to state 0
  g.setrule(rule_name) # make an infinite plane
  #
  # If there is only one seed, then we simply set the
  # default live state (1) to the desired live state.
  # If there are two seeds, we set their colours separately
  # and then we merge them.
  #
  if (len(seed_list) == 1):
    # if there is only one seed, change the live state as requested
    seed = change_live_state(seed_list[0], live_states[0])
  elif (len(seed_list) == 2): 
    # if there are two seeds, change both of their live states
    part1 = change_live_state(seed_list[0], live_states[0])
    part2 = change_live_state(seed_list[1], live_states[1])
    # now join them into a single seed, with part1 on the left
    # and part2 on the right
    seed = join_seeds(part1, part2)
  else:
    # no plan for three or more seeds
    assert False
  #
  # Copy the seed into Golly.
  #
  for x in range(seed.xspan):
    for y in range(seed.yspan):
      state = seed.cells[x][y]
      g.setcell(x, y, state)
  #
  # Run the game for num_steps steps.
  #
  if (steps == 0):
    g.show(description)
    g.fit()
    g.update() # show the start state
  else:
    g.show(description)
    g.update() # show the start state
    g.run(steps) # run the Game of Life for steps
    g.fit()
    g.update() # show the end state
  #
  # Take the photo and save it.
  #
  time.sleep(pause)
  photo_object = pyautogui.screenshot()
  photo_object.save(file_path)
  #
  # return nothing -- photo is written to specified file_path
  return
#
#