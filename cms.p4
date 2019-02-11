// basic 2 arrray CMS

/* basic headers/parsing */

header_type ethernet_t {
    fields {
        bit<48> dstAddr;
        bit<48> srcAddr;
        bit<16> etherType;
    }
}


header_type ipv4_t {
    fields {
        bit<4> version;
        bit<4> ihl;
        bit<8> diffserv;
        bit<16> totalLen;
        bit<16> identification;
        bit<3> flags;
        bit<13> fragOffset;
        bit<8> ttl;
        bit<8> protocol;
        bit<16> hdrChecksum;
        bit<32> srcAddr;
        bit<32> dstAddr;
    }
}

parser start {
    return parse_ethernet;
}

#define ETHERTYPE_IPV4 0x0800

header ethernet_t ethernet;

parser parse_ethernet {
    extract(ethernet);
    return select(latest.etherType) {
        ETHERTYPE_IPV4 : parse_ipv4;
        default: ingress;
    }
}

header ipv4_t ipv4;

field_list ipv4_checksum_list {
    ipv4.version;
    ipv4.ihl;
    ipv4.diffserv;
    ipv4.totalLen;
    ipv4.identification;
    ipv4.flags;
    ipv4.fragOffset;
    ipv4.ttl;
    ipv4.protocol;
    ipv4.srcAddr;
    ipv4.dstAddr;
}

field_list_calculation ipv4_checksum {
    input {
        ipv4_checksum_list;
    }
    algorithm : csum16;
    output_width : 16;
}

calculated_field ipv4.hdrChecksum  {
    verify ipv4_checksum;
    update ipv4_checksum;
}

parser parse_ipv4 {
    extract(ipv4);
    return ingress;
}


action _drop() {
    drop();
}

header_type routing_metadata_t {
    fields {
        bit<32> nhop_ipv4;
    }
}

metadata routing_metadata_t routing_metadata;

register drops_register {
    width: 32;
    static: drop_expired;
    instance_count: 16;
}

register drops_register_enabled {
    width: 1;
    static: drop_expired;
    instance_count: 16;
}

action do_drop_expired() {
    drops_register[0] = drops_register[0] + ((drops_register_enabled[0] == 1) ?
    (bit<32>)1 : 0);
    drop();
}

table drop_expired {
    actions { do_drop_expired; }
    size: 0;
}

ction set_nhop(in bit<32> nhop_ipv4, in bit<9> port) {
    routing_metadata.nhop_ipv4 = nhop_ipv4;
    standard_metadata.egress_spec = port;
    ipv4.ttl = ipv4.ttl - 1;
}

table ipv4_lpm {
    reads {
        ipv4.dstAddr : lpm;
    }
    actions {
        set_nhop;
        _drop;
    }
    size: 1024;
}

action set_dmac(in bit<48> dmac) {
    ethernet.dstAddr = dmac;
    // modify_field still valid
    // modify_field(ethernet.dstAddr, dmac);
}

table forward {
    reads {
        routing_metadata.nhop_ipv4 : exact;
    }
    actions {
        set_dmac;
        _drop;
    }
    size: 512;
}

action rewrite_mac(in bit<48> smac) {
    ethernet.srcAddr = smac;
}

table send_frame {
    reads {
        standard_metadata.egress_port: exact;
    }
    actions {
        rewrite_mac;
        _drop;
    }
    size: 256;
}


/* fields to hash */
field_list hash_list {
    ipv4.srcAddr;
    ipv4.dstAddr;
    ipv4.protocol;
}

field_list_calculation count1_hash {
    input {
        hash_list;
    }
    algorithm : my_hash_1;
    output_width : 11;
}

field_list_calculation count2_hash {
    input {
        hash_list;
    }
    algorithm : my_hash_2;
    output_width : 11;
}

header_type cms_metadata_t {
    fields {
	bit<11> index1;
	bit<11> index2;
	bit<32> count1;
	bit<32> count2;
	bit<32> count_min;
    }
}

metadata cms_metadata_t cms_meta;


/* count-min sketch arrays */

register counter1 {
    width: 32;
    instance_count: 2048;
}

register counter2 {
    width: 32;
    instance_count: 2048;
}


action count1(){
    /* compute hash index */
    modify_field_with_hash_based_offset(cms_meta.index1, 0, count1_hash, 11);

    /* increment counter  - read, increment, write*/
    cms_meta.count1 = counter1[cms_meta.index1];
    counter1[cms_meta.index1] = cms_meta.count1 + 1;
}


action count2(){
    /* compute hash index */
    modify_field_with_hash_based_offset(cms_meta.index2, 0, count2_hash, 11);

    /* increment counter  - read, increment, write*/
    cms_meta.count2 = counter2[cms_meta.index2];
    counter2[cms_meta.index2] = cms_meta.count2 + 1;
}

action countall(){
    count1();
    count2();
}


table counter {
    actions { countall; }
    size: 0;
}

      
action do_find_min1()
{
    cms_meta.count_min = cms_meta.count1;
}

action do_find_min2()
{       
    cms_meta.count_min = cms_meta.count2;
}

table find_min1 {
    actions { do_find_min1; }
}

table find_min2 {
    actions { do_find_min2; }
}


control ingress 
{
    // cms update
    apply(counter);
    // find min
    apply(find_min1);
    if (cms_meta.count_min > cms_meta.count2) {
	apply(find_min2);
    }

    // forwarding
    if(valid(ipv4)) {
        if(ipv4.ttl > 1) {
            apply(ipv4_lpm);
            apply(forward);
        } else {
            apply(drop_expired);
        }
    }

}
 
