import json
from scapy.all import *

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



class Opt(pkts):
    def __init__(self, pktpcap):
        self.ground_truth = 0
        self.pkts = pktpcap

    def gen_traffic(self):
        info = {}
        info["switches"] = 1
        info["max time"] = 9999999
        info["default input gap"] = 100
        info["random seed"] = 0
        info["python file"] = "rtt.py"
        events = []
        starttime = 1261067164.398500 # placeholder until figure out timestamps
        with PcapReader(self.pkts) as pcap_reader:
            for pkt in pcap_reader:
                if not (pkt.haslayer(IP)) or not (pkt.haslayer(TCP)):
                    continue
                src_int = int(hexadecimal(pkt[IP].src),0)
                dst_int = int(hexadecimal(pkt[IP].dst),0)
                pktlen = pkt[IP].len
                ihl = pkt[IP].ihl
                offset = pkt[TCP].dataofs
                seq = pkt[TCP].seq
                ack = pkt[TCP].ack
                sport = pkt[TCP].sport
                dport = pkt[TCP].dport
                timestamp = int((pkt.time-starttime)*1000000000)    # placeholder until figure out timestamps
                # getting int value of flags
                # this is so annoying is there a better way?
                f_str = pkt[TCP].flags
                f_int = 0
                if "F" in f_str:
                    f_int += 1
                if "S" in f_str:
                    f_int += 2
                if "R" in f_str:
                    f_int += 4
                if "P" in f_str:
                    f_int += 8
                if "A" in f_str:
                    f_int += 16
                args = [f_int, pktlen, ihl, offset, seq, ack, src_int, dst_int, sport, dport, timestamp]
                p = {"name":"tcp_in", "args":args}
                events.append(p)
                if len(events) > 200:
                    break
        info["events"] = events
        with open('rtt.json', 'w') as f:
            json.dump(info, f, indent=4)

        self.ground_truth = len(events)

    # measurements are num collisions, num timeouts, num rtt samples
    # don't currently calc total num of rtt samples in trace, but can calc in gen_traffic
    def calc_cost(self,measure):
        # placeholder for now, should ideally include all 3 measurements
        # TODO: how to use collisions/timeouts to guide search? timeouts affected by timeout value and struct size?
        return measure[0]/self.ground_truth

    def init_iteration(self,symbs):
        pass




