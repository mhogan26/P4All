# we're not allowing symbolic reg sizes here (i.e., can't make regs wider)

# ACTION EXPRESSIONS
# INCLUDES/PACKAGES?
# ACTION/CONTROL ARGUMENTS
# PARSER + CHECKSUM
# MORE STMTS? (direct application/call to other control blocks in control, exit, return, empty, etc.)
# SEPARATE BLOCK STMTS FROM BLOCK STMTS ALLOWED IN FOR LOOPS???
# MORE OPERATIONS IN ACTIONS - BINARY, STRING_LITERAL, ETC.
# can non symbolic actions be in for loops?
# NESTED LOOPS????
# NESTED CONDITIONALS???
# ACTS IN MULTIPLE CONDITIONALS? would we ever have the same action appear in different if stmts?
# ELSE STMTS?
# ADD MORE HASH ALGOS? SHOULD THIS BE HARDCODED??
# ADD CONST VARS TO CONTROL BLOCK - WHERE CAN THESE BE USED? ARE THEY LOCAL TO AN ACTION?
# ALLOW TYPEDEFS TO BE USED IN SYMBOLIC HEADER FIELDS?
# SYMBOLIC HEADER FIELD (INSTEAD OF IN META??)
# ASSUMING THAT AN ACTION HAS AT MOST HASH - SHOULD WE ALLOW FOR MORE?
# ^ BUT WITH REG ACTIONS
# ASSUME ONLY 1 STRUCT DEF (METADATA) - ALLOW MULTIPLE STRUCTS
# UPDATE SAME_SIZE TO ALLOW FOR MULT SYMBOLIC ACTIONS TO ACCESS THE SAME SYM REG ARRAY
# CHECK TODOs IN CODE
# error checking for python code???

# ADD CASES WHERE WE CREATE MULT INSTANCES OF ILP AND PICK BEST (bloom filter)
# FIX PARSING TO WORK FOR UTILS W/O SWITCH STMTS
# UPDATE PARSING TO SUPPORT MULTIPLE UTIL FUNCS DEFINED
# ADD HEADER FIELDS TO META SIZE SECTION
# FIX UPPER BOUND: IF ONE ACT IN LOOP IS STATEFUL, THEN THEY'RE ALL BOUND BY THAT
# MULT LOOPS W/ DIFF SYM VALUE - DEP ANALYSIS WILL BE DIFFERENT (??)
# FIX sym_reg_array_decl - instances doesn't always have to be symbolic (could be fixed size) - ILP ALSO DOES THIS
from lark import Lark, Visitor, Token, Tree
from lark.visitors import Visitor_Recursive

# control block vars

