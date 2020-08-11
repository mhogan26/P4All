#!/usr/bin/python
from gurobipy import *
import time


# CMS W/ ORIG UTIL: .1414 SECONDS
# CMS W/ PWL UTIL: 8.665 SECONDS (with PWL for every mem var)
# PWL doesn't work if only set for 1st mem_var - others will be 0

# input will be something like:
#	N = total number of actions in unrolled p4 program
#	stateful = [list of indices of stateful actions]
#	groups = [list of [groups] that must occur together]


def t_util():
	output = []
	for w in range(128):
		if w==0:
			output.append(100)
			continue
		output.append(3/float(w))
	return output

start_time = time.time()

# input from unrolled p4 program:
# N value (upper bound on num actions)
N = 2
# list of stateful action indices
stateful = [0,1]
# list of actions w/ corresponding metadata
meta = [0,1]
# amount of metadata per action
meta_per = 64
# list of groups
groups = [[0,2], [1,3]]
# list of which actions are in same loop
loops = [[0,1], [2,3]]
# dictionary of dependency between actions
deps = {(0,2):1,(1,3):1,(2,3):2}
# list of which actions are in tables that require TCAM (ternary match)
tcam_acts = []
# list of REQUIRED tcam actions and their sizes
required_tcam = []

# switch resources input:
# total available stateful memory
total_mem = 4096
# lower bound for reg size
reg_bound = 256
# num stages
num_stg = 12
# stateful actions per stg
num_state = 4
# phv
phv = 4096
# TCAM per stg
tcam = 2048
# size of item stored in tcam
tcam_size = 16
# size of each register in reg array (size of items store in regs in bits)
item_size = 32


# Model
m = Model("test")

# Variables
act_vars = []		# contains list for each action
stages_vars = []	# list for each stage, composed of STATEFUL actions for each stg
for i in range(num_stg):
	stages_vars.append([])
# decision variable for every (action num, stg num) pair
# we multiply N by 2 bc we have 2 actions to consider (hash and min calc)
# because act var is binary, we by default only allow an action to be placed once in a single stage (won't get two of action A in stg 1)
for i in range(N*2):
	act_vars.append([])
	for j in range(num_stg):
		act_vars[i].append(m.addVar(vtype=GRB.BINARY,name="%s%s"%(i,j)))
		if i in stateful:
			stages_vars[j].append(act_vars[i][j])

	#m.addConstr(quicksum(act_vars[i])<=1)	# only place action once - we relax this to allow reg arrays to be split across stages (longer)

# stateful action constraint
for x in stages_vars:
	m.addConstr(quicksum(x)<=num_state)

#'''
# group constraints (all or nothing)
# is it always the case that if one reg array is split across stages then the corresponding action is still placed only once?
# or are there instances where you have to place the corresponding action FOR EACH STG other action is placed in
# need to look at more examples/data structures
# for now, we'll model after CMS - for each hashing action, we have ONLY ONE min action (no matter how many stages the single hashing action is split across)
# this is the more difficult case, it's trivial to place corresponding action every time we split across stages
for g in groups:
	a1 = g[0]
	#a2 = g[1]
	for a2 in g:
		if a2 not in stateful:
			m.addConstr(quicksum(act_vars[a2])<=1)	# not sure this is necessary, but leaving it just in case
			m.addConstr(quicksum(act_vars[a2])>=0)
			#m.addConstr(quicksum(act_vars[a1])==quicksum(act_vars[a]))	# this is the trivial case
			m.addConstr(quicksum(act_vars[a2])*quicksum(act_vars[a1])==quicksum(act_vars[a1]))
			m.addConstr((1-quicksum(act_vars[a1]))<=(1-quicksum(act_vars[a2])))
		else:	# THIS IS NOT TESTED YET! not sure if this case even comes up in any applications, but conceivably it might?
			m.addConstr(quicksum(act_vars[a1])*quicksum(act_vars[a2])>=quicksum(act_vars[a1]))

#'''

