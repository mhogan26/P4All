/*******************************************************************************
 * BAREFOOT NETWORKS CONFIDENTIAL & PROPRIETARY
 *
 * Copyright (c) 2015-2019 Barefoot Networks, Inc.

 * All Rights Reserved.
 *
 * NOTICE: All information contained herein is, and remains the property of
 * Barefoot Networks, Inc. and its suppliers, if any. The intellectual and
 * technical concepts contained herein are proprietary to Barefoot Networks,
 * Inc.
 * and its suppliers and may be covered by U.S. and Foreign Patents, patents in
 * process, and are protected by trade secret or copyright law.
 * Dissemination of this information or reproduction of this material is
 * strictly forbidden unless prior written permission is obtained from
 * Barefoot Networks, Inc.
 *
 * No warranty, explicit or implicit is provided, unless granted under a
 * written agreement with Barefoot Networks, Inc.
 *
 ******************************************************************************/

#include <core.p4>
#include <tna.p4>

#define VLAN_DEPTH 2
#define ETHERTYPE_IPV4 0x0800
#define ETHERTYPE_ARP  0x0806
#define ETHERTYPE_VLAN 0x8100
#define IP_PROTOCOLS_ICMP   1
#define IP_PROTOCOLS_IGMP   2
#define IP_PROTOCOLS_IPV4   4
#define IP_PROTOCOLS_TCP    6
#define IP_PROTOCOLS_UDP    17



const bit<2> SWITCH_PKT_TYPE_UNICAST = 0;
const bit<2> SWITCH_PKT_TYPE_MULTICAST = 1;
const bit<2> SWITCH_PKT_TYPE_BROADCAST = 2;

const bit<2> SWITCH_IP_TYPE_IPV4 = 1;

typedef bit<32> switch_uint32_t;

typedef bit<10> switch_port_lag_index_t;

#ifndef _P4_HEADERS_
#define _P4_HEADERS_

typedef bit<48> mac_addr_t;
typedef bit<32> ipv4_addr_t;
typedef bit<12> vlan_id_t;

typedef bit<2> switch_ip_frag_t;

header ethernet_h {
    mac_addr_t dst_addr;
    mac_addr_t src_addr;
    bit<16> ether_type;
}

header vlan_tag_h {
    bit<3> pcp;
    bit<1> cfi;
    vlan_id_t vid;
    bit<16> ether_type;
}

header ipv4_h {
    bit<4> version;
    bit<4> ihl;
    bit<8> diffserv;
    bit<16> total_len;
    bit<16> identification;
    bit<3> flags;
    bit<13> frag_offset;
    bit<8> ttl;
    bit<8> protocol;
    bit<16> hdr_checksum;
    ipv4_addr_t src_addr;
    ipv4_addr_t dst_addr;
}

header tcp_h {
    bit<16> src_port;
    bit<16> dst_port;
    bit<32> seq_no;
    bit<32> ack_no;
    bit<4> data_offset;
    bit<4> res;
    bit<8> flags;
    bit<16> window;
    bit<16> checksum;
    bit<16> urgent_ptr;
}

header udp_h {
    bit<16> src_port;
    bit<16> dst_port;
    bit<16> length;
    bit<16> checksum;
}

header icmp_h {
    bit<8> type;
    bit<8> code;
    bit<16> checksum;
    // ...
}

header igmp_h {
    bit<8> type;
    bit<8> code;
    bit<16> checksum;
    // ...
}

// Address Resolution Protocol -- RFC 6747
header arp_h {
    bit<16> hw_type;
    bit<16> proto_type;
    bit<8> hw_addr_len;
    bit<8> proto_addr_len;
    bit<16> opcode;
    // ...
}

#endif /* _P4_HEADERS_ */


struct switch_header_t {
    ethernet_h ethernet;
    vlan_tag_h[VLAN_DEPTH] vlan_tag;
    ipv4_h ipv4;
    arp_h arp;
    udp_h udp;
    icmp_h icmp;
    igmp_h igmp;
    tcp_h tcp;
}

// Ingress metadata
typedef PortId_t switch_port_t;
typedef bit<32> switch_ig_port_lag_label_t;
typedef bit<8> switch_drop_reason_t;
typedef bit<2> switch_pkt_type_t;
typedef bit<2> switch_ip_type_t;


struct switch_lookup_fields_t {
    switch_pkt_type_t pkt_type;

    mac_addr_t mac_src_addr;
    mac_addr_t mac_dst_addr;
    bit<16> mac_type;
    bit<3> pcp;

