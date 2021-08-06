from lark import Lark, Visitor, Token, Tree, Transformer, v_args
from lark.visitors import Visitor_Recursive

from visit import *



#TODO: make this work if for loop w/in conditional
#TODO: make this work for expressions directly in control? not in actions?
def merge_dicts(x,y):
        #if "ipv4_lpm" in x:
        #       print "X"
        #       print x["ipv4_lpm"]
        #if "ipv4_lpm" in y:
        #       print "Y"
        #       print y["ipv4_lpm"]
        #z = x.copy()
        #z.update(y)
        #return z

        z = {}
        for xk in x:
                if xk in y.keys():
                        if x[xk]==y[xk]:
                                z[xk] = x[xk]
                        else:
                                z[xk] = x[xk]+y[xk]
                else:
                        z[xk] = x[xk]
        for yk in y:
                if yk not in z.keys():
                        z[yk] = y[yk]

        return z

# TODO: GET ACTS THAT ARE IN THE SAME IF/ELSE BLOCKS
# IF THEY'RE IN THE SAME BLOCK, THEN WE DON'T ERROR OUT IF THEY USE THE SAME REG
# ONLY COUNT REG ONCE FOR THOSE ACTIONS (CHECK IF THEY'RE IN THE SAME IF/ELSE BLOCK)

def get_expr_acts(ct,if_expr,expr_acts,ch,counter):
        counter += 1
        #if ch:
        #       print "START"
        #       print counter
        #       print expr_acts
        #if ch and "ipv4_lpm" in expr_acts:
        #       print expr_acts["ipv4_lpm"]
        if_expr+=[ct.children[2]]
        #print if_expr
        for ct_c in ct.children:
                if isinstance(ct_c,Token):
                        continue
                #if ch:
                #       print "FOR_LOOP"
                #       print expr_acts
                if ct_c.data=="block_stmt":
                        if ct_c.children[0].data=="conditional":
                                #print ct_c
                                #if ch and "ipv4_lpm" in expr_acts:
                                #       print "BEFORE"
                                #       print expr_acts["ipv4_lpm"]
                                n_expr_acts=merge_dicts(copy.deepcopy(expr_acts),get_expr_acts(ct_c.children[0],if_expr,copy.deepcopy(expr_acts),ch,counter))
                                expr_acts = n_expr_acts
                                #if ch and "ipv4_lpm" in expr_acts:
                                #       print "AFTER"
                                #       print expr_acts["ipv4_lpm"]
                        elif ct_c.children[0].data=="table_apply":
                                #if ch:
                                #       print "IN"                              
                                #       print if_expr
                                if ct_c.children[0].children[0].value not in expr_acts:
                                        expr_acts[ct_c.children[0].children[0].value] = [if_expr]
                                else:
                                        #if ch:
                                        #       print "here"
                                        expr_acts[ct_c.children[0].children[0].value].append(if_expr)
                        elif isinstance(ct_c.children[0].children[0],Tree) and ct_c.children[0].children[0].data=="lvalue":
                                #print "lv"
                                #print if_expr
                                #print expr_acts
                                #if ch:
                                #       print expr_acts["ipv4_lpm"]
                                if ct_c.children[0].children[0].children[0].value not in expr_acts:
                                        expr_acts[ct_c.children[0].children[0].children[0].value]=[if_expr]
                                else:
                                        expr_acts[ct_c.children[0].children[0].children[0].value].append(if_expr)
        #if ch:
        #       print expr_acts["ipv4_lpm"]

        #if ch:
        #       print "RETURN"
        #       print counter
        #       print expr_acts

        return expr_acts

def get_conds(v2):
	conditionals = {}
	conditional_act_groups = []
	for ct in v2.t: # each of these is a conditional block
		ch = 0
		x=get_expr_acts(ct,[],conditionals,ch,0)
		if x.keys() not in conditional_act_groups:
			conditional_act_groups.append(x.keys())
		conditionals = x

	# THIS ONLY WORKS IF ACTS ARE CALLED ONCE IN CONTROL!!!!!
	for x in conditionals:
		keep = []
		for v in conditionals[x]:
			if len(v) > len(keep):
				keep = v
		conditionals[x] = keep
	return conditionals, conditional_act_groups

def clean_tables(v1):
	# clean up table dicts
	for t in v1.tables_acts:
		a_names = []
		for a in v1.tables_acts[t].children:
			if a.type=="NAME" and a.value != "NoAction":
				a_names.append(a.value)
		v1.tables_acts[t] = a_names
	# assuming for now that all matches are header fields
	for t in v1.tables_match:
		mat = []
		for m in v1.tables_match[t].children:
			if isinstance(m,Tree) and m.data=="lvalue":
				if m.children[0].type=="HDR":
					mat.append(m.children[2].value+"."+m.children[4].value)
				else:
					mat.append(m.children[2].value)
		v1.tables_match[t]=mat

