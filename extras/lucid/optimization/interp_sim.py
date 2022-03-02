import subprocess, json, math, pickle, time
from optalgos import *

# this function runs interpreter with whatever symb file is in directory and returns measurement of interest
def interp_sim(lucidfile,outfiles):
    # run the interpreter
    cmd = ["../../dpt", "--suppress-final-state", lucidfile]

    #with open('output.txt','w') as outfile:
    #    ret = subprocess.run(cmd, stdout=outfile, shell=True)
    ret = subprocess.run(cmd)
    if ret.returncode != 0: # stop if there's an error running interp
        print("err")
        quit()


    # get output from interpreter
    # we might have multiple files, so we loop through and store measurements from all of them
    measurement = []
    for out in outfiles:
        measurement.append(pickle.load(open(out,"rb")))

    '''
    # OLD
    # get the measurement output by interpreter (reg array)
    measurement = []
    lastline = ""
    pipeline = False
    with open('output.txt','r') as datafile:
        # skip until we get to the Pipeline line
        # for cms example, we always want the last reg in the pipeline
        lines = datafile.readlines()
        for line in lines:
            if "Pipeline" in line:
                pipeline = True
                lastline = line
                continue
            if pipeline:
                if line.strip()=="]":   # end of reg output, so the last line has the measurement reg
                    measurement=ast.literal_eval(lastline.split(':')[1].replace(';',',').replace("u32","").strip())
                    break
                lastline=line

    '''
    return measurement

'''
# we need both of these for simulated annealing
# (not necessary to use sim annealing, can use any optimization)
# new represents the concretes/measurements from most recent test
# curr is used to choose next solution, we set curr = new w/ some probability based on the costs
# (^ specific to simulated annealing)
curr_cost = 0
new_cost = 0
curr_sol = best_sol
new_sol = best_sol
# sim annealing params
temp=100
# bounds and step_size determine how far we move each iteration
bounds=[1,5]
step_size=[1,1]
# keep track of top x (2) solutions to see if they compile
top_sols = [best_sol, best_sol]

while True:
    # sim annealing
    # we need at least 2 data points for sim annealing, so if it's first iteration just randomly choose next one
    if iterations < 1:
        best_cost = new_cost
        curr_cost = new_cost
        cols,rows = sim_move()
        new_sol = [rows,cols]
        write_symb(rows,cols)
        # let's keep this list sorted by total memory used (rows*cols)
        if rows*cols <= best_sol[0]*best_sol[1]:
            top_sols[0] = new_sol
        else:
            top_sols[1] = new_sol
        iterations += 1
        continue
    # we have at least 2 data points, so can do sim annealing
    curr_sol, curr_cost, new_sol, best_sol, best_cost, temp = simulated_annealing_step(curr_sol,curr_cost,new_sol,new_cost,best_sol,best_cost,temp,iterations,step_size,bounds)
    write_symb(new_sol[0],new_sol[1])
    # if the best solution uses less total mem than what's stored in top_sols, replace (or add)
    if best_sol[0]*best_sol[1] < top_sols[0][0]*top_sols[0][1]:
        top_sols[1] = top_sols[0]
        top_sols[0] = best_sol
    elif best_sol[0]*best_sol[1] < top_sols[1][0]*top_sols[1][1]:
        top_sols[1] = best_sol
    iterations += 1
    # random
    if iterations < 1:
        best_cost = new_cost
        while (rows,cols) in tested_sols:   # don't test the same sols
            cols,rows = sim_move()
        best_sol = [rows,cols]
        write_symb(rows,cols)
        iterations += 1
        continue

    #if (new_cost < best_cost) or (new_cost==best_cost and rows*cols <= best_sol[0]*best_sol[1]):
    if (new_cost < best_cost) or (new_cost==best_cost and cols <= best_sol[1]):
        best_cost = new_cost
        best_sol = [rows,cols]

    while (rows,cols) in tested_sols:   # don't test the same sols
        cols,rows = sim_move()
    tested_sols.append((rows,cols))
    write_symb(rows,cols)
    iterations += 1
    '''


def write_symb(sizes, symbolics, logs, symfile):
    # we often have symbolics that should = log2(some other symbolic)
    # in that case, we compute it here
    for var in logs:
        if logs[var] in sizes:
            log = int(math.log2(sizes[logs[var]]))
        else:
            log = int(math.log2(symbolics[logs[var]]))
        if var in sizes:
            sizes[var] = log
        else:
            symbolics[var] = log
    concretes = {}
    concretes["sizes"] = sizes
    concretes["symbolics"] = symbolics
    with open(symfile, 'w') as f:
        json.dump(concretes, f, indent=4)


def update_sym_sizes(symbolics_opt, sizes, symbolics):
    for var in symbolics_opt:
        if var in sizes:
            sizes[var] = symbolics_opt[var]
            continue
        if var in symbolics:
            symbolics[var] = symbolics_opt[var]
    return sizes, symbolics

def gen_cost(symbolics_opt_vars,syms_opt, opt_info, o, scipyalgo):
    # if scipyalgo is true, then symolics_opt is np array, not dict
    print("VARS")
    print(symbolics_opt_vars)
    if scipyalgo:
        symbolics_opt = {}
        sym_keys = list(syms_opt.keys())
        for v in range(len(symbolics_opt_vars)):
            symbolics_opt[sym_keys[v]] = int(symbolics_opt_vars[v])
    else:
        symbolics_opt = symbolics_opt_vars
    # gen symbolic file
    update_sym_sizes(symbolics_opt, opt_info["symbolicvals"]["sizes"], opt_info["symbolicvals"]["symbolics"]) # python passes dicts as reference, so this is fine
    write_symb(opt_info["symbolicvals"]["sizes"],opt_info["symbolicvals"]["symbolics"],opt_info["symbolicvals"]["logs"],opt_info["symfile"])

    # compile to p4 (once new memops implemented) and check if stgs <= tofino --> what to return if it takes too many stgs/doesn't compile? inf cost? boolean?

    # call init_iteration for opt class
    o.init_iteration(symbolics_opt)

    # run interp!
    m = interp_sim(opt_info["lucidfile"],opt_info["outputfiles"])

    # pass measurement(s) to cost func, get cost of sol
    cost = o.calc_cost(m)

    return cost