    // 1 for ARP request, 2 for ARP reply.
    bit<16> arp_opcode;

    switch_ip_type_t ip_type;
    bit<8> ip_proto;
    bit<8> ip_ttl;
    bit<8> ip_tos;
    bit<2> ip_frag;
    bit<128> ip_src_addr;
    bit<128> ip_dst_addr;

    bit<8> tcp_flags;
    bit<16> l4_src_port;
    bit<16> l4_dst_port;
}

struct switch_ingress_flags_t {
    bool ipv4_checksum_err;
    bool inner_ipv4_checksum_err;
    bool link_local;
    bool routed;
    bool acl_deny;
    bool racl_deny;
    bool port_vlan_miss;
    bool rmac_hit;
    bool dmac_miss;
    bool myip;
    bool glean;
    bool storm_control_drop;
    bool acl_meter_drop;
    bool port_meter_drop;
    bool flood_to_multicast_routers;
    bool peer_link;
    bool capture_ts;
    bool mac_pkt_class;
    bool pfc_wd_drop;
    // Add more flags here.
}


struct switch_ingress_metadata_t {
    switch_port_t port;                            /* ingress port */
    switch_port_lag_index_t port_lag_index;        /* ingress port/lag index */
    bit<48> timestamp;
    switch_ingress_flags_t flags;
    switch_ig_port_lag_label_t port_lag_label;
    switch_drop_reason_t drop_reason;
    switch_lookup_fields_t lkp;
}

struct switch_port_metadata_t {
    switch_port_lag_index_t port_lag_index;
    switch_ig_port_lag_label_t port_lag_label;
}

// Egress metadata
typedef bit<16> switch_pkt_length_t;

struct switch_qos_metadata_t {
    bit<19> qdepth; // Egress only.
}


struct switch_egress_metadata_t {
    switch_pkt_length_t pkt_length;
    switch_port_t port;                         /* Mutable copy of egress port */
    switch_qos_metadata_t qos;
}



parser SwitchIngressParser(
        packet_in pkt,
        out switch_header_t hdr,
        out switch_ingress_metadata_t ig_md,
        out ingress_intrinsic_metadata_t ig_intr_md) {

    Checksum() ipv4_checksum;

    state start {
        pkt.extract(ig_intr_md);
        ig_md.port = ig_intr_md.ingress_port;
        ig_md.timestamp = ig_intr_md.ingress_mac_tstamp;
        transition parse_port_metadata;
    }
    state parse_port_metadata {
        // Parse port metadata produced by ibuf
        switch_port_metadata_t port_md = port_metadata_unpack<switch_port_metadata_t>(pkt);
        ig_md.port_lag_index = port_md.port_lag_index;
        ig_md.port_lag_label = port_md.port_lag_label;
        transition parse_packet;
    }
    state parse_packet {
        transition parse_ethernet;
    }
    state parse_ethernet {
        pkt.extract(hdr.ethernet);
        transition select(hdr.ethernet.ether_type, ig_intr_md.ingress_port) {
            (ETHERTYPE_IPV4, _) : parse_ipv4;
            default : accept;
        }
    }
    state parse_ipv4 {
        pkt.extract(hdr.ipv4);
        ipv4_checksum.add(hdr.ipv4);
        transition parse_ipv4_no_options;
    }
    state parse_ipv4_no_options {
        ig_md.flags.ipv4_checksum_err = ipv4_checksum.verify();
        transition select(hdr.ipv4.protocol, hdr.ipv4.frag_offset) {
            (IP_PROTOCOLS_ICMP, 0) : parse_icmp;
            (IP_PROTOCOLS_IGMP, 0) : parse_igmp;
            (IP_PROTOCOLS_TCP, 0) : parse_tcp;
            (IP_PROTOCOLS_UDP, 0) : parse_udp;
            // Do NOT parse the next header if IP packet is fragmented.
            default : accept;
        }
    }

    state parse_arp {
        pkt.extract(hdr.arp);
        transition accept;
    }

    state parse_vlan {
        pkt.extract(hdr.vlan_tag.next);
        transition select(hdr.vlan_tag.last.ether_type) {
            ETHERTYPE_ARP : parse_arp;
            ETHERTYPE_IPV4 : parse_ipv4;
            ETHERTYPE_VLAN : parse_vlan;
            default : accept;
        }
    }

    state parse_udp {
        pkt.extract(hdr.udp);
        transition accept; 
    }

    state parse_tcp {
        pkt.extract(hdr.tcp);
        transition accept;
    }

    state parse_icmp {
        pkt.extract(hdr.icmp);
        transition accept;
    }

    state parse_igmp {
        pkt.extract(hdr.igmp);
        transition accept;
    }


}