def get_meta_sizes(v1):
	# get sizes for each meta declaration
	meta_sizes = {}
	sym_meta_sizes = {}
	total_req_meta=0
	for m in v1.metas:
		for f in m:
			if f.data=="sym_structfield":   # we can also pull the symbolic value here, but we don't need it for now
				sym_meta_sizes[f.children[2].value]=int(f.children[0].value.replace('bit<','').replace('>',''))
				continue
			if f.children[0].type=="TYPENAME":
				meta_sizes[f.children[1].value]=int(v1.typenames[f.children[0].value].replace('bit<','').replace('>',''))
				total_req_meta+=meta_sizes[f.children[1].value]
				continue
			meta_sizes[f.children[1].value]=int(f.children[0].value.replace('bit<','').replace('>',''))
			total_req_meta+=meta_sizes[f.children[1].value]
	return meta_sizes, sym_meta_sizes, total_req_meta


def get_reads_writes(v1,v2,conditionals):
	# dep analysis
	# first we call read and write on each action from V_r2 - they should be in the same order as they're called in control loop
	# then we have a list of the reads and writes for each action, so we can construct dep graph
	# instead of doing graph, gonna do same dep as p4all uses (1-ordered,2-unordered,3-same stg)
	# if no deps, just ignore (no edges/no entry)
	# raw, war, waw - for now, everything is ordered
	# NOTE: python's set() method removes duplicates
	# NOTE: the ONLY time we would ever get a dep between the same actions is when a symbolic action accesses the same NON SYMBOLIC field
	reads = []
	writes = []
	sym_reads = []
	sym_writes = []
	regs = []
	sym_regs = []
	stateful = []
	hashes = []
	meta_used_acts = {}
	regs_used_acts = {}
	sym_meta_used_acts = {}
	sym_regs_used_acts = {}
	acts_writes = {}
	tables_acts_cond = {}
	for a in v2.stmts:
        	#print a
        	if "table_" in a:
                	t_r = []
               		t_w = []
                	t_re = []
                	t_s_r = []
                	t_s_w = []
                	t_s_re = []
                	# for each action in the table, we read from the conditional - add this value to table match?
                	if a.replace("table_","") in conditionals:
                        	for c in conditionals[a.replace("table_","")]:
                                	vc = Cond_reads()
                                	vc.visit(c)
                                	#print vc.table_checks
                                	#if len(vc.table_checks):
                                	v1.tables_match[a.replace("table_","")]+=vc.reads
                	# go through each action in table --> read includes match field
               		# for now, assume don't have symbolic num of tables --> TODO: symbolic array of tables?
                	for k in v1.tables_match[a.replace("table_","")]:
                        	t_r.append(k)
                	for ta in v1.tables_acts[a.replace("table_","")]:
                        	for ta_e in v1.action_defs[ta]:
                                	v = Act_reads_writes(hashes,ta)
                                	v.visit(ta_e)
                                	hashes = v.hashes
                                	t_r += v.reads
                                	t_w += v.writes
                                	if v.regs not in t_re:
                                        	t_re += v.regs
                                        	if ta not in stateful and len(v.regs) > 0:
                                                	stateful.append(ta)
                        	acts_writes[ta] = list(set(t_w))
                	writes.append(set(t_w))
                	reads.append(set(t_r))
                	regs.append(set(t_re))
                	continue
        	a_r = []
        	a_w = []
        	s_r = []
        	s_w = []
        	re = []
        	s_re = []
        	for e in v1.action_defs[a]:
                	v = Act_reads_writes(hashes,a)
                	v.visit(e)
                	hashes = v.hashes
                	a_r+=v.reads
                	a_w+=v.writes
                	re+=v.regs
                	if a in v2.sym_stmts:
                        	s_r+=v.sym_reads
                        	s_w+=v.sym_writes
                        	s_re+=v.sym_regs
        	if a in conditionals:
                	for c in conditionals[a]:
                        	vc = Cond_reads()
                        	vc.visit(c)
                        	#for tc in vc.table_checks:
                        	#       a_r+=v1.tables_match[tc]
                        	#       print reads[v2.stmts.index("table_"+tc)]
                        	#       print writes[
                        	#       print v1.tables_match[tc]
                        	a_r+=vc.reads
                        	s_r+=vc.sym_reads
        	if len(re)>0 and set(re) not in regs:
                	stateful.append(a)
        	reads.append(set(a_r))
        	writes.append(set(a_w))
        	acts_writes[a] = list(set(a_w))
        	if len(a_r) > 0 or len(a_w) > 0:
                	meta_used_acts[a] = a_r+a_w
        	if set(re) not in regs:
                	regs.append(set(re))
        	else:
                	regs.append(set([]))
        	if len(re)>0:
                	regs_used_acts[a]=re
        	if a in v2.sym_stmts:
                	sym_reads.append(set(s_r))
                	sym_writes.append(set(s_w))
                	sym_regs.append(set(s_re))
                	if len(s_r) > 0 or len(s_w) > 0:
                        	sym_meta_used_acts[a] = list(set(s_r+s_w))      # convert to set then list just to remove dups
                	if len(s_re)>0 and a not in stateful:
                        	stateful.append(a)
                	if len(s_re) > 0:
                        	sym_regs_used_acts[a]=s_re

	return reads, writes, sym_reads, sym_writes, regs, sym_regs, stateful, hashes, meta_used_acts, regs_used_acts, sym_meta_used_acts, sym_regs_used_acts, acts_writes, tables_acts_cond



