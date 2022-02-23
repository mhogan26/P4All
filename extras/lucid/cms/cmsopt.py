# (user-provided) class containing functions necessary for optimization:
#   gen traffic (as json), init function called each time we run interp iteration

import json
from scapy.all import *

# helpers
def i2Hex (n):
    hstr = str(hex(int(n)))
    if "0x" in hstr:
        if len(hstr[2:]) == 1: return "0" + hstr[2:].upper()
        else: return hstr[2:].upper()
    else:
        return hstr.upper()

def hexadecimal (ip_addr):
    # 0xC00002EB ( Hexadecimal )
    return "0x" + "".join( map( i2Hex,  ip_addr.split(".") ) )

class Opt:
    def __init__(self, pktpcap):
        self.ground_truth = {}
        self.pkts = pktpcap


    # this should convert pcap into json format for interp (can write it here, or write in init_iteration, see starflow)
    # call this once before we start optimization
    def gen_traffic(self):
        info = {}
        info["switches"] = 1
        info["max time"] = 9999999
        info["default input gap"] = 100
        info["random seed"] = 0
        info["python file"] = "cms_sym.py"
        events = []
        with PcapReader(self.pkts) as pcap_reader:
            for pkt in pcap_reader:
                if not (pkt.haslayer(IP)):
                    continue
                src_int = int(hexadecimal(pkt[IP].src),0)
                dst_int = int(hexadecimal(pkt[IP].dst),0)
                args = [128, src_int, dst_int]
                p = {"name":"ip_in", "args":args}
                events.append(p)
                if str(src_int)+str(dst_int) not in self.ground_truth:
                    self.ground_truth[str(src_int)+str(dst_int)] = 1
                else:
                    self.ground_truth[str(src_int)+str(dst_int)] += 1
                #print(pkt[IP].src)
                #print(int(hexadecimal(pkt[IP].src),0))
                #print(pkt[IP].dst)
                #print(int(hexadecimal(pkt[IP].dst),0))
                if len(events) > 20:
                    break

        info["events"] = events
        with open('cms_sym.json', 'w') as f:
            json.dump(info, f, indent=4)

    # called after every interp run
    # measurement is list of measurements (one measurement for each output file)
    # order in list is same ordered specified in opt json
    def calc_cost(self,measure):  # compute avg error for our cms (mean abs error)
        m = measure[0]  # cms only has 1 output file, so 1 set of measurements
        s = 0
        for k in self.ground_truth:
            s += abs(m[k]-self.ground_truth[k])
        return float(s)/float(len(m))

    # called before every interp run
    def init_iteration(self, symbs):
        pass


