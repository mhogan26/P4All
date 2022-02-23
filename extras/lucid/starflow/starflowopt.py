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
        self.ground_truth = 0
        self.pkts = pktpcap
        self.events = []

    # gen traffic (but don't write json yet, do that in init_iteration)
    def gen_traffic(self):
        with PcapReader(self.pkts) as pcap_reader:
            for pkt in pcap_reader:
                if not (pkt.haslayer(IP)):
                    continue
                src_int = int(hexadecimal(pkt[IP].src),0)
                dst_int = int(hexadecimal(pkt[IP].dst),0)
                pktlen = pkt[IP].len
                tos = pkt[IP].tos
                args = [128, src_int, dst_int, pktlen, tos]
                p = {"name":"ip_in", "args":args}
                self.events.append(p)
                if len(self.events) > 2000:
                    break
        self.ground_truth = len(self.events)


    # our measurement is total number of cache evictions/flushes
    def calc_cost(self,measure):
        ratio = measure[0]/self.ground_truth
        if ratio < 0.4: # all sols that produce eviction ratio less than thresh are equally as good (not considering resources)
            ratio = 0
        return ratio

    # we need free block events before we send data traffic to init long cache
    def init_iteration(self, symbs): # all sols that produce eviction ratio less than thresh are equally as good (not considering resources):
        info = {}
        info["switches"] = 1
        info["max time"] = 9999999
        info["default input gap"] = 100
        info["random seed"] = 0
        info["python file"] = "starflow.py"

        fb_events = []
        for i in range(1,symbs["L_SLOTS"]):
            fb_events.append({"name":"free_block","args":[i,0]})

        info["events"] = fb_events+self.events

        with open('starflow.json','w') as f:
            json.dump(info, f, indent=4)