control SwitchIngress(
        inout switch_header_t hdr,
        inout switch_ingress_metadata_t ig_md,
        in ingress_intrinsic_metadata_t ig_intr_md,
        in ingress_intrinsic_metadata_from_parser_t ig_intr_from_prsr,
        inout ingress_intrinsic_metadata_for_deparser_t ig_intr_md_for_dprsr,
        inout ingress_intrinsic_metadata_for_tm_t ig_intr_md_for_tm) {

    const switch_uint32_t table_size = 64;

    action malformed_pkt(bit<8> reason) {
       ig_md.drop_reason = reason;
    }

    action malformed_non_ip_pkt(bit<8> reason) {
        ig_md.lkp.mac_src_addr = hdr.ethernet.src_addr;
        ig_md.lkp.mac_dst_addr = hdr.ethernet.dst_addr;
        ig_md.lkp.mac_type = hdr.ethernet.ether_type;
        malformed_pkt(reason);
    }

    action valid_unicast_pkt_untagged() {
        ig_md.lkp.pkt_type = SWITCH_PKT_TYPE_UNICAST;
        ig_md.lkp.mac_src_addr = hdr.ethernet.src_addr;
        ig_md.lkp.mac_dst_addr = hdr.ethernet.dst_addr;
        ig_md.lkp.mac_type = hdr.ethernet.ether_type;
    }

    action valid_multicast_pkt_untagged() {
        ig_md.lkp.pkt_type = SWITCH_PKT_TYPE_MULTICAST;
        ig_md.lkp.mac_src_addr = hdr.ethernet.src_addr;
        ig_md.lkp.mac_dst_addr = hdr.ethernet.dst_addr;
        ig_md.lkp.mac_type = hdr.ethernet.ether_type;
    }

    action valid_broadcast_pkt_untagged() {
        ig_md.lkp.pkt_type = SWITCH_PKT_TYPE_BROADCAST;
        ig_md.lkp.mac_src_addr = hdr.ethernet.src_addr;
        ig_md.lkp.mac_dst_addr = hdr.ethernet.dst_addr;
        ig_md.lkp.mac_type = hdr.ethernet.ether_type;
    }



    action valid_unicast_pkt_tagged() {
        ig_md.lkp.pkt_type = SWITCH_PKT_TYPE_UNICAST;
        ig_md.lkp.mac_src_addr = hdr.ethernet.src_addr;
        ig_md.lkp.mac_dst_addr = hdr.ethernet.dst_addr;
        ig_md.lkp.mac_type = hdr.vlan_tag[0].ether_type;
        ig_md.lkp.pcp = hdr.vlan_tag[0].pcp;
    }

    action valid_multicast_pkt_tagged() {
        ig_md.lkp.pkt_type = SWITCH_PKT_TYPE_MULTICAST;
        ig_md.lkp.mac_src_addr = hdr.ethernet.src_addr;
        ig_md.lkp.mac_dst_addr = hdr.ethernet.dst_addr;
        ig_md.lkp.mac_type = hdr.vlan_tag[0].ether_type;
        ig_md.lkp.pcp = hdr.vlan_tag[0].pcp;
    }

    action valid_broadcast_pkt_tagged() {
        ig_md.lkp.pkt_type = SWITCH_PKT_TYPE_BROADCAST;
        ig_md.lkp.mac_src_addr = hdr.ethernet.src_addr;
        ig_md.lkp.mac_dst_addr = hdr.ethernet.dst_addr;
        ig_md.lkp.mac_type = hdr.vlan_tag[0].ether_type;
        ig_md.lkp.pcp = hdr.vlan_tag[0].pcp;
    }

    table validate_ethernet {
        key = {
            hdr.ethernet.src_addr : ternary;
            hdr.ethernet.dst_addr : ternary;
            hdr.vlan_tag[0].isValid() : ternary;
        }

        actions = {
            malformed_non_ip_pkt;
            valid_unicast_pkt_untagged;
            valid_multicast_pkt_untagged;
            valid_broadcast_pkt_untagged;
            valid_unicast_pkt_tagged;
            valid_multicast_pkt_tagged;
            valid_broadcast_pkt_tagged;
        }

        size = table_size;
        /* const entries = {
            (_, _, _) : malformed_non_ip_pkt(SWITCH_DROP_SRC_MAC_MULTICAST);
            (0, _, _) : malformed_non_ip_pkt(SWITCH_DROP_SRC_MAC_ZERO);
            (_, 0, _) : malformed_non_ip_pkt(SWITCH_DROP_DST_MAC_ZERO);
        } */
    }


//-----------------------------------------------------------------------------
// Validate outer IPv4 header and set the lookup fields.
// - Drop the packet if ttl is zero, ihl is invalid, src addr is multicast, or
// - version is invalid.
//-----------------------------------------------------------------------------
    action malformed_ipv4_pkt(bit<8> reason) {
        // Set common lookup fields just for dtel acl and hash purposes
        ig_md.lkp.ip_type = SWITCH_IP_TYPE_IPV4;
        ig_md.lkp.ip_tos = hdr.ipv4.diffserv;
        ig_md.lkp.ip_proto = hdr.ipv4.protocol;
        ig_md.lkp.ip_ttl = hdr.ipv4.ttl;
        ig_md.lkp.ip_src_addr = (bit<128>) hdr.ipv4.src_addr;
        ig_md.lkp.ip_dst_addr = (bit<128>) hdr.ipv4.dst_addr;
        malformed_pkt(reason);
    }

    action valid_ipv4_pkt(switch_ip_frag_t ip_frag) {
        // Set common lookup fields
        ig_md.lkp.ip_type = SWITCH_IP_TYPE_IPV4;
        ig_md.lkp.ip_tos = hdr.ipv4.diffserv;
        ig_md.lkp.ip_proto = hdr.ipv4.protocol;
        ig_md.lkp.ip_ttl = hdr.ipv4.ttl;
        ig_md.lkp.ip_src_addr = (bit<128>) hdr.ipv4.src_addr;
        ig_md.lkp.ip_dst_addr = (bit<128>) hdr.ipv4.dst_addr;
        ig_md.lkp.ip_frag = ip_frag;
    }


    table validate_ipv4 {
        key = {
            ig_md.flags.ipv4_checksum_err : ternary;
            hdr.ipv4.version : ternary;
            hdr.ipv4.ihl : ternary;
            hdr.ipv4.flags : ternary;
            hdr.ipv4.frag_offset : ternary;
            hdr.ipv4.ttl : ternary;
            hdr.ipv4.src_addr[31:24] : ternary;
        }

        actions = {
            valid_ipv4_pkt;
            malformed_ipv4_pkt;
        }

        size = table_size;
    }


//-----------------------------------------------------------------------------
// Set L4 and other lookup fields
//-----------------------------------------------------------------------------
    action set_tcp_ports() {
        ig_md.lkp.l4_src_port = hdr.tcp.src_port;
        ig_md.lkp.l4_dst_port = hdr.tcp.dst_port;
        ig_md.lkp.tcp_flags = hdr.tcp.flags;
    }

    action set_udp_ports() {
        ig_md.lkp.l4_src_port = hdr.udp.src_port;
        ig_md.lkp.l4_dst_port = hdr.udp.dst_port;
        ig_md.lkp.tcp_flags = 0;
    }

    action set_icmp_type() {
        ig_md.lkp.l4_src_port[7:0] = hdr.icmp.type;
        ig_md.lkp.l4_src_port[15:8] = hdr.icmp.code;
        ig_md.lkp.l4_dst_port = 0;
        ig_md.lkp.tcp_flags = 0;
    }

    action set_igmp_type() {
        ig_md.lkp.l4_src_port = 0;
        ig_md.lkp.l4_dst_port = 0;
        ig_md.lkp.tcp_flags = 0;
    }

    action set_arp_opcode() {
        ig_md.lkp.l4_src_port = 0;
        ig_md.lkp.l4_dst_port = 0;
        ig_md.lkp.tcp_flags = 0;
        ig_md.lkp.arp_opcode = hdr.arp.opcode;
    }
    // Not much of a validation as it only sets the lookup fields.
    table validate_other {
        key = {
            hdr.tcp.isValid() : exact;
            hdr.udp.isValid() : exact;
            hdr.icmp.isValid() : exact;
            hdr.igmp.isValid() : exact;
            hdr.arp.isValid() : exact;
        }

        actions = {
            NoAction;
            set_tcp_ports;
            set_udp_ports;
            set_icmp_type;
            set_igmp_type;
            set_arp_opcode;
        }

        const default_action = NoAction;
        const entries = {
            (true, false, false, false, false) : set_tcp_ports();
            (false, true, false, false, false) : set_udp_ports();
            (false, false, true, false, false) : set_icmp_type();
            (false, false, false, true, false) : set_igmp_type();
            (false, false, false, false, true) : set_arp_opcode();
        }
    }




    apply {
        switch(validate_ethernet.apply().action_run) {
            malformed_non_ip_pkt : {}
            default : {
                if (hdr.ipv4.isValid()) {
                    validate_ipv4.apply();
                } 
                validate_other.apply();
	    }
	}
    }

}

