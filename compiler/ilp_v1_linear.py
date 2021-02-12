#!/usr/bin/python
from gurobipy import *
import time
import ast
import sys


# FIX LOOPS CONSTRAINT - DON'T ENFORCE ORDERED?
# or will have to add something to input that groups nums of SAME symbolic act together (not just acts in same loop)

# THIS IS THE MOST BASIC VERSION OF ILP - 
# does not allow for PWL utilities (only linear expressions)
# SRAM/TCAM cannot stretch across stages


# CMS W/ ORIG UTIL: .1414 SECONDS
# CMS W/ PWL UTIL: 8.665 SECONDS (with PWL for every mem var)
# PWL doesn't work if only set for 1st mem_var - others will be 0

# input will be something like:
#	N = total number of actions in unrolled p4 program
#	stateful = [list of indices of stateful actions]
#	meta [list of actions that require/use metadata]
#	meta_per = the amount of metadata (in bits) required by each new instance of an aciton
#	groups = [list of [groups] that must occur together]
#	loops = [list of [actions in the same loop] - if not in a loop, then action is in its own list]
#	deps = {dictionary of (action pair tuple): and depedency value}

#'''
# cms utility
def t_util(upper):
	output = []
	for w in upper:
		if w==0:
			output.append(100000000.123456)
			continue
		output.append(1000000*3/float(w))
	return output
#'''




prog_info = []
with open(sys.argv[1],'r') as f:
	prog_info = f.readlines()
prog_info = [x.strip() for x in prog_info]



# input from unrolled p4 program:
# N value (upper bound on num actions)
N = int(prog_info[11])
# list of stateful action indices (ex: stateful = [0,1])
stateful = list(map(int, prog_info[0].split()))
# list of actions w/ corresponding metadata (ex: meta = [0,1])
meta = list(map(int, prog_info[1].split()))
# list of metadata size per action (ex: meta_per = [64,64,64])
meta_per = list(map(int, prog_info[2].split()))
# list of groups (ex: groups = [[0,2], [1,3]])
groups = [ast.literal_eval(x) for x in prog_info[3].split()]
# list of which actions are in same loop (ex: loops = [[0,1], [2,3]])
loops = [ast.literal_eval(x) for x in prog_info[4].split()]
# dictionary of dependency between actions (ex: deps = {(0,2):1,(1,3):1,(2,3):2})
deps = ast.literal_eval(prog_info[5])
# list of which actions are in tables that require TCAM (ternary match)
tcam_acts = list(map(int, prog_info[6].split()))
# list of REQUIRED tcam actions and their sizes
required_tcam = list(map(int, prog_info[7].split()))
# size of each register (bits) in reg array (size of items store in regs in bits) - this is ONLY for symbolic values
item_size = list(map(int, prog_info[8].split()))
# flag to tell us if user provided utility (if not, then default utility is minimize stgs used)
utility_incl = int(prog_info[9])
# list of actions that use a hash
hash_acts = list(map(int, prog_info[10].split()))
# list of stateful(?) actions that share the same symbolic (must be the same size)
same_size = [ast.literal_eval(x) for x in prog_info[12].split()]
# LINEAR utility function
util_func = prog_info[13]


switch_info = []
with open(sys.argv[2],'r') as f:
	switch_info = f.readlines()
switch_info = [int(x.strip()) for x in switch_info]

# switch resources input:
# total available stateful memory
total_mem = switch_info[0]
# lower bound for reg size - do we even need this?
#reg_bound = 256
# num stages
num_stg = switch_info[1]
# stateful actions per stg
num_state = switch_info[2]
# phv
phv = switch_info[3]
# TCAM per stg
tcam = switch_info[4]
# size of item stored in tcam
tcam_size = switch_info[5]
# hashes per stg
hashes = switch_info[6]

tcam_size = 32

start_time = time.time()


# Model
m = Model("test")

# Variables
act_vars = []		# contains list for each action
stateful_stages_vars = []	# list for each stage, composed of STATEFUL actions for each stg
stages_vars = []
hash_stages_vars = []
for i in range(num_stg):
	stages_vars.append([])
	stateful_stages_vars.append([])
	hash_stages_vars.append([])