def non_sym_dep(v1,v2,conditional_act_groups,writes,reads,regs,regs_used_acts):
	# for now, we're not recording what fields are causing the dependency, but we can easily add this later
	deps = {}
	# this is deps for NON SYMBOLIC fields
	# if a symbolic action (aka in a loop) uses a NON symbolic meta field, we record the dep (bc we have to unroll the loop)
	for a1 in v2.stmts:
        	a1_t = False
        	if "table_" in a1:
                	a1_t = True
        	a1_i = v2.stmts.index(a1)
        	for a2 in v2.stmts:
                	a2_t = False
                	if "table_" in a2:
                        	a2_t = True
                	a2_i = v2.stmts.index(a2)
                	if a1 not in v2.sym_stmts and a2 not in v2.sym_stmts:
                        	if a1_i >= a2_i:
                                	continue
                	elif a1_i > a2_i:
                        	continue
                	# check if acts are in if/else block
                	ie = False
                	for cg in conditional_act_groups:
                        	if (set([a1,a2]).issubset(set(cg))):
                                	ie = True
                                	break
                	if a1==a2 and a1 in v2.sym_stmts:       # we have an action in a symbolic loop, check to see what non-symbolics it uses
                        	if len(writes[a1_i]) > 0:       # symbolic actions write to same non-symbolic field
                                	deps[(a1,a2)] = 1
                        	continue                        # don't care if they read from same fields bc can have concurrent reads
                	# read after write
                	if len(writes[a1_i].intersection(reads[a2_i])) > 0 and not ie:
                        	if "table_" in a1 and "table_" in a2:
                                	deps[(v1.tables_acts[a1.replace("table_","")][0],v1.tables_acts[a2.replace("table_","")][0])] = 1
                        	elif "table_" in a1:
                                	deps[(v1.tables_acts[a1.replace("table_","")][0],a2)] = 1
                        	elif "table_" in a2:
                                	deps[(a1,v1.tables_acts[a2.replace("table_","")][0])] = 1
                        	else:
                                	deps[(a1,a2)]=1
                        	#continue
                	# write after read
                	if len(reads[a1_i].intersection(writes[a2_i])) > 0 and not ie:
                        	if "table_" in a1 and "table_" in a2:
                                	deps[(v1.tables_acts[a1.replace("table_","")][0],v1.tables_acts[a2.replace("table_","")][0])] = 1
                        	elif "table_" in a1:
                                	deps[(v1.tables_acts[a1.replace("table_","")][0],a2)] = 1
                        	elif "table_" in a2:
                                	deps[(a1,v1.tables_acts[a2.replace("table_","")][0])] = 1
                        	else:
                                	deps[(a1,a2)]=1
                        	#continue
                	# write after write
                	if len(writes[a1_i].intersection(writes[a2_i])) > 0 and not ie:
                        	if "table_" in a1 and "table_" in a2:
                                	deps[(v1.tables_acts[a1.replace("table_","")][0],v1.tables_acts[a2.replace("table_","")][0])] = 1
                        	elif "table_" in a1:
                                	deps[(v1.tables_acts[a1.replace("table_","")][0],a2)] = 1
                        	elif "table_" in a2:
                                	deps[(a1,v1.tables_acts[a2.replace("table_","")][0])] = 1
                        	else:
                                	deps[(a1,a2)]=1
                        	#continue
                	# access same reg
                	if len(regs[a1_i].intersection(regs[a2_i])) > 0 or (a1.replace("table_","") in regs_used_acts and a2.replace("table_","") in regs_used_acts and regs_used_acts[a1.replace("table_","")][0] in regs_used_acts[a2.replace("table_","")]):
                        	if (a1,a2) in deps or (a1_t and (v1.tables_acts[a1.replace("table_","")][0],a2) in deps) or (a2_t and (a1,v1.tables_acts[a2.replace("table_","")][0]) in deps):
                                	if a1==a2:
                                        	print "ERROR: symbolic action %s accesses the same non-symbolic register in different iterations"%(a1)
                                        	exit()

                                	if ie:
                                        	deps.pop((a1,a2),None)
                                	else:
                                        	print "ERROR: actions %s and %s access the same register but have a dependency"%(a1,a2)
                                        	exit()
                        	deps[(a1,a2)]=3

	return deps

def sym_dep(v2, sym_writes, sym_reads, sym_regs, deps):
	# SYMBOLIC DEPS
	# if two actions in the SAME iteration of a loop use same meta or reg (different iterations mean different vals in unrolled prog) 
	for a1 in v2.sym_stmts:
        	a1_i = v2.sym_stmts.index(a1)
        	for a2 in v2.sym_stmts:
                	a2_i = v2.sym_stmts.index(a2)
                	if a1_i >= a2_i:
                        	continue
                	if len(sym_writes[a1_i].intersection(sym_reads[a2_i])) > 0 and (a1,a2) not in deps:
                        	deps[(a1,a2)]=1
                        	#continue
                	if len(sym_reads[a1_i].intersection(sym_writes[a2_i])) > 0 and (a1,a2) not in deps:
                        	deps[(a1,a2)]=1
                        	#continue
                	if len(sym_writes[a1_i].intersection(sym_writes[a2_i])) > 0 and (a1,a2) not in deps:
                        	deps[(a1,a2)]=1
                        	#continue
                	if len(sym_regs[a1_i].intersection(sym_regs[a2_i])) > 0:
                        	if (a1,a2) in deps and deps[(a1,a2)]==1:
                                	print "ERROR: actions %s and %s access the same register but have a dependency"%(a1,a2)

                        	deps[(a1,a2)]=3

