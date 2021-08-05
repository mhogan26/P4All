from lark import Lark, Visitor, Token, Tree, Transformer, v_args
from lark.visitors import Visitor_Recursive
import random

# walk through tree
# we can save off action definitions, and then reference them when we go through apply block?
# let's just get a list the stmts in the apply block, in the same order we call them (so we can find deps)
# should we use transformer to replace action calls with action definition in apply block??
#       do you replace function calls with their definitions in a parse tree to get control flow graph??
# along with deps, we need to get other info (hashings, stateful, etc.)
# sym_method_calls ONLY happen within a for loop - the dep analysis for these might look different??
class V_r1(Visitor_Recursive):
        def __init__(self):
                self.action_defs={}
                self.sym_action_defs={}
                self.apply = []
                self.metas = []
                self.hdrs = []
                self.typenames = {}
                self.reg_widths = {}    # reg array declarations with NO symbolic elements
                self.sym_reg_widths = {}        # reg array declaration with symbolic num instances
                self.sym_reg_array_widths = {}  # symbolic array of regs decl
                self.util = []
                self.reg_inst = {}
                self.sym_reg_inst = {}
                self.sym_reg_array_inst = {}
                self.sym_reg_array_length = {}  # this is the length of the symbolic array (should be symbolic val)
                self.opt_keyword = ""
                self.switch_var = ""
                self.step_size = 0
                self.case_stmts = {}
                self.tables_acts = {}
                self.tables_match = {}
                self.tables_size = {}
                self.symbolics = []
                self.funcs = []
                self.assumes = []
        def __default__(self,tree):
                if tree.data=="action_decl":
                        if isinstance(tree.children[4],Token):  # we have params in the action
                                self.action_defs[tree.children[1].value]=tree.children[5:]
                        else:
                                self.action_defs[tree.children[1].value]=tree.children[4:]
                elif tree.data=="sym_action_decl":
                        self.action_defs[tree.children[1].value]=tree.children[4:]
                elif tree.data=="apply_block":
                        self.apply.append(tree)
                elif tree.data=="type_def":
                        self.typenames[tree.children[2].value]=tree.children[1].value
                elif tree.data=="struct_decl" and tree.children[1].value!="headers":
                        self.metas.append(tree.children[3:-1])
                elif tree.data=="header_decl":
                        self.hdrs.append(tree.children[3:-1])
                elif tree.data=="reg_decl":
                        if tree.children[5].children[0].value in self.symbolics:
                                self.sym_reg_widths[tree.children[7].value] = tree.children[1].value
                                self.sym_reg_inst[tree.children[7].value]=tree.children[5].children[0].value
                        else:
                                self.reg_widths[tree.children[7].value]=tree.children[1].value
                                self.reg_inst[tree.children[7].value]=tree.children[5].children[0].value
                elif tree.data=="sym_reg_array_decl":
                        self.sym_reg_array_widths[tree.children[8].value]=tree.children[1].value
                        self.sym_reg_array_inst[tree.children[8].value]=tree.children[5].children[0].value
                        self.sym_reg_array_length[tree.children[8].value] = tree.children[7].value
                elif tree.data=="opt_expr":
                        self.opt_keyword = tree.children[0].children[0].value
                        self.util.append(tree)
                elif tree.data=="step":
                        self.step_size = int(tree.children[2].value)
                elif tree.data=="table_decl":
                        self.tables_acts[tree.children[1].value] = tree.children[4]
                        self.tables_match[tree.children[1].value] = tree.children[3]
                        self.tables_size[tree.children[1].value] = tree.children[5].children[2].value
                elif tree.data=="sym_decl":
                        self.symbolics.append(tree.children[1].value)
                elif tree.data=="function":
                        self.funcs.append(tree.children[2].children[0])
                elif tree.data=="assume_stmt":
                        self.assumes.append(tree)


