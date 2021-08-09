import sys
import pdb
import copy
import math
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
# ASSUMING THAT AN ACTION HAS AT MOST ONE HASH - SHOULD WE ALLOW FOR MORE?
# ^ BUT WITH REG ACTIONS
# ASSUME ONLY 1 STRUCT DEF (METADATA) - ALLOW MULTIPLE STRUCTS
# UPDATE SAME_SIZE TO ALLOW FOR MULT SYMBOLIC ACTIONS TO ACCESS THE SAME SYM REG ARRAY
# CHECK TODOs IN CODE
# error checking for python code???
# FIX TABLE CODE SO THAT META FIELDS CAN ALSO BE MATCHED IN TABLE?
# ACTION DEFINED ONCE BUT USED IN MULT TABLES - HOW TO DO THIS IN ILP?
# PRAGMAS??

# ASSUME STMTS THAT COMPARE 2 SYMBOLICS???
# DEP ANALYSIS UPPER BOUND (GRAPH WALK)
# IF SIMPLE UTIL, DON'T USE PWL
# TRANSFORM ASSUME STMTS INTO ILP CONSTRAINTS
# FOR LOOP IN CONDITIONAL???
# ADD TYPECASTING TO HASH_NUM -> (bit<32>)
# MARK TO DROP WRITES CERTAIN FIELDS
# ADD ARGUMENTS TO DROP FUNCTION
# ADD CASES WHERE WE CREATE MULT INSTANCES OF ILP AND PICK BEST (bloom filter)
# FIX PARSING TO WORK FOR UTILS W/O SWITCH STMTS
# UPDATE PARSING TO SUPPORT MULTIPLE UTIL FUNCS DEFINED
# ADD HEADER FIELDS TO META SIZE SECTION
# FIX UPPER BOUND: IF ONE ACT IN LOOP IS STATEFUL, THEN THEY'RE ALL BOUND BY THAT
# MULT LOOPS W/ DIFF SYM VALUE - DEP ANALYSIS WILL BE DIFFERENT (??)
# FIX sym_reg_array_decl - instances doesn't always have to be symbolic (could be fixed size) - ILP ALSO DOES THIS
from lark import Lark, Visitor, Token, Tree, Transformer, v_args
from lark.visitors import Visitor_Recursive

#from ilp_parse import *
from visit import *
from lark.reconstruct import Reconstructor


# control block vars

