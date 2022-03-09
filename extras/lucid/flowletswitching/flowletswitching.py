# count the number of flowlets per hop (flowlethopcounts) by recording every time we get a new flowlet and have to decide where it goes
# also count num pkts sent out on each path (pkthopcounts)
# could also probs count num pkts/flowlet

import pickle

flowlethopcounts = {}
pkthopcounts = {}

def log_newflowlethop(hop,thresh):
    if thresh:  # new flowlet
        if hop not in flowlethopcounts:
            flowlethopcounts[hop] = 1
        else:
            flowlethopcounts[hop] += 1
        with open('flowlethops.txt','wb') as f:
            pickle.dump(flowlethopcounts, f)

def log_pkthop(hop):
    if hop not in pkthopcounts:
        pkthopcounts[hop] = 1
    else:
        pkthopcounts[hop] += 1
    with open('pkthops.txt','wb') as f:
        pickle.dump(pkthopcounts, f)


def log_test(hop,timedelta):
    with open('testhop.txt','a') as f:
        f.write(str(hop) + "\n")
    with open('testtime.txt','a') as f:
        f.write(str(timedelta)+"\n")

def log_testmemops(hop,timedelta):
    with open('memophop.txt','a') as f:
        f.write(str(hop) + "\n")
    with open('memoptime.txt','a') as f:
        f.write(str(timedelta)+"\n")


