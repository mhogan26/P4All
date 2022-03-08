import math, json, sys, copy, time
from random import randint
from random import random
from interp_sim import gen_cost
import numpy as np
from scipy.optimize import basinhopping

# helper funcs
'''
# narrow down best sols to 1, using priority
# is there a better/simpler way to do this?????
# NOTE: might want to save original list of solutions, in case one we choose doesn't compile to tofino (more sols to try before we're forced to rerun optimize)
def prioritize(best_sols, opt_info):
    prefs_sym = (opt_info["symbolicvals"]["priority"].keys())
    if len(best_sols) > 1:  # multiple best sols, use priority prefs
        best_sol = [best_sols[0],0]
        for v in prefs_sym: # start w highest priority symbolic, narrow down best sols until we reach 1
            if len(best_sols) == 1: # we've picked a single solution, no need to continue
                break
            to_remove = []
            pref_direction = opt_info["symbolicvals"]["priority"][v]
            for s in range(1,len(best_sols)):   # find solutions that are suboptimal according to priority (higher, lower)
                if pref_direction == "higher":
                    if best_sols[s][v] > best_sol[0][v]:
                        to_remove.append(best_sol[1])
                        best_sol = [best_sols[s],s]
                        continue
                    elif best_sols[s][v] < best_sol[0][v]:
                        to_remove.append(s)
                        continue
                elif pref_direction == "lower":
                    if best_sols[s][v] < best_sol[0][v]:
                        to_remove.append(best_sol[1])
                        best_sol = [best_sols[s],s]
                        continue
                    elif best_sols[s][v] > best_sol[0][v]:
                        to_remove.append(s)
                        continue
                else:
                    print("invalid preference, must be higher or lower")
                    quit()

            to_remove.sort(reverse=True)    # throw out solutions that don't match priority
            to_remove=list(set(to_remove))  # get rid of duplicates
            for i in to_remove:
                best_sols.pop(i)
            best_sol[1] = best_sols.index(best_sol[0])  # in case things get shuffled around after pops
    return best_sol[0]
'''
# helper for sim annealing, rounds to closest power of 2
# copied from: https://stackoverflow.com/questions/28228774/find-the-integer-that-is-closest-to-the-power-of-two
def closest_power(x):
    possible_results = math.floor(math.log2(x)), math.ceil(math.log2(x))
    return 2**min(possible_results, key= lambda z: abs(x-2**z))



# RANDOM OPTIMIZATION
# randomly choose, given some var
def get_next_random(symbolics_opt, logs, bounds):
    new_vars = {}
    for var in symbolics_opt:
        if var in logs.values(): # this var has to be multiple of 2
            new_vars[var] = 2**randint(int(math.log2(bounds[var][0])),int(math.log2(bounds[var][1])))
            continue
        new_vars[var] = randint(bounds[var][0],bounds[var][1])
    return new_vars

def random_opt(symbolics_opt, opt_info, o):
    iterations = 0
    # init best solution as starting, and best cost as inf
    best_sols = [copy.deepcopy(symbolics_opt)]
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
    if "stop_iter" in opt_info["optparams"]:
        iters = True
    if "stop_time" in opt_info["optparams"]:
        simtime = True
    if iters and simtime:
        iter_time = True

    # start loop
    start_time = time.time()
    while True:
        # check iter/time conditions
        if iters or iter_time:
            if iterations >= opt_info["optparams"]["stop_iter"]:
                break
        if simtime or iter_time:
            if (time.time()-start_time) >= opt_info["optparams"]["stop_time"]:
                break

        # get cost
        cost = gen_cost(symbolics_opt,symbolics_opt,opt_info, o,False)

        # add sol to tested_sols to count it as already evaluated
        # is it stupid to do deepcopy here? can we be smarter about changing symbolics_opt to avoid this? or is it a wash?
        tested_sols.append(copy.deepcopy(symbolics_opt))

        # if new cost < best, replace best (if stgs <= tofino)
        if cost < best_cost:
            best_cost = cost
            # not sure if this is slow, but these dicts are likely small (<10 items) so shouldn't be an issue
            best_sols = [copy.deepcopy(symbolics_opt)]
        elif cost == best_cost:
            best_sols.append(copy.deepcopy(symbolics_opt))

        # get next values
        symbolics_opt = get_next_random(symbolics_opt, opt_info["symbolicvals"]["logs"], opt_info["symbolicvals"]["bounds"])

        # incr iterations
        iterations += 1

    # if we have multiple solutions equally as good, use priority from user to narrow it down to 1
    #best_sol = prioritize(best_sols,opt_info)

    # return the first solution in list of acceptable sols
    return best_sols[0], best_cost