//-----------------------------------------------------------------------------
// Ingress Deparser
//-----------------------------------------------------------------------------
control SwitchIngressDeparser(
    packet_out pkt,
    inout switch_header_t hdr,
    in switch_ingress_metadata_t ig_md,
    in ingress_intrinsic_metadata_for_deparser_t ig_intr_md_for_dprsr) {


    apply {
        pkt.emit(hdr.ethernet);
        pkt.emit(hdr.vlan_tag);
        pkt.emit(hdr.arp); // Ingress only.
        pkt.emit(hdr.ipv4);
        pkt.emit(hdr.udp);
        pkt.emit(hdr.tcp); // Ingress only.
        pkt.emit(hdr.icmp); // Ingress only.
        pkt.emit(hdr.igmp); // Ingress only.
    }
}




//----------------------------------------------------------------------------
// Egress parser
//----------------------------------------------------------------------------
parser SwitchEgressParser(
        packet_in pkt,
        out switch_header_t hdr,
        out switch_egress_metadata_t eg_md,
        out egress_intrinsic_metadata_t eg_intr_md) {


    state start {
	pkt.extract(eg_intr_md);
        eg_md.pkt_length = eg_intr_md.pkt_length;
        eg_md.port = eg_intr_md.egress_port;
        eg_md.qos.qdepth = eg_intr_md.deq_qdepth;
	transition parse_packet;
    }

    state parse_packet {
        transition parse_ethernet;
    }

    state parse_ethernet {
        pkt.extract(hdr.ethernet);
        transition select(hdr.ethernet.ether_type, eg_intr_md.egress_port) {
            (ETHERTYPE_IPV4, _) : parse_ipv4;
            (ETHERTYPE_VLAN, _) : parse_vlan;
            default : accept;
        }
    }
    state parse_vlan {
        pkt.extract(hdr.vlan_tag.next);
        transition select(hdr.vlan_tag.last.ether_type) {
            ETHERTYPE_IPV4 : parse_ipv4;
            ETHERTYPE_VLAN : parse_vlan;
            default : accept;
        }
    }
    state parse_ipv4 {
        pkt.extract(hdr.ipv4);
	transition accept;
    }

}


