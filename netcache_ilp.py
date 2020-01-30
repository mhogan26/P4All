# REWRITE so that there's a decision variable per action per stage - Xij = 1 if action i is in stage j
# sum of decision variables for a single action = 1
# sum of decision variables for a single stage <= num_state
# if Xij = 1 for action a, then Xik = 1 for b, where j < k


#!/usr/bin/python
from gurobipy import *
import time
import pickle

# N value (upper bound on num actions)
N = 1325
act_nums = {}
with open("act_nums.txt",'r') as a:
	act_nums = pickle.load(a)


#loops = [[0],[1],[2],[3],[4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57,58,59,60,61,62,63,64,65,66,67,68,69,70,71,72,73,74,75],[76],[77]]
# NESTED FOR LOOPS????? OR JUST GROUP BY OUTERMOST LOOP?

loops = [[0],[1],[],[],[act_nums["reply_read_hit_before"]],[],[act_nums["reply_read_hit_after"]]]
stateful = []
groups = []
meta = [[],[]]
stateful.append(0)
for i in range(600):
	loops[2].append(act_nums["hh_load_count_"+str(i)])
	loops[3].append(act_nums["report_hot_2_"+str(i)])
	stateful.append(act_nums["hh_load_count_"+str(i)])
	groups.append([act_nums["hh_load_count_"+str(i)],act_nums["report_hot_2_"+str(i)]])
	meta[0].append(act_nums["hh_load_count_"+str(i)])

for i in range(12):
	loops[5].append(act_nums["add_value_header_"+str(i)])
        loops[5].append(act_nums["read_value_1_"+str(i)])
        loops[5].append(act_nums["read_value_2_"+str(i)])
        loops[5].append(act_nums["read_value_3_"+str(i)])
        loops[5].append(act_nums["read_value_4_"+str(i)])
        loops[5].append(act_nums["write_value_1_"+str(i)])
        loops[5].append(act_nums["write_value_2_"+str(i)])
        loops[5].append(act_nums["write_value_3_"+str(i)])
        loops[5].append(act_nums["write_value_4_"+str(i)])
        loops[5].append(act_nums["remove_value_header_"+str(i)])
	stateful.append(act_nums["read_value_1_"+str(i)])
	stateful.append(act_nums["read_value_2_"+str(i)])
	stateful.append(act_nums["read_value_3_"+str(i)])
	stateful.append(act_nums["read_value_4_"+str(i)])
	groups.append([act_nums["add_value_header_"+str(i)],act_nums["read_value_1_"+str(i)],act_nums["read_value_2_"+str(i)],act_nums["read_value_3_"+str(i)],act_nums["read_value_4_"+str(i)],act_nums["write_value_1_"+str(i)],act_nums["write_value_2_"+str(i)],act_nums["write_value_3_"+str(i)],act_nums["write_value_4_"+str(i)],act_nums["remove_value_header_"+str(i)],act_nums["read_value_1_"+str(i)],act_nums["read_value_2_"+str(i)],act_nums["read_value_3_"+str(i)],act_nums["read_value_4_"+str(i)],])
	meta[1].append(act_nums["add_value_header_"+str(i)])


#first_iters = [[4,5,6,7,8,9]]

first_iters = [[act_nums["hh_load_count_0"]],[act_nums["report_hot_2_0"]],[act_nums["add_value_header_0"],act_nums["read_value_1_0"],act_nums["read_value_1_1"],act_nums["read_value_1_2"],act_nums["read_value_1_3"],act_nums["write_value_1_0"],act_nums["write_value_1_1"],act_nums["write_value_1_2"],act_nums["write_value_1_3"],act_nums["remove_value_header_0"]]]

#groups = [[4,5,6,7,8,9],[10,11,12,13,14,15],[16,17,18,19,20,21],[22,23,24,25,26,27],[28,29,30,31,32,33],[34,35,36,37,38,39],[40,41,42,43,44,45],[46,47,48,49,50,51],[52,53,54,55,56,57],[58,59,60,61,62,63],[64,65,66,67,68,69],[70,71,72,73,74,75]]

# we only include read actions in stateful
# corresponding write actions must be in same stg and read will never happen at same time as write (if/else)
#stateful = [1,5,6,11,12,17,18,23,24,29,30,35,36,41,42,47,48,53,54,59,60,65,66,71,72]


deps = {}
with open("deps.txt",'r') as d:
	deps = pickle.load(d)

# same array read/writes MUST be in same stg
# acts 1 + 2 in same stg, 5+10, 6+11, etc.
# these are designated w/ dep type 3 in dep list

