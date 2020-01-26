import sys
import re
import json
import time

# go through headers, metadata
# go to ingress control - apply block (get actions to replicate)
# replicate actions + registers in ingress control
# go to egress control
# replicate actions + registers in egress control


# TO CALL: python unroll.py .p4all constraint file(.txt) 0(init)/1(afterILP) symb value symb value(if afterILP)

# change so regex matches instead of if " " + or if "\t" + etc.

start_time = time.time()

afterILP = False

concrete = {}
# check input - if not flag, then before ILP, so don't look for symbolic var input and use arbitrary vals
# if flag, then after ILP calc, so parse input
if int(sys.argv[3]) == 1:
	afterILP = True
	i = 4
	while (i+1) < len(sys.argv):
		concrete[sys.argv[i]] = int(sys.argv[i+1])
		i+=2
#concrete = {"num_arrays":1,"depth":4} # this is a map from symbolic var name: value

p4all_name = sys.argv[1]
constraint_name = sys.argv[2]

upper = 1
# get basic upper bound for symbolic vars (stateless * stages) from constraint file if before ILP
if not afterILP:
	with open(constraint_name, "r") as con_file:
		for line in con_file:
			line = line.split()
			if "stateless" in line[0] or "stages" in line[0]:
				upper = upper * int(line[1])

# parse p4all file into list of lines
with open(p4all_name, "r") as p4all_file:
    p4all = p4all_file.readlines()


# check for symbolic vars in parsed file and save var names
# if this is second pass, we already know the symbolics and we don't need to save them
symbolics = []
assume = []

# this loop should quit as soon as we get through the symbolics
current_index = 0
sym_section = False
arrays = {}
for i in range(len(p4all)):
	current_index = i
	line = p4all[i]
	if not re.search('[a-zA-Z]', line):
		continue
	if "symbolic " in line:
		sym_section = True
		if not afterILP:
			l = line.split()
			symbolics.append(l[2].replace(';',''))
			concrete[l[2].replace(';','')] = upper
		p4all[i] = ""	# remove symbolic var dec from file
		continue
	if "assume(" in line: 	# assume (var < > <= >= int/var?)
		sym_section = True
		if not afterILP:
			line = line.split("(")
			l = line[1].split(")")
			assume.append(l[0])
		p4all[i] = ""	# remove assume stmt from file
		continue
	if "=[" in line.replace(' ',''):	# we have an array
		ar_name = line.replace(' ','').split("=")[0].strip()
                ar_vals = line.replace(' ','').split("=")[1].split('[')[1].split(']')[0].split(',') 
		if len(ar_vals) < upper:
			temp = [ar_vals[-1]]*(upper-len(ar_vals))
			ar_vals = ar_vals+temp
                arrays[ar_name] = ar_vals
                p4all[i] = ""   # remove array def from file	
	if sym_section:	# line isn't blank, and doesn't have assume or symbolic - we've reached the end of the symoblic section
		break



# this next section goes until we hit the parser
# unroll metadata (anything outside blocks)
# check for structs - assume can't have nested structs
# save off structs in dict so when/if we have to unroll, we know what fields we need
# this ignores headers - assume we can't make changes to regular ipv4, ethernet, etc. headers - metadata always in struct
# should we also skip the struct headers def?? - leaving it in now, but not sure if symb var would ever actually show up here
structs = {}
c_i = current_index
for i in range(c_i,len(p4all)):
	current_index = i
	line = p4all[i]
	if "struct" in line:
		l = line.split()
		name = l[1]
		fields = {}
		# keep iterating until end of struct
		o = 1
		nex = p4all[i+o]
		while "}" not in nex:
			fields[nex] = i+o
			o +=1
			nex = p4all[i+o]
		fields[nex] = i+o
		structs[name] = [i,fields]

	if "parser" in line:
		break

# check for symbolic var in struct fields
# find struct it refers to
# replicate those struct fields in orig structs with new names - need to know what line num to put them
# remove replicated struct
meta_to_unroll = {}
for var in symbolics:
	val = concrete[var]
	for s in structs:
		for f in structs[s][1]:
			if "["+var+"]" in f:
				temp = f.split("[")
				meta_to_unroll[temp[1].split()[1].replace(';','')] = s
				str_unroll_f = structs[temp[0].strip()][1]
				p4all[structs[temp[0].strip()][0]] = ""		# remove struct declaration
				unrolled_fields = []
				for field in str_unroll_f:
					p4all[str_unroll_f[field]] = ""
					if "}" in field:
						continue
					for i in range(val):
						fi = field.split(';')
						fi[0] = fi[0]+"_%s"%i
						unrolled_fields.append(fi[0]+';')
				# need to replace line f with unrolled_fields
				# line f is p4all[structs[s][1][f]]
				# join unrolled_fields together w/ newline
				p4all[structs[s][1][f]] = "\n".join(unrolled_fields)
				