class V_r2(Visitor_Recursive):
        def __init__(self, a_d):
                self.stmts = []
                self.sym_stmts = []
                self.loop_stmts = {}
                self.action_defs = a_d
                self.conditionals = {}
                self.conditional_acts = []
                self.t = []
        def __default__(self,tree):
                '''
                # ????? we need to replace action calls with action defs, and use those to construct basic blocks
                if tree.data=="apply_block" and tree.children[1].data=="block_stmt" and tree.children[1].children[0].data=="method_call":
                        self.stmts.append(tree)
                        # replace w/ action def
                        tree.children[1] = self.action_defs['t']
                '''
                if tree.data=="for_loop":
                        if tree.children[3] not in self.loop_stmts:
                                self.loop_stmts[tree.children[3].value] = [tree.children[6:-1]]
                        else:
                                self.loop_stmts[tree.children[3].value].append(tree.children[6:-1])
                if tree.data=="method_call":
                        self.stmts.append(tree.children[0].children[0].value)
                elif tree.data=="sym_method_call":      # these only happen w/in for loop
                        self.stmts.append(tree.children[0].children[0].value)
                        self.sym_stmts.append(tree.children[0].children[0].value)
                elif tree.data=="conditional":
                        self.conditional_acts.append([])
                        # conditional dictionary is action(table) name: conditional_expr
                        #if tree.children[0].type=="IF":        # if stmt
                        if_expr = [tree.children[2]]
                        #else:  # else if
                        #       if_expr = tree.children[3]
                        for c in tree.children[5:-1]:

                                # nested conditionals: dict value should be a list, not a single expr
                                # we check to see if we've already added the value to the dict (if not, create new entry)
                                # every time we hit a conditional, we go through EVERY action in its body and append the expression to its list
                                # this is a lot of extra work, and is NOT efficient, but will work for now


                                if isinstance(c,Tree) and c.data=="block_stmt":
                                        if isinstance(c.children[0].children[0], Tree): # we call an action, not a table
                                                if c.children[0].children[0].children[0].value in self.conditionals:
                                                        self.conditionals[c.children[0].children[0].children[0].value]+=if_expr
                                                        self.conditional_acts[-1].append(c.children[0].children[0].children[0].value)
                                                else:
                                                        self.conditionals[c.children[0].children[0].children[0].value]=if_expr
                                                        self.conditional_acts[-1].append(c.children[0].children[0].children[0].value)

                                        elif c.children[0].data=="table_apply": # table apply --> WILL NEED TO ASSOCIATE ACTS W/IN TABLE TO IF EXPR
                                                if c.children[0].children[0].value in self.conditionals:
                                                        self.conditionals[c.children[0].children[0].value]+=if_expr
                                                        self.conditional_acts[-1].append(c.children[0].children[0].value)
                                                else:
                                                        self.conditionals[c.children[0].children[0].value] = if_expr
                                                        self.conditional_acts[-1].append(c.children[0].children[0].value)

                                elif isinstance(c,Tree) and c.data=="expression":
                                        if_expr.append(c)
                        self.t.append(tree)
                elif tree.data=="table_apply":
                        self.stmts.append("table_"+tree.children[0].value)


# this function (called for each action def) produces a list of the meta that an action reads and/or writes to
# looks on either side of = in assignment stmts
# expressions are on right side, lvalues are on right side --> can we use this?
# we know that if we see a meta lvalue, we're definintely writing to it - right? bc we can't call a function on meta
# i think the lang is strict enough for this to be true
# AND CHECKS REG READS/WRITES - READ FROM/WRITE TO META
# is it safe to hardcode some the children indices?
class Act_reads_writes(Visitor_Recursive):
        def __init__(self,hashes,name):
                self.reads = []
                self.writes = []
                self.sym_reads = []
                self.sym_writes = []
                self.regs = []
                self.sym_regs = []
                self.hashes=hashes
                self.name = name
        def __default__(self,tree):
                # check lvalue to find meta fields we're writing to
                if tree.data=="lvalue":
                        if isinstance(tree.children[0],Token) and tree.children[0].type=="META":
                                if tree.children[2].type=="META_NAME":
                                        self.writes.append(tree.children[2].value)
                                if tree.children[2].type=="SYM_ARRAY_NAME":
                                        self.sym_writes.append(tree.children[2].value)
                        if isinstance(tree.children[0],Token) and tree.children[0].type=="HDR":
                                self.writes.append(tree.children[2]+"."+tree.children[4])
                # check to see if we're reading from meta fields
                if tree.data=="expression":
                        if isinstance(tree.children[-1],Token):
                                if tree.children[-1].type=="META_NAME":
                                        self.reads.append(tree.children[-1].value)
                                if tree.children[-1].type=="SYM_ARRAY_NAME":
                                        self.sym_reads.append(tree.children[-1].value)
                                if tree.children[-1].type=="HDR_FIELD":
                                        self.reads.append(tree.children[-3]+"."+tree.children[-1].value)
                # checking what meta fields we use w/ reg writes and reads
                if tree.data=="index_field":
                        if tree.children[2].type=="META_NAME":
                                self.reads.append(tree.children[2].value)
                        # if we have symbolic index field instead of regular meta
                        if tree.children[2].type=="SYM_ARRAY_NAME":
                                self.sym_reads.append(tree.children[2].value)
                        if tree.children[0].type=="HDR":
                                self.reads.append(tree.children[2]+"."+tree.children[4])
                if tree.data=="read_field":
                        if tree.children[0].type=="INT":
                                return
                        if tree.children[2].type=="META_NAME":
                                self.reads.append(tree.children[2].value)
                        if tree.children[2].type=="SYM_ARRAY_NAME":
                                self.sym_reads.append(tree.children[2].value)
                        if tree.children[0].type=="HDR":
                                self.reads.append(tree.children[2]+"."+tree.children[4])
                if tree.data=="write_field":
                        if tree.children[2].type=="META_NAME":
                                self.writes.append(tree.children[2].value)
                        if tree.children[2].type=="SYM_ARRAY_NAME":
                                self.sym_writes.append(tree.children[2].value)
                        if tree.children[0].type=="HDR":
                                self.writes.append(tree.children[2]+"."+tree.children[4])
                # check to see what regs we read from/write to - acts that access same reg MUST be in same stg
                if tree.data=="reg_write" or tree.data=="reg_read":
                        self.regs.append(tree.children[0].value)
                if tree.data=="sym_reg_write" or tree.data=="sym_reg_read":
                        self.sym_regs.append(tree.children[0].value.replace('[i]',''))

                # check to see what fields we use for hashing
                if tree.data=="hash_fields" and isinstance(tree.children[2],Token):
                        # if we hit this case, we know the action does a hash
                        if self.name not in self.hashes:
                                self.hashes.append(self.name)
                        if tree.children[2].type=="META_NAME":
                                self.reads.append(tree.children[2].value)
                        if tree.children[2].type=="SYM_ARRAY_NAME":
                                self.sym_reads.append(tree.children[2].value)
                        if tree.children[0].type=="HDR":
                                self.reads.append(tree.children[2]+"."+tree.children[4])
                if tree.data=="hash_index":
                        if tree.children[2].type=="META_NAME":
                                self.writes.append(tree.children[2].value)
                        if tree.children[2].type=="SYM_ARRAY_NAME":
                                self.sym_writes.append(tree.children[2].value)
                        if tree.children[0].type=="HDR":
                                self.writes.append(tree.children[2]+"."+tree.children[4])
                '''
                if tree.data=="assignment":
                        # check lvalue (write)
                        # need to verify this as meta value
                        if tree.children[0].data=="lvalue":     # i think this is always true, no need to check
                                self.writes.append(tree.children[0].children[2].value)
                        # check rvalue (read)
                        if isinstance(tree.children[2].children[0],Token):      # skip it if it's not a meta value/complex expr
                                return
                        # this doesn't work if we have complex expr
                        # check the type of the tokens in the expression?
                        # every time we add something to the right side, we get another expr tree
                        if tree.children[2].children[0].children[0].value=="meta":
                                self.reads.append(tree.children[2].children[2].value)
                '''

