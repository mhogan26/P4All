from lark import Lark, Transformer, v_args


calc_grammar = """
    ?start: scalefun

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

    SCALE: "scale"
    MATH: "math"
    EXP: "exp"
    LAMBDA: "lambda"

    %import common.CNAME -> NAME
    %import common.NUMBER
    %import common.WS_INLINE

    %ignore WS_INLINE
"""


@v_args(inline=True)    # Affects the signatures of the methods
class InitTran(Transformer):
    def __init__(self):
        self.vars = {}
	self.linear=1
	self.num_vars=0
	self.scale=0

    #from operator import neg
    number = float

    def neg(self, a):
	return "-"+a

    def var(self, name):
	self.num_vars+=1
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
#	we know it's multivariate if symbolic includes range syntax/number of vars > 1

calc_parser = Lark(calc_grammar, parser='lalr')
#calc = calc_parser.parse

tree = calc_parser.parse("sum(1,kv_items,lambda x: (1/x))")
tran = InitTran()
print tran.transform(tree)
print tran.linear