grammar = """
start: p4allprogram+
 
p4allprogram: topleveldecl
            | variabledecl
            | derivedtypedecl
            | includes
            | switch_main
            | switch_pipeline

topleveldecl: control_decl
            | utility_func
            | opt_expr

variabledecl: sym_decl
            | assume_stmt
            | define
            | type_def

derivedtypedecl: struct_decl
               | header_decl

includes: HT INCLUDE LESSTHAN NAME DOT P4 GREATERTHAN
        | HT INCLUDE DOUBLEQUOTE NAME DOT P4 DOUBLEQUOTE
struct_decl: STRUCT NAME LBRACE (sym_structfield|structfield)+ RBRACE 
header_decl: HEADER NAME LBRACE (sym_structfield|structfield)+ RBRACE

structfield: BIT_SIZE NAME SEMICOLON 
           | TYPENAME NAME SEMICOLON
sym_structfield: sym_size "[" NAME "]" NAME SEMICOLON 

sym_decl: SYMBOLIC NAME SEMICOLON
assume_stmt: ASSUME LPAREN a_expression RPAREN SEMICOLON

define: HT DEFINE CONST_NAME SIGNED_INT
type_def: TYPEDEF BIT_SIZE TYPENAME SEMICOLON

control_decl: CONTROL NAME LPAREN direction HDRT NAME COMMA direction METAT NAME COMMA direction I_IMETA NAME COMMA direction I_IPMETA NAME COMMA direction I_IDMETA NAME COMMA direction I_ITMETA NAME RPAREN LBRACE control_block RBRACE
            | CONTROL NAME LPAREN direction HDRT NAME COMMA direction METAT NAME COMMA direction E_IMETA NAME COMMA direction E_IPMETA NAME COMMA direction E_IDMETA NAME COMMA direction E_ITMETA NAME LBRACE control_block RBRACE

control_block: controllocaldecl* apply_block
controllocaldecl: action_decl
                | sym_action_decl
                | reg_decl
                | sym_reg_array_decl
                | reg_act_decl
                | sym_reg_act_decl
                | table_decl
                | hash_decl
                | sym_hash_decl
                | stage_pragma

action_decl: ACTION NAME LPAREN params* RPAREN LBRACE act_block_stmt+ RBRACE
sym_action_decl: ACTION NAME LPAREN RPAREN "[" "i" "]" LBRACE act_block_stmt+ RBRACE
reg_decl: REGISTER "<" BIT_SIZE COMMA "_" ">" LPAREN reg_depth RPAREN NAME SEMICOLON
sym_reg_array_decl: REGISTER "<" BIT_SIZE COMMA "_" ">" LPAREN reg_depth RPAREN "[" NAME "]" NAME SEMICOLON
reg_act_decl: REGACT "<" BIT_SIZE COMMA "_" COMMA BIT_SIZE ">" LPAREN NAME RPAREN NAME ASSIGN LBRACE reg_apply RBRACE SEMICOLON
sym_reg_act_decl: REGACT "<" BIT_SIZE COMMA "_" COMMA BIT_SIZE ">" LPAREN SYM_ARRAY_NAME RPAREN SYM_ARRAY_NAME ASSIGN LBRACE reg_apply RBRACE SEMICOLON
apply_block: APPLY "{" block_stmt+ "}"
table_decl: TABLE NAME LBRACE key actions size default? entries? RBRACE
hash_decl: HASH "<" BIT_SIZE ">" LPAREN algo RPAREN NAME SEMICOLON
sym_hash_decl: HASH "<" sym_size ">" LPAREN algo RPAREN "[" NAME "]" NAME SEMICOLON
stage_pragma: AT PRAGMA STAGE INT

sym_size: BIT_SIZE
        | sym_bit_size
sym_bit_size: "bit<" NAME ">"

reg_depth: INT
         | NAME

reg_apply: VOID APPLY LPAREN direction BIT_SIZE NAME COMMA direction BIT_SIZE NAME RPAREN LBRACE (assignment)+  RBRACE

direction: IN
         | OUT
         | INOUT 

params: (BIT_SIZE|NAME) NAME    -> type_param
      | params COMMA params     -> param_list

key: KEY ASSIGN LBRACE (lvalue COLON match_type SEMICOLON)+ RBRACE
actions: ACTIONS ASSIGN LBRACE (NAME SEMICOLON)+ RBRACE
size: SIZE ASSIGN (INT|NAME) SEMICOLON
default: DEFAULT_ACTION ASSIGN NAME LPAREN RPAREN SEMICOLON
entries: CONST ENTRIES ASSIGN LBRACE entry+ RBRACE
entry: LPAREN? match RPAREN? COLON method_call 
match: HEX (INT|LETTER)+ 
     | match COMMA match
match_type: EXACT
          | TERNARY
          | LPM

act_block_stmt: method_call
              | sym_method_call
              | assignment
              | reg_act_exec
              | sym_reg_act_exec
              | hash_func
              | sym_hash_func
              | drop

block_stmt: conditional
          | method_call
          | for_loop
          | sym_method_call
          | assignment
          | reg_act_exec
          | sym_reg_act_exec
          | hash_func
          | sym_hash_func
          | table_apply
          | drop

drop: DROP LPAREN RPAREN SEMICOLON
conditional: IF LPAREN expression RPAREN LBRACE block_stmt+ RBRACE (ELSE IF LPAREN expression RPAREN LBRACE block_stmt+ RBRACE)* (ELSE LBRACE block_stmt+ RBRACE)?


method_call: lvalue LPAREN RPAREN SEMICOLON
sym_method_call: lvalue LPAREN RPAREN "[" "i" "]" SEMICOLON
for_loop: FOR LPAREN "i" LESSTHAN NAME RPAREN LBRACE block_stmt+ RBRACE 
assignment: lvalue ASSIGN expression SEMICOLON

reg_act_exec: lvalue ASSIGN NAME DOT EXECUTE LPAREN index_field RPAREN SEMICOLON
sym_reg_act_exec: lvalue ASSIGN SYM_ARRAY_NAME DOT EXECUTE LPAREN index_field RPAREN SEMICOLON

table_apply: NAME DOT APPLY LPAREN RPAREN SEMICOLON
hash_func: lvalue ASSIGN NAME DOT GET LPAREN hash_list RPAREN SEMICOLON
sym_hash_func: lvalue ASSIGN NAME "[" "i" "]" DOT GET LPAREN hash_list RPAREN SEMICOLON

utility_func: OPTIMIZE NAME LBRACE function step? RBRACE

opt_expr: opt func SEMICOLON

opt: MAXIMIZE
   | MINIMIZE

function: FUNCTION COLON func SEMICOLON

step: STEP COLON INT SEMICOLON

func: scalefun

?scalefun: sum 
    | SCALE "(" sum ")" 
?sum: exp
    | sum "+" exp   -> add
    | sum "-" exp   -> sub

?exp: summation
    | MATH "." EXP atom

?summation: product
    | "sum" "(" atom "," atom "," LAMBDA NAME ":" atom ")"

?product: atom
    | product "*" atom  -> mul
    | product "/" atom  -> div
    | product "**" atom -> pow
?atom: NUMBER           -> number
     | "-" atom         -> neg
     | NAME             -> var
     | "(" sum ")"

lvalue: NAME                                    -> nonsym_l
      | SYM_ARRAY_NAME                          -> sym_l
      | meta DOT META_NAME                      -> nonsymmeta_l
      | meta DOT SYM_ARRAY_NAME                 -> symmeta_l
      | HDR DOT HDR_NAME DOT HDR_FIELD          -> nonsymhdr_l
      | HDR DOT HDR_NAME DOT SYM_ARRAY_NAME     -> symhdr_l

expression: INT                                                 -> e_int
          | HEX (INT|LETTER)+                                   -> e_hex
          | TRUE                                                -> e_true
          | FALSE                                               -> e_false
          | hdr_valid
          | expression PLUS expression                          -> e_plus
          | expression MINUS expression                         -> e_minus
          | NAME                                                -> e_name
          | SYM_ARRAY_NAME                                      -> e_symname
          | meta DOT META_NAME                                  -> e_meta
          | meta DOT SYM_ARRAY_NAME                             -> e_symmeta
          | HDR DOT HDR_NAME DOT HDR_FIELD (LPAREN RPAREN)?     -> e_hdr
          | HDR DOT HDR_NAME DOT SYM_ARRAY_NAME (LPAREN RPAREN)?     -> e_symhdr
          | expression LPAREN RPAREN                            -> e_p
          | expression LESSTHAN expression                      -> e_less
          | expression GREATERTHAN expression                   -> e_greater
          | expression EQ expression                            -> e_eq
          | expression NEQ expression                           -> e_neq
          | expression OR expression                            -> e_or
          | expression AND expression                           -> e_and
          | table_hit
          | table_miss
          | min
          | max

min: MIN LPAREN lvalue COMMA lvalue RPAREN
max: MAX LPAREN lvalue COMMA lvalue RPAREN 


a_expression: INT                                               -> intexp
            | NAME                                              -> nexp
            | a_expression EQ a_expression                      -> eexp
            | a_expression LESSTHAN ASSIGN a_expression         -> lexp
            | a_expression GREATERTHAN ASSIGN a_expression      -> gexp

hdr_valid: HDR DOT HDR_NAME DOT VALID
table_hit: table_apply DOT HIT
table_miss: table_apply DOT MISS

index_field: NAME                                       -> i_name
           | SYM_ARRAY_NAME                             -> i_symname
           | meta DOT META_NAME                         -> i_meta
           | meta DOT SYM_ARRAY_NAME                    -> i_symmeta
           | HDR DOT HDR_NAME DOT HDR_FIELD             -> i_hdr
           | HDR DOT HDR_NAME DOT SYM_ARRAY_NAME        -> i_symhdr
           | INT                                        -> i_int

hash_list: LBRACE hash_fields RBRACE 

hash_fields: meta DOT META_NAME                         -> nonsymmeta
           | meta DOT SYM_ARRAY_NAME                    -> symmeta
           | HDR DOT HDR_NAME DOT HDR_FIELD             -> nonsymhdr
           | HDR DOT HDR_NAME DOT SYM_ARRAY_NAME        -> symhdr
           | hash_fields COMMA hash_fields              -> hlist
           | GET_SEED                                   -> seed
           | SIGNED_INT                                 -> s_int

algo: HASH_A DOT IDENTITY
    | HASH_A DOT RANDOM
    | HASH_A DOT CRC8
    | HASH_A DOT CRC16
    | HASH_A DOT CRC32
    | HASH_A DOT CRC64
    | HASH_A DOT CUSTOM

switch_pipeline: PIPELINE LPAREN NAME LPAREN RPAREN COMMA NAME LPAREN RPAREN COMMA NAME LPAREN RPAREN COMMA NAME LPAREN RPAREN COMMA NAME LPAREN RPAREN COMMA NAME LPAREN RPAREN RPAREN NAME SEMICOLON
switch_main: SWITCH LPAREN NAME RPAREN MAIN SEMICOLON

meta: IG_META
    | EG_META
    | IG_INT_META
    | EG_INT_META
    | IG_PAR_META
    | EG_PAR_META
    | IG_DEP_META
    | EG_DEP_META
    | IG_TM_META
    | EG_TM_META


TYPEDEF: "typedef"
SYMBOLIC: "symbolic"
CONTROL: "control"
VOID: "void"
APPLY: "apply"
ACTION: "action"
REGISTER: "Register"
REGACT: "RegisterAction"
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
IG_META: "ig_md"
EG_META: "eg_md"
IG_INT_META: "ig_intr_md"
EG_INT_META: "eg_intr_md"
IG_PAR_META: "ig_prsr_md"
EG_PAR_META: "eg_prsr_md"
IG_DEP_META: "ig_dprsr_md"
EG_DEP_META: "eg_dprsr_md"
IG_TM_META: "ig_tm_md"
EG_TM_META: "eg_tm_md"
HASH: "Hash"
HASH_A: "HashAlgorithm_t"
IDENTITY: "IDENTITY"
RANDOM: "RANDOM"
CRC8: "CRC8"
CRC16: "CRC16"
CRC32: "CRC32"
CRC64: "CRC64"
CUSTOM: "CUSTOM"
LBRACE: "{"
RBRACE: "}"
HT: "#"
DEFINE: "define"
SIGNED_INT: INT ("w"|"s") INT
CONST_NAME: NAME
LESSTHAN: "<"
GREATERTHAN: ">"
DOUBLEQUOTE: /"/
HDR: "hdr"
MAXIMIZE: "maximize"
MINIMIZE: "minimize"
FUNCTION: "function"
STEP: "step"
DEFAULT: "default"
CASE: "case"
SCALE: "scale"
MATH: "math"
EXP: "exp"
LAMBDA: "lambda"
TABLE: "table"
EQ: "=="
DEFAULT_ACTION: "default_action"
ACTIONS: "actions"
KEY: "key"
EXACT: "exact"
TERNARY: "ternary"
LPM: "lpm"
SIZE: "size"
DROP: "mark_to_drop"
ELSE: "else"
HIT: "hit"
MISS: "miss"
NEQ: "!="
AND: "&&"
OR: "||"
VALID: "isValid()"
ASSUME: "assume"
GET: "get"
IN: "in"
OUT: "out"
INOUT: "inout"
EXECUTE: "execute"
MIN: "min"
MAX: "max"
OPTIMIZE: "optimize"
META_NAME: NAME
SYM_ARRAY_NAME: NAME "[" "i" "]"
BIT_SIZE: "bit" "<" INT ">"
TYPENAME: NAME
HDR_NAME: NAME
HDR_FIELD: NAME
CONST: "const"
ENTRIES: "entries"
INCLUDE: "include"
P4: "p4"
PIPELINE: "Pipeline"
SWITCH: "Switch"
MAIN: "main"
HDRT: "header_t"
METAT: "metadata_t"
I_IMETA: "ingress_intrinsic_metadata_t"
E_IMETA: "egress_intrinsic_metadata_t"
I_IPMETA: "ingress_intrinsic_metadata_from_parser_t"
E_IPMETA: "egress_intrinsic_metadata_from_parser_t"
I_IDMETA: "ingress_intrinsic_metadata_for_deparser_t"
E_IDMETA: "egress_intrinsic_metadata_for_deparser_t"
I_ITMETA: "ingress_intrinsic_metadata_for_tm_t"
E_ITMETA: "egress_intrinsic_metadata_for_tm_t"
GET_SEED: "get_seed()"
AT: "@"
PRAGMA: "pragma"
STAGE: "stage"
HEX: "0x"

%import common.CNAME -> NAME
%import common.WS
%import common.WORD
%import common.LETTER
%import common.INT
%import common.CPP_COMMENT
%import common.NUMBER
%import common.LETTER
%ignore WS
%ignore CPP_COMMENT

"""