grammar = """
start: p4allprogram+
 
p4allprogram: topleveldecl
	    | variabledecl
	    | derivedtypedecl

topleveldecl: control_decl
	    | utility_func

variabledecl: sym_decl
	    | define
	    | type_def

derivedtypedecl: struct_decl
	       | header_decl


struct_decl: STRUCT NAME LBRACE (sym_structfield|structfield)+ RBRACE 
header_decl: HEADER NAME LBRACE (sym_structfield|structfield)+ RBRACE

structfield: BIT_SIZE NAME SEMICOLON 
	   | TYPENAME NAME SEMICOLON
sym_structfield: BIT_SIZE "[" NAME "]" NAME SEMICOLON 

sym_decl: SYMBOLIC NAME SEMICOLON
define: HT DEFINE CONST_NAME SIGNED_INT
type_def: TYPEDEF BIT_SIZE TYPENAME SEMICOLON

control_decl: CONTROL NAME control_block
control_block: "{" controllocaldecl* apply_block "}"
controllocaldecl: action_decl
		| sym_action_decl
		| reg_decl
		| sym_reg_decl
		| sym_reg_array_decl
action_decl: ACTION NAME LPAREN RPAREN "{" block_stmt+ "}"
sym_action_decl: ACTION NAME LPAREN RPAREN "[" "i" "]" "{" block_stmt+ "}"
reg_decl: REGISTER "<" BIT_SIZE ">" LPAREN REG_DEPTH RPAREN NAME SEMICOLON
sym_reg_decl: REGISTER "<" BIT_SIZE ">" LPAREN SYM_REG_DEPTH RPAREN NAME SEMICOLON
sym_reg_array_decl: REGISTER "<" BIT_SIZE ">" LPAREN SYM_REG_DEPTH RPAREN "[" NAME "]" NAME SEMICOLON
apply_block: APPLY "{" block_stmt+ "}"

block_stmt: conditional
	  | method_call
	  | for_loop
	  | sym_method_call
	  | assignment
	  | reg_write
	  | reg_read
	  | sym_reg_write
	  | sym_reg_read
	  | hash_func

conditional: IF LPAREN expression RPAREN LBRACE block_stmt+ RBRACE
method_call: lvalue LPAREN RPAREN SEMICOLON
sym_method_call: lvalue LPAREN RPAREN "[" "i" "]" SEMICOLON
for_loop: FOR LPAREN "i" LESSTHAN NAME RPAREN LBRACE block_stmt+ RBRACE 
assignment: lvalue ASSIGN expression SEMICOLON
reg_write: NAME DOT WRITE LPAREN index_field COMMA read_field RPAREN SEMICOLON
reg_read: NAME DOT READ LPAREN write_field COMMA index_field RPAREN SEMICOLON
sym_reg_write: SYM_ARRAY_NAME DOT WRITE LPAREN index_field COMMA read_field RPAREN SEMICOLON
sym_reg_read: SYM_ARRAY_NAME DOT READ LPAREN write_field COMMA index_field RPAREN SEMICOLON
hash_func: HASH LPAREN hash_index COMMA algo COMMA hash_num COMMA hash_list COMMA hash_num RPAREN SEMICOLON

utility_func: opt NAME LBRACE function step? RBRACE


opt: MAXIMIZE
   | MINIMIZE

function: FUNCTION COLON func_def SEMICOLON

func_def: switch
	| python_func

switch: SWITCH NAME LBRACE cases+ RBRACE
cases: CASE INT LBRACE SCALE? python_func RBRACE
     | DEFAULT LBRACE SCALE? python_func RBRACE

step: STEP COLON INT SEMICOLON

python_func: PYTHONCODE


lvalue: NAME
      | SYM_ARRAY_NAME
      | META DOT META_NAME 
      | META DOT SYM_ARRAY_NAME
      | HDR DOT HDR_NAME DOT HDR_FIELD

expression: INT
	  | TRUE
          | FALSE
          | expression PLUS expression
          | expression MINUS expression
	  | NAME
	  | SYM_ARRAY_NAME
	  | META DOT META_NAME
          | META DOT SYM_ARRAY_NAME
	  | HDR DOT HDR_NAME DOT HDR_FIELD	
          | expression LPAREN RPAREN 
	  | expression LESSTHAN expression
	  | expression GREATERTHAN expression

write_field: NAME
           | SYM_ARRAY_NAME
           | META DOT META_NAME 
           | META DOT SYM_ARRAY_NAME
	   | HDR DOT HDR_NAME DOT HDR_FIELD

read_field: NAME
          | SYM_ARRAY_NAME
          | META DOT META_NAME 
          | META DOT SYM_ARRAY_NAME
	  | INT
	  | HDR DOT HDR_NAME DOT HDR_FIELD

index_field: NAME
           | SYM_ARRAY_NAME
           | META DOT META_NAME 
           | META DOT SYM_ARRAY_NAME
	   | HDR DOT HDR_NAME DOT HDR_FIELD

hash_index: NAME
           | SYM_ARRAY_NAME
           | META DOT META_NAME 
           | META DOT SYM_ARRAY_NAME
           | HDR DOT HDR_NAME DOT HDR_FIELD

hash_num: CONST_NAME
	| SIGNED_INT

hash_list: LBRACE hash_fields RBRACE 

hash_fields: META DOT META_NAME
	   | META DOT SYM_ARRAY_NAME
	   | HDR DOT HDR_NAME DOT HDR_FIELD
	   | hash_fields COMMA hash_fields

algo: HASH_A DOT CRC16
    | HASH_A DOT CRC32

TYPEDEF: "typedef"
SYMBOLIC: "symbolic"
CONTROL: "control"
APPLY: "apply"
ACTION: "action"
REGISTER: "register"
STRUCT: "struct"
HEADER: "header"
IF: "if"
FOR: "for"
DOT: "."
ASSIGN: "="
TRUE: "true"
FALSE: "false"
PLUS: "+"
MINUS: "-"
LPAREN: "("
RPAREN: ")"
SEMICOLON: ";"
COMMA: ","
COLON: ":"
WRITE: "write"
READ: "read"
META: "meta"
HASH: "hash"
HASH_A: "HashAlgorithm"
CRC16: "crc16"
CRC32: "crc32"
LBRACE: "{"
RBRACE: "}"
HT: "#"
DEFINE: "define"
SIGNED_INT: INT ("w"|"s") INT
CONST_NAME: NAME
LESSTHAN: "<"
GREATERTHAN: ">"
HDR: "hdr"
MAXIMIZE: "maximize"
MINIMIZE: "minimize"
FUNCTION: "function"
SCALE: "scale"
STEP: "step"
SWITCH: "switch"
DEFAULT: "default"
CASE: "case"
PYTHONCODE: /.+/ 

NAME: (WORD|"_") (LETTER|INT|"_")*
META_NAME: NAME
SYM_ARRAY_NAME: NAME "[" "i" "]"
BIT_SIZE: "bit" "<" INT ">"
REG_DEPTH: INT
SYM_REG_DEPTH: NAME
TYPENAME: NAME
HDR_NAME: NAME
HDR_FIELD: NAME

%import common.WS
%import common.WORD
%import common.LETTER
%import common.INT
%import common.CPP_COMMENT
%ignore WS
%ignore CPP_COMMENT

"""