# dependency constraints
for key in deps:
	a0 = key[0]
	a1 = key[1]
	if deps[key] == 1:	# ordered (a0 must come BEFORE a1)
		for x in range(len(act_vars[a0])):
			z = 0
			while z <= x:
				m.addConstr(act_vars[a1][z]<=(1-act_vars[a0][x]))
				z += 1
	elif deps[key] == 2:    # unordered (a0 and a1 CANNOT be in same stg, order doesn't matter)
		for x in range(len(act_vars[a0])):
			m.addConstr(act_vars[a0][x]<=(1-act_vars[a1][x]))
	elif deps[key] == 3:	# same stg (a0 and a1 MUST be in the same stg)
		for x in range(len(act_vars[a0])):
			m.addConstr(act_vars[a0][x] == act_vars[a1][x])

# constraint for actions outside loop (non-symbolic actions) - they MUST get placed or we fail compilation
for l in loops:		# loops is a misnomer, it contains ALL actions, but groups actions in the same loop together
	if len(l) == 1:	# action isn't in a symbolic loop (or the upper bound of the loop = 1)
		m.addConstr(quicksum(a_vars[l[0]]) >= 1)
	else:
	# add constraint that makes solution ordered - higher values won't = 1 if lower values = 0
	# sum of act_var lists <= sum of higher index act_var lists
	# do we really want to enforce this? is there a situation where we wouldn't?
		for i in range(len(l)):
			if i == 0:
				continue
			m.addConstr(quicksum(act_vars[l[i]])*quicksum(act_vars[l[i-1]])>=quicksum(act_vars[l[i]]))
			# old, without multi-stage arrays:
			#m.addConstr(quicksum(a_vars[l[i]]) <= quicksum(a_vars[l[i-1]]))
#'''
# memory constraint - regsiter arrays in SRAM
# one memory var for every stg, STATEFUL action (same as decision vars for actions)
# mem var <= a_var * total_mem --> if decision var is 0 (action not in stg), then no memory allocated to that mem var
# organize mem vars by action and stage (like act_vars) - sum of each stg list <= total_mem
mem_vars = []
stages_mem_vars = []
for i in range(num_stg):
	stages_mem_vars.append([])
#act_count = 0
for l in stateful:
	j = stateful.index(l)
	stg_count = 0
	mem_vars.append([])
	for i in range(len(act_vars[l])):
		mem_vars[j].append(m.addVar(lb=0,ub=total_mem/item_size,vtype=GRB.INTEGER,name="mem%s%s"%(l,stg_count)))
		stages_mem_vars[i].append(mem_vars[j][-1])
		m.addConstr(mem_vars[j][-1]*item_size <= act_vars[l][i]*total_mem)	# actions not allocated have 0 memory
		m.addConstr(mem_vars[j][-1]*item_size >= act_vars[l][i])		# actions in stgs have nonzero memory allocation
		stg_count += 1
	#act_count += 1

for l in stages_mem_vars:
	m.addConstr(quicksum(l)*item_size <= total_mem)			# memory allocated in each stg adheres to memory constraints
# constraint so each row gets SAME amount of memory - how to identify this in orig program/represent in graph?
# all reg arrays contained in symbolic array in p4all program should get same amount memory
c = -1

for me in mem_vars:
	c+=1
	if c == 0:
		continue
	m.addConstr(quicksum(me)*quicksum(act_vars[0])==quicksum(mem_vars[0])*quicksum(act_vars[c]))
#'''

# TCAM constraint
# these constraints are only for tables with symbolic size
# if the size is concrete (not symbolic), we MUST place the table - else we fail
tcam_vars = []
stages_tcam_vars = []
for i in range(num_stg):
	stages_tcam_vars.append([])
for l in tcam_acts:
	j = tcam_acts.index(l)
	stg_count = 0
	tcam_vars.append([])
	for i in range(len(act_vars[l])):
		tcam_vars[j].append(m.addVar(lb=0,ub=tcam/tcam_size,vtype=GRB.INTEGER,name="tcam%s%s"%(l,stg_count)))
		stages_tcam_vars[i].append(tcam_vars[j][-1])
		m.addConstr(tcam_vars[j][-1]*tcam_size <= act_vars[l][i])			# actions not allocated have 0 TCAM
		m.addConstr(tcam_vars[j][-1]*tcam_size >= act_vars[l][i])			# actions in stgs have nonzero TCAM allocation

for l in stages_tcam_vars:		# tcam adheres to constraints
	m.addConstr(quicksum(l)*tcam_size <= tcam)

# ADD CONSTRAINT SO THAT EACH ONE IS EQUAL?? IF USE SAME SYMBOLIC, THEN EQUAL; ELSE CAN BE DIFFERENT