def tcam_dep(v1, v2, deps, acts_writes):
	# TCAM DEPS
	# actions in same table must be in same stg
	tcam_acts = []
	ilp_tcam_size = []
	for t in v1.tables_acts:
        	if v1.tables_size[t] in v1.symbolics:
                	ilp_tcam_size.append(-1)
        	else:
                	ilp_tcam_size.append(v1.tables_size[t])
        	tcam_acts.append(v1.tables_acts[t][0])
        	for a_i in range(len(v1.tables_acts[t])):
                	if a_i==0:
                        	continue
                	deps[(v1.tables_acts[t][a_i-1],v1.tables_acts[t][a_i])]=3

        	# If table matches to field that is modified before table, CANNOT be in same stage (raw)
        	t_i = v2.stmts.index("table_"+t)
        	if t_i==0:      # table is first thing in apply block, nothing modified before
                	continue
        	for a in v2.stmts[:t_i]:
                	if "table_" not in a:
                        	for aw in acts_writes[a]:
                                	if aw in v1.tables_match[t]:
                                        	for at in v1.tables_acts[t]:
                                                	deps[(a,at)]=1

                	else:
                        	for at in v1.tables_acts[a.replace("table_","")]:
                                	for aw in acts_writes[at]:
                                        	if aw in v1.tables_match[t]:
                                                	for at2 in v1.tables_acts[t]:
                                                        	deps[(at,at2)]=1

	return tcam_acts, ilp_tcam_size


def set_nums_upper_bounds(v1, v2, stateful):
	# maybe we do this in ILP? so we don't have to read from resource file multiple times?
	# we need to create mapping from action name to number (numbers used in ILP)
	# number corresponds to order they appear in control
	# we also need to expand for loop actions here (num stateless * num stgs)
	# if action in both stmts and sym_stmts, we know it's in a loop
	#we also add non-symbolic actions to the loop list here
	act_num = 0
	name_to_num = {}
	num_to_name = {}
	stateless_upper_bound = 14 # this is stateless ALUs * num stgs
	stateful_upper_bound = 14       # this is stateful ALUs * num stgs
	ilp_loops = []
	# give SYMBOLIC VAL an upper bound, not an action
	for a in v2.stmts:
        	if "table_" in a:
                	for at in v1.tables_acts[a.replace("table_","")]:
                        	name_to_num[at]=[act_num]
                       		act_num += 1
                	continue
        	# we have a symolic in a loop
        	if a in v2.sym_stmts:
                	if "table_" in a:
                        	continue
                	name_to_num[a]=[]
                	ub = stateless_upper_bound
                	if a in stateful:       # make the upper bound a little smaller if we can
                        	ub = stateful_upper_bound
                	for i in range(ub):
                        	name_to_num[a].append(act_num)
                        	num_to_name[act_num]=a
                        	act_num += 1
                	continue
        	# non-symbolic action
        	else:
                	name_to_num[a]=[act_num]
                	num_to_name[act_num]=a
                	ilp_loops.append([act_num])
                	act_num += 1

	# after we finish the loop, act_num = TOTAL NUM OF ACTIONS we have in the prog
	# utility function on ilp memory variables, upper bound is max memory in stg
	mem_per_stg = 2097152

	return act_num, name_to_num, num_to_name, stateless_upper_bound, stateful_upper_bound, ilp_loops, mem_per_stg 

def ilp_tcam(tcam_acts, name_to_num):
	# tcam acts - TODO: ALLOW FOR SYMBOLIC NUM OF TABLES?
	ilp_tcam_acts = []
	for at in tcam_acts:
        	ilp_tcam_acts.append(name_to_num[at][0])

	return ilp_tcam_acts

def ilp_state(stateful, name_to_num):
	# get list of stateful actions that use numbers instead of name
	ilp_stateful = []
	for a in stateful:
        	for a_n in name_to_num[a]:
                	ilp_stateful.append(a_n)

	return ilp_stateful

def ilp_hash(hashes, name_to_num):
	# get list of hashes using act numbers
	ilp_hashes = []
	for a in hashes:
        	for a_n in name_to_num[a]:
                	ilp_hashes.append(a_n)

	return ilp_hashes

def ilp_dependency(v2, deps, name_to_num):
	# convert deps to use number instead of action name (will need to duplicate for symbolic acts)
	# how to handle symbolic acts that are dependent on each other in different iterations? - (0,1) (1,2) (2,3) OR (0,1) (0,2) etc.????
	# i think we can do the latter ONLY if all deps are ordered (will have to adjust if include unordered)
	ilp_deps = {}
	for (a1,a2) in deps:
        	# symbolic dep
        	if a1==a2:
                	for a_n in name_to_num[a1][:-1]:
                        	ilp_deps[(a_n,a_n+1)]=deps[(a1,a2)]
                	continue
        	# no symbolics
        	if a1 not in v2.sym_stmts and a2 not in v2.sym_stmts:
                	ilp_deps[(name_to_num[a1][0],name_to_num[a2][0])]=deps[(a1,a2)]
                	continue
        	# both symbolic, but different actions
        	elif a1 in v2.sym_stmts and a2 in v2.sym_stmts:
                	for a_i in range(len(name_to_num[a1])):
                        	ilp_deps[(name_to_num[a1][a_i],name_to_num[a2][a_i])]=deps[(a1,a2)]
        	# one symbolic, one non-symbolic
        	elif a1 in v2.sym_stmts:
                	for a_n in name_to_num[a1]:
                        	ilp_deps[(a_n,name_to_num[a2][0])]=deps[(a1,a2)]
                	continue
        	elif a2 in v2.sym_stmts:
                	for a_n in name_to_num[a2]:
                        	ilp_deps[(name_to_num[a1][0],a_n)]=deps[(a1,a2)]

	return ilp_deps

