# REWRITE so that there's a decision variable per action per stage - Xij = 1 if action i is in stage j
# sum of decision variables for a single action = 1
# sum of decision variables for a single stage <= num_state
# if Xij = 1 for action a, then Xik = 1 for b, where j < k


#!/usr/bin/python
from gurobipy import *


# N value (upper bound on num actions)
N = 18

# 0 is check cache exist
# 1 is check cache valid
# 2 is set cache valid
# 3 is read hit before
# 4,5,6 are add header and read array1
# 10,11,12 are write array1 and remove header
# 7,8,9 are add header and read array2
# 13,14,15 are write array2 and remove header
# 16 is read hit after
# 17 is ipv4
loops = [[0],[1],[2],[3],[4,5,6,7,8,9],[10,11,12,13,14,15],[16],[17]]
# 0-3, 16-17 are required (if act is singleton in loop list, then require)
# NESTED FOR LOOPS????? OR JUST GROUP BY OUTERMOST LOOP?
first_iters = [[4,5,6], [10,11,12]]

groups = [[4,5,6,10,11,12],[7,8,9,13,14,15]]

# we only include read actions in stateful
# corresponding write actions must be in same stg and read will never happen at same time as write (if/else)
stateful = [1,5,6,8,9]

# these deps are probs not correct, just based on an init manual pass through netcache code
deps = {(0,1):1, (0,2):1, (0,10):1, (0,11):1, (0,12):1, (0,13):1, (0,14):1, (0,15):1, (0,5):1, (0,6):1, (0,8):1, (0,9):1, (1,3):1, (1,4):1, (1,5):1, (1,6):1, (1,7):1, (1,8):1, (1,9):1, (1,16):1, (3,16):1, (4,5):1, (4,6):1, (7,8):1, (7,9):1, (10,12):1, (11,12):1, (13,15):1, (14,15):1, (4,7):2, (12,15):2, (1,2):3, (5,10):3, (6,11):3, (8,13):3, (9,14):3}

# same array read/writes MUST be in same stg
# acts 1 + 2 in same stg, 5+10, 6+11, etc.
# these are designated w/ dep type 3 in dep list

num_slices = 2	# is this supposed to be the same # of stateful actions in a stage?
num_arrays = 2
# total available stateful memory
total_mem = 2048
# lower bound for reg size
reg_bound = 256
# num stages
num_stg = 8
# stateful actions per stg
num_state = 2

# Model
m = Model("test")

# Variables
a_vars = []	# contains list for each action
stages_a = []	# list for each stage, composed of actions for each stg
for i in range(num_stg):
	stages_a.append([])

# decision variable for every (action num, stg num) pair
for i in range(N):
	a_vars.append([])
	for j in range(num_stg):
		a_vars[i].append(m.addVar(vtype=GRB.BINARY,name="act%s%s"%(i,j)))
		if i in stateful:
			stages_a[j].append(a_vars[i][j])
	m.addConstr(quicksum(a_vars[i]) <= 1)	# only place action/reg once


# dep constraints
for key in deps:
        a0 = key[0]
        a1 = key[1]
        if deps[key] == 1:      # ordered
                for x in range(len(a_vars[a0])):
                        z = 0
                        while z <= x:
                                m.addConstr(a_vars[a1][z]<=(1-a_vars[a0][x]))
                                z += 1

        elif deps[key] == 2:    # unordered
                for x in range(len(a_vars[a0])):
                        m.addConstr(a_vars[a0][x]<=(1-a_vars[a1][x]))
	#'''
	elif deps[key] == 3:	# same stg
		for x in range(len(a_vars[a0])):
			m.addConstr(a_vars[a0][x] == a_vars[a1][x])
	#'''

# constraint to ensure actions outside loop ALWAYS get placed
for l in loops:
	if len(l) == 1:
		m.addConstr(quicksum(a_vars[l[0]]) == 1)
	# if loop w/ mult iterations, make solution ordered - DOES NOT ACCOUNT FOR NESTED LOOPS, ONLY OUTERMOST LOOP
	else:
		for i in range(len(l)):
			if i == 0:
				continue
			m.addConstr(quicksum(a_vars[l[i]]) <= quicksum(a_vars[l[i-1]]))
#at least one iteration is placed
# do we need to mark of iterations of loops? - for each action in first iteration, sum of each action is at least one
for l in first_iters:
	for a in l:
		m.addConstr(quicksum(a_vars[a]) >= 1)

# group constraints (all or nothing)
for g in groups:
        a1 = g[0]
        for a in g:
                m.addConstr(quicksum(a_vars[a1])==quicksum(a_vars[a]))


# stateful action constraint
for x in stages_a:
	m.addConstr(quicksum(x)<=num_state)

'''
# actions/regs cannot go in same stage
for x in stages_a:
	m.addConstr(quicksum(x)<=1)
'''

# memory constraint
# one memory var for every stg, action (same as decision vars for actions)
# mem var <= a_var * total_mem --> if decision var is 0 (action not in stg), then no memory allocated to that mem var
# organize mem vars by action and stage (like a_vars) - sum of each stg list <= total_mem
mem_vars = []
stages_mem_vars = []
for i in range(num_stg):
	stages_mem_vars.append([])
for l in stateful:
	stg_count = 0
	for i in range(len(a_vars[l])):
		mem_vars.append(m.addVar(lb=0,vtype=GRB.INTEGER,name="mem%s%s"%(l,stg_count)))
		stages_mem_vars[i].append(mem_vars[-1])
		m.addConstr(mem_vars[-1] <= a_vars[l][i]*total_mem)	# actions not allocated have 0 memory
		m.addConstr(mem_vars[-1] >= a_vars[l][i])		# actions in stgs have nonzero memory allocation
		stg_count += 1
for l in stages_mem_vars:
	m.addConstr(quicksum(l) <= total_mem)			# memory allocated in each stg adheres to memory constraints

# how to split mem equally / ensure that one action doesn't get allocated all the memory??
# do we need to account for this?


# Objective to optimize
# m.setObjective(quicksum(x for i in a_vars for x in i), GRB.MAXIMIZE)
m.setObjective(quicksum(mem_vars), GRB.MAXIMIZE)

# Solve
m.optimize()

# print all variable values
for v in m.getVars():
        print('%s %g' % (v.varName, v.x))



