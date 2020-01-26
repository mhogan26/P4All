import time
import sys
import json


# takes as input:
#       .dot file from tofino
#	list of action names (after upper bound) and number for ILP
#	reg_acts
#	upper bound

actions_list = [["count"],["set_min"]]
actions = {}

dot = sys.argv[1]

actions_in_dot = ["count_0","count_1","set_min_0","set_min_1"]

loops = {"num_arrays":["count","set_min"]}
uppers = {"num_arrays":14}

act_loops = {}

start_time = time.time()

'''
actions_file = sys.argv[2]
actions = {}
with open(actions_file,"r") as actfile:
	actions = json.load(actfile)


start_time = time.time()

'''

deps = {}

for l in loops:
	up = uppers[l]
	for temp in loops[l]:
		act_loops[temp] = l
	for i in range(len(actions_list)):
		acts = actions_list[i]
		if isinstance(acts, basestring):
			continue
		if acts[0] in loops[l]:
			new_list = []
			for v in range(up):
				for a in acts:
					new_list.append(a+"_"+str(v))
			actions_list[i] = new_list

act_num = 0
for act in actions_list:
	if isinstance(act, basestring):
		actions[act] = act_num
		act_num += 1
		continue
	for a in act:
		actions[a] = act_num
		act_num += 1



# include actions that must go in same stg - this will be if/else stmts in p4 file
#	 this will NOT come from dot file

with open(dot) as f:
	x = f.readlines()
	conditions = {}
	for line in x:	# if green, concat w/ action
		if "->" not in line:
                        continue
                l = line.split("->")
                a0 = l[0].replace(" ","")
                a1 = l[1].split()[0].replace(" ","")
		if "color=green" in line:
			# is there a case where this would include an action out of upper bounds for symbolic?
			if a0 not in actions and a1 not in actions:
				continue
			conditions[a0] = a1
		else:
			continue
	for line in x:
		if "->" not in line:
			continue
		l = line.split("->")
		a0 = l[0].replace(" ","")
		a1 = l[1].split()[0].replace(" ","")
		if a0 in conditions:
			a0 = conditions[a0]
		elif a1 in conditions:
			a1 = conditions[a1]
		if a0 not in actions or a1 not in actions:
			continue
		if "color=red" in line:
			#print line
			deps[(a0,a1)] = 1
		elif "color=blue" in line:
			#print line
			deps[(a0,a1)] = 1

to_add = {}
checked = []
not_in_dot_checked = {}
for d in deps:
	# if in actions_list, then we know it's not in a loop
	a0 = d[0]
	a1 = d[1]
	if a0 not in actions_list and a1 not in actions_list:
		if int(a0[-1])==int(a1[-1]): 	# same iteration - WHAT IF FROM 2 LOOPS W/ DIFF SYMBOLIC VARS?
			if (a0[0:-2],a1[0:-2]) not in checked:
				checked.append((a0[0:-2],a1[0:-2]))
				for i in range(2,uppers[act_loops[a0[0:-2]]]):
					to_add[((a0[0:-1]+str(i),a1[0:-1]+str(i)))] = deps[d]
		else:	# should be one away if same symb var - WHAT IF FROM 2 LOOPS W/ DIFF SYMBOLIC VARS?
			if (a0[0:-2],a1[0:-2]) not in checked:
				checked.append((a0[0:-2],a1[0:-2]))
				for i in range(2,uppers[act_loops[a0[0:-2]]]):
					to_add[((a0[0:-1]+str(i-1),a1[0:-1]+str(i)))] = deps[d]
	elif a0 in actions_list and a1 in actions_list:
		continue
	# this case should work for all examples - nested loop, etc.
	else:	# we have an action that's not in a loop
		if a0 in actions_list:
			if (a0,a1[0:-2]) not in not_in_dot_checked:
				not_in_dot_checked[(a0,a1[0:-2])] = 1
				continue
			elif not_in_dot_checked[(a0,a1[0:-2])] == 1:
				for i in range(2,uppers[act_loops[a1[0:-2]]]):
					to_add[(a0,a1[0:-1]+str(i))] = deps[d]
			else:
				continue

		if a1 in actions_list:
                        if (a0[0:-2],a1) not in not_in_dot_checked:
                                not_in_dot_checked[(a0[0:-2],a1)] = 1
                                continue
                        elif not_in_dot_checked[(a0[0:-2],a1)] == 1:
                                for i in range(2,uppers[act_loops[a0[0:-2]]]):
                                        to_add[(a0[0:-1]+str(i),a1)] = deps[d]
                        else:
                                continue



deps.update(to_add)

#print deps

print("--- %s seconds ---" % (time.time() - start_time))

