import math, json, sys, copy, time
from random import randint
from random import random
from interp_sim import *

# randomly choose, given some var
def get_next_random(symbolics_opt, logs, bounds):
    new_vars = {}
    for var in symbolics_opt:
        if var in logs.values(): # this var has to be multiple of 2
            new_vars[var] = 2**randint(int(math.log2(bounds[var][0])),int(math.log2(bounds[var][1])))
            continue
        new_vars[var] = randint(bounds[var][0],bounds[var][1])
    return new_vars

# TODO: check that dicts get updated correctly
def random_opt(symbolics_opt, opt_info, o):
    iterations = 0
    # init best solution as starting, and best cost as inf
    best_sol = copy.deepcopy(symbolics_opt)
    best_cost = float("inf")
    # keep track of sols we've already tried so don't repeat
    tested_sols = []
    # we need bounds for random
    bounds = {}
    if "bounds" in opt_info["symbolicvals"]:    # not necessarily required for every opt, but def for random
        bounds = opt_info["symbolicvals"]["bounds"]
    else:
        sys.exit("random opt requires bounds on symbolics")
    # decide if we're stopping by time, iterations, or both (whichever reaches thresh first)
    iters = False
    simtime = False
    iter_time = False
    if "stop_iter" in opt_info:
        iters = True
    if "stop_time" in opt_info:
        simtime = True
    if iters and simtime:
        iter_time = True

    # start loop
    start_time = time.time()
    while True:
        # check iter/time conditions
        if iters or iter_time:
            if iterations >= opt_info["stop_iter"]:
                break
        if simtime or iter_time:
            if (time.time()-start_time) >= opt_info["stop_time"]:
                break

        # get cost
        cost = gen_cost(symbolics_opt,opt_info, o)

        # add sol to tested_sols to count it as already evaluated
        # is it stupid to do deepcopy here? can we be smarter about changing symbolics_opt to avoid this? or is it a wash?
        tested_sols.append(copy.deepcopy(symbolics_opt))

        # if new cost < best, replace best (if stgs <= tofino)
        if cost < best_cost:
            best_cost = cost
            # not sure if this is slow, but these dicts are likely small (<10 items) so shouldn't be an issue
            best_sol = copy.deepcopy(symbolics_opt)

        # get next values
        symbolics_opt = get_next_random(symbolics_opt, opt_info["symbolicvals"]["logs"], opt_info["symbolicvals"]["bounds"])

        # incr iterations
        iterations += 1

    return best_sol, best_cost


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





