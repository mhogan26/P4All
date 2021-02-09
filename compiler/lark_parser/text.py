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
# ADD CONST VARS TO CONTROL BLOCK
# ALLOW TYPEDEFS TO BE USED IN SYMBOLIC HEADER FIELDS?

# ADD HEADER FIELDS TO DEPS ( not just meta fields )
# ADD HEADER FIELDS TO HASH FIELDS
# MULT LOOPS W/ DIFF SYM VALUE - DEP ANALYSIS WILL BE DIFFERENT (??)
# FIX sym_reg_array_decl - instances doesn't always have to be symbolic (could be fixed size)
from lark import Lark, Visitor, Token, Tree
from lark.visitors import Visitor_Recursive

# control block vars

grammar = """
start: p4allprogram+
 
p4allprogram: topleveldecl
	    | variabledecl
	    | derivedtypedecl

topleveldecl: control_decl

variabledecl: sym_decl
	    | define
	    | type_def

derivedtypedecl: struct_decl
	       | header_decl


struct_decl: STRUCT NAME "{" (sym_structfield|structfield)+ "}" 
header_decl: HEADER NAME "{" (sym_structfield|structfield)+ "}"

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
for_loop: FOR LPAREN "i" "<" NAME RPAREN "{" block_stmt+ "}" 
assignment: lvalue ASSIGN expression SEMICOLON
reg_write: NAME DOT WRITE LPAREN index_field COMMA read_field RPAREN SEMICOLON
reg_read: NAME DOT READ LPAREN write_field COMMA index_field RPAREN SEMICOLON
sym_reg_write: SYM_ARRAY_NAME DOT WRITE LPAREN index_field COMMA read_field RPAREN SEMICOLON
sym_reg_read: SYM_ARRAY_NAME DOT READ LPAREN write_field COMMA index_field RPAREN SEMICOLON
hash_func: HASH LPAREN index_field COMMA algo COMMA hash_num COMMA hash_list COMMA hash_num RPAREN SEMICOLON

lvalue: NAME
      | SYM_ARRAY_NAME
      | lvalue DOT META_NAME 
      | lvalue DOT SYM_ARRAY_NAME

expression: INT
	  | TRUE
          | FALSE
          | expression PLUS expression
          | expression MINUS expression
	  | NAME
	  | SYM_ARRAY_NAME
	  | expression DOT META_NAME
          | expression DOT SYM_ARRAY_NAME
          | expression LPAREN RPAREN 
	  | expression LESSTHAN expression
	  | expression GREATERTHAN expression

write_field: NAME
           | SYM_ARRAY_NAME
           | META DOT META_NAME 
           | META DOT SYM_ARRAY_NAME

read_field: NAME
          | SYM_ARRAY_NAME
          | META DOT META_NAME 
          | META DOT SYM_ARRAY_NAME
	  | INT

index_field: NAME
           | SYM_ARRAY_NAME
           | META DOT META_NAME 
           | META DOT SYM_ARRAY_NAME

hash_num: CONST_NAME
	| SIGNED_INT

hash_list: LBRACE hash_fields RBRACE 

hash_fields: META DOT META_NAME
	   | META DOT SYM_ARRAY_NAME
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

NAME: (WORD|"_") (LETTER|INT|"_")*
META_NAME: NAME
SYM_ARRAY_NAME: NAME "[" "i" "]"
BIT_SIZE: "bit" "<" INT ">"
REG_DEPTH: INT
SYM_REG_DEPTH: NAME
TYPENAME: NAME

%import common.WS
%import common.WORD
%import common.LETTER
%import common.INT
%import common.CPP_COMMENT
%ignore WS
%ignore CPP_COMMENT

"""

p = Lark(grammar,parser="earley")



with open('t.txt', 'r') as file:
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
	def __default__(self,tree):
		if tree.data=="action_decl":
			self.action_defs[tree.children[1].value]=tree.children[4:]
		elif tree.data=="sym_action_decl":
			self.action_defs[tree.children[1].value]=tree.children[4:]
		elif tree.data=="apply_block":
			self.apply.append(tree)
class V_r2(Visitor_Recursive):
	def __init__(self, a_d):
		self.stmts = []
		self.sym_stmts = []
		self.loop_stmts = []
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
	def __init__(self):
		self.reads = []
		self.writes = []
		self.sym_reads = []
		self.sym_writes = []
		self.regs = []
		self.sym_regs = []
	def __default__(self,tree):
		# check lvalue to find meta fields we're writing to
		if tree.data=="lvalue":
			if isinstance(tree.children[0],Tree) and tree.children[0].children[0].value=="meta":
				if tree.children[2].type=="META_NAME":
					self.writes.append(tree.children[2].value)
				if tree.children[2].type=="SYM_ARRAY_NAME":
					self.sym_writes.append(tree.children[2].value)
		# check to see if we're reading from meta fields
		if tree.data=="expression":
			if isinstance(tree.children[-1],Token): 
				if tree.children[-1].type=="META_NAME":
					self.reads.append(tree.children[-1].value)	
				if tree.children[-1].type=="SYM_ARRAY_NAME":
					self.sym_reads.append(tree.children[-1].value) 
		# checking what meta fields we use w/ reg writes and reads
		if tree.data=="index_field":
			if tree.children[2].type=="META_NAME":
				self.reads.append(tree.children[2].value)
			# if we have symbolic index field instead of regular meta
			if tree.children[2].type=="SYM_ARRAY_NAME":
				self.sym_reads.append(tree.children[2].value)
		if tree.data=="read_field":
			if tree.children[0].type=="META":
                                self.reads.append(tree.children[2].value)
		if tree.data=="write_field":
			if tree.children[0].type=="META":
                                self.writes.append(tree.children[2].value)
		# check to see what regs we read from/write to - acts that access same reg MUST be in same stg
		if tree.data=="reg_write" or tree.data=="reg_read":
			self.regs.append(tree.children[0].value)
		if tree.data=="sym_reg_write" or tree.data=="sym_reg_read":
                        self.sym_regs.append(tree.children[0].value)

		# check to see what fields we use for hashing
		if tree.data=="hash_fields" and isinstance(tree.children[2],Token):
			if tree.children[2].type=="META_NAME":
				self.reads.append(tree.children[2].value)
			if tree.children[2].type=="SYM_ARRAY_NAME":
				self.sym_reads.append(tree.children[2].value)
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
	
v2 = V_r2(v1.action_defs)
v2.visit(v1.apply[0])	# assuming we only have one apply block in the v1.apply list
#print v2.stmts
#print v2.conditionals

'''
v3 = Act_reads_writes()
v3.visit(v1.action_defs['x'])
print v3.writes
print v3.reads
v4 = Act_reads_writes()
v4.visit(v1.action_defs['t'])
'''

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
for a in v2.stmts:
	a_r = []
	a_w = []
	s_r = []
	s_w = []
	re = []
	s_re = []
	for e in v1.action_defs[a]:
		v = Act_reads_writes()
		v.visit(e)
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
	reads.append(set(a_r))
	writes.append(set(a_w))
	regs.append(set(re))
	if a in v2.sym_stmts:
		sym_reads.append(set(s_r))
		sym_writes.append(set(s_w))
		sym_regs.append(set(s_re))

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

print deps