def ilp_loop_groups(v2, name_to_num, ilp_loops):
	# keep track of actions that are in the same loop
	loop_name = {}
	# mapping symbolic value to action - this allows us to translate utility function that uses symbolic to util that uses ilp act vars
	# we only count the first action in a loop for the utility function
	# this shouldn't matter in the ILP bc we require that all acts in a loop get placed the same number of times
	#'''
	ilp_sym_to_act_num = {}
	for sym_loop in v2.loop_stmts:
        	ilp_sym_to_act_num[sym_loop] = []
        	loop_name[sym_loop] = []
        	for l in v2.loop_stmts[sym_loop]:
                	curr_loop = []
                	for a in l:
                        	if a.children[0].data=="conditional":
                                	for act in a.children[0].children[5:-1]:
                                        	a_name = act.children[0].children[0].children[0].value
                                        	loop_name[sym_loop].append(a_name)
                                        	for n in name_to_num[a_name]:
                                                	curr_loop.append(n)
                                                	#if len(ilp_sym_to_act_num[sym_loop]) <= len(name_to_num[a_name]):
                                                	ilp_sym_to_act_num[sym_loop].append(n)
                                	continue
                        	a_name = a.children[0].children[0].children[0].value
                        	loop_name[sym_loop].append(a_name)
                        	for n in name_to_num[a_name]:
                                	curr_loop.append(n)
                                	#if len(ilp_sym_to_act_num[sym_loop]) <= len(name_to_num[a_name]):
                                	ilp_sym_to_act_num[sym_loop].append(n)
                	ilp_loops.append(curr_loop)
	#'''
	# groups for ILP - actions that must be placed together
	# these are the actions in the same iterations of loops indexed by same symbolic var
	ilp_groups = []
	for sym in loop_name:
	        for a_i in range(len(name_to_num[loop_name[sym][0]])):  # this assumes ALL ACTS IN LOOP HAVE SAME UPPER BOUND! (not enforced yet!)
                	curr_it = []
                	for a in loop_name[sym]:
                        	curr_it.append(name_to_num[a][a_i])
                	ilp_groups.append(curr_it)


	return ilp_sym_to_act_num, ilp_groups

def ilp_metas(sym_meta_used_acts, name_to_num):
	# any meta that isn't symbolic is automatically placed - if we can't place that, then we automatically fail (don't even go to ILP)
	# we need to give ILP the amount of metadata AFTER we subtract the required meta (and headers)
	# ^ this is total_req_meta
	# the section below ONLY associates symbolic meta to actions (we're ignoring non-symbolic meta)

	# list of acts that use metadata
	# these have to be in order - meta_per relies on this
	# we're ignoring header fields for now - SHOULD WE DO THIS?
	# TODO: test this - we're only counting each meta field ONCE
	# ^ so for CMS, we count "count" for ONLY index or count action - so we might get index associated with 32 bits for each instance
	# and count associated with 32 bits for each instance (even though count really requires 64 bits of meta, but we already counted 32 with index)
	ilp_meta = []
	ilp_meta_sizes = []
	meta_num = {}
	for a in sym_meta_used_acts:
        	for a_n in name_to_num[a]:
                	curr_meta = []
                	curr_meta_sizes = []
                	for m in sym_meta_used_acts[a]:
                        	if "." in m:    # this is a header field, we're only looking at metadata
                                	continue
                        	curr_meta.append(m.replace('[i]',''))
                        	curr_meta_sizes.append(sym_meta_sizes[m.replace('[i]','')])
                        	break
                	meta_num[a_n]=curr_meta
                	if len(curr_meta)>0:
                        	ilp_meta.append(a_n)
                        	ilp_meta_sizes.append(sum(curr_meta_sizes))

	return ilp_meta, ilp_meta_sizes, meta_num