# parsers
# MUST REPLACE METADATA AND WHEREVER USED! --> PARSER
c_i = current_index
for i in range(c_i,len(p4all)):
	current_index = i
	if "control MyVerifyChecksum" in p4all[i]:
		break

# checksum
c_i = current_index
for i in range(c_i,len(p4all)):
	current_index = i
	if "control MyIngress" in p4all[i]:
		break

# SEPARATE INGRESS/EGRESS UNROLLING

# this happens to everything w/ in control block (metadata processed separately above)
# replace wherever symbolic vars are used with ilp vals

control_start = current_index
c = 0
in_act = False
unroll_act = False
acts_to_unroll = {}	# (name,start index): [body strings] - including }!
current_name = ""
curr_name_index = control_start
reg_to_unroll = {}	# (array name, original reg decl name): concrete val of symb
reg_index = {}	# name: index
memory_symbolics = []
for i in range(control_start,len(p4all)):
	current_index = i
	if "apply {" in p4all[i]:	# we got to the end of action/reg declarations
		break
	if p4all[i] == "\n":
		continue

	# REGISTERS
	# we can only have registers defined OUTSIDE of action defs	
	if "register<" in p4all[i] and not in_act:
		# first check to see if it uses a sym var (will only be for size), then replace with concrete
			# this reg array def will only have 1 symbolic var at most - bit size should't be symbolic
		size = p4all[i].split('(')[1].split(')')[0]
		if size in concrete.keys():
			p4all[i] = p4all[i].replace(size,str(concrete[size]))
		# let's store reg arr declaration indexes so we can easily go back and unroll them without looping through file
		regname = p4all[i].strip().split(')')[1].split(';')[0].strip()
		reg_index[regname] = i
	# check if we have a declaration of array of reg arrays - we have to unroll those regs
	# this declaration should ALWAYS have symbolic var - they can use assume stmts to set sym var to specific value if needed
	# check for '[' and ']' - if there's an equal sign, this is a regular array
	if '[' in p4all[i] and ']' in p4all[i] and '=' not in p4all[i] and "action" not in p4all[i] and not in_act:
		size = p4all[i].split('[')[1].split(']')[0]
		if size in concrete.keys():
			arrname = p4all[i].strip().split(']')[1].strip().split(';')[0]
			regname = p4all[i].strip().split('[')[0]
			reg_to_unroll[(arrname,regname)] = concrete[size]
			memory_symbolics.append(size)
		else:
			print "Array size must be symbolic var"
			exit()
		p4all[i] = ""	# get rid of this array of regs declaration

	'''
	# ARRAYS
	# we can save off explicitly defined arrays (i.e., hashes, salts, whatever) as actual arrays to use when unrolling
	# we can only have arrays defined OUTSIDE of action defs
	# there should NOT by symbolic vars here
	line = p4all[i]
	if "=[" in line.replace(" ","") and not in_act:	# we have an array - let's assume only one line	
		ar_name = line.replace(' ','').split("=")[0].strip()
		ar_vals = line.replace(' ','').split("=")[1].split('[')[1].split(']')[0].split(',') 
		arrays[ar_name] = ar_vals
		p4all[i] = ""	# remove array def from file
	'''

	# ACTIONS
	# we need to save off actions that have [int i] param - these will have to be unrolled
	# we should also check here if action uses a register - this will tell us which actions use same regs
	if "{\n" in p4all[i]:
		c += 1
	elif "}\n" in p4all[i]:
		c -= 1
		if c==0 and in_act:	# we got to the end of an action, set flags to False
			if unroll_act:
				 acts_to_unroll[(current_name,curr_name_index)].append(line)
			in_act = False
			unroll_act = False
			continue
	if "action " in p4all[i]:
		in_act = True
		if "[int i]" in p4all[i]:
			unroll_act = True
			current_name = p4all[i].split("action")[1].strip().split("(")[0]
			curr_name_index = i
			acts_to_unroll[(current_name,curr_name_index)] = [p4all[i]]
			continue
		else:	# this action doesn't have to be unrolled, but we should check reg used
			continue
	if in_act and unroll_act:
		line = p4all[i]
		acts_to_unroll[(current_name,curr_name_index)].append(line)


