# count the number of flowlets per hop (flowlethopcounts) by recording every time we get a new flowlet and have to decide where it goes
# also count num pkts sent out on each path (pkthopcounts)
# could also probs count num pkts/flowlet

import pickle

flowlethopcounts = {}
pkthopcounts = {}

def log_newflowlethop(hop):
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


