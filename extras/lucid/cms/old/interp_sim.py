import subprocess, os, ast, json, math, pickle, time
from move import *
from traffic import *


# this function runs interpreter with whatever symb file is in directory and returns measurement of interest
def interp_sim(lucidfile,outfile):
    # run the interpreter
    cmd = ["../../dpt", "--suppress-final-state", lucidfile]

    #with open('output.txt','w') as outfile:
    #    ret = subprocess.run(cmd, stdout=outfile, shell=True)
    ret = subprocess.run(cmd)
    if ret.returncode != 0: # stop if there's an error running interp
        print("err")
        quit()


    # get output from interpreter
    # we only have one line (final measurement), but can put this in a loop and read mult lines if we want
    measurement = pickle.load(open(outfile,"rb"))

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


# compute avg error for our cms (mean abs error)
def calc_cost(m, ground_truth):
    s = 0
    for k in ground_truth:
        s += abs(m[k]-ground_truth[k])
    return float(s)/float(len(m))

def write_symb(rows,cols):
    logcols = int(math.log2(cols))
    concretes = {}
    concretes["sizes"] = {"logcols":logcols, "rows":rows}
    concretes["symbolics"] = {"cols":cols}
    with open('cms_sym.symb', 'w') as f:
        json.dump(concretes, f, indent=4)

# create init symb file
cols = 128
rows = 4
write_symb(cols,rows)

#write_symb(sizes,symbolics)

# compute ground truth
#ground_truth = [0]*100
ground_truth = gen_traffic("univ1_pt1.pcap")
#ground_truth = gen_traffic("equinix-chicago.dirA.20160121-125911.UTC.anon.pcap")

# we keep track of best solution(s) and cost(s)
best_sol = [rows,cols]
best_cost = 0
iterations = 0
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

tested_sols = [(rows,cols)]

start_time = time.time()
while True:
    # stop after x iterations
    if iterations >= 100:
        break
    print(rows,cols)
    # run interp w/ current symb file
    m = interp_sim("cms_sym.dpt","test.txt")
    # use measurement to choose next vals --> compare w ground truth, and then move accordingly
    new_cost = calc_cost(m,ground_truth)
    '''
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
    '''
    # random
    if iterations < 1:
        best_cost = new_cost
        while (rows,cols) in tested_sols:   # don't test the same sols
            cols,rows = sim_move()
        tested_sols.append((rows,cols))
        best_sol = [rows,cols]
        write_symb(rows,cols)
        iterations += 1
        continue

    if (new_cost < best_cost) or (new_cost==best_cost and rows*cols <= best_sol[0]*best_sol[1]):
        best_cost = new_cost
        best_sol = [rows,cols]

    while (rows,cols) in tested_sols:   # don't test the same sols
        cols,rows = sim_move()
    tested_sols.append((rows,cols))
    write_symb(rows,cols)
    iterations += 1

end_time = time.time()
print("BEST:")
print(best_sol)
print("TIME(s):")
print(end_time-start_time)

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

