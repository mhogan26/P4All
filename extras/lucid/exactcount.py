# python class for non-approximate version of lucid code (counting structs)
# just use dictionary indexed by some predefined flowid
# we only need to do exact computation once, not per interpreter test

from scapy.all import *

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
