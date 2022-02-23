from random import randint
import math
from random import random
import json

# randomly choose, given some var
def random_opt(symbolics_opt, logs, bounds):
    new_vars = {}
    for var in symbolics_opt:
        if var in logs.values(): # this var has to be multiple of 2
            new_vars[var] = 2**randint(int(math.log2(bounds[var][0])),int(math.log2(bounds[var][1])))
            continue
        new_vars[var] = randint(bounds[var][0],bounds[var][1])
    return new_vars

'''
# TODO: there's a bug here somewhere
# single step of simulated_annealing
# we call this after we have TWO COSTS (call simple initially?)
def simulated_annealing_step(curr_state, curr_cost, new_state, new_cost, best_state, best_cost, temp, iteration, step_size, bounds):
    # COST CALCULATION
    if new_cost < best_cost or (new_cost==best_cost and (new_state[0]*new_state[1])<=(best_state[0]*best_state[1])):
    #if new_cost < best_cost or (new_cost==best_cost and new_state[1]<=best_state[1])
        best_state = new_state
        best_cost = new_cost

    diff = new_cost - curr_cost
    t = temp / float(iteration+1)
    if t==0:
        print("ZERO TEMP")
        print(iteration)
        print(temp)
        quit()
    try:
        metropolis = math.exp(-diff/t)
    except OverflowError:
        metropolis = float('inf')
    if diff < 0 or random() < metropolis:
        curr_state, curr_cost = new_state, new_cost

    # gen next step
    # random value w/in bounds
    #new_state = sim_move()
    rows = curr_state[0]+randint(-1*bounds[0],bounds[0])*step_size[0]
    if rows < 1:
        rows = 1
    elif rows > 10:
        rows = 10
    cols = 2**(math.log2(curr_state[1])+randint(-1*bounds[1],bounds[1]))*step_size[1]
    if cols < 2:
        cols = 2
    elif cols > 2048:
        cols = 2048
    new_state = [rows, int(cols)]

    return curr_state, curr_cost, new_state, best_state, best_cost, t

'''

# bayesian optimization

# genetic algo