# array of registers unrolling
for r in reg_to_unroll:
	arr = r[0]
	reg = r[1]
	val = reg_to_unroll[r]
	to_dup = p4all[reg_index[reg]]
	s = ""
	for v in range(val):
		# add _v to line, then add it to the string
		x = to_dup.split(';')
		x[0] = x[0]+"_"+str(v)
		s = s+';'.join(x)

	p4all[reg_index[reg]] = s


# apply block inside ingress control

# unroll for loops
#	replace metadata/reg arrays that use for loop index
#	replace action calls with unrolled name
# number each action and save off in a file? - we need this for ILP conversion

# we assume the apply block is last thing in ingress
# stop once we hit egress block
apply_start = current_index+1   # we add one because we can skip the first "apply {" line
in_loop = False
curr_symb = ""	# this won't work for nested loops, we'd have more than one
c = 0
loop_body = []
loop_index = 0
acts_iters = {}
for_sym = ""
act_numbers = {} # act_name: number
curr_act_num = 0
for i in range(apply_start,len(p4all)):
	current_index = i
	if "control MyEgress" in p4all[i]:
		break	
	if p4all[i]=='\n':
		continue
	if p4all[i].strip()=='{' or p4all[i].strip()=='}' and not in_loop:	# ignoring lines that aren't loop or action/table call
		continue
	if "for(" in p4all[i].replace(' ',''):
		in_loop = True
		# for now, we can assume '{' will always be in the same line as for declaration
		if '{' in p4all[i]:	# keeping track of when we get to end of loop body
			c += 1
		# parse out symbolic var and save off concrete val - so we know how much to unroll
		iterations = concrete[p4all[i].strip().split('<')[1].split(')')[0].strip()]
		for_sym = p4all[i].strip().split('<')[1].split(')')[0].strip()
		p4all[i] = ""
		loop_index = i
		continue
	if '{' in p4all[i] and in_loop:
		c += 1
	if '}\n' in p4all[i] and in_loop:
		c -= 1
		if c==0:
			in_loop=False
			p4all[i] = ""
			# duplicate loop_body
			for val in range(iterations):
				for a in loop_body:
					# check for if stmt with meta [i] - don't care about else stmts, just ifs (or else ifs)
					if ");" in a.strip() and "[i]" not in a.replace(' ',''):
						act_numbers[a.strip().split("(")[0]] = curr_act_num
						curr_act_num += 1
					if "if(" in a.replace(' ','') and "[i]" in a.replace(' ',''):
						# replace meta[i]
						old_name = a.strip().split("[i]")[0].split("meta.")[1]
						old_val = a.strip().split("[i]")[1].split('.')[1].split("==")[0].split("<")[0].split(">")[0].strip()
						a = a.replace(old_val,old_val+"_"+str(val))
						a = a.replace(old_name+"[i].","")
						p4all[loop_index] = p4all[loop_index]+a
						continue
					# check for action with [i]
					if "[i]" in a.replace(' ',''):
						a = a.replace("[i]",'')
						old_act = a.strip().split('(')[0]
						acts_iters[old_act] = (iterations,for_sym)
						a = a.replace(old_act,old_act+"_"+str(val))
						act_numbers[old_act+"_"+str(val)] = curr_act_num
						curr_act_num += 1
						p4all[loop_index] = p4all[loop_index]+a
						continue

					p4all[loop_index] = p4all[loop_index]+a		# if it doesn't match above cases, it's a regular line we can add

			loop_body = []

	if in_loop:	# we'll have to unroll whatever is in the loop
		loop_body.append(p4all[i])
		p4all[i] = ""	# just remove this, we'll add the actions to the line of the loop decl

	# if we're outside of loop, we probably won't have any calls to meta[i] with some concrete val for i, skip this check for now

	else:
		# this is an action (unless it's a "{"/"}") and we should count it
		if ");" in p4all[i].strip():
			# this won't work if we have a table call!!!! ONLY for action calls (?)
			act_numbers[p4all[i].strip().split("(")[0]] = curr_act_num
			curr_act_num += 1