#m.addConstr(quicksum(mem_vars[0])-quicksum(mem_vars[1]) <= (quicksum(act_vars[0]))*(quicksum(act_vars[1]))*total_mem)
#m.addConstr(quicksum(mem_vars[1])-quicksum(mem_vars[0]) >= (quicksum(act_vars[0]))*(quicksum(act_vars[1]))*(-total_mem))

#m.addConstr(quicksum(mem_vars[1])-quicksum(mem_vars[2]) <= (quicksum(act_vars[1]))*(quicksum(act_vars[2]))*total_mem)
#m.addConstr(quicksum(mem_vars[2])-quicksum(mem_vars[1]) >= (quicksum(act_vars[1]))*(quicksum(act_vars[2]))*(-total_mem))

#m.addConstr(quicksum(mem_vars[2])-quicksum(mem_vars[3]) <= (quicksum(act_vars[2]))*(quicksum(act_vars[3]))*total_mem)
#m.addConstr(quicksum(mem_vars[3])-quicksum(mem_vars[2]) >= (quicksum(act_vars[2]))*(quicksum(act_vars[3]))*(-total_mem))

# how to split mem equally / ensure that one action doesn't get allocated all the memory??
# do we need to account for this?

# phv constraint
# meta variables correspond to act_vars
# not totally sure the constraint here will work for all cases - when action isn't placed, meta could still = 1
# TEST THIS
meta_vars = []
for met in meta:
	meta_vars.append(m.addVar(lb=0,vtype=GRB.BINARY,name="meta%s"%(met)))
	m.addConstr(meta_vars[-1]*quicksum(act_vars[met])==quicksum(act_vars[met]))
	m.addConstr((1-quicksum(act_vars[met]))<=(1-meta_vars[-1]))

m.addConstr(quicksum(meta_vars)*meta_per <= phv)


# Objective to optimize
#m.setObjective(2/quicksum(mem_vars[0]), GRB.MINIMIZE)
#m.setObjective(.75*quicksum(x for i in act_vars for x in i)+.25*quicksum(y for z in mem_vars for y in z), GRB.MAXIMIZE)
#m.setObjective(quicksum(x for i in act_vars for x in i),GRB.MAXIMIZE)
#m.setObjective(quicksum(x for i in mem_vars for x in i), GRB.MAXIMIZE)

#'''
# PWL OBJECTIVE
cols = list(range(128))
#err = [-w for w in t_util()]
err = t_util()
for i in range(len(mem_vars)):
	for j in range(len(mem_vars[i])):
		m.setPWLObj(mem_vars[i][j], cols, err)
#'''
# Solve
m.optimize()

print("--- %s seconds ---" % (time.time() - start_time))
#'''
# print all variable values
for v in m.getVars():
        print('%s %g' % (v.varName, v.x))
'''
# print out solution in a nicer format to use when constructing layout/p4 program

# figure out what stages each action is in (act, stg) - if not placed, not included in list
# STAGE NUMBER IS INCREMENTED BY 1, SO STARTS AT 1 INSTEAD OF 0
act_sol = []	# contains tuples of act and stg numbers
for i in range(len(act_vars)):
	for j in range(len(act_vars[i])):
		if act_vars[i][j].X > 0:
			act_sol.append((i,j+1))
		
#print act_sol

# figure out what stages each reg array is in and how big they are
mem_act_sol = []	# first number corresponds to associated action, second is stg number
mem_size_sol = []	# first number corresponds to associated action, second is size
# SHOULD MULTIPLY BY ITEM_SIZE HERE? OR DO WE WANT NUM REGS, NOT ARRAY SIZE????
for i in range(len(mem_vars)):
	for j in range(len(mem_vars[i])):
		if mem_vars[i][j].X > 0:
			mem_act_sol.append((i,j+1))
			mem_size_sol.append((i,mem_vars[i][j].X))

#print mem_size_sol

# figure out how much metadata we need - first number is assocaited action, second is size of metadata in bits
meta_sol = []
for i in range(len(meta_vars)):
	if meta_vars[i].X > 0:
		meta_sol.append((i,meta_vars[i].X*meta_per))

#print meta_sol		

# output: for each stage, print out action, number of registers + size
#for i in range(num_stg):
'''