# conditional analysis - adds fields used in if stmt to an actions reads (do we ever write in conditional?)
# we call this in the same place we call Act_reads_writes
# just need to scan expression and look for (symbolic) meta/hdr fields
class Cond_reads(Visitor_Recursive):
        def __init__(self):
                self.reads = []
                self.sym_reads = []
                self.table_checks = []
        def __default__(self,tree):
                if tree.data=="expression":
                        if isinstance(tree.children[-1],Token):
                                if tree.children[-1].type=="META_NAME":
                                        self.reads.append(tree.children[-1].value)
                                if tree.children[-1].type=="SYM_ARRAY_NAME":
                                        self.sym_reads.append(tree.children[-1].value)
                                if tree.children[0].type=="HDR":
                                        self.reads.append(tree.children[2].value+".valid")
                                if tree.children[-1].type=="HDR_FIELD":
                                        self.reads.append(tree.children[2].value+"."+tree.children[4].value)

                        if isinstance(tree.children[0],Tree) and isinstance(tree.children[0].children[0],Tree) and tree.children[0].children[0].data=="table_apply":
                                self.table_checks.append(tree.children[0].children[0].children[0].value)




# transformer for utilty function trees
@v_args(inline=True)    # Affects the signatures of the methods
class UtilFuncTran(Transformer):
    def __init__(self):
        self.vars = []
        self.linear=1
        self.num_vars=0
        self.scale=0

    #from operator import neg
    number = float

    def neg(self, a):
        return "-"+a

    def var(self, name):
        self.num_vars+=1
        self.vars.append(name[0:])
        return name[0:]

    def add(self, a, b):
        return str(a)+"+"+str(b)

    def sub(self, a, b):
        return str(a)+"-"+str(b)

    def mul(self, a, b):
        self.linear=0
        return str(a)+"*"+str(b)

    def div(self, a, b):
        self.linear=0
        return str(a)+"/"+str(b)

    def pow(self, a, b):
        self.linear=0
        return str(a)+"**"+str(b)

    def scalefun(self,a,b):
        self.scale=1
        return b

    def exp(self,a,b,c):
        self.linear=0
        return str(a)+"."+str(b)+"("+c+")"

    def summation(self, a, b, c, d, e):
        self.linear=0
        low = 0
        hi = 0
        try:
                low=int(a)
        except ValueError:
                low=a
        try:
                hi=int(b)
        except ValueError:
                hi=b
        return "sum(map("+str(c)+" "+str(d)+": "+e+",range("+str(low)+","+str(hi)+")))"
# sum(start, stop, lambda x: (function))

# if not PWL, need to return equation but with var replaced with ILP vars (quicksum of something?)
# if multivariate, need to create mult ilp instances
#       we know it's multivariate if symbolic includes range syntax/number of vars > 1



class AssumeTran(Transformer):
        def assume_stmt(self,a):
                return a[2]

        def nexp(self, a):      # NAME
                return a[0][0:]

        def intexp(self,a):     # INT
                return a[0][0:]

        def gexp(self,a):       # greater than
                return a[0]+">="+a[3]

        def lexp(self,a):       # less than
                return a[0]+"<="+a[3]

        def eexp(self,a):       # equal
                return a[0]+"=="+a[2]