def ilp_regs(v1, ilp_stateful, num_to_name, sym_regs_used_acts, regs_used_acts):
	# need reg width for each stateful symbolic action
	# assume each stateful action uses at most one reg
	# we save sym reg sizes as a tuple (width, instances)
	# ILP just takes width for now, assumes instances is also symbolic (TODO: update this)
	# ILP relies on this being ordered (same order as stateful actions, numerically increasing) - which is why we sort ilp_stateful
	ilp_reg_inst = []
	ilp_reg_width = []
	# mapping symbolic value to reg size (by using the act num associated with each reg)
	ilp_sym_to_reg_act_num = {}
	sym_to_reg_width = {}
	for a_n in ilp_stateful:
        	a = num_to_name[a_n]
        	# would do a loop here if more than one reg in action, but for now we allow only 1
        	# sym_regs_used_acts is ONLY stateful actions w/in for loop (symbolic array of regs)
        	if a in sym_regs_used_acts:
                	ilp_reg_width.append(int(v1.sym_reg_array_widths[sym_regs_used_acts[a][0]].replace('bit<','').replace('>','')))
                	ilp_reg_inst.append(-1)
                	if v1.sym_reg_array_inst[sym_regs_used_acts[a][0]] not in sym_to_reg_width:
                        	sym_to_reg_width[v1.sym_reg_array_inst[sym_regs_used_acts[a][0]]] = ilp_reg_width[-1]
                	if v1.sym_reg_array_inst[sym_regs_used_acts[a][0]] in ilp_sym_to_reg_act_num:
                        	ilp_sym_to_reg_act_num[v1.sym_reg_array_inst[sym_regs_used_acts[a][0]]].append(a_n)
                	else:
                        	ilp_sym_to_reg_act_num[v1.sym_reg_array_inst[sym_regs_used_acts[a][0]]] = [a_n]
                	#continue
        	if a in regs_used_acts: # this could be non-symbolic regs or regs with symbolic size but NOT symbolic array of regs
                	if regs_used_acts[a][0] in v1.reg_inst:
                        	ilp_reg_width.append(int(v1.reg_widths[regs_used_acts[a][0]].replace('bit<','').replace('>','')))
                        	ilp_reg_inst.append(int(v1.reg_inst[regs_used_acts[a][0]]))
                	elif regs_used_acts[a][0] in v1.sym_reg_inst:
                        	ilp_reg_width.append(int(v1.sym_reg_widths[regs_used_acts[a][0]].replace('bit<','').replace('>','')))
                        	ilp_reg_inst.append(-1)
                        	if v1.sym_reg_inst[regs_used_acts[a][0]] not in sym_to_reg_width:
                                	sym_to_reg_width[v1.sym_reg_inst[regs_used_acts[a][0]]]=ilp_reg_width[-1]
                        	if v1.sym_reg_inst[regs_used_acts[a][0]] in ilp_sym_to_reg_act_num:
                                	ilp_sym_to_reg_act_num[v1.sym_reg_inst[regs_used_acts[a][0]]].append(a_n)
                        	else:
                                	ilp_sym_to_reg_act_num[v1.sym_reg_inst[regs_used_acts[a][0]]]=[a_n]

	return ilp_reg_inst, ilp_reg_width, ilp_sym_to_reg_act_num, sym_to_reg_width


def ilp_same_reg_inst(sym_regs_used_acts):
	# stateful acts that share the same symbolic reg array
	# the size (# instances) of each reg array must be the same (bc indexed on same sym value)
	# assume sym reg arrays ALWAYS have sym instances - THIS IS NOT ALWAYS TRUE!!! (TODO: update this)
	# assume that no two symbolic actions will access the same reg - NOT ALWAYS TRUE!!! (TODO: update this)
	# assume that a sym actions access AT MOST one reg array (TODO: update this)
	ilp_same_size = []
	for a in sym_regs_used_acts:
        	ilp_same_size.append(name_to_num[a])

	return ilp_same_size

def get_assumes(v1):
	astmt = []

	for a in v1.assumes:
        	atran = AssumeTran()
        	astmt.append(atran.transform(v1.assumes[0]))

	return astmt

def pwl_util(v1, ilp_sym_to_reg_act_num, ilp_sym_to_act_num, stateful, sym_to_reg_width, stateful_upper_bound, stateless_upper_bound, mem_per_stg, astmt):
	# parsing util function:
	# minimize or maximize? -> if minimize, we don't need to change anything (gurobi does this by default)
	# if maximize - we negate everything
	#
	# ignore util name for now, we'll only use this if we have a combination of utilities (using optimize keyword)?
	#
	# switch statement with symbolic var -> this will tell us what ILP vars we need to use
	# if symbolic is in ilp_sym_to_reg_act_num, then we know it's mem vars, otherwise it's action
	#
	# we transform case statements into if/elses
	# we do function calculation in here instead of ILP (ilp really just needs list of x and y vals for PWL)
	# we'll need to get upper bound for cols somehow - use resources?
	# if memory variable, we need to use max mem in stg and max alus?
	#
	# step size - use this when creating x val list

	#opt = 'minimize'
	#switch_var = 'cols'
	#cases = {'0':'1', 'default': 'float(3)/float(x)'}
	#step = 2
	mem_var = 0
	act_var = 0
	stateful_v = 0

	#for fx in v1.funcs:
        	#print fx
	# PUT THIS IN LOOP FOR MULT OBJECTIVE FUNCS
	# TODO: HOW TO KNOW WHAT SYMBOLIC IS USED IN FUNCTION (if not switch stmt) (tran.vars)
	tran=UtilFuncTran()
	fu = tran.transform(v1.funcs[0]).replace(tran.vars[0],"symvar")
	fe = lambda symvar: eval(fu)

	# this assumes util functions with single variable
	# TODO: multivariate utils
	uvar = tran.vars[0]
	# this tells is if util applies to mem vars or act vars in ilp
	if uvar in ilp_sym_to_reg_act_num:
        	mem_var=1
	elif uvar in ilp_sym_to_act_num:
        	act_var=1
        	if ilp_sym_to_act_num[0] in stateful:
                	stateful_v=1


	# set lower and upper bounds for PWL functions (based on resources and/or assume stmts)
	# lower bound (lb) is inclusive, upper bound (ub) is exclusive
	ub = 0
	lb = 0
	if mem_var:
        	if uvar in sym_to_reg_width:
                	ub = 1+mem_per_stg/sym_to_reg_width[uvar]
	# utility function on ilp act vars, upper bound is max alus in stg
	elif stateful_v:
        	ub = stateful_upper_bound+1
	else:
        	ub = stateless_upper_bound+1


	# if >= val, then start range from val
	# if <= val, then end range at val+1
	# if ==
	# if val <= <= val, then combo of first 2 cases
	for a in astmt:
        	if "<="+uvar+"<=" in a:
                	s = a.replace("<=","").replace(">=","").split(uvar)
                	# set lb
                	lb = int(s[0])
                	# set ub
                	ub = int(s[1])+1
        	elif uvar+">=" in a or "<="+uvar in a:
                	# set lb
                	lb = int(a.replace(uvar,"").replace("<=","").replace(">=",""))
        	elif uvar+"<=" in a or ">="+uvar in a:
                	# set ub
                	ub = int(a.replace(uvar,"").replace("<=","").replace(">=",""))+1

	x_vals = range(lb,ub,v1.step_size)      # we generate list of x vals from bounds and step size
	y_vals = []

	# evaluate the function for each x val to corresponding y val for PWL function
	for v in x_vals:
        	y_vals.append(fe(v))


	return mem_var, act_var, uvar, x_vals, y_vals