p = Lark(grammar,parser="earley")



with open('../cms.p4all', 'r') as file:
    data = file.read()

# parse takes string as input
parse_tree = p.parse(data)
#print( parse_tree.pretty() )



# walk through tree
# we can save off action definitions, and then reference them when we go through apply block?
# let's just get a list the stmts in the apply block, in the same order we call them (so we can find deps)
# should we use transformer to replace action calls with action definition in apply block??
#	do you replace function calls with their definitions in a parse tree to get control flow graph??
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
		self.reg_widths = {}	# reg array declarations with NO symbolic elements
		self.sym_reg_widths = {}	# reg array declaration with symbolic num instances
		self.sym_reg_array_widths = {}	# symbolic array of regs decl with symbolc instances
		self.util = []
		self.reg_inst = {}
		self.sym_reg_inst = {}
		self.sym_reg_array_inst = {}
		self.opt_keyword = ""
		self.switch_var = ""
		self.step_size = 0
		self.case_stmts = {}
	def __default__(self,tree):
		if tree.data=="action_decl":
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
			self.reg_widths[tree.children[5].value]=tree.children[1].value
			self.reg_inst[tree.children[5].value]=tree.children[3].value
		elif tree.data=="sym_reg_decl":
			self.sym_reg_widths[tree.children[5].value] = tree.children[1].value
			self.sym_reg_inst[tree.children[5].value] = tree.children[3].value
		elif tree.data=="sym_reg_array_decl":
			self.sym_reg_array_widths[tree.children[6].value]=tree.children[1].value
			if tree.children[3].type== "SYM_REG_DEPTH":
				self.sym_reg_array_inst[tree.children[6].value]=tree.children[3].value
		elif tree.data=="opt":
			self.opt_keyword = tree.children[0].value	# this assumes we only have one util func defined
		elif tree.data=="switch":
			self.switch_var = tree.children[1].value
		elif tree.data=="cases":
			if tree.children[0].type=="DEFAULT":
				if isinstance(tree.children[2],Token):	# we're scaling the function
					self.case_stmts[tree.children[0].value]=(tree.children[3].children[0].value,1)
				else:
					self.case_stmts[tree.children[0].value]=(tree.children[2].children[0].value,0)
			if tree.children[0].type=="CASE":
				if isinstance(tree.children[3],Token):  # we're scaling the function
					self.case_stmts[tree.children[1].value]=(tree.children[4].children[0].value,1)
				else:
					self.case_stmts[tree.children[1].value]=(tree.children[3].children[0].value,0)
		elif tree.data=="step":
			self.step_size = int(tree.children[2].value)