# NAME: (WORD|"_") (LETTER|INT|"_")*

p = Lark(grammar,parser="earley")

unroll = False

concretes = {}

if len(sys.argv) > 2:   # we're unrolling the p4all program --> p4 code
        unroll = True
        for i in range(2,len(sys.argv)):
                if i%2==0:      # name of symbolic
                        concretes[sys.argv[i]] = 0
                else:           # concrete val
                        concretes[sys.argv[i-1]] = int(sys.argv[i])

with open(sys.argv[1], 'r') as file:
    data = file.read()

# parse takes string as input
parse_tree = p.parse(data)
#print( parse_tree.pretty() )
#print parse_tree

#if not unroll:
#       ilp_parse(parse_tree)
#       exit()

#print( parse_tree.pretty() )
remove_sym = SymTran(concretes)
no_sym = remove_sym.transform(parse_tree)
#remove_sym_acts = SymActUnroll(remove_sym.lines, remove_sym.con_acts, remove_sym.acts_post, remove_sym.acts_index)
#remove_sym_acts.unroll()
#for i in remove_sym.lines:
#        print i,

li = []
with open('p4src/cms/parsers_temp.p4','r') as f:
    li = f.readlines()
    for l in li:
        if "//METAS" in l:
            li[li.index(l)+1] = ''.join(remove_sym.metas)

    #print li
    #f.writelines(li)
with open('p4src/cms/parsers.p4','w') as f:
    for l in li:
        f.write(l)


lines = ''.join(remove_sym.lines)
with open(sys.argv[1].replace(".p4all",".p4"),'w+') as f:
    f.write(lines)


# to generate p4 code:
# remove symbolic declarations and assume statements
# remove utility function/simulation record
# unroll symbolic metadata arrays / replace symbolic meta sizes
# (unroll symbolic header field arrays?)
# unroll symbolic hash declarations
# unroll symbolic actions that use hashes
# unroll symbolic reg arrays / replace symbolic reg instances
# unroll symbolic reg actions
# unroll actions that use symbolic reg actions
# unroll symbolic actions
# unroll symbolic tables
# unroll for loops in apply block


