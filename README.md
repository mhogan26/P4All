# P4All

Input: P4All file (with or without symbolic values) + specification of hardware resources

Compiler steps: parse p4all file to get info described below, determine dependencies, run ILP, use ILP solution (concrete values) to create layout or unrolled p4 program

ILP needs: objective function, list of stateful actions (that use register arrays), list of actions that use metadata, the amount of metadata each action requires (in bits), list of groups (actions that must be placed together - all or nothing), list of actions in symbolic loops and not in loops, dependencies between actions, actions that require TCAM and the size of the TCAM table (-1 is symbolic), width of register arrays, actions that use hashing, total number of actions, list of symbolic register arrays that must be same size, size of non-symbolic phv, sizes of register arrays (-1 is symbolic), which variables to apply objective function to, objective function values


Utility function is written as a record with two parts: function and step (optional). Function can be single line or can be a switch statement, defining different functions for specific values. Function should be written in (limited) python syntax[+, -, *, /, \*\*, math.exp, sum(lo,hi,lambda func)].


Assume statements: [<=, >=, ==] (to match the comparators allowed by Gurobi), one expression per statement, only one symbolic per expression, expressions can only include a symbolic and an integer
