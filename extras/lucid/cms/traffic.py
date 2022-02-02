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


# this should generate cms_sym.json file
# also retuns ground truth counts (for cms)
# we're concatenating all fields in flow key as a string w/o delimiters, but can add if needed
def gen_traffic(pkts):
    info = {}
    info["switches"] = 1
    info["max time"] = 9999999
    info["default input gap"] = 100
    info["random seed"] = 0
    info["python file"] = "cms_sym.py"
    events = []
    exact = {}  # ground truth counts
    with PcapReader(pkts) as pcap_reader:
        for pkt in pcap_reader:
            if not (pkt.haslayer(IP)):
                continue
            src_int = int(hexadecimal(pkt[IP].src),0)
            dst_int = int(hexadecimal(pkt[IP].dst),0)
            args = [128, src_int, dst_int]
            p = {"name":"ip_in", "args":args}
            events.append(p)
            if str(src_int)+str(dst_int) not in exact:
                exact[str(src_int)+str(dst_int)] = 1
            else:
                exact[str(src_int)+str(dst_int)] += 1
            #print(pkt[IP].src)
            #print(int(hexadecimal(pkt[IP].src),0))
            #print(pkt[IP].dst)
            #print(int(hexadecimal(pkt[IP].dst),0))
            if len(events) > 2000:
                break

    info["events"] = events
    with open('cms_sym.json', 'w') as f:
        json.dump(info, f, indent=4)

    #return ground_truth = [0]*100
    return exact 


#exact = gen_traffic("univ1_pt1.pcap")
#print(exact)