class V_r2(Visitor_Recursive):
	def __init__(self, a_d):
		self.stmts = []
		self.sym_stmts = []
		self.loop_stmts = {}
		self.action_defs = a_d
		self.conditionals = {}
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
		elif tree.data=="sym_method_call":	# these only happen w/in for loop
			self.stmts.append(tree.children[0].children[0].value)
			self.sym_stmts.append(tree.children[0].children[0].value)
		elif tree.data=="conditional":
			for c in tree.children[5:-1]:
				self.conditionals[c.children[0].children[0].children[0].value]=tree.children[2]

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
			if tree.children[0].data=="lvalue":	# i think this is always true, no need to check
				self.writes.append(tree.children[0].children[2].value)
			# check rvalue (read)
			if isinstance(tree.children[2].children[0],Token):	# skip it if it's not a meta value/complex expr
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
	def __default__(self,tree):
		if tree.data=="expression":
                	if isinstance(tree.children[-1],Token):
                        	if tree.children[-1].type=="META_NAME":
                                	self.reads.append(tree.children[-1].value)
                        	if tree.children[-1].type=="SYM_ARRAY_NAME":
                                	self.sym_reads.append(tree.children[-1].value)


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
#print v1.reg_widths
#print v1.reg_inst
#print v1.sym_reg_widths
#print v1.sym_reg_inst
#print v1.opt_keyword
#print v1.switch_var
#print v1.step_size
#print v1.case_stmts

v2 = V_r2(v1.action_defs)
v2.visit(v1.apply[0])	# assuming we only have one apply block in the v1.apply list
#print v2.stmts
#print v2.conditionals
#print v2.loop_stmts

'''
v3 = Act_reads_writes()
v3.visit(v1.action_defs['x'])
print v3.writes
print v3.reads
v4 = Act_reads_writes()
v4.visit(v1.action_defs['t'])
'''

# get sizes for each meta declaration
meta_sizes = {}
sym_meta_sizes = {}
total_req_meta=0
for m in v1.metas:
	for f in m:
		if f.data=="sym_structfield":	# we can also pull the symbolic value here, but we don't need it for now
			sym_meta_sizes[f.children[2].value]=int(f.children[0].value.replace('bit<','').replace('>',''))
			continue
		if f.children[0].type=="TYPENAME":
			meta_sizes[f.children[1].value]=int(v1.typenames[f.children[0].value].replace('bit<','').replace('>',''))
			total_req_meta+=meta_sizes[f.children[1].value]
			continue
		
		meta_sizes[f.children[1].value]=int(f.children[0].value.replace('bit<','').replace('>',''))
		total_req_meta+=meta_sizes[f.children[1].value]

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
for a in v2.stmts:
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
	if a in v2.conditionals:
		vc = Cond_reads()
		vc.visit(v2.conditionals[a])
		a_r+=vc.reads
		s_r+=vc.sym_reads
	if len(re)>0:
		stateful.append(a)
	reads.append(set(a_r))
	writes.append(set(a_w))
	if len(a_r) > 0 or len(a_w) > 0:
		meta_used_acts[a] = a_r+a_w
	regs.append(set(re))
	if len(re)>0:
		regs_used_acts[a]=re
	if a in v2.sym_stmts:
		sym_reads.append(set(s_r))
		sym_writes.append(set(s_w))
		sym_regs.append(set(s_re))
		if len(s_r) > 0 or len(s_w) > 0:
			sym_meta_used_acts[a] = list(set(s_r+s_w))	# convert to set then list just to remove dups
		if len(s_re)>0 and a not in stateful:
			stateful.append(a)
		if len(s_re) > 0:
			sym_regs_used_acts[a]=s_re

