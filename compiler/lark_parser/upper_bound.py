import networkx as nx
import time
# takes as input:
#	dep dict parsing - deps
#	symbolic var and list of which actions are in the same for loop - loop_act_name
#	resource file
#	list of stateful acts - stateful

#	separate dict for nested loops w/ actions {outer: [actions, {inner: actions}, actions]}
#	list of actions that are in same conditional stmt



def get_upper_bound(loop, stateful, stateless_ub, state_ub, num_stages, deps):
# input here is list of actions in the loop
	# create graph nodes for each action in a for loop
	acts_to_add = []
	ub = stateless_ub
	for act in loop:		# if we have a stateful action, we can make upper bound smaller
		if act in stateful:
			ub = state_ub
			break

	added = []
	combined = {}
	reverse_combined = {}
	g = nx.DiGraph()
	# TODO: non-sym deps (more edges)
	for (a0,a1) in deps:
		if deps[(a0,a1)]==3:
			if a0 in combined:
				combined[a0].append(a1)
				if a1 not in reverse_combined:
					reverse_combined[a1] = a0
				continue
			if a1 in combined:
				combined[a1].append(a0)
				if a0 not in reverse_combined:
					reverse_combined[a0] = a1
				continue
			if a0 in reverse_combined:
				combined[reverse_combined[a0]].append(a1)
				reverse_combined[a1] = reverse_combined[a0]
				continue
			if a1 in reverse_combined:
				combined[reverse_combined[a1]].append(a0)
				reverse_combined[a0] = reverse_combined[a1]
				continue
			combined[a0] = [a1]
			reverse_combined[a1] = a0
	for (a0,a1) in deps:
		if a0 not in loop and a1 not in loop:	# we only care about actions that are the loop
			continue
		if deps[(a0,a1)]==1:			# dep actions, we need an edge
			if a0 in reverse_combined:
				a0 = reverse_combined[a0]
			if a1 in reverse_combined:
				a1 = reverse_combined[a1]
			if a0 not in added:
				for i in range(ub):
					g.add_node(a0+"_"+str(i))
				added.append(a0)
			if a1 not in added:
				for i in range(ub):
					g.add_node(a1+"_"+str(i))
				added.append(a0)
			if a0==a1:
				for i in range(0,ub-1):
					g.add_edge(a0+"_"+str(i),a0+"_"+str(i+1))
				continue
			for i in range(ub):
				g.add_edge(a0+"_"+str(i),a1+"_"+str(i))


	if loop[0] in reverse_combined:
		start = reverse_combined[loop[0]]+"_"+str(0)
	else:
		start = loop[0]+"_"+str(0)

	if loop[-1] in reverse_combined:
		end = reverse_combined[loop-1]+"_"+str(ub-1)
	else:
		end = loop[-1]+"_"+str(ub-1)

	#'''
	# case where graph has edges:
	#	walk graph, longest path where num nodes = num stages / num edges = num stages - 1
	#start = new_loop[0]
	#start = "remove_value_header_0"
	#end = "add_value_header_1199"
	#end = new_loop[-1]

	paths = list(nx.all_simple_paths(g,start,end))
	iterations = 0

	# case where graph has no edges:
	#       upper bound is stateless_ub = stateless * num stages
	if len(g.edges()) <= 0:
		iterations = ub
		return iterations
	short = True
	for p in paths:
		if len(p) >= num_stages:
			short = False

	if short:
		return ub

	# for each path, find num stages node - whichever node has highest iteration, pick it
	for p in paths:
		n = p[num_stages-1]
		n = n.split("_")
		if int(n[-1].replace(" ","")) > iterations:
			iterations = n[-1]
			break

	return int(iterations) + 1
	#'''

	#return ub

'''
def get_netsted_upper_bound(loop):
# input is list w/ a dictionary for inner loops
	# assume we only have 1 inner loop for now, then change to allow for mult. inner loops
	# what about triple+ nested loops? will this still work? [only tested on doubly nested]
	#	recursion
	outer_iterations = 0
	inner_iterations = {}
	# start with outer = 1 and find max inner, then switch
	# we can ignore actions outside inner loop, because we're looking at inner loop bound
	for a in loop:	# loop is a list w/ a dictionary for inner loops
		if not isinstance(a, dict):	# ignore actions outside inner loop
			continue
		for act in a:	# what if a has another dict inside it? triple nested loops?
			inner_iterations[act] =  get_upper_bound(a[act])
		

	# inner = 1, find max outer
	# we have to do actions inside and outside inner loop
	acts = []
	for a in loop:
		if not isinstance(a, dict):
			acts.append(a)
		else:
			for act in a:	# what if a has another dict inside it? triple nested loops?
				acts.append(a[act])
	outer_iterations = get_upper_bound(acts)
				
	return outer_iterations, inner_iterations
'''
'''
start_time = time.time()

for sym in loops:
	print sym + ": " + str(get_upper_bound(loops[sym],start,end))


# if dict is NOT empty, do nested loop calc
#if bool(nested):
#	for inner in nested:
#		print get_nested_upper_bound(nested[inner])
#	print "non empty"


print("--- %s seconds ---" % (time.time() - start_time))
'''