# decision variable for every (action num, stg num) pair
# we get as input N, which is total number of actions
for i in range(N):
	act_vars.append([])
	for j in range(num_stg):
		act_vars[i].append(m.addVar(vtype=GRB.BINARY,name="act%s_%s"%(i,j)))
		if i in stateful:
			stateful_stages_vars[j].append(act_vars[i][j])
		stages_vars[j].append(act_vars[i][j])
		if i in hash_acts:
			hash_stages_vars[j].append(act_vars[i][j])

	m.addConstr(quicksum(act_vars[i])<=1)	# only place action once - we relax this to allow reg arrays to be split across stages (longer)

# stateful action constraint
for x in stateful_stages_vars:
	m.addConstr(quicksum(x)<=num_state)

# hash action constraint
for x in hash_stages_vars:
	m.addConstr(quicksum(x)<=hashes)

# group constraints (all or nothing)
for g in groups:
	a1 = g[0]
	#a2 = g[1]
	for a2 in g:
		if a2 not in stateful:
			#m.addConstr(quicksum(act_vars[a2])<=1)	# not sure this is necessary, but leaving it just in case
			#m.addConstr(quicksum(act_vars[a2])>=0)
			#m.addConstr(quicksum(act_vars[a1])==quicksum(act_vars[a]))	# for split arrays; this is the trivial case
			m.addConstr(quicksum(act_vars[a2])*quicksum(act_vars[a1])==quicksum(act_vars[a1]))
			m.addConstr((1-quicksum(act_vars[a1]))<=(1-quicksum(act_vars[a2])))
		else:	# THIS IS NOT TESTED YET! not sure if this case even comes up in any applications, but conceivably it might?
			m.addConstr(quicksum(act_vars[a1])*quicksum(act_vars[a2])>=quicksum(act_vars[a1]))

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
required = []
for l in loops:		# loops is a misnomer, it contains ALL actions, but groups actions in the same loop together
	if len(l) == 1:	# action isn't in a symbolic loop (or the upper bound of the loop = 1)
		m.addConstr(quicksum(act_vars[l[0]]) >= 1)
		required.append(l[0])
	else:	 # THIS IS WRONG!!!! Won't work if mult actions in same loop
	# add constraint that makes solution ordered - higher values won't = 1 if lower values = 0
	# sum of act_var lists <= sum of higher index act_var lists
	# do we really want to enforce this? is there a situation where we wouldn't?
		for i in range(len(l)):
			if i == 0:
				continue
			# for multi-stage arrays:
			#m.addConstr(quicksum(act_vars[l[i]])*quicksum(act_vars[l[i-1]])>=quicksum(act_vars[l[i]]))
			# old, without multi-stage arrays:
			m.addConstr(quicksum(act_vars[l[i]]) <= quicksum(act_vars[l[i-1]]))


#'''
# memory constraint - regsiter arrays in SRAM
# one memory var for every stg, STATEFUL action (same as decision vars for actions)
# mem var <= a_var * total_mem --> if decision var is 0 (action not in stg), then no memory allocated to that mem var
# organize mem vars by action and stage (like act_vars) - sum of each stg list <= total_mem
mem_vars = []
stages_mem_vars = []
same_size_mem_vars = []	# this contains index of the vars we care about in mem_vars, each item is a list of indices that have same symbolic

for s in same_size:
	same_size_mem_vars.append([])

for i in range(num_stg):
	stages_mem_vars.append([])
#act_count = 0
for l in stateful:
	j = stateful.index(l)
	stg_count = 0
	mem_vars.append([])
	for i in range(len(act_vars[l])):
		mem_vars[j].append(m.addVar(lb=0,ub=total_mem/item_size[j],vtype=GRB.INTEGER,name="mem%s_%s"%(l,stg_count)))
		stages_mem_vars[i].append(mem_vars[j][-1])
		m.addConstr(mem_vars[j][-1]*item_size[j] <= act_vars[l][i]*total_mem)	# actions not allocated have 0 memory
		m.addConstr(mem_vars[j][-1]*item_size[j] >= act_vars[l][i])		# actions in stgs have nonzero memory allocation

		stg_count += 1

	# j is the index we care about?
	for s in same_size:
		if l in s:
			same_size_mem_vars[same_size.index(s)].append(j)


	#act_count += 1

