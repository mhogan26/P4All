# takes as input:
#       .dot file from tofino
#	list of action names (after upper bound) and number for ILP
dot = "cms/cms1_ingress_tables_dep.dot"
actions = {"count_0":0, "set_min_0": 1, "count_1":2, "set_min_1":3}

deps = {}

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
			deps[(actions[a0],actions[a1])] = 1
		elif "color=blue" in line:
			#print line
			deps[(actions[a0],actions[a1])] = 2
			
print deps