#print regs_used_acts

#print reads
#print writes
#print sym_reads
# for now, we're not recording what fields are causing the dependency, but we can easily add this later
deps = {}
# this is deps for NON SYMBOLIC fields
# if a symbolic action (aka in a loop) uses a NON symbolic meta field, we record the dep (bc we have to unroll the loop)
for a1 in v2.stmts:
	a1_i = v2.stmts.index(a1)
	for a2 in v2.stmts:
		a2_i = v2.stmts.index(a2)
		if a1 not in v2.sym_stmts and a2 not in v2.sym_stmts:
			if a1_i >= a2_i:
				continue
		elif a1_i > a2_i:
			continue
		# read after write
		if len(writes[a1_i].intersection(reads[a2_i])) > 0:
			deps[(a1,a2)]=1
			#continue
		# write after read
		if len(reads[a1_i].intersection(writes[a2_i])) > 0:
                        deps[(a1,a2)]=1
                        #continue
		# write after write
                if len(writes[a1_i].intersection(writes[a2_i])) > 0:
                        deps[(a1,a2)]=1
                        #continue
		# access same reg
		if len(regs[a1_i].intersection(regs[a2_i])) > 0:
			if (a1,a2) in deps:
				if a1==a2:
					print "ERROR: symbolic action %s accesses the same non-symbolic register in different iterations"%(a1)
					exit()
				print "ERROR: actions %s and %s access the same register but have a dependency"%(a1,a2)
				exit()
			deps[(a1,a2)]=3

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

#v4_w_set = set(v4.writes)
#v3_w_set = set(v3.writes)
#print list(v3_w_set.intersection(v4_w_set))

#print deps


# maybe we do this in ILP? so we don't have to read from resource file multiple times?
# we need to create mapping from action name to number (numbers used in ILP)
# number corresponds to order they appear in control
# we also need to expand for loop actions here (num stateless * num stgs)
# if action in both stmts and sym_stmts, we know it's in a loop
# we also add non-symbolic actions to the loop list here
act_num = 0
name_to_num = {}
num_to_name = {}
stateless_upper_bound = 10 # this is stateless ALUs * num stgs
stateful_upper_bound = 10	# this is stateful ALUs * num stgs
ilp_loops = []
for a in v2.stmts:
	# we have a symolic in a loop
	if a in v2.sym_stmts:
		name_to_num[a]=[]
		ub = stateless_upper_bound
		if a in stateful:	# make the upper bound a little smaller if we can
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

# get list of stateful actions that use numbers instead of name
ilp_stateful = []
for a in stateful:
	for a_n in name_to_num[a]:
		ilp_stateful.append(a_n)


# get list of hashes using act numbers
ilp_hashes = []
for a in hashes:
	for a_n in name_to_num[a]:
		ilp_hashes.append(a_n)

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



# keep track of actions that are in the same loop
loop_name = {}
# mapping symbolic value to action - this allows us to translate utility function that uses symbolic to util that uses ilp act vars
# we only count the first action in a loop for the utility function
# this shouldn't matter in the ILP bc we require that all acts in a loop get placed the same number of times
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

#print ilp_sym_to_act_num