# total available stateful memory
total_mem = 2048
# lower bound for reg size
reg_bound = 256
# num stages
num_stg = 12
# stateful actions per stg
num_state = 4
# phv left after const - 568
phv = 3628
# meta each action takes - 80 for cms, 128 for kv
meta_per = [80,128]

start_time = time.time()

# Model
m = Model("test")

# Variables
a_vars = []	# contains list for each action
stages_a = []	# list for each stage, composed of actions for each stg
for i in range(num_stg):
	stages_a.append([])

# decision variable for every (action num, stg num) pair
cms_vars = []
cms_vars_nums = []
kv_vars = []
kv_vars_nums = []
for i in range(N):
	a_vars.append([])
	for j in range(num_stg):
		a_vars[i].append(m.addVar(vtype=GRB.BINARY,name="act%s%s"%(i,j)))
		if i >= act_nums["hh_load_count_0"] and i <= act_nums["report_hot_2_599"]:
			cms_vars.append(a_vars[i][-1])
			cms_vars_nums.append(i)
		elif i >= act_nums["add_value_header_0"] and i <= act_nums["remove_value_header_11"]:
			kv_vars.append(a_vars[i][-1])
			kv_vars_nums.append(i)
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
cms_mem_vars = []
kv_mem_vars = []
cms_mem_nums = []
kv_mem_nums = []
cms_mem_vars_cons = []
kv_mem_vars_cons = []
cms_m_i = -1
kv_m_i = -1
for i in range(num_stg):
	stages_mem_vars.append([])
for l in stateful:
	j = stateful.index(l)
	stg_count = 0
	mem_vars.append([])
	if l > 0 and l < act_nums["read_value_1_0"]:
		cms_mem_vars_cons.append([])
		cms_m_i += 1
	elif l >= act_nums["read_value_1_0"]:
		kv_mem_vars_cons.append([])
		kv_m_i += 1
	for i in range(len(a_vars[l])):
		mem_vars[j].append(m.addVar(lb=0,vtype=GRB.INTEGER,name="mem%s%s"%(l,stg_count)))
		stages_mem_vars[i].append(mem_vars[j][-1])
		m.addConstr(mem_vars[j][-1] <= a_vars[l][i]*total_mem)	# actions not allocated have 0 memory
		m.addConstr(mem_vars[j][-1] >= a_vars[l][i])		# actions in stgs have nonzero memory allocation
		stg_count += 1
		if l > 0 and l < act_nums["read_value_1_0"]:
			cms_mem_vars.append(mem_vars[j][-1])
			cms_mem_nums.append(l)
			cms_mem_vars_cons[cms_m_i].append(mem_vars[j][-1])
		elif l >= act_nums["read_value_1_0"]:
			kv_mem_vars.append(mem_vars[j][-1])
			kv_mem_nums.append(l)
			kv_mem_vars_cons[kv_m_i].append(mem_vars[j][-1])
for l in stages_mem_vars:
	m.addConstr(quicksum(l) <= total_mem)			# memory allocated in each stg adheres to memory constraints

#'''
c = -1
for me in cms_mem_vars_cons:
	c += 1
	if c == 0:
		continue
	m.addConstr(quicksum(me)*quicksum(a_vars[2])==quicksum(cms_mem_vars_cons[0])*quicksum(a_vars[2+c]))
#'''
c = -1
add = 0
for me in kv_mem_vars_cons:
        c += 1
        if c == 0:
                continue
	if c%4==0:
		add += 1
	add_i = (add*6)
        m.addConstr(quicksum(me)*quicksum(a_vars[1205])==quicksum(kv_mem_vars_cons[0])*quicksum(a_vars[1205+c+add_i]))
#'''
#m.addConstr(quicksum(a_vars[4]) == 0)
#m.addConstr(quicksum(cms_mem_vars_cons[2])==0)
#m.addConstr(quicksum(cms_mem_vars_cons[1])*quicksum(a_vars[2])==quicksum(cms_mem_vars_cons[0])*quicksum(a_vars[3]))
#m.addConstr(quicksum(cms_mem_vars_cons[2])*quicksum(a_vars[2])==quicksum(cms_mem_vars_cons[0])*quicksum(a_vars[4]))
#m.addConstr(quicksum(cms_mem_vars_cons[3])*quicksum(a_vars[cms_mem_nums[0]])==quicksum(cms_mem_vars_cons[0])*quicksum(a_vars[cms_mem_nums[3]]))
#m.addConstr(quicksum(cms_mem_vars_cons[4])*quicksum(a_vars[cms_mem_nums[0]])==quicksum(cms_mem_vars_cons[0])*quicksum(a_vars[cms_mem_nums[4]]))