control SwitchEgress(
        inout switch_header_t hdr,
        inout switch_egress_metadata_t eg_md,
        in egress_intrinsic_metadata_t eg_intr_md,
        in egress_intrinsic_metadata_from_parser_t eg_intr_md_from_prsr,
        inout egress_intrinsic_metadata_for_deparser_t eg_intr_md_for_dprsr,
        inout egress_intrinsic_metadata_for_output_port_t eg_intr_md_for_oport) {


    apply {

    }

}


control SwitchEgressDeparser(
        packet_out pkt,
        inout switch_header_t hdr,
        in switch_egress_metadata_t eg_md,
        in egress_intrinsic_metadata_for_deparser_t eg_intr_md_for_dprsr) {
    Checksum() ipv4_checksum;
    apply {
	if (hdr.ipv4.isValid()) {
            hdr.ipv4.hdr_checksum = ipv4_checksum.update({
                hdr.ipv4.version,
                hdr.ipv4.ihl,
                hdr.ipv4.diffserv,
                hdr.ipv4.total_len,
                hdr.ipv4.identification,
                hdr.ipv4.flags,
                hdr.ipv4.frag_offset,
                hdr.ipv4.ttl,
                hdr.ipv4.protocol,
                hdr.ipv4.src_addr,
                hdr.ipv4.dst_addr});
        }
        pkt.emit(hdr.ethernet);
        pkt.emit(hdr.vlan_tag);
        pkt.emit(hdr.ipv4);
    }
}

Pipeline(SwitchIngressParser(),
        SwitchIngress(),
        SwitchIngressDeparser(),
        SwitchEgressParser(),
        SwitchEgress(),
        SwitchEgressDeparser()) pipe;

Switch(pipe) main;
