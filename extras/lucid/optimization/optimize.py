import time, importlib
from optalgos import *
from interp_sim import update_sym_sizes, write_symb

def init_opt():
    # import json file
    opt_info = json.load(open(sys.argv[1]))

    # import opt class that has funcs we need to get traffic, cost
    optmod = importlib.import_module(opt_info["optmodule"])
    o = optmod.Opt(opt_info["trafficpcap"])

    # gen traffic
    o.gen_traffic()

    # it's easier for gen next values if we exclude logs and don't separate symbolics/sizes, so let's do that here
    symbolics_opt = {}

    # is there a better way to merge? quick solution for now
    for var in opt_info["symbolicvals"]["sizes"]:
        if var not in opt_info["symbolicvals"]["logs"]:
            symbolics_opt[var] = opt_info["symbolicvals"]["sizes"][var]
    for var in opt_info["symbolicvals"]["symbolics"]:
        if var not in opt_info["symbolicvals"]["logs"]:
            symbolics_opt[var] = opt_info["symbolicvals"]["symbolics"][var]

    return opt_info,symbolics_opt, o

# usage: python3 optimize.py <json opt info file>
def main():
    if len(sys.argv) < 2:
        print("usage: python3 optimize.py <json opt info file>")
        quit()
    # initialize everything we need to run opt algo
    opt_info,symbolics_opt, o = init_opt()

    # optimize!
    start_time = time.time()
    #basin_hopping(symbolics_opt, opt_info,o)
    #quit()
    # TODO: allow user to pass in func
    if "optalgofile" in opt_info["optparams"]:   # only include field in json if using own algo
        # import module, require function to have standard name and arguments
        user = True


    elif opt_info["optparams"]["optalgo"] == "random":    # if not using own, should for sure have optalgo field
        best_sol, best_cost = random_opt(symbolics_opt, opt_info, o)

    elif opt_info["optparams"]["optalgo"] == "simannealing":
        best_sol, best_cost = simulated_annealing(symbolics_opt, opt_info, o)

    end_time = time.time()
    # write symb with final sol
    update_sym_sizes(best_sol, opt_info["symbolicvals"]["sizes"], opt_info["symbolicvals"]["symbolics"])
    write_symb(opt_info["symbolicvals"]["sizes"], opt_info["symbolicvals"]["symbolics"], opt_info["symbolicvals"]["logs"], opt_info["symfile"])

    '''
    # try compiling to tofino?
    # we could test the top x solutions to see if they compile --> if they do, we're done!
    # else, we can repeat optimization, excluding solutions we now know don't compile
    # (we have to have a harness p4 file for this step, but not for interpreter)
    # NOTE: use vagrant vm to compile
    for sol in top_sols:
        write_symb(sol[0],sol[1])
        # compile lucid to p4
        cmd_lp4 = ["../../dptc cms_sym.dpt ip_harness.p4 linker_config.json cms_sym_build --symb cms_sym.symb"]
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



    print("BEST:")
    print(best_sol)
    print("BEST COST:")
    print(best_cost)
    print("TIME(s):")
    print(end_time-start_time)



if __name__ == "__main__":
    main()



'''
json fields:
    symbolicvals: (anything info related to symbolics)
        sizes: symbolic sizes and starting vals
        symbolics: symbolic vals (ints, bools) and starting vals
        logs: which (if any) symbolics are log2(another symbolic)
        bounds: [lower,upper] bounds for symbolics, inclusive (don't need to include logs, bc they're calculated from other syms)
    optparams: (any info related to optimization algo)
        optalgo: if using one of our provided functions, tell us the name (random, simannealing)
        optalgofile: if using your own, tell us where to find it (python file)
        stop_iter: num iterations to stop at
        stop_time: time to stop at (in seconds)
        temp: initial temp for simannealing (init temps are almost arbitrary??)
        stepsize: stddev for simannealing (per symbolic? or single?
    symfile: file to write symbolics to
    lucidfile: dpt file
    outputfiles: list of files that output is stored in (written to by externs)
    optmodule: name of module that has class w/ necessary funcs
    trafficpcap: name of pcap file to use

sys reqs:
    python3
    lucid
    numpy

'''