# groups for ILP - actions that must be placed together
# these are the actions in the same iterations of loops indexed by same symbolic var
ilp_groups = []
for sym in loop_name:
	for a_i in range(len(name_to_num[loop_name[sym][0]])):	# this assumes ALL ACTS IN LOOP HAVE SAME UPPER BOUND! (not enforced yet!)
		curr_it = []
		for a in loop_name[sym]:
			curr_it.append(name_to_num[a][a_i])
		ilp_groups.append(curr_it)



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
			if "." in m:	# this is a header field, we're only looking at metadata
				continue
			curr_meta.append(m.replace('[i]',''))
			curr_meta_sizes.append(sym_meta_sizes[m.replace('[i]','')])
			break
		meta_num[a_n]=curr_meta
		if len(curr_meta)>0:
			ilp_meta.append(a_n)
			ilp_meta_sizes.append(sum(curr_meta_sizes))
# need reg width for each stateful symbolic action
# assume each stateful action uses at most one reg
# we save sym reg sizes as a tuple (width, instances)
# ILP just takes width for now, assumes instances is also symbolic (TODO: update this)
# ILP relies on this being ordered (same order as stateful actions, numerically increasing)
ilp_stateful.sort()
ilp_reg_inst = []
ilp_reg_width = []
# mapping symbolic value to reg size (by using the act num associated with each reg)
ilp_sym_to_reg_act_num = {}
sym_to_reg_width = {}
for a_n in ilp_stateful:
	a = num_to_name[a_n]
	# would do a loop here if more than one reg in action, but for now we allow only 1
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
	if a in regs_used_acts:
		if regs_used_acts[a][0] in v1.reg_inst:
			ilp_reg_width.append(int(v1.reg_widths[regs_used_acts[a][0]].replace('bit<','').replace('>','')))
			ilp_reg_inst.append(int(v1.reg_inst[regs_used_acts[a][0]]))
		elif regs_used_acts[a][0] in v1.sym_reg_inst:
			ilp_reg_width.append(int(v1.sym_reg_widths[regs_used_acts[a][0]].replace('bit<','').replace('>','')))
			ilp_reg_inst.append(-1)
			if v1.sym_reg_inst[regs_used_acts[a][0]] in ilp_sym_to_reg_act_num:
				ilp_sym_to_reg_act_num[v1.sym_reg_inst[regs_used_acts[a][0]]].append(a_n)
			else:
				ilp_sym_to_reg_act_num[v1.sym_reg_inst[regs_used_acts[a][0]]]=[a_n]


#print ilp_sym_to_reg_act_num

# stateful acts that share the same symbolic reg array
# the size (# instances) of each reg array must be the same (bc indexed on same sym value)
# assume sym reg arrays ALWAYS have sym instances - THIS IS NOT ALWAYS TRUE!!! (TODO: update this)
# assume that no two symbolic actions will access the same reg - NOT ALWAYS TRUE!!! (TODO: update this)
# assume that a sym actions access AT MOST one reg array (TODO: update this)
ilp_same_size = []
for a in sym_regs_used_acts:
	ilp_same_size.append(name_to_num[a])




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

#print v1.sym_reg_array_inst
#print sym_regs_used_acts


#print ilp_stateful
#print ilp_reg_width
#print ilp_reg_inst

#print ilp_sym_to_act_num

# regs w/ symbolic sizes are those in v1.sym_reg_inst and v1.sym_reg_array_inst
# will use sym_regs_used_acts and reg_used_acts to connect them to nums?


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
# we can do function calculation in here instead of ILP?? ilp really just needs list of x and y vals
# we need to replace switch_var with x - so we can easily apply the function
# for now, function should be in python syntax
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
stateful = 0

# replacing the switch_var with x in these functions to make it work with python better TODO: is there a way around this?
for c in v1.case_stmts:
	v1.case_stmts[c] = (v1.case_stmts[c][0].replace(v1.switch_var,"x"),v1.case_stmts[c][1])

