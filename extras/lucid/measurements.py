# python class for non-approximate version of lucid code (counting structs)
# just use dictionary indexed by some predefined flowid
# we only need to do exact computation once, not per interpreter test

from scapy.all import *

'''
# flowid has to be immutable, so just concat vals into str
class ExactCount:
    def __init__(self, pkts, flowid):
        self.pkts = pkts	
        self.exact = {}
        self.flowid = flowid

    def compute_exact():
        # iterate through pkts in pcap
        with PcapReader(self.pkts) as pcap_reader:
            for pkt in pcap_reader:
                # get flowid
                flowid = ""
                #for field in self.flowid:

                # if flowid not in dict, add it w/ count of 1
                if flowid not in self.exact:
                    self.exact[flowid] = 1
                # else, increment count
                else:
                    self.exact[flowid] += 1

    def get_exact():
        return self.exact
'''

# init measuremnt structs - exact counter and one for measuring interp output
# use arrays, w/ a dict that stores flowid(str): number 

class Measurements:
    def __init__(self, pkts, idfields):
        self.pkts = pkts
        self.exact = {}
        self.interp_measure = {}
        self.idfields = idfields
  
    def compute_exact_init_interp_measure():    # should only need to do this once before we start optimization
        # could/should also gen json file for interpreter here
        # iterate through pkts in pcap
        with PcapReader(self.pkts) as pcap_reader:
            for pkt in pcap_reader:
                # get flowid (pull fields from trace - e.g., srcaddr, dstaddr, etc.)
                # NOTE: how can we do this??? user passes us list of fields they want to access, then we need to grab them from packet
                # scapy doesn't like this though
                flowid = ""
                # if flowid not in dict, add it w/ count of 1
                if flowid not in self.exact:
                    self.exact[flowid] = 1
                    self.interp_measure[flowid] = 0 # init interp_measure w/ 0 for all flows 
                # else, increment count
                else:
                    self.exact[flowid] += 1    


    def get_exact():
        return self.exact

    def update_counts(count, fields):   # NOTE: gotta make sure the format of fields works w/ this
        fields = [str(x) for x in fields]
        self.interp_measure[''.join(fields)] = count

    def get_interp_measure():
        return self.interp_measure

    def reset_inter_measure():
        self.interp_measure = [0]*len(self.interp_measure)
        self.interp_measure = dict.fromkeys(self.interp_measure, 0)

