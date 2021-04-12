# P4All

Input: P4All file (with or without symbolic values) + specification of hardware resources

Compiler steps: parse p4all file to get info described below, parse/determine dependencies, run ILP, use ILP solution (concrete values) to create layout or unrolled p4 program

ILP needs: utility function, upper bound on each symbolic value, list of stateful actions (that use register arrays), list of actions that use metadata, the amount of metadata each action requires (in bits), list of groups (actions that must be placed together - all or nothing), list of actions in symbolic loops and not in loops, dependencies between actions, actions that require TCAM and the size of the TCAM table


Utility function is written as a record with two parts: function and step (optional). Function can be single line or can be a switch statement, defining different functions for specific values. Function should be written in (limited) python syntax[+, -, *, /, \*\*, math.exp, sum(lo,hi,lambda func)].


Assume statements: [<=, >=, ==] (to match the comparators allowed by Gurobi), one expression per statement
