#!/usr/bin/python
from gurobipy import *
import time


# input will be something like:
#	N = total number of actions in unrolled p4 program
#	deps = dict{tuple:dep} [1 = ordered dep, 2 = unordered dep]
#	stateful = [list of indices of stateful actions]
#	groups = [list of [groups] that must occur together]


start_time = time.time()

# input from unrolled p4 program:
# N value (upper bound on num actions)
N = 10
# dependencies
deps = {(0,5):1, (1,6):1, (2,7):1, (3,8):1, (4,9):1, (5,6):2, (5,7):2, (5,8):2, (5,9):2, (6,7):2, (6,8):2, (6,9):2, (7,8):2, (7,9):2, (8,9):2}
# list of stateful action indices
stateful = [0,1,2,3,4]
# list of groups
groups = [[0,5], [1,6], [2,7], [3,8], [4,9]]
# list of which actions are in same loop
loops = [[0,1,2,3,4], [5,6,7,8,9]]

# switch resources input:
# total available stateful memory
total_mem = 2048
# lower bound for reg size
reg_bound = 256
# num stages
num_stg = 3
# stateful actions per stg
num_state = 5

# Model
m = Model("test")

# Variables
act_vars = []		# contains list for each action
stages_vars = []	# list for each stage, composed of STATEFUL actions for each stg
for i in range(num_stg):
	stages_vars.append([])
# decision variable for every (action num, stg num) pair
for i in range(N):
	act_vars.append([])
	for j in range(num_stg):
		act_vars[i].append(m.addVar(vtype=GRB.BINARY,name="%s%s"%(i,j)))
		if i in stateful:
			stages_vars[j].append(act_vars[i][j])

	m.addConstr(quicksum(act_vars[i])<=1)	# only place action once

# dep constraints
for key in deps:
	a0 = key[0]
	a1 = key[1]
	if deps[key] == 1:	# ordered
		for x in range(len(act_vars[a0])):
			z = 0
			while z <= x:
				m.addConstr(act_vars[a1][z]<=(1-act_vars[a0][x]))
				z += 1

	elif deps[key] == 2:	# unordered
		for x in range(len(act_vars[a0])):
			m.addConstr(act_vars[a0][x]<=(1-act_vars[a1][x]))

        elif deps[key] == 3:    # same stg
                for x in range(len(act_vars[a0])):
                        m.addConstr(act_vars[a0][x] == act_vars[a1][x])


# stateful action constraint
for x in stages_vars:
	m.addConstr(quicksum(x)<=num_state)

# group constraints (all or nothing)
for g in groups:
	a1 = g[0]
	for a in g:
		m.addConstr(quicksum(act_vars[a1])==quicksum(act_vars[a]))

# add constraint that makes solution ordered - higher values won't = 1 if lower values = 0
# sum of act_var lists <= sum of higher index act_var lists
# do we really want to enforce this? is there a situation where we wouldn't?
for l in loops:
	for i in range(len(l)):
		if i == 0:
			continue
		m.addConstr(quicksum(act_vars[l[i]]) <= quicksum(act_vars[l[i-1]]))

# memory constraint
# one memory var for every stg, STATEFUL action (same as decision vars for actions)
# mem var <= a_var * total_mem --> if decision var is 0 (action not in stg), then no memory allocated to that mem var
# organize mem vars by action and stage (like a_vars) - sum of each stg list <= total_mem
mem_vars = []
stages_mem_vars = []
for i in range(num_stg):
	stages_mem_vars.append([])
#act_count = 0
for l in stateful:
	stg_count = 0
	mem_vars.append([])
	for i in range(len(act_vars[l])):
		mem_vars[l].append(m.addVar(lb=0,vtype=GRB.INTEGER,name="mem%s%s"%(l,stg_count)))
		stages_mem_vars[i].append(mem_vars[l][-1])
		m.addConstr(mem_vars[l][-1] <= act_vars[l][i]*total_mem)	# actions not allocated have 0 memory
		m.addConstr(mem_vars[l][-1] >= act_vars[l][i])		# actions in stgs have nonzero memory allocation
		stg_count += 1
	#act_count += 1

for l in stages_mem_vars:
	m.addConstr(quicksum(l) <= total_mem)			# memory allocated in each stg adheres to memory constraints
# constraint so each row gets SAME amount of memory - how to identify this in orig program/represent in graph?
# all reg arrays contained in array in p4all program should get same amount memory
'''
for l in range(len(mem_vars)):
	if l == 0:
		continue
	m.addConstr(quicksum(mem_vars[(l-1)])-quicksum(mem_vars[l]) >= (1-quicksum(act_vars[l-1]))*(1-quicksum(act_vars[l]))*total_mem)
        m.addConstr(quicksum(mem_vars[(l)])-quicksum(mem_vars[l-1]) <= (1-quicksum(act_vars[l-1]))*(1-quicksum(act_vars[l]))*(-total_mem))
'''

#m.addConstr(quicksum(mem_vars[0])-quicksum(mem_vars[1]) <= (quicksum(act_vars[0]))*(quicksum(act_vars[1]))*total_mem)
#m.addConstr(quicksum(mem_vars[1])-quicksum(mem_vars[0]) >= (quicksum(act_vars[0]))*(quicksum(act_vars[1]))*(-total_mem))

#m.addConstr(quicksum(mem_vars[1])-quicksum(mem_vars[2]) <= (quicksum(act_vars[1]))*(quicksum(act_vars[2]))*total_mem)
#m.addConstr(quicksum(mem_vars[2])-quicksum(mem_vars[1]) >= (quicksum(act_vars[1]))*(quicksum(act_vars[2]))*(-total_mem))

#m.addConstr(quicksum(mem_vars[2])-quicksum(mem_vars[3]) <= (quicksum(act_vars[2]))*(quicksum(act_vars[3]))*total_mem)
#m.addConstr(quicksum(mem_vars[3])-quicksum(mem_vars[2]) >= (quicksum(act_vars[2]))*(quicksum(act_vars[3]))*(-total_mem))

# how to split mem equally / ensure that one action doesn't get allocated all the memory??
# do we need to account for this?


# Objective to optimize
m.setObjective(quicksum(x for i in act_vars for x in i), GRB.MAXIMIZE)
#m.setObjective(quicksum(x for i in mem_vars for x in i), GRB.MAXIMIZE)

# Solve
m.optimize()

print("--- %s seconds ---" % (time.time() - start_time))

# print all variable values
for v in m.getVars():
        print('%s %g' % (v.varName, v.x))


'''
# memory constraint
# does this have to happen after first ilp? is it ok to do it after?
# maybe this should be an iterative process - if mem allocation doesn't fit user constraints then redo both ilps

# Model
m0 = Model("mem")

# reorganize vars from first ilp so we only have a vars that are allocated

# allocate mem - is this even an ilp? or are we just equally dividing mem?

# Solve
m0.optimize()

# print all variable values
for v in m0.getVars():
        print('%s %g' % (v.varName, v.x))
'''