#m.addConstr(quicksum(cms_mem_vars_cons[-1])*quicksum(a_vars[cms_mem_nums[-2]])==quicksum(cms_mem_vars_cons[-2])*quicksum(a_vars[cms_mem_nums[-1]]))



i_1 = stateful.index(act_nums["read_value_1_0"])
i_2 = stateful.index(act_nums["read_value_2_0"])
i_3 = stateful.index(act_nums["read_value_3_0"])
i_4 = stateful.index(act_nums["read_value_4_0"])

m.addConstr(quicksum(mem_vars[0])==quicksum(mem_vars[i_1]))
m.addConstr(quicksum(mem_vars[0])==quicksum(mem_vars[i_2]))
m.addConstr(quicksum(mem_vars[0])==quicksum(mem_vars[i_3]))
m.addConstr(quicksum(mem_vars[0])==quicksum(mem_vars[i_4]))

# how to split mem equally / ensure that one action doesn't get allocated all the memory??
# do we need to account for this?

#m.addConstr(quicksum(mem_vars[0]) == quicksum(mem_vars[1]))
#m.addConstr(quicksum(mem_vars[1]) == quicksum(mem_vars[2]))

meta_vars = []
for met in range(len(meta)):
	meta_vars.append([])
	for me in meta[met]:
		meta_vars[met].append(m.addVar(lb=0,vtype=GRB.BINARY,name="meta%s"%(me)))
		m.addConstr(meta_vars[met][-1]==quicksum(a_vars[me]))

m.addConstr(quicksum(meta_vars[0])*meta_per[0] + quicksum(meta_vars[1])*meta_per[1] <= phv) 


# Objective to optimize
# m.setObjective(quicksum(x for i in a_vars for x in i), GRB.MAXIMIZE)
#m.setObjective(quicksum(x for i in mem_vars for x in i), GRB.MAXIMIZE)

m.setObjective(.25*quicksum(kv_mem_vars) + .75*quicksum(cms_mem_vars), GRB.MAXIMIZE)

# Solve
m.optimize()


'''
for a in a_vars:
	for j in range(len(a)):
		i = a[j]
		if i.x == 1:
			print "act: "+str(i.varName)+ "stg: "+str(j)
			break
'''

'''
# print all variable values
for v in m.getVars():
        print('%s %g' % (v.varName, v.x))
'''


print("--- %s seconds ---" % (time.time() - start_time))

# find way to print out cms vars and kv vars separate - get stages easier

inv_map = {v: k for k, v in act_nums.iteritems()}

for v in a_vars[0]:
	if v.x == 1:
		print "check_cache_valid: "+v.varName.replace("act"+str(act_nums["check_cache_valid"]),'')
for v in a_vars[1]:
        if v.x == 1:
                print "set_cache_valid: "+v.varName.replace("act"+str(act_nums["set_cache_valid"]),'')
for v in mem_vars[0]:
	if v.x > 0:
		print "Valid memory: "+str(v.x)

for v in a_vars[act_nums["reply_read_hit_before"]]:
        if v.x == 1:
                print "reply_read_hit_before: "+v.varName.replace("act"+str(act_nums["reply_read_hit_before"]),'')
for v in a_vars[-1]:
        if v.x == 1:
                print "reply_read_hit_after: "+v.varName.replace("act"+str(act_nums["reply_read_hit_after"]),'')
i_c = 0
for v in cms_vars:
	t = cms_vars_nums[i_c]
	i_c += 1
	if v.x == 1:
		print "cms: "+inv_map[t]+" "+v.varName.replace("act"+str(t),'')
i_k = 0
for v in kv_vars:
	t = kv_vars_nums[i_k]
	i_k += 1
        if v.x == 1:
                print "kv: "+inv_map[t]+" "+v.varName.replace("act"+str(t),'')

cms_m_sum = 0
for v in cms_mem_vars:
	cms_m_sum += v.x
kv_m_sum = 0
for v in kv_mem_vars:
	kv_m_sum += v.x

print "CMS memory: "+str(cms_m_sum)
print "KV memory: "+str(kv_m_sum)

for v in cms_mem_vars:
	if v.x > 0:
		print "cms: "+v.varName+" "+str(v.x)

for v in kv_mem_vars:
	if v.x > 0:
                print "kv: "+v.varName+" "+str(v.x)

# print all variable values
#for v in m.getVars():
#        print('%s %g' % (v.varName, v.x))