# each reg in stages_mem could have a different item_size, so we iterate through each item size
sum_list = []
if len(stateful) > 0:
	for l in range(len(stages_mem_vars)):
		sum_list.append([])
		for r in range(len(stages_mem_vars[l])):
			sum_list[-1].append(stages_mem_vars[l][r]*item_size[r])	# this should be ok because items in both lists are in the same order			

	for l in range(len(sum_list)):
		m.addConstr(quicksum(sum_list[l])<= total_mem)			# memory allocated in each stg adheres to memory constraints



# constraint so each row gets SAME amount of memory - how to identify this in orig program/represent in graph?
# all reg arrays contained in symbolic array in p4all program should get same amount memory

# same_size is list, items are list of act_var numbers

c = -1
if len(stateful) > 0:	# if we have stateful acts
	for sl in same_size:
		for s in sl:
			if sl.index(s) == 0:
				continue
			m.addConstr(quicksum(mem_vars[same_size_mem_vars[same_size.index(sl)][sl.index(s)]])*quicksum(act_vars[sl[0]])==quicksum(mem_vars[same_size_mem_vars[same_size.index(sl)][0]])*quicksum(act_vars[s]))



# enforce same mem constraint for required vars
# do we need this???
'''
for r in required:
	if required.index(r)==0:
		continue
	if r not in stateful:
		continue
	m.addConstr(quicksum(mem_vars[r])==quicksum(mem_vars[r-1]))
'''

'''
for me in range(len(mem_vars)):
	if me==0:
		continue
	m.addConstr(quicksum(mem_vars[me])==quicksum(mem_vars[me-1]))

'''
'''
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
		m.addConstr(tcam_vars[j][-1]*tcam_size <= act_vars[l][i]*tcam)			# actions not allocated have 0 TCAM
		m.addConstr(tcam_vars[j][-1]*tcam_size >= act_vars[l][i])			# actions in stgs have nonzero TCAM allocation

		stg_count += 1
'''
'''
# REQUIRED TCAM (tables that we have to fit on the switch - w/o them, we fail compilation
req_tcam_vars = []
for l in required_tcam:
	if l <= 0:
		continue
	req_tcam_vars.append([])
	for i in range(num_stg):
		req_tcam_vars[-1].append(m.addVar(lb=0,ub=l+1,vtype=GRB.INTEGER,name="req_tcam%s%s"%(required_tcam.index(l),i)))
		stages_tcam_vars[i].append(req_tcam_vars[-1][-1])
		m.addConstr(req_tcam_vars[-1][-1] <= act_vars[required_tcam.index(l)][i]*tcam)
		m.addConstr(req_tcam_vars[-1][-1] >= act_vars[required_tcam.index(l)][i])
	m.addConstr(quicksum(req_tcam_vars[-1])==l)

for l in stages_tcam_vars:              # tcam adheres to constraints
        m.addConstr(quicksum(l)<= tcam/tcam_size)

# ADD CONSTRAINT SO THAT EACH ONE IS EQUAL?? IF USE SAME SYMBOLIC, THEN EQUAL; ELSE CAN BE DIFFERENT
'''


#'''

#m.addConstr(quicksum(mem_vars[0])-quicksum(mem_vars[1]) <= (quicksum(act_vars[0]))*(quicksum(act_vars[1]))*total_mem)
#m.addConstr(quicksum(mem_vars[1])-quicksum(mem_vars[0]) >= (quicksum(act_vars[0]))*(quicksum(act_vars[1]))*(-total_mem))