def write_pwl_to_ilp_file(ilp_stateful, ilp_meta, ilp_meta_sizes, ilp_groups, ilp_loops, ilp_deps, ilp_tcam_acts, ilp_tcam_size, ilp_reg_width, ilp_hashes, act_num, ilp_same_size, total_req_meta, ilp_reg_inst, mem_var, ilp_sym_to_reg_act_num,  uvar, act_var, ilp_sym_to_act_num, x_vals, y_vals):
	# write info to a file for ILP to use
	with open("ilp_input.txt", "w") as f:
        	f.writelines("%s " % s for s in ilp_stateful)           # numbers of acts that are stateful
        	f.write("\n")
        	f.writelines("%s " % m for m in ilp_meta)               # numbers of acts that use symbolic meta
        	f.write("\n")
        	f.writelines("%s " % ms for ms in ilp_meta_sizes)       # sizes of each instance of symbolic meta (corresponding to act nums)
        	f.write("\n")  
        	f.writelines("%s " % str(g).replace(" ","")  for g in ilp_groups)               # nums of acts in groups (acts that must ALL be placed - all or nothing)
        	f.write("\n")
        	f.writelines("%s " % str(l).replace(" ","") for l in ilp_loops)         # nums of acts in the same loop (not in loop - in list by itself)
        	f.write("\n")
        	f.write(str(ilp_deps))                                  # list of deps
        	f.write("\n")
        	f.writelines("%s " % ta for ta in ilp_tcam_acts)        # list of acts that use TCAM TODO: make this symbolic?
        	f.write("\n")
        	f.writelines("%s " % ts for ts in ilp_tcam_size)        # size for tcam tables
        	f.write("\n")
        	f.writelines("%s " % rw for rw in ilp_reg_width)        # width of each reg array (corresponding to stateful act nums)
        	f.write("\n")
        	#f.write("1")                                            # utililty provided? TODO: get rid of this
        	#f.write("\n")  
        	f.writelines("%s " % h for h in ilp_hashes)             # nums of acts that hash
        	f.write("\n")
        	f.write(str(act_num))                                   # total number of acts we have
        	f.write("\n")
        	f.writelines("%s " % str(ss).replace(" ","") for ss in ilp_same_size)   # list of reg arrays that must have same num of instances
        	f.write("\n")
        	f.write(str(total_req_meta))                            # the amount of phv that's non-symbolic (required)
        	f.write("\n")
        	f.writelines("%s " % ri for ri in ilp_reg_inst)         # number of instances for each reg array (correspond to stateful act nums)
        	f.write("\n")
        	if mem_var:                                             # our util func applies to memory ILP vars
                	f.write("mem\n")
                	f.writelines("%s " % mv for mv in ilp_sym_to_reg_act_num[uvar]) # numbers that correspond to ILP vars that we use for util
        	elif act_var:                                           # our util func applies to act ILP vars
                	f.write("act\n")
                	f.writelines("%s " % av for av in ilp_sym_to_act_num[uvar])     # numbers that correspond to ILP vars
        	f.write("\n")
        	f.writelines("%s " % xv for xv in x_vals)               # x values for PWL util
        	f.write("\n")
        	f.writelines("%s " % yv for yv in y_vals)               # y values for PWL util (util values)