class SymTran(Transformer):
	def __init__(self,concretes):
		self.lines = []
		self.concretes = concretes
		self.con_regacts = {}
		self.con_acts = {}
		self.metas = []
	def includes(self,a):
		self.lines.append(a[0]+a[1]+" <"+a[2]+a[3]+a[4]+">\n")
	def sym_decl(self,a):
		return ""
	def assume_stmt(self,a):
		return ""
	def type_def(self,a):
		self.lines.append(a[0]+" "+a[1]+" "+a[2]+a[3]+"\n")
		return ""
	def define(self,a):
		self.lines.append(a[0]+a[1]+" "+a[2]+" "+a[3]+"\n")
		return ""
	def structfield(self,a):
		#self.lines.append(a[0] + " " + a[1] + a[2]+"\n")
		return a[0] + " " + a[1] + a[2]+"\n"
	def sym_structfield(self,a):
		unrolled = ""
		for i in range(self.concretes[a[1]]):
			unrolled += a[0]+" "+a[2]+"_"+str(i)+a[3]+"\n"
		return unrolled
	def struct_decl(self,a):
		self.metas.append(a[0]+" "+a[1]+" "+a[2]+"\n")
		for i in range(3,len(a)-1):
			self.metas.append(a[i]+"\n")
		self.metas.append(a[-1]+"\n")
		return ""
	def header_decl(self,a):
		#print a
		self.metas.append(a[0]+" "+a[1]+" "+a[2]+"\n")
		for i in range(3,len(a)-1):
			self.metas.append(a[i]+"\n")
		self.metas.append(a[-1]+"\n")
		return ""
	def reg_depth(self,a):
		if a[0] in self.concretes:
			return self.concretes[a[0]]
		else:
			return a[0]
	def reg_decl(self,a):
		#self.lines.append(a[0]+"<"+a[1]+a[2]+"_>"+a[3]+a[4]+a[5]+" "+a[6]+a[7]+"\n")
		return a[0]+"<"+a[1]+a[2]+"_>"+a[3]+a[4]+a[5]+" "+a[6]+a[7]+"\n"
	def sym_reg_array_decl(self,a):
		unrolled = ""
		self.con_regacts[str(a[7])]=self.concretes[a[6]]
		for i in range(self.concretes[a[6]]):
			unrolled+=a[0]+"<"+a[1]+a[2]+"_>"+a[3]+str(a[4])+a[5]+" "+a[7]+"_"+str(i)+a[8]+"\n"
		#self.lines.append(unrolled)
		return unrolled
	def sym_reg_act_decl(self,a):
		r_stmt=""
		unroll=self.con_regacts[a[6].replace("[i]","")]
		#print a[10]
		for x in range(unroll):
			r_stmt+=a[0]+"<"+a[1]+a[2]+"_"+a[3]+a[4]+"> "+a[5]+a[6].replace("[i]","_"+str(x))+a[7]+" "+a[8].replace("[i]","_"+str(x))+" "+a[9]+a[10]+"\n"
			# reg_appy a[11]
			if isinstance(a[11],list):	# there's a symbolic stmt somewhere here
				for val in a[11]:
					#print a[11]
					if isinstance(val,Tree):	# assignment with symbolic val (either sym lvalue or sym expr)
						if val.data=="sym_l" or val.data=="symmeta_l" or val.data=="symhdr_l":
							r_stmt+=self.sym_lvalue_proc(val,x)
							continue
						elif val.data=="e_symname" or val.data=="e_symmeta" or val.data=="e_symhdr":
							r_stmt+=self.sym_expr_proc(val,x)
							continue
					r_stmt+=val		# string (non-sym piece)
					if isinstance(val,Token) and (val.type=="LBRACE" or val.type=="RBRACE" or val.type=="SEMICOLON"):
						r_stmt+="\n"
				#self.lines.append("\n}\n")
			else:
				r_stmt+=a[11]
			r_stmt+=a[12]+a[13]+"\n"
		return r_stmt
	def match_type(self,a):
		return a[0]
	def key(self,a):
		r_stmt = a[0]+a[1]+a[2]+"\n"
		i = 3
		while i < len(a)-1:
			r_stmt+=a[i]+" "+a[i+1]+" "+a[i+2]+a[i+3]+"\n"
			i+=4
		r_stmt+=a[-1]+"\n"
		return r_stmt
	def actions(self,a):
		r_stmt = a[0]+a[1]+a[2]+"\n"
		i = 3
		while i < len(a)-1:
			r_stmt+=a[i]+a[i+1]+"\n"
			i+=2
		r_stmt+=a[-1]+"\n"
		return r_stmt
	def size(self,a):
		return a[0]+a[1]+a[2]+a[3]+"\n"
	def default(self,a):
		return a[0]+a[1]+a[2]+a[3]+a[4]+a[5]+"\n"
	def match(self,a):
		r_stmt = "0x"
		for i in range(len(a)):
			r_stmt += a[i]
		return r_stmt
	def entry(self,a):
		if isinstance(a[0],Token) and a[0].type=="LPAREN":	# we have parenthesis around entry
			return a[0]+a[1]+a[2]+" "+a[3]+" "+ a[4]
		return a[0]+" "+a[1]+" "+a[2]
	def entries(self,a):
		r_stmt = a[0]+" "+a[1]+a[2]+a[3]+"\n"
		for i in range(4, len(a)-1):
			r_stmt += a[i]
		r_stmt += a[-1]+"\n"
		return r_stmt
	def table_decl(self,a):
		r_stmt = a[0]+" "+a[1]+" "+a[2]+"\n"+a[3]+a[4]+a[5]
		i = 6
		while i < len(a)-1:
			r_stmt+=a[i]
			i+=1
		r_stmt+=a[-1]+"\n"
		#self.lines.append(r_stmt)
		return r_stmt
	def algo(self,a):
		return a[0]+a[1]+a[2]
	def hash_decl(self,a):
		#self.lines.append(a[0]+"<"+a[1]+">"+a[2]+a[3]+a[4]+" "+a[5]+a[6]+"\n")
		return a[0]+"<"+a[1]+">"+a[2]+a[3]+a[4]+" "+a[5]+a[6]+"\n"
	def sym_hash_decl(self,a):
		unrolled = ""
		for i in range(self.concretes[a[5]]):
			unrolled += a[0]+"<"+a[1]+">"+a[2]+a[3]+a[4]+" "+a[6]+"_"+str(i)+a[7]+"\n"
		#self.lines.append(unrolled)
		return unrolled
	def type_param(self,a):
		return a[0]+" "+a[1]
	def param_list(self,a):
		return a[0]+","+a[1]
	def act_block_stmt(self,a):
		return a[0]
	def block_stmt(self,a):
		return a[0]
	def action_decl(self,a):
		r_stmt=""
		# we should have NO sym block stmts here bc not a symbolic action
		if isinstance(a[3],Token):	# checking for params (we have none)
			r_stmt+=a[0]+" "+a[1]+a[2]+a[3]+a[4]+"\n"
			for i in range(5,len(a)-1):	# add each block stmt to output
				r_stmt+=a[i]
			r_stmt+=a[-1]+"\n"
		else:	# we have params
			r_stmt+=a[0]+" "+a[1]+a[2]+a[3]+a[4]+a[5]+"\n"
			for i in range(6,len(a)-1):
				r_stmt+=a[i]
			r_stmt+=a[-1]+"\n"
		return r_stmt
	def sym_action_decl(self,a):
		#print self.con_acts
		self.lines.append("")
		return a
	def direction(self,a):
		return a[0]
	def reg_apply(self,a):
		for i in range(12,len(a)):
			if isinstance(a[i],list):
				return self.removeNestings(a)
		r_stmt = a[0]+" "+a[1]+a[2]+a[3]+" "+a[4]+" "+a[5]+a[6]+" "+a[7]+" "+a[8]+" "+a[9]+a[10]+a[11]+"\n"
		for i in range(12,len(a)-1):
			r_stmt+=a[i]
		r_stmt+=a[-1]+"\n"
		return r_stmt
	def reg_act_decl(self,a):
		#self.lines.append(a[0]+"<"+a[1]+a[2]+"_"+a[3]+a[4]+">"+a[5]+a[6]+a[7]+" "+a[8]+a[9]+a[10]+"\n"+a[11]+a[12]+a[13]+"\n")
		return a[0]+"<"+a[1]+a[2]+"_"+a[3]+a[4]+">"+a[5]+a[6]+a[7]+" "+a[8]+a[9]+a[10]+"\n"+a[11]+a[12]+a[13]+"\n"
	# lvalue (nonsym) things
	def nonsym_l(self,a):
		return a[0]
	def nonsymmeta_l(self,a):
		return a[0]+a[1]+a[2]
	def nonsymhdr_l(self,a):
		return a[0]+a[1]+a[2]+a[3]
	# epxression
	def e_int(self,a):
		return a[0]
	def e_true(self,a):
		return a[0]
        def e_false(self,a):
                return a[0]
        def hdr_valid(self,a):
                return a[0]+a[1]+a[2]+a[3]+a[4]
        def e_plus(self,a):
		if isinstance(a[0],Tree) or isinstance(a[2],Tree):
			return a
                return a[0]+a[1]+a[2]
        def e_minus(self,a):
                if isinstance(a[0],Tree) or isinstance(a[2],Tree):
                        return a
                return a[0]+a[1]+a[2]
        def e_name(self,a):
                return a[0]
        def e_meta(self,a):
                return a[0]+a[1]+a[2]
        def e_hdr(self,a):
		if len(a) > 5:
			return a[0]+a[1]+a[2]+a[3]+a[4]+a[5]+a[6]
		else:
                	return a[0]+a[1]+a[2]+a[3]+a[4]
	def e_p(self,a):
                if isinstance(a[0],Tree):
                        return a
                return a[0]+a[1]+a[2]
	def e_less(self,a):
                if isinstance(a[0],Tree) or isinstance(a[2],Tree):
                        return a
                return a[0]+a[1]+a[2]
	def e_greater(self,a):
                if isinstance(a[0],Tree) or isinstance(a[2],Tree):
                        return a
                return a[0]+a[1]+a[2]
	def e_eq(self,a):
                if isinstance(a[0],Tree) or isinstance(a[2],Tree):
                        return a
                return a[0]+a[1]+a[2]
	def e_neq(self,a):
                if isinstance(a[0],Tree) or isinstance(a[2],Tree):
                        return a
                return a[0]+a[1]+a[2]
	def e_or(self,a):
                if isinstance(a[0],Tree) or isinstance(a[2],Tree):
                        return a
                return a[0]+a[1]+a[2]
	def e_and(self,a):
                if isinstance(a[0],Tree) or isinstance(a[2],Tree):
                        return a
                return a[0]+a[1]+a[2]
	def table_hit(self,a):
		return a[0]+a[1]+a[2]
	def table_miss(self,a):
		return a[0]+a[1]+a[2]
	def min(self,a):
		if isinstance(a[2],Tree) or isinstance(a[4],Tree):
			return a
		return a[0]+a[1]+a[2]+a[3]+a[4]+a[5]
	def max(self,a):
                if isinstance(a[2],Tree) or isinstance(a[4],Tree):
                        return a
		return a[0]+a[1]+a[2]+a[3]+a[4]+a[5]
	def expression(self,a):
		if isinstance(a[0],list):
			return self.removeNestings(a[0])
		else:
			return a[0]
	# block stmts
	def conditional(self,a):
		lines = []
		r_stmt = ""
		sym_cond = False
		sym_body = False
		#print a
		if isinstance(a[2],list):	# condition has symbolic field in it
			sym_cond = True
			lines.append(a[0]+" "+a[1])
			lines+=self.removeNestings(a[2])
			lines.append(a[3]+a[4]+"\n")
		else:
			lines.append(a[0]+" "+a[1]+a[2]+a[3]+a[4]+"\n")
			r_stmt += a[0]+" "+a[1]+a[2]+a[3]+a[4]+"\n"
		i = 5
		non_sym_body = ""
		while not (isinstance(a[i],Token) and a[i].type=="RBRACE"):
			if isinstance(a[i],list):
				sym_body = True
				lines+=self.removeNestings(a[i])
			elif isinstance(a[i],Tree):
				sym_body = True
				lines.append(a[i])
			else:
				non_sym_body+=a[i]
				lines.append(a[i])
			i+=1
		if not sym_body:	# body of for loop is entirely non-symbolic
			r_stmt+=non_sym_body+a[i]+"\n"
		lines.append(a[i]+"\n") # rbrace
		i+=1
		if i==len(a):	# we don't have any else ifs/elses
			if sym_cond or sym_body:
				return lines
			return r_stmt
		# check for else ifs (we can have many)
		while i < len(a) and isinstance(a[i+1],Token) and a[i+1].type=="IF":
			if isinstance(a[i+3],list):
				sym_cond = True
				lines.append(a[i]+" "+a[i+1]+" "+a[i+2])
				lines+=self.removeNestings(a[i+3])
				lines.append(a[i+4]+" "+a[i+5]+"\n")
			else:
				r_stmt+=a[i]+" "+a[i+1]+" "+a[i+2]+a[i+3]+a[i+4]+" "+a[i+5]+"\n"
			i += 6
			non_sym_body = ""
			while not (isinstance(a[i],Token) and a[i].type=="RBRACE"):
				if isinstance(a[i],list):
					sym_body = True
					lines+=self.removeNestings(a[i])
				elif isinstance(a[i],Tree):
					sym_body = True
					lines.append(a[i])
				else:
					non_sym_body+=a[i]
					lines.append(a[i])
				i+=1
			if not sym_body:
				r_stmt+=non_sym_body+a[i]+"\n"	# rbrace
			lines.append(a[i]+"\n")
			i+=1
		# check for elses (we can have at most one)
		if i==len(a):	# no elses
			if sym_cond or sym_body:
				return lines
			return r_stmt
		r_stmt+=a[i]+" "+a[i+1]+"\n"
		lines.append(a[i]+" "+a[i+1]+"\n")
		i += 2
		non_sym_body = ""
		while not (isinstance(a[i],Token) and a[i].type=="RBRACE"):
			if isinstance(a[i],list):
				sym_body = True
				lines+=self.removeNestings(a[i])
			elif isinstance(a[i],Tree):
				sym_body = True
				lines.append(a[i])
			else:
				non_sym_body+=a[i]
				lines.append(a[i])
			i+=1
		if not sym_body:
			r_stmt+=non_sym_body+a[i]+"\n"
		lines.append(a[i]+"\n")
		if sym_cond or sym_body:
			return lines
		return r_stmt
	def method_call(self,a):
		# a[0] shouldn't be symbolic (bc not sym method call), so when we call this func, it should be a string
		#self.lines.append(a[0]+a[1]+a[2]+a[3]+"\n")
		return a[0]+a[1]+a[2]+a[3]+"\n"
	def sym_lvalue_proc(self,l,x):
		if l.data=="sym_l":
			return l.children[0].replace("[i]","_"+str(x))
		elif l.data=="symmeta_l":
			return l.children[0]+l.children[1]+l.children[2].replace("[i]","_"+str(x))
		elif l.data=="symhdr_l":
			return l.children[0]+l.children[1]+l.children[2]+l.children[3]+l.children[4].replace("[i]","_"+str(x))
	def sym_expr_proc(self,e,x):
		if e.data=="e_symname":
			return e.children[0].replace("[i]","_"+str(x))
		if e.data=="e_symmeta":
			return e.children[0]+e.children[1]+e.children[2].replace("[i]","_"+str(x))
		if e.data=="e_symhdr":
			return e.children[0]+e.children[1]+e.children[2]+e.children[3]+e.children[4].replace("[i]","_"+str(x))
	def sym_index_field_proc(self,i,x):
		if i.data=="i_symname":
			return i.children[0].replace("[i]","_"+str(x))
		elif i.data=="i_symmeta":
			return i.children[0]+i.children[1]+i.children[2].replace("[i]","_"+str(x))
		elif i.data=="i_symhdr":
			return i.children[0]+i.children[1]+i.children[2]+i.children[3]+i.children[4].replace("[i]","_"+str(x))
	def sym_method_call_proc(self,t,x):
		return t.children[0]+"_"+str(x)+t.children[1]+t.children[2]+t.children[3]+"\n"
	def sym_hash_list_proc(self,hl,x):
		r_stmt = ""
		for val in hl:
			if isinstance(val,Tree):
				if val.data=="symmeta":
					r_stmt+=val.children[0]+val.children[1]+val.children[2].replace("[i]","_"+str(x))
				elif val.data=="symhdr":
					r_stmt+=val.children[0]+val.children[1]+val.children[2]+val.children[3].replace("[i]","_"+str(x))
				elif val.data=="seed":
					r_stmt+=self.get_seed()
			else:
				r_stmt+=val
		return r_stmt
	def sym_reg_act_exec_proc(self,t,x):
		r_stmt = ""
		if isinstance(t.children[0],Tree):
			r_stmt+=self.sym_lvalue_proc(t.children[0],x)
		else:
			r_stmt+=t.children[0]
		r_stmt+=t.children[1]+t.children[2].replace("[i]","_"+str(x))+t.children[3]+t.children[4]+t.children[5]
		if isinstance(t.children[6],Tree):
			r_stmt+=self.sym_index_field_proc(t.children[6],x)
		else:
			r_stmt+=t.children[6]
		r_stmt+=t.children[7]+t.children[8]+"\n"
		return r_stmt
	def sym_hash_func_proc(self,t,x):
		r_stmt=""
		if isinstance(t.children[0],Tree):
			r_stmt+=self.sym_lvalue_proc(t.children[0],x)
		else:
			r_stmt+=t.children[0]
		r_stmt+=t.children[1]+t.children[2]+"_"+str(x)+t.children[3]+t.children[4]+t.children[5]
		if isinstance(t.children[6],str) or isinstance(t.children[6],unicode):	# non-sym hash fields
			r_stmt+=t.children[6]
		else:
			r_stmt+=t.children[6][0]      # lbrace
			if isinstance(t.children[6][1],list):
				r_stmt+=self.sym_hash_list_proc(t.children[6][1],x)
			else:
				r_stmt+=t.children[6][1]
			r_stmt+=t.children[6][2]
		r_stmt+=t.children[7]+t.children[8]+"\n"
		return r_stmt
	def for_loop(self,a):
		symval = a[3]
		con = self.concretes[a[3]]
		lines = ""
		for x in range(con):
			i = 6
			while i < len(a)-1:
				# if sym method call, sym conditional, we need to add _x to the names AND make sure we know name: num times unrolled
				if isinstance(a[i],Tree):
					if a[i].data=="sym_method_call":
						lines+=self.sym_method_call_proc(a[i],x)
						self.con_acts[str(a[i].children[0])]=self.concretes[a[3]]
					elif a[i].data=="sym_reg_act_exec":
						lines+=self.sym_reg_act_exec_proc(a[i],x)
					elif a[i].data=="sym_hash_func":
						lines+=self.sym_hash_func_proc(a[i],x)
				elif isinstance(a[i],list):	# assignment OR condtional with symbolic in it
					for e in a[i]:
						if isinstance(e,Tree): 
							# sym expr (e_symname, e_symmeta, e_symhdr) or sym l value (sym_l, symmeta_l, symhdr_l) or sym block (sym_method_call, sym_reg_act_exec, sym_hash_func)
							if e.data=="e_symname" or e.data=="e_symmeta" or e.data=="e_symhdr":
								lines+=self.sym_expr_proc(e,x)
								continue
							if e.data=="sym_l" or e.data=="symmeta_l" or e.data=="symhdr_l":
								lines+=self.sym_lvalue_proc(e,x)
								continue
							if e.data=="sym_method_call":
								lines+=self.sym_method_call_proc(e,x)
								continue
							if e.data=="sym_reg_act_exec":
								lines+=self.sym_reg_act_exec_proc(e,x)
								continue
							if e.data=="sym_hash_func":
								lines+=self.sym_hash_func_proc(e,x)
								continue
						lines+=e	
					#print a[i]
				# if non symbolic, we just add mult instances w/o changing
				else:
					lines+=a[i]
				i+=1
		#print lines
		return lines
	def assignment(self,a):
		if isinstance(a[0],Tree) or isinstance(a[2],Tree): # symbolics
			#print a
			return a
		elif isinstance(a[0],list) or isinstance(a[2],list):
			if isinstance(a[0],list):
				a[0]=self.removeNestings(a[0])
			if isinstance(a[2],list):
				a[2]=self.removeNestings(a[2])
			return [a[0],a[1],a[2],a[3],"\n"]
		else: # we don't have symbolic values
			return a[0]+a[1]+a[2]+a[3]+"\n"
	# index_field
	def i_name(self,a):
		return a[0]
	def i_meta(self,a):
		return a[0]+a[1]+a[2]
	def i_hdr(self,a):
		return a[0]+a[1]+a[2]+a[3]+a[4]
	def i_int(self,a):
		return a[0]
	def reg_act_exec(self,a):
		return a[0]+a[1]+a[2]+a[3]+a[4]+a[5]+a[6]+a[7]+a[8]+"\n"
	# hash fields
	def nonsymmeta(self,a):
		return a[0]+a[1]+a[2]
	#def symmeta(self,a):
	#	return a
	def nonsymhdr(self,a):
		return a[0]+a[1]+a[2]+a[3]+a[4]
	#def symhdr(self,a):
	#	return a
	def removeNestings(self,l):
		output = []
		#print l
    		for i in l:
        		if isinstance(i,list):
            			output+=self.removeNestings(i)
        		else:
				#print i
            			output.append(i)

		return output
	def hlist(self,a):
		if isinstance(a[0],Tree) or isinstance(a[2],Tree) or isinstance(a[0],list) or isinstance(a[2],list):
			#print a
			#print [ item for elem in a for item in elem]
			return a
		else:
			return a[0]+a[1]+a[2]
	def hash_list(self,a):
		if isinstance(a[1],Tree) or isinstance(a[1],list):
			if isinstance(a[1],list):
				#print a[1]
				a[1]=self.removeNestings(a[1])
			return a
		else:
			return a[0]+a[1]+a[2]
	def hash_func(self,a):
		# a[0] shouldn't be symbolic bc not sym hash func
		return a[0]+a[1]+a[2]+a[3]+a[4]+a[5]+a[6]+a[7]+a[8]+"\n"
	def apply_block(self,a):
		r_stmt=a[0]+" {\n"
		#self.lines.append(a[0]+" {\n")
		for i in range(1,len(a)):
			#self.lines.append(a[i])
			r_stmt+=a[i]
		#self.lines.append("}\n")
		r_stmt+="}\n"
		return r_stmt
	def controllocaldecl(self,a):
		return a[0]
	def control_block(self,a):
		u=""
		#	need to check for symbolic sym_act decls and unroll
		#'''
		for i in range(len(a)):
			#print a[i]
			if isinstance(a[i],list):	# we have a symbolic action to unroll
				#print a[i]
				a_name = a[i][1]
				#u = ""
				for x in range(self.con_acts[a_name]):
					u+=a[i][0]+" "+a[i][1]+"_"+str(x)+a[i][2]+a[i][3]+" "+a[i][4]+"\n"
					for s in a[i][5:-1]:
						if isinstance(s,Tree):		# sym act_block_stmt
							if s.data=="sym_method_call":
                                                		u+=self.sym_method_call_proc(s,x)
                                        		elif s.data=="sym_reg_act_exec":
                                                		u+=self.sym_reg_act_exec_proc(s,x)
                                        		elif s.data=="sym_hash_func":
                                                		u+=self.sym_hash_func_proc(s,x)
						elif isinstance(s,list):	# assignment OR condtional with symbolic in it
							 for e in s:
                                                		if isinstance(e,Tree):
                                                        	# sym expr (e_symname, e_symmeta, e_symhdr) or sym l value (sym_l, symmeta_l, symhdr_l) or sym block (sym_method_call, sym_reg_act_exec, sym_hash_func)
                                                        		if e.data=="e_symname" or e.data=="e_symmeta" or e.data=="e_symhdr":
                                                                		u+=self.sym_expr_proc(e,x)
                                                                		continue
                                                        		if e.data=="sym_l" or e.data=="symmeta_l" or e.data=="symhdr_l":
                                                                		u+=self.sym_lvalue_proc(e,x)
                                                                		continue
                                                        		if e.data=="sym_method_call":
                                                                		u+=self.sym_method_call_proc(e,x)
                                                                		continue
                                                        		if e.data=="sym_reg_act_exec":
                                                                		u+=self.sym_reg_act_exec_proc(e,x)
                                                                		continue
                                                        		if e.data=="sym_hash_func":
                                                                		u+=self.sym_hash_func_proc(e,x)
                                                                		continue
                                                		u+=e

						else:	# non sym statement
							u+=s
					u+="\n"+a[i][-1]+"\n"
			else:
				u+=a[i]
		#print a
		return u
	def control_decl(self,a):
		self.lines.append(a[0]+" "+a[1]+a[2]+a[3]+" "+a[4]+" "+a[5]+a[6]+a[7]+" "+a[8]+" "+a[9]+a[10]+a[11]+" "+a[12]+" "+a[13]+a[14]+a[15]+" "+a[16]+" "+a[17]+a[18]+a[19]+" "+a[20]+" "+a[21]+a[22]+a[23]+" "+a[24]+" "+a[25]+a[26]+a[27]+"\n"+a[28]+a[29]+"\n")
		#self.lines.append(a[0]+" "+a[1]+" "+a[2]
		#print a
		return a
	def table_apply(self,a):
		return a[0]+a[1]+a[2]+a[3]+a[4]+a[5]+"\n"
	def drop(self,a):
		return a[0]+a[1]+a[2]+a[3]+"\n"
	def utility_func(self,a):
		return ""
	def opt_expr(self, a):
		return ""
	def switch_pipeline(self,a):
		for i in range(len(a)):
			self.lines.append(a[i])
		self.lines.append("\n")
		return a
	def switch_main(self,a):
		for i in range(len(a)):
			self.lines.append(a[i])
		self.lines.append("\n")
		return a
	def meta(self,a):
		return a[0]
	def get_seed(self):
    		wid=random.randint(3,6)
    		num=random.randint(0,2**wid-1)
    		return str(wid)+"w"+str(num)
	#def seed(self,a):
	#	return self.get_seed()



'''
'''


