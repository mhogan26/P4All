from random import randint
import math
from random import random
import json

def move_simple(states, measurements, iteration, groundtruth):
    x = abs((measurements[-1] - groundtruth)/groundtruth)
    rows = states[-1][0]
    cols = states[-1][1]
    if iteration > 10 and x<.1:
        return -1
    elif x >.1:
        if rows < 10:
            rows += 1
        if cols < 4096:
            cols = 2**randint(math.log(cols,2)+1,12)
    else:
        if rows > 1:
            rows -= 1
        if cols > 2:
            cols = 2**randint(1,math.log(cols,2)-1)
    hash_w = math.log(cols,2)
    return [rows,int(cols),int(hash_w)]

'''
# simulated annealing algorithm
def simulated_annealing(objective, bounds, n_iterations, step_size, temp):
	# generate an initial point
	best = bounds[:, 0] + rand(len(bounds)) * (bounds[:, 1] - bounds[:, 0])
	# evaluate the initial point
	best_eval = objective(best)
	# current working solution
	curr, curr_eval = best, best_eval
	# run the algorithm
	for i in range(n_iterations):
		# take a step
		candidate = curr + randn(len(bounds)) * step_size
		# evaluate candidate point
		candidate_eval = objective(candidate)
		# check for new best solution
		if candidate_eval < best_eval:
			# store new best point
			best, best_eval = candidate, candidate_eval
			# report progress
			print('>%d f(%s) = %.5f' % (i, best, best_eval))
		# difference between candidate and current point evaluation
		diff = candidate_eval - curr_eval
		# calculate temperature for current epoch
		t = temp / float(i + 1)
		# calculate metropolis acceptance criterion
		metropolis = exp(-diff / t)
		# check if we should keep the new point
		if diff < 0 or rand() < metropolis:
			# store the new current point
			curr, curr_eval = candidate, candidate_eval
	return [best, best_eval]
'''

# randomly choose cms rows/cols, given some bounds
def sim_move():
    rows = randint(1,10)
    cols = 2**randint(1,15)
    #hash_w = math.log2(cols)
    return cols,rows

# single step of simulated_annealing
# we call this after we have TWO COSTS (call simple initially?)
def simulated_annealing_step(curr_state, curr_cost, new_state, new_cost, best_state, best_cost, temp, iteration, step_size, bounds):
    # COST CALCULATION
    if new_cost < best_cost or (new_cost==best_cost and (new_state[0]*new_state[1])<=(best_state[0]*best_state[1])):
        best_state = new_state
        best_cost = new_cost

    diff = new_cost - curr_cost
    t = temp / float(iteration+1)
    metropolis = math.exp(-diff/t)
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


# bayesian optimization



'''
# write new sym values to json file - cols, rows, logcols
logcols = math.log2(cols)
concretes = {}
concretes["sizes"] = {"logcols":logcols, "rows":rows}
concretes["symbolics"] = {"cols":cols}
with open('cms_sym.symb', 'w') as f:
    json.dump(concretes, f, indent=4)

'''