def ilp_parse(parse_tree):
	v1 = V_r1()
	v1.visit(parse_tree)
	#print v1.apply
	#print v1.action_defs
	#print v1.typenames
	#print v1.metas
	#print v1.hdrs
	#print v1.sym_reg_array_widths
	#print v1.util
	#print v1.sym_reg_array_inst
	#print v1.sym_reg_array_length
	#print v1.reg_widths
	#print v1.reg_inst
	#print v1.sym_reg_widths
	#print v1.sym_reg_inst
	#print v1.opt_keyword
	#print v1.switch_var
	#print v1.step_size
	#print v1.case_stmts
	#print v1.tables_acts
	#print v1.tables_match
	#print v1.tables_size
	#print v1.funcs
	#print v1.assumes

	v2 = V_r2(v1.action_defs)
	v2.visit(v1.apply[0])   # assuming we only have one apply block in the v1.apply list
	#print v2.stmts
	#print v2.conditionals["write_kvs"]
	#print v2.loop_stmts
	#print v2.t
	#print v2.conditional_acts
	#print v2.t

	conditionals, conditional_act_groups = get_conds(v2)

	'''
	v3 = Act_reads_writes()
	v3.visit(v1.action_defs['x'])
	print v3.writes
	print v3.reads
	v4 = Act_reads_writes()
	v4.visit(v1.action_defs['t'])
	'''

	clean_tables(v1)

	meta_sizes, sym_meta_sizes, total_req_meta = get_meta_sizes(v1)

	reads, writes, sym_reads, sym_writes, regs, sym_regs, stateful, hashes, meta_used_acts, regs_use
d_acts, sym_meta_used_acts, sym_regs_used_acts, acts_writes, tables_acts_cond = get_reads_writes(v1,v2,conditionals)

	deps = non_sym_dep(v1,v2,conditional_act_groups,writes,reads,regs,regs_used_acts)

	sym_dep(v2, sym_writes, sym_reads, sym_regs, deps)

	tcam_acts, ilp_tcam_size = tcam_dep(v1, v2, deps, acts_writes)

	# ilp actions get info for ilp, in format readable by ilp
	act_num, name_to_num, num_to_name, stateless_upper_bound, stateful_upper_bound, ilp_loops, mem_per_stg = set_nums_upper_bounds(v1, v2, stateful)

	ilp_tcam_acts = ilp_tcam(tcam_acts, name_to_num)

	ilp_stateful = ilp_state(stateful, name_to_num)
	ilp_stateful.sort()

	ilp_hashes = ilp_hash(hashes, name_to_num)

	ilp_deps = ilp_dependency(v2, deps, name_to_num)

	ilp_sym_to_act_num, ilp_groups = ilp_loop_groups(v2, name_to_num, ilp_loops)

	ilp_meta, ilp_meta_sizes, meta_num = ilp_metas(sym_meta_used_acts, name_to_num)

	ilp_reg_inst, ilp_reg_width, ilp_sym_to_reg_act_num, sym_to_reg_width = ilp_regs(v1, ilp_stateful, num_to_name, sym_regs_used_acts, regs_used_acts)

	ilp_same_size = ilp_same_reg_inst(sym_regs_used_acts)

	# mapping symbolic value to meta
	# DO WE NEED THIS? this should ALWAYS correspond to the symbolic used in a for loop. so we should just be able to use ILP's act vars

	# ilp_sym_to_reg_act_num contains the mapping described below
	# mapping symbolic value to reg size
	# ILP reg var numbers correspond to act vars bc we use regs in acts
	# so we need stateful SYMBOLIC actions (regs that have symbolic size)
	# we associate each symbolic reg array with an action
	# the sizes of each of those symbolic reg arrays is a symbolic val
	# so we can link that val with the act numbers (and hence ILP mem var numbers) --> is this right?
	# when we parse, need to save name of array: symbolic value size
	# we have to do this for EVERY symbolic reg array???? - maybe not, bc ILP makes sure that things that share sym val are same size
	# or is that just for regs in same sym array?
	# for PWL utils, i think we need to know for EVERY reg array BUT only need to do it for one action

	# regs w/ symbolic sizes are those in v1.sym_reg_inst and v1.sym_reg_array_inst
	# will use sym_regs_used_acts and reg_used_acts to connect them to nums?

	astmt = get_assumes(v1)

	mem_var, act_var, uvar, x_vals, y_vals = pwl_util(v1, ilp_sym_to_reg_act_num, ilp_sym_to_act_num, stateful, sym_to_reg_width, stateful_upper_bound, stateless_upper_bound, mem_per_stg, astmt)


	# we need to translate assume statements to ILP constraints
	# m.addConstr(quicksum()>=0)

	# for each stmt:
	# we isolate the symbolic and check if it's in either dict
	# if in reg dict - we make quicksum of mem_vars ---> how to get index of mem_vars? vals in dict are act nums
	# if in act dict - quicksum of act_vars
	#       for a in act dict[sym]:
	#               m.addConstr(quicksum(act_vars[a]) ... )
	#print ilp_sym_to_reg_act_num
	#print ilp_sym_to_act_num
	#exit()

	write_pwl_to_ilp_file(ilp_stateful, ilp_meta, ilp_meta_sizes, ilp_groups, ilp_loops, ilp_deps, ilp_tcam_acts, ilp_tcam_size, ilp_reg_width, ilp_hashes, act_num, ilp_same_size, total_req_meta, ilp_reg_inst, mem_var, ilp_sym_to_reg_act_num,  uvar, act_var, ilp_sym_to_act_num, x_vals, y_vals)