#m.addConstr(quicksum(mem_vars[1])-quicksum(mem_vars[2]) <= (quicksum(act_vars[1]))*(quicksum(act_vars[2]))*total_mem)
#m.addConstr(quicksum(mem_vars[2])-quicksum(mem_vars[1]) >= (quicksum(act_vars[1]))*(quicksum(act_vars[2]))*(-total_mem))

#m.addConstr(quicksum(mem_vars[2])-quicksum(mem_vars[3]) <= (quicksum(act_vars[2]))*(quicksum(act_vars[3]))*total_mem)
#m.addConstr(quicksum(mem_vars[3])-quicksum(mem_vars[2]) >= (quicksum(act_vars[2]))*(quicksum(act_vars[3]))*(-total_mem))

#'''
# phv constraint
# meta variables correspond to act_vars
# not totally sure the constraint here will work for all cases - when action isn't placed, meta could still = 1
# ^ how????? is this still true???
# TEST THIS


# THIS IS WRONG!!! what if same meta used in mult actions?
# we have to make sure we're only counting meta once
meta_vars = []
#bloom_meta_vars = []
for met in meta:
	meta_vars.append(m.addVar(lb=0,vtype=GRB.BINARY,name="meta%s"%(met)))
	#m.addConstr(meta_vars[-1]*quicksum(act_vars[met])==quicksum(act_vars[met]))
	#m.addConstr((1-quicksum(act_vars[met]))<=(1-meta_vars[-1]))
	m.addConstr(meta_vars[-1]==quicksum(act_vars[met]))



meta_sum_list = []
if len(meta) > 0:
        for l in range(len(meta_vars)):
		meta_sum_list.append(meta_vars[l]*meta_per[l])


	m.addConstr(quicksum(meta_sum_list) <= phv)


# if we don't have any dependencies, then let's try to force actions in early stages
#if len(deps.keys())<=0:
#	for i in range(num_stg):
#		if i == 0:
#			continue
#		m.addConstr(quicksum(stages_vars[i])<=quicksum(stages_vars[i-1]))

'''
if utility_incl == 0:
	stg_vars = []
	for i in range(num_stg):
		stg_vars.append(m.addVar(lb=0, vtype=GRB.BINARY,name="stg%s"%(i)))
		m.addConstr(stg_vars[-1]*quicksum(stages_vars[i])==quicksum(stages_vars[i]))
		m.addConstr((1-quicksum(stages_vars[i]))<=(1-stg_vars[-1]))

	m.setObjective(quicksum(stg_vars),GRB.MINIMIZE)
'''

# Objective to optimize
#m.setObjective(2/quicksum(mem_vars[0]), GRB.MINIMIZE)
#m.setObjective(.75*quicksum(x for i in act_vars for x in i)+.25*quicksum(y for z in mem_vars for y in z), GRB.MAXIMIZE)
#m.setObjective(quicksum(x for i in act_vars for x in i),GRB.MAXIMIZE)
m.setObjective(quicksum(x for i in mem_vars for x in i), GRB.MAXIMIZE)

#m.setObjective(quicksum(x for i in act_vars for x in i), GRB.MINIMIZE) 
#m.setObjective(quicksum(x for i in stages_vars for x in i), GRB.MAXIMIZE)

#m.setObjective(quicksum(x for i in tcam_vars for x in i),GRB.MAXIMIZE)


#m.addConstr(tcam_vars[0][0] >= 2)

#m.setObjective(quicksum(tcam_vars[0]),GRB.MAXIMIZE)

# Solve
m.optimize()

print("--- %s seconds ---" % (time.time() - start_time))
#'''
# print all variable values
for v in m.getVars():
        print('%s %g' % (v.varName, v.x))

print('Obj: %g' % m.objVal)

m.printStats()

#'''
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

# figure out how much metadata we need - first number is associated action, second is size of metadata in bits
# do we actually need to know size? or is it enough to just know which actions use meta?
meta_sol = []
for i in range(len(meta_vars)):
	if meta_vars[i].X > 0:
		meta_sol.append((i,meta_vars[i].X*meta_per[i]))

#print meta_sol		

# output: for each stage, print out action, number of registers + size
#for i in range(num_stg):
#'''