# SIMULATED ANNEALING
# copied from: https://machinelearningmastery.com/simulated-annealing-from-scratch-in-python/
# good for objective functions that have single global optima and mult local optima where search might get stuck
# using numpy.random.randn() - gaussian distr (gives us negative vals, so can move up and down)  
# some notes on step size:
#   if the var has large search space, probably want larger step size
#   step size is std dev --> 99% of all steps w/in 3*stepsize of curr var val
#   ^ not exactly true, bc we have to do some rounding (can't have floats)
def simulated_annealing(symbolics_opt, opt_info, o):
    temp = opt_info["optparams"]["temp"]
    bounds = opt_info["symbolicvals"]["bounds"]
    step_size = opt_info["optparams"]["stepsize"]
    logvars = opt_info["symbolicvals"]["logs"].values()
    # generate and evaluate an initial point
    best_sols = [copy.deepcopy(symbolics_opt)]
    best_cost = gen_cost(symbolics_opt,symbolics_opt,opt_info, o,False)

    # current working solution
    curr, curr_cost = copy.deepcopy(symbolics_opt), best_cost

    # run the algorithm
    for i in range(opt_info["optparams"]["stop_iter"]-1):   # minus 1 bc counting init cost as iteration
        # take a step
        for s in step_size:
            # random step with gaussian distr, with mean = curr[s] and stddev = step_size[s]
            # could do single call to randn and gen array of values, or get single value at a time
            symbolics_opt[s] = curr[s] + np.random.randn() * step_size[s]
            # if we happen to hit bottom or top of bounds, set to min/max
            if symbolics_opt[s] < bounds[s][0]:
                symbolics_opt[s] = bounds[s][0]
            elif symbolics_opt[s] > bounds[s][1]:
                symbolics_opt[s] = bounds[s][1]
            # we'll get a float, so round to nearest acceptable int
            if s in logvars:    # var has to be power of 2
                symbolics_opt[s] = closest_power(symbolics_opt[s])
            else:   # doesn't have to be power of 2, just round to nearest int
                symbolics_opt[s] = round(symbolics_opt[s])

        # evaluate candidate point
        candidate_cost = gen_cost(symbolics_opt, symbolics_opt, opt_info, o, False)

        # check for new best solution
        if candidate_cost < best_cost:
            # store new best point
            best_sols, best_cost = [copy.deepcopy(symbolics_opt)], candidate_cost
        elif candidate_cost == best_cost:
            best_sols.append(copy.deepcopy(symbolics_opt))

        # difference between candidate and current point evaluation
        diff = candidate_cost - curr_cost

        # calculate temperature for current epoch
        t = temp / float(i + 1)

        # calculate metropolis acceptance criterion
        metropolis = math.exp(-diff / t)

        # check if we should keep the new point
        if diff < 0 or np.random.rand() < metropolis:
            # store the new current point
            curr, curr_cost = copy.deepcopy(symbolics_opt), candidate_cost

    #best_sol = prioritize(best_sols,opt_info)

    # return first sol in list of sols
    return best_sols[0], best_cost

'''
# BASIN HOPPING (with scipy, like sim annealing)
# scipy doesn't let us restrict to ints (not floats), and doesn't let us restrict to powers of 2
def basin_hopping(symbolics_opt, opt_info, o):
    # put symbolic vars in np array
    x0 = np.empty(shape=(len(symbolics_opt)), dtype=int)
    i = 0
    for v in symbolics_opt:
        x0[i] = symbolics_opt[v]
        i+=1
    # extra args that cost func needs
    args ={'args':(symbolics_opt,opt_info, o, True)}
    # as of python3.7, dicts are insertion order, so should be ok to rely on ordering
    res = basinhopping(gen_cost, x0, minimizer_kwargs=args,niter=100)
'''

# bayesian optimization

# genetic algo