# action def duplication
# acts_to_unroll -> (name,start index): [body strings] - including }!
# acts_iters -> name: iteration nums
arr_constraints = {}	# array name: symbolic variable
reg_acts = {}	# reg name: [actions using reg]
for k in acts_to_unroll:
	a_name = k[0]
	a_start = k[1]
	iterations = acts_iters[a_name][0]
	sym = acts_iters[a_name][1]
	p4all[a_start] = ""
	decl = acts_to_unroll[k][0].replace("[int i]","")
	for val in range(iterations):
		d = decl.split("(")
		d[0] = d[0]+"_"+str(val)
		curr_act_iter = d[0].strip().split("action")[1]
		d = "(".join(d)
		p4all[a_start] = p4all[a_start] + d
		for l in range(len(acts_to_unroll[k])):
			if l==0:	# we've already dealt with action decl above
				continue
			p4all[a_start+l] = ""
			line = acts_to_unroll[k][l]
			if "[i]" in line:	# we have register, meta, and/or array we have to replace
				if "meta." in line:	# we have metadata, but check to see if we have to unroll it
					line = line.split("meta.")
					for m in range(len(line)):
						if line[m].split("[i]")[0].strip() in meta_to_unroll:
							# we have to replace this metadata
							line[m] = line[m].replace(line[m].split("[i]")[0].strip(),"")
							line[m] = line[m].replace(line[m].split("[i]")[1].strip().split(" ")[0].split(",")[0].split(")")[0].split("(")[0].split("{")[0].split("}")[0].split(";")[0], line[m].split("[i]")[1].strip().split(" ")[0].split(",")[0].split(")")[0].split("(")[0].split("{")[0].split("}")[0].split(";")[0]+"_"+str(val))
							line[m] = line[m].replace("[i].","")

					line = "meta.".join(line)
			if "[i]" in line:	# we have registers and/or arrays left to replace
				# let's just do basic search to find what we have
				for a in arrays:
					if a+"[i]" in line:
						line = line.replace(a+"[i]",arrays[a][val])
						if a not in arr_constraints:
							arr_constraints[a] = sym
				for r in reg_to_unroll:
					arr = r[0]
					reg = r[1]
					if arr+"[i]" in line:
						line = line.replace(arr+"[i]",reg+"_"+str(val))

			p4all[a_start] = p4all[a_start] + line
			if ".read(" in line:   # stateful action that uses register
				r_name = line.split(".read")[0].strip()
				if r_name not in reg_acts:
					reg_acts[r_name] = []
                                if curr_act_iter not in reg_acts[r_name]:
					reg_acts[r_name].append(curr_act_iter)
			if ".write(" in line:   # stateful action that uses register
				r_name = line.split(".write")[0].strip()
                                if r_name not in reg_acts:
                                        reg_acts[r_name] = []
				if curr_act_iter not in reg_acts[r_name]:
                                	reg_acts[r_name].append(curr_act_iter)
				
'''
# FIX SO SYMBOLIC VAR NAME COMMENTED OUT DOESN'T GET REPLACED
# INCORPORATE TABLES INTO P4ALL


# REMOVE EXTRA TAB IN FRONT OF LINES IN FOR LOOP BODY????
# WHAT ABOUT MULITPLE FOR LOOPS INDEXED ON DIFFERENT VARIABLES?
# NESTED FOR LOOPS?

# how to handle standalone action calls? like write()[0]? do we allow this in p4all? --> have to find all instances of action call, then check if [] is i or num
# 	restrict language so those aren't allowed - to make standalone call, requires separate action that DOES NOT USE SYMBOLICS???
#	that would require allowing if i == _ stmts in for loop so different iterations are treated differently --> HOW TO UNROLL THIS?
# if num, then replace with that num
# if i, then replace with iteration value
# need to check for metadata uses - check if in if statement
#	given above restriction, unrolled metadata is ONLY in for loop
# for loop actions: create separate action function for each iteration
	# find action _____ in p4all file and copy body for each iteration


# write to p4 file / stdout
with open("output.p4","w") as p4:
	for line in p4all:
		p4.write(line)
'''
'''
for line in p4all:
	print(line)
'''

'''
# write symbolic var names to file if before ILP
# memory sybmolics treated differently - mem_symbolics
if not afterILP:
	with open("symb.txt","w") as symb:
		for k in concrete:
			symb.write(k+"\n")
# write assume constraints to file if before ILP
if not afterILP:
	with open("assume.txt","w") as assu:
		for l in assume:
			assu.write(l+"\n")

# write loop groupings to file
with open("loops.txt","w") as loopf:
	loopf.write(json.dumps(loop_acts))
# write reg_acts to file - to know which acts use same register

# write arr_constraints to file - to know which actions use fixed-length array (ILP const)

'''

print("--- %s seconds ---" % (time.time() - start_time))