if v1.switch_var in ilp_sym_to_reg_act_num:
	mem_var = 1
elif v1.switch_var in ilp_sym_to_act_num:
	act_var = 1
	if ilp_sym_to_act_num[0] in stateful:
		stateful = 1

ub = 0
# utility function on ilp memory variables, upper bound is max memory in stg
mem_per_stg = 1024
if mem_var:
	ub = mem_per_stg/sym_to_reg_width[v1.switch_var]


# utility function on ilp act vars, upper bound is max alus in stg
# CHECK IF STATELESS OR STATEFUL
elif stateful:
	ub = stateful_upper_bound	
else:
	ub = stateless_upper_bound

x_vals = list(range(0,ub,v1.step_size))
y_vals = []

for v in x_vals:
	if str(v) in v1.case_stmts:
		f = lambda x: eval(v1.case_stmts[str(v)][0])
		y_v = f(v)
		if v1.opt_keyword=="maximize":
			y_v = -1*y_v
		if v1.case_stmts[str(v)][1]:
			y_vals.append(y_v*1000000)
		else:
			y_vals.append(y_v)
		continue
	else:
		f = lambda x: eval(v1.case_stmts['default'][0])
		y_v = f(v)
                if v1.opt_keyword=="maximize":
                        y_v = -1*y_v
		if v1.case_stmts['default'][1]:
			y_vals.append(y_v*1000000)
		else:
			y_vals.append(y_v)
		continue

#print y_vals


with open("ilp_input.txt", "w") as f:
	f.writelines("%s " % s for s in ilp_stateful)		# numbers of acts that are stateful
	f.write("\n")
	f.writelines("%s " % m for m in ilp_meta)		# numbers of acts that use symbolic meta
        f.write("\n")
        f.writelines("%s " % ms for ms in ilp_meta_sizes)	# sizes of each instance of symbolic meta (corresponding to act nums)
        f.write("\n")	
	f.writelines("%s " % str(g).replace(" ","")  for g in ilp_groups)		# nums of acts in groups (acts that must ALL be placed - all or nothing)
	f.write("\n")
	f.writelines("%s " % str(l).replace(" ","") for l in ilp_loops)		# nums of acts in the same loop (not in loop - in list by itself)
	f.write("\n")
	f.write(str(ilp_deps))					# list of deps
	f.write("\n")
	# TODO: TCAM ACT NUMS
	f.write("\n")
	# TODO: TCAM SIZES
	f.write("\n")
	f.writelines("%s " % rw for rw in ilp_reg_width)	# width of each reg array (corresponding to stateful act nums)
	f.write("\n")
	f.write("1")						# utililty provided? TODO: get rid of this
	f.write("\n")	
	f.writelines("%s " % h for h in ilp_hashes) 		# nums of acts that hash
	f.write("\n")
	f.write(str(act_num))					# total number of acts we have
	f.write("\n")
	f.writelines("%s " % ss for ss in ilp_same_size)	# list of reg arrays that must have same num of instances
	f.write("\n")
	f.write(str(total_req_meta))				# the amount of phv that's non-symbolic (required)
	f.write("\n")
	f.writelines("%s " % ri for ri in ilp_reg_inst)		# number of instances for each reg array (correspond to stateful act nums)
	f.write("\n")
	if mem_var: 						# our util func applies to memory ILP vars
		f.write("mem\n")
		f.writelines("%s " % mv for mv in ilp_sym_to_reg_act_num[v1.switch_var])	# numbers that correspond to ILP vars that we use for util
	elif act_var:						# our util func applies to act ILP vars
		f.write("act\n")
		f.writelines("%s " % av for av in ilp_sym_to_act_num[v1.switch_var])	# numbers that correspond to ILP vars
	f.write("\n")
	f.writelines("%s " % xv for xv in x_vals)		# x values for PWL util
	f.write("\n")
	f.writelines("%s " % yv for yv in y_vals)		# y values for PWL util (util values)





