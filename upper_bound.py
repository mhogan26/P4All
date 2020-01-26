import networkx as nx
# takes as input:
#	.dot file from tofino
#	symbolic var and list of which actions are in the same for loop
#	separate dict for nested loops w/ actions {outer: [actions, {inner: actions}, actions]}
#	num_stages
#	list of actions that are in same conditional stmt

dot = "cms/cms1_ingress_tables_dep.dot"
loops = {"num_rows":["count_0", "set_min_0", "count_1", "set_min_1"]}
nested = {}
num_stages = 3
stateless = 4
conditionals = []	# only need this if tofino graph DOES NOT have edges for all actions

# triple+ nested loops
# fix condition so if stmt goes with every action in if body, not just first one
#	this means adding a separate edge for each action in body
#	IS THIS NECESSARY? or does tofino already make edges for all of them?

def get_upper_bound(loop):
# input here is list of actions in the loop
	# create graph nodes for each action in a for loop
	g = nx.DiGraph()
	for a in loop:
		g.add_node(a)

# red: ordered dep
# blue: unordered dep
# dotted: no dep
# yellow: no dep
# green: no dep (conditional)
#	if green, make single node out of condition and other node its connected to
# add dep edges to graph
	with open(dot) as f:
		x = f.readlines()
		conditions = {}
		for line in x:
			if "->" not in line:
                        	continue
			if "color=green" in line:
				l = line.split("->")
               			a0 = l[0].replace(" ","")
                		a1 = l[1].split()[0].replace(" ","")
				if a1 not in loop:	# if action isn't in current loop, skip it
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
			# no dep, no edge - ??? WILL THIS WORK FOR UPPER BOUND CALC?
			if "style=dotted" in line or "color=yellow" in line or "color=green" in line:
				continue
			elif "color=red" in line:
				if a0 in conditions:
					a0 = conditions[a0]
				elif a1 in conditions:
					a1 = conditions[a1]
				if a0 not in loop or a1 not in loop:	# if action isn't in current loop, skip it
					continue
				g.add_edge(a0,a1)
			elif "color=blue" in line:	# bidrectional edge
                        	if a0 in conditions:
                                	a0 = conditions[a0]
                        	elif a1 in conditions:
                                	a1 = conditions[a1]
                                if a0 not in loop or a1 not in loop:	# if action isn't in current loop, skip it
                                        continue
				g.add_edge(a0,a1)
				g.add_edge(a1,a0)

	# case where graph has edges:
	#	walk graph, longest path where num nodes = num stages / num edges = num stages - 1
	start = loop[0]
	end = loop[-1]
	paths = list(nx.all_simple_paths(g,start,end))

	iterations = 0

	# case where graph has no edges:
	#       upper bound is stateless * num stages
	if len(g.edges()) <= 0:
		iterations = num_stages * stateless
		return iterations

	# for each path, find num stages node - whichever node has highest iteration, pick it
	for p in paths:
		n = p[num_stages-1]
		n = n.split("_")
		if int(n[-1].replace(" ","")) > iterations:
			iterations = n[-1]

	return int(iterations) + 1

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

for sym in loops:
	print sym + ": " + str(get_upper_bound(loops[sym]))

# if dict is NOT empty, do nested loop calc
if bool(nested):
	for inner in nested:
		print get_nested_upper_bound(nested[inner])
	print "non empty"
