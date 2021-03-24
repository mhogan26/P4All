from ark import Lark, Transformer, v_args


calc_grammar = """
    ?start: scalefun

    ?scalefun: sum 
	  | SCALE "(" sum ")" 

    ?sum: exp
        | sum "+" exp   -> add
        | sum "-" exp   -> sub

    ?exp: product
        | MATH "." EXP atom

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


# add summation (is summation PWL??)
# if not PWL, need to return equation but with var replaced with ILP vars (quicksum of something?)
# if multivariate, need to create mult ilp instances
#	we know it's multivariate if symbolic includes range syntax/number of vars > 1

calc_parser = Lark(calc_grammar, parser='lalr')
#calc = calc_parser.parse

tree = calc_parser.parse("scale((1-math.exp(-hashes*100/bits))**hashes)")
tran = InitTran()
print tran.transform(tree)
print tran.linear

