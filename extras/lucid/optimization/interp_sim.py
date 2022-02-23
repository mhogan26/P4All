import sys, subprocess, os, ast, json, math, pickle, time, importlib, copy
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
'''
end_time = time.time()
print("BEST:")
print(best_sol)
print("TIME(s):")
print(end_time-start_time)
'''
# we test the top x solutions to see if they compile --> if they do, we're done!
# else, we can repeat above loop, excluding solutions we now know don't compile
# (we have to have a harness p4 file for this step, but not for interpreter)
# for now, we have a second lucid program that doesn't have interpreter sim measurements, this is the version we want to compile to tofino
# NOTE: use vagrant vm to compile
'''
for sol in top_sols:
    write_symb(sol[0],sol[1])
    # compile lucid to p4
    cmd_lp4 = ["../../dptc cms_sym_nomeasure.dpt ip_harness.p4 linker_config.json cms_sym_build --symb cms_sym.symb"]
    ret_lp4 = subprocess.run(cmd_lp4, shell=True)
    # we shouldn't have an issue compiling to p4, but check anyways
    if ret_lp4.returncode != 0:
        print("error compiling lucid code to p4")
        break
    # compile p4 to tofino
    cmd_tof = ["cd cms_sym_build; make build"]
    ret_tof = subprocess.run(cmd_tof, shell=True)
    # return value of make build will always be 0, even if it fails to compile
    # how can we check if it compiles????

    # if compiles, break bc we've found a soluion
'''


def write_symb(sizes, symbolics, logs):
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
    with open('cms_sym.symb', 'w') as f:
        json.dump(concretes, f, indent=4)


def update_sym_sizes(symbolics_opt, sizes, symbolics):
    for var in symbolics_opt:
        if var in sizes:
            sizes[var] = symbolics_opt[var]
            continue
        if var in symbolics:
            symbolics[var] = symbolics_opt[var]


# usage: python3 interp_sim.py <json opt info file>
def main():
    # import json file
    opt_info = json.load(open(sys.argv[1]))

    # write init symb file
    sizes = opt_info["symbolicvals"]["sizes"]
    symbolics = opt_info["symbolicvals"]["symbolics"]
    logs = opt_info["symbolicvals"]["logs"]
    write_symb(sizes,symbolics,logs)

    # import opt class that has funcs we need to get traffic, cost
    optmod = importlib.import_module(opt_info["optmodule"])
    o = optmod.Opt(opt_info["trafficpcap"])

    # gen traffic
    o.gen_traffic()

    # init vars for interp loop
    iterations = 0
    # it's easier for gen next values if we exclude logs and don't separate symbolics/sizes, so let's do that here
    symbolics_opt = {}
    # is there a better way to merge? quick solution for now
    for var in sizes:
        if var not in logs:
            symbolics_opt[var] = sizes[var]
    for var in symbolics:
        if var not in logs:
            symbolics_opt[var] = symbolics[var]
    # init best solution as starting, and best cost as inf
    best_sol = copy.deepcopy(symbolics_opt)
    best_cost = float("inf")
    # keep track of sols we've already tried so don't repeat
    tested_sols = []
    # decide if we're stopping by time, iterations, or both (whichever reaches thresh first)
    iters = False
    simtime = False
    iter_time = False
    if "stop_iter" in opt_info:
        iters = True
    if "stop_time" in opt_info:
        simtime = True
    if iters and simtime:
        iter_time = True
    # decide if we're using a builtin algo, or user-provided
    random = False
    simanneal = False
    user = False
    if "optalgofile" in opt_info:   # only include field in json if using own algo
        user = True
    elif opt_info["optalgo"] == "random":    # if not using own, should for sure have optalgo field
        random = True
    elif opt_info["optalgo"] == "simannealing":
        simanneal = True
    bounds = opt_info["symbolicvals"]["bounds"]

    # start loop
    start_time = time.time()
    while True:
        # check iter/time conditions
        if iters or iter_time:
            if iterations >= opt_info["stop_iter"]:
                break
        if simtime or iter_time:
            if (time.time()-start_time) >= opt_info["stop_time"]:
                break

        # call init_iteration for opt class
        o.init_iteration()

        # run interp!
        m = interp_sim(opt_info["lucidfile"],opt_info["outputfiles"])

        # pass measurement(s) to cost func, get cost of sol
        cost = o.calc_cost(m)

        # add sol to tested_sols to count it as already evaluated
        # is it stupid to do deepcopy here? can we be smarter about changing symbolics_opt to avoid this? or is it a wash?
        tested_sols.append(copy.deepcopy(symbolics_opt))

        # compile to p4 (once new memops implemented) and check if stgs <= tofino
        # if new cost < best, replace best (if stgs <= tofino)
        if cost < best_cost:
            best_cost = cost
            # not sure if this is slow, but these dicts are likely small (<10 items) so shouldn't be an issue
            best_sol = copy.deepcopy(symbolics_opt)

        # gen next concrete vals and write the symb file
        #symbolics_opt["cols"] = 32
        #symbolics_opt["rows"] = 1
        # if using our builtins, call appropriate func here
        # else, call user's code
        # pass in tested_sols? or handle that here?
        # either case should be updating symbolics_opt --> symbolics_opt = FUNCALL
        # be careful with how we set symbolics_opt in function, bc we don't want it to change what's in tested_sols
        # should be ok though if we have deepcopy when we add to tested_sols
        symbolics_opt = random_opt(symbolics_opt, logs, bounds)
        update_sym_sizes(symbolics_opt, sizes, symbolics) # python passes dicts as reference, so this is fine
        write_symb(sizes, symbolics, logs)

        # incr iterations
        iterations += 1


if __name__ == "__main__":
    main()



'''
json fields:
    symbolicvals:
        sizes: symbolic sizes and starting vals
        symbolics: symbolic vals (ints, bools) and starting vals
        logs: which (if any) symbolics are log2(another symbolic)
        bounds: [lower,upper] bounds for symbolics (don't need to include logs, bc they're calculated from other syms)
    symfile: file to write symbolics to
    lucidfile: dpt file
    outputfiles: list of files that output is stored in (written to by externs)
    stop_iter: num iterations to stop at
    stop_time: time to stop at (in seconds)
    optalgo: if using one of our provided functions, tell us the name
    optalgofile: if using your own, tell us where to find it (python file)
    optmodule: name of module that has class w/ necessary funcs
    trafficpcap: name of pcap file to use
'''





