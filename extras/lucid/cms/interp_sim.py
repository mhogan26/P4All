import subprocess, os, ast, json, math
from move import *
from traffic import *

# this function runs interpreter with whatever symb file is in directory and returns measurement of interest
def interp_sim():
    # run the interpreter
    cmd = ["../../dpt cms_sym.dpt --spec cms_sym.json"]

    with open('output.txt','w') as outfile:
        ret = subprocess.run(cmd, stdout=outfile, shell=True)


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


    return measurement


# compute avg error for our cms (mean abs error)
def calc_cost(m, ground_truth):
    s = 0
    for i in range(len(m)):
        s += abs(m[i]-ground_truth[i])
    return float(s)/float(len(m))

def write_symb(rows,cols):
    logcols = int(math.log2(cols))
    concretes = {}
    concretes["sizes"] = {"logcols":logcols, "rows":rows}
    concretes["symbolics"] = {"cols":cols}
    with open('cms_sym.symb', 'w') as f:
        json.dump(concretes, f, indent=4)

# create init symb file
cols = 4
rows = 4
write_symb(cols,rows)

# compute ground truth
#ground_truth = [0]*100
ground_truth = gen_traffic()

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
temp=10
# bounds and step_size determine how far we move each iteration
bounds=[1,5]
step_size=[1,1]
# keep track of top x (2) solutions to see if they compile
top_sols = [best_sol, best_sol]

while True:
    print(new_sol)
    # stop after x iterations
    if iterations >= 10:
        break
    # run interp w/ current symb file
    m = interp_sim()
    # use measurement to choose next vals --> compare w ground truth, and then move accordingly
    new_cost = calc_cost(m,ground_truth)
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


# we test the top x solutions to see if they compile --> if they do, we're done!
# else, we can repeat above loop, excluding solutions we now know don't compile
# (we have to have a harness p4 file for this step, but not for interpreter)
# compile command doesn't work rn, can't find .symb file?????
# NOTE: use vagrant vm to compile
for sol in top_sols:
    write_symb(sol[0],sol[1])
    # compile lucid to p4
    cmd_lp4 = ["../../dptc cms_sym.dpt ip_harness.p4 linker_config.json cms_sym_build"]
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
    
