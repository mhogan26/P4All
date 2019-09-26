//#include <core.p4>
//#include <v1model.p4>

//typedef bit<32> ip4Addr_t;

header_type ipv4_t {
    fields {
	version: 4;
	ihl: 4;
	diffserv: 8;
	totalLen: 16;
	identification: 16;
	flags: 3;
	fragOffset: 13;
	ttl: 8;
	protocol: 8;
	hdrChecksum: 16;
	srcAddr: 32;
	dstAddr: 32;
    }
}

header ipv4_t ipv4;

header_type  udp_t {
    fields {
	srcPort: 16;
	dstPort: 16;
	len: 16;
	checksum: 16;
    }
} 

header udp_t udp;

header_type  nc_hdr_t {
    fields {
	op: 8;
	key: 128;
    }
}

header nc_hdr_t nc_hdr;

header_type  nc_value_1_t {
    fields {
	value_1_1 :32;
        value_1_2 :32;
        value_1_3 :32;
        value_1_4 :32;
    }
}

header nc_value_1_t nc_value_1;

header_type  nc_value_2_t {
    fields {
        value_2_1 :32;
        value_2_2 :32;
        value_2_3 :32;
        value_2_4 :32;
    }
}

header nc_value_2_t nc_value_2;

header_type  nc_value_3_t {
    fields {
        value_3_1 :32;
        value_3_2 :32;
        value_3_3 :32;
        value_3_4 :32;
    }
}

header nc_value_3_t nc_value_3;

header_type  nc_value_4_t {
    fields {
        value_4_1 :32;
        value_4_2 :32;
        value_4_3 :32;
        value_4_4 :32;
    }
}

header nc_value_4_t nc_value_4;

header_type  nc_value_5_t {
    fields {
        value_5_1 :32;
        value_5_2 :32;
        value_5_3 :32;
        value_5_4 :32;
    }
}

header nc_value_5_t nc_value_5;

header_type  nc_value_6_t {
    fields {
        value_6_1 :32;
        value_6_2 :32;
        value_6_3 :32;
        value_6_4 :32;
    }
}

header nc_value_6_t nc_value_6;

header_type  nc_value_7_t {
    fields {
        value_7_1 :32;
        value_7_2 :32;
        value_7_3 :32;
        value_7_4 :32;
    }
}

header nc_value_7_t nc_value_7;

header_type  nc_value_8_t {
    fields {
        value_8_1 :32;
        value_8_2 :32;
        value_8_3 :32;
        value_8_4 :32;
    }
}

header nc_value_8_t nc_value_8;


header custom_metadata_t {
    fields {
        cache_exist: 1;
        cache_index: 14;
        cache_valid: 1;
	ipv4_srcAddr: 32;
	ipv4_dstAddr: 32;
    }
}

metadata custom_metadata_t meta;


parser start {
	return parse_ipv4;
}

parser parse_ipv4 {
	extract (ipv4);
	return parse_udp;
}

parser parse_udp {
	extract (udp);
	return parse_nc_hdr;
}

parser parse_nc_hdr {
	extract (nc_hdr);
	return select (latest.op) {
		NC_READ_REQUST: ingress;
		NC_READ_REPLY: parse_value;
		NC_UPDATE_REQUEST: ingress;
		NC_UPDATE_REPLY: parse_value;
		default: ingress;
	}
}

parser parse_value {
	return parse_nc_value_1;
}

parser parse_nc_value_1 {
	extract (nc_value_1);
	return parse_nc_value_2;
}

parser parse_nc_value_2 {
        extract (nc_value_2);
        return parse_nc_value_3;
}

parser parse_nc_value_3 {
        extract (nc_value_3);
        return parse_nc_value_4;
}

parser parse_nc_value_4 {
        extract (nc_value_4);
        return parse_nc_value_5;
}
 
parser parse_nc_value_5 {
        extract (nc_value_5);
        return parse_nc_value_6;
}
 
parser parse_nc_value_6 {
        extract (nc_value_6);
        return parse_nc_value_7;
}
 
parser parse_nc_value_7 {
        extract (nc_value_7);
        return parse_nc_value_8;
}
 
parser parse_nc_value_8 {
        extract (nc_value_8);
        return parse_nc_value_9;
}
 
parser parse_nc_value_9 {
	return ingress;
}


register value_1_1_reg {
	width: 32;
	instance_count: NUM_CACHE;
}
register value_1_2_reg {
        width: 32;
        instance_count: NUM_CACHE;
}
register value_1_3_reg {
        width: 32;
        instance_count: NUM_CACHE;
}
register value_1_4_reg {
        width: 32;
        instance_count: NUM_CACHE;
}

register value_2_1_reg {
        width: 32;
        instance_count: NUM_CACHE;
}
register value_2_2_reg {
        width: 32;
        instance_count: NUM_CACHE;
}
register value_2_3_reg {
        width: 32;
        instance_count: NUM_CACHE;
}
register value_2_4_reg {
        width: 32;
        instance_count: NUM_CACHE;
}

register value_3_1_reg {
        width: 32;
        instance_count: NUM_CACHE;
}
register value_3_2_reg {
        width: 32;
        instance_count: NUM_CACHE;
}
register value_3_3_reg {
        width: 32;
        instance_count: NUM_CACHE;
}
register value_3_4_reg {
        width: 32;
        instance_count: NUM_CACHE;
}

register value_4_1_reg {
        width: 32;
        instance_count: NUM_CACHE;
}
register value_4_2_reg {
        width: 32;
        instance_count: NUM_CACHE;
}
register value_4_3_reg {
        width: 32;
        instance_count: NUM_CACHE;
}
register value_4_4_reg {
        width: 32;
        instance_count: NUM_CACHE;
}

register value_5_1_reg {
        width: 32;
        instance_count: NUM_CACHE;
}
register value_5_2_reg {
        width: 32;
        instance_count: NUM_CACHE;
}
register value_5_3_reg {
        width: 32;
        instance_count: NUM_CACHE;
}
register value_5_4_reg {
        width: 32;
        instance_count: NUM_CACHE;
}

register value_6_1_reg {
        width: 32;
        instance_count: NUM_CACHE;
}
register value_6_2_reg {
        width: 32;
        instance_count: NUM_CACHE;
}
register value_6_3_reg {
        width: 32;
        instance_count: NUM_CACHE;
}
register value_6_4_reg {
        width: 32;
        instance_count: NUM_CACHE;
}

register value_7_1_reg {
        width: 32;
        instance_count: NUM_CACHE;
}
register value_7_2_reg {
        width: 32;
        instance_count: NUM_CACHE;
}
register value_7_3_reg {
        width: 32;
        instance_count: NUM_CACHE;
}
register value_7_4_reg {
        width: 32;
        instance_count: NUM_CACHE;
}

register value_8_1_reg {
        width: 32;
        instance_count: NUM_CACHE;
}
register value_8_2_reg {
        width: 32;
        instance_count: NUM_CACHE;
}
register value_8_3_reg {
        width: 32;
        instance_count: NUM_CACHE;
}
register value_8_4_reg {
        width: 32;
        instance_count: NUM_CACHE;
}


// store src and dst addresses in metadata (if we have a read request and cache valid)
action reply_read_hit_before_act() {
    modify_field (meta.ipv4_srcAddr, ipv4.srcAddr);
    modify_field (meta.ipv4_dstAddr, ipv4.dstAddr);
}


table reply_read_hit_before {
    actions {
        reply_read_hit_before_act;
    }
}

// send reply back - swap src and dst addresses (if read request and cache valid)
action reply_read_hit_after_act() {
    modify_field (ipv4.srcAddr, meta.ipv4_dstAddr);
    modify_field (ipv4.dstAddr, meta.ipv4_srcAddr);
    modify_field (nc_hdr.op, NC_READ_REPLY);
}

table reply_read_hit_after {
    actions {
        reply_read_hit_after_act;
    }
}

action read_value_1_1_act() {
	register_read(nc_value_1.value_1_1, value_1_1_reg, meta.cache_index);
}
table read_value_1_1 {
	actions {
		read_value_1_1_act;
	}
}

action read_value_1_2_act() {
        register_read(nc_value_1.value_1_2, value_1_2_reg, meta.cache_index);
}
table read_value_1_2 {
        actions {
                read_value_1_2_act;
        }
}

action read_value_1_3_act() {
        register_read(nc_value_1.value_1_3, value_1_3_reg, meta.cache_index);
}
table read_value_1_3 {
        actions {
                read_value_1_3_act;
        }
}

action read_value_1_4_act() {
        register_read(nc_value_1.value_1_4, value_1_4_reg, meta.cache_index);
}
table read_value_1_4 {
        actions {
                read_value_1_4_act;
        }
}

action read_value_2_1_act() {
        register_read(nc_value_2.value_2_1, value_2_1_reg, meta.cache_index);
}
table read_value_2_1 {
        actions {
                read_value_2_1_act;
        }
}

action read_value_2_2_act() {
        register_read(nc_value_2.value_2_2, value_2_2_reg, meta.cache_index);
}
table read_value_2_2 {
        actions {
                read_value_2_2_act;
        }
}

action read_value_2_3_act() {
        register_read(nc_value_2.value_2_3, value_2_3_reg, meta.cache_index);
}
table read_value_2_3 {
        actions {
                read_value_2_3_act;
        }
}

action read_value_2_4_act() {
        register_read(nc_value_2.value_2_4, value_2_4_reg, meta.cache_index);
}
table read_value_2_4 {
        actions {
                read_value_2_4_act;
        }
}
action read_value_3_1_act() {
        register_read(nc_value_3.value_3_1, value_3_1_reg, meta.cache_index);
}
table read_value_3_1 {
        actions {
                read_value_3_1_act;
        }
}

action read_value_3_2_act() {
        register_read(nc_value_3.value_3_2, value_3_2_reg, meta.cache_index);
}
table read_value_3_2 {
        actions {
                read_value_3_2_act;
        }
}

action read_value_3_3_act() {
        register_read(nc_value_3.value_3_3, value_3_3_reg, meta.cache_index);
}
table read_value_3_3 {
        actions {
                read_value_3_3_act;
        }
}

action read_value_3_4_act() {
        register_read(nc_value_3.value_3_4, value_3_4_reg, meta.cache_index);
}
table read_value_3_4 {
        actions {
                read_value_3_4_act;
        }
}
action read_value_4_1_act() {
        register_read(nc_value_4.value_4_1, value_4_1_reg, meta.cache_index);
}
table read_value_4_1 {
        actions {
                read_value_4_1_act;
        }
}

action read_value_4_2_act() {
        register_read(nc_value_4.value_4_2, value_4_2_reg, meta.cache_index);
}
table read_value_4_2 {
        actions {
                read_value_4_2_act;
        }
}

action read_value_4_3_act() {
        register_read(nc_value_4.value_4_3, value_4_3_reg, meta.cache_index);
}
table read_value_4_3 {
        actions {
                read_value_4_3_act;
        }
}

action read_value_4_4_act() {
        register_read(nc_value_4.value_4_4, value_4_4_reg, meta.cache_index);
}
table read_value_4_4 {
        actions {
                read_value_4_4_act;
        }
}
action read_value_5_1_act() {
        register_read(nc_value_5.value_5_1, value_5_1_reg, meta.cache_index);
}
table read_value_5_1 {
        actions {
                read_value_5_1_act;
        }
}

action read_value_5_2_act() {
        register_read(nc_value_5.value_5_2, value_5_2_reg, meta.cache_index);
}
table read_value_5_2 {
        actions {
                read_value_5_2_act;
        }
}

action read_value_5_3_act() {
        register_read(nc_value_5.value_5_3, value_5_3_reg, meta.cache_index);
}
table read_value_5_3 {
        actions {
                read_value_5_3_act;
        }
}

action read_value_5_4_act() {
        register_read(nc_value_5.value_5_4, value_5_4_reg, meta.cache_index);
}
table read_value_5_4 {
        actions {
                read_value_5_4_act;
        }
}
action read_value_6_1_act() {
        register_read(nc_value_6.value_6_1, value_6_1_reg, meta.cache_index);
}
table read_value_6_1 {
        actions {
                read_value_6_1_act;
        }
}

action read_value_6_2_act() {
        register_read(nc_value_6.value_6_2, value_6_2_reg, meta.cache_index);
}
table read_value_6_2 {
        actions {
                read_value_6_2_act;
        }
}

action read_value_6_3_act() {
        register_read(nc_value_6.value_6_3, value_6_3_reg, meta.cache_index);
}
table read_value_6_3 {
        actions {
                read_value_6_3_act;
        }
}

action read_value_6_4_act() {
        register_read(nc_value_6.value_6_4, value_6_4_reg, meta.cache_index);
}
table read_value_6_4 {
        actions {
                read_value_6_4_act;
        }
}
action read_value_7_1_act() {
        register_read(nc_value_7.value_7_1, value_7_1_reg, meta.cache_index);
}
table read_value_7_1 {
        actions {
                read_value_7_1_act;
        }
}

action read_value_7_2_act() {
        register_read(nc_value_7.value_7_2, value_7_2_reg, meta.cache_index);
}
table read_value_7_2 {
        actions {
                read_value_7_2_act;
        }
}

action read_value_7_3_act() {
        register_read(nc_value_7.value_7_3, value_7_3_reg, meta.cache_index);
}
table read_value_7_3 {
        actions {
                read_value_7_3_act;
        }
}

action read_value_7_4_act() {
        register_read(nc_value_7.value_7_4, value_7_4_reg, meta.cache_index);
}
table read_value_7_4 {
        actions {
                read_value_7_4_act;
        }
}
action read_value_8_1_act() {
        register_read(nc_value_8.value_8_1, value_8_1_reg, meta.cache_index);
}
table read_value_8_1 {
        actions {
                read_value_8_1_act;
        }
}

action read_value_8_2_act() {
        register_read(nc_value_8.value_8_2, value_8_2_reg, meta.cache_index);
}
table read_value_8_2 {
        actions {
                read_value_8_2_act;
        }
}

action read_value_8_3_act() {
        register_read(nc_value_8.value_8_3, value_8_3_reg, meta.cache_index);
}
table read_value_8_3 {
        actions {
                read_value_8_3_act;
        }
}

action read_value_8_4_act() {
        register_read(nc_value_8.value_8_4, value_8_4_reg, meta.cache_index);
}
table read_value_8_4 {
        actions {
                read_value_8_4_act;
        }
}


action add_value_header_1_act() {
        add_to_field(ipv4.totalLen, 16);
        add_to_field(udp.len, 16);
        add_header(nc_value_1);
}

table add_value_header_1 {
        actions {
            add_value_header_1_act;
        }
}

action add_value_header_2_act() { 
        add_to_field(ipv4.totalLen, 16);
        add_to_field(udp.len, 16);
        add_header(nc_value_2);
}

table add_value_header_2 { 
        actions { 
            add_value_header_2_act;
        } 
}

action add_value_header_3_act() { 
        add_to_field(ipv4.totalLen, 16);
        add_to_field(udp.len, 16);
        add_header(nc_value_3);
}

table add_value_header_3 { 
        actions { 
            add_value_header_3_act;
        } 
}

action add_value_header_4_act() { 
        add_to_field(ipv4.totalLen, 16);
        add_to_field(udp.len, 16);
        add_header(nc_value_4);
}

table add_value_header_4 {
        actions { 
            add_value_header_4_act;
        } 
}

action add_value_header_5_act() { 
        add_to_field(ipv4.totalLen, 16);
        add_to_field(udp.len, 16);
        add_header(nc_value_5);
}

table add_value_header_5 { 
        actions { 
            add_value_header_5_act;
        } 
}

action add_value_header_6_act() { 
        add_to_field(ipv4.totalLen, 16);
        add_to_field(udp.len, 16);
        add_header(nc_value_6);
}

table add_value_header_6 { 
        actions { 
            add_value_header_6_act;
        } 
}

action add_value_header_7_act() { 
        add_to_field(ipv4.totalLen, 16);
        add_to_field(udp.len, 16);
        add_header(nc_value_7);
}

table add_value_header_7 {
        actions { 
            add_value_header_7_act;
        } 
}

action add_value_header_8_act() { 
        add_to_field(ipv4.totalLen, 16);
        add_to_field(udp.len, 16);
        add_header(nc_value_8);
}

table add_value_header_8 {
        actions { 
            add_value_header_8_act;
        } 
}


action write_value_1_1_act() {
	register_write(value_1_1_reg, meta.cache_index, nc_value_1.value_1_1);
}
table write_value_1_1 {
	actions {
		write_value_1_1_act;
        }
}
action write_value_1_2_act() { 
        register_write(value_1_2_reg, meta.cache_index, nc_value_1.value_1_2);
}
table write_value_1_2 {
        actions { 
                write_value_1_2_act; 
        } 
}
action write_value_1_3_act() { 
        register_write(value_1_3_reg, meta.cache_index, nc_value_1.value_1_3);
}
table write_value_1_3 {
        actions { 
                write_value_1_3_act; 
        } 
}
action write_value_1_4_act() { 
        register_write(value_1_4_reg, meta.cache_index, nc_value_1.value_1_4);
}
table write_value_1_4 {
        actions { 
                write_value_1_4_act; 
        } 
}

action write_value_2_1_act() { 
        register_write(value_2_1_reg, meta.cache_index, nc_value_2.value_2_1);
}
table write_value_2_1 {
        actions { 
                write_value_2_1_act; 
        } 
}
action write_value_2_2_act() {
        register_write(value_2_2_reg, meta.cache_index, nc_value_2.value_2_2);
}
table write_value_2_2 {
        actions {
                write_value_2_2_act;
        }
}
action write_value_2_3_act() {
        register_write(value_2_3_reg, meta.cache_index, nc_value_2.value_2_3);
}
table write_value_2_3 {
        actions {
                write_value_2_3_act;
        }
}
action write_value_2_4_act() {
        register_write(value_2_4_reg, meta.cache_index, nc_value_2.value_2_4);
}
table write_value_2_4 {
        actions {
                write_value_2_4_act;
        }
}

action write_value_3_1_act() { 
        register_write(value_3_1_reg, meta.cache_index, nc_value_3.value_3_1);
}
table write_value_3_1 {
        actions { 
                write_value_3_1_act; 
        } 
}
action write_value_3_2_act() {
        register_write(value_3_2_reg, meta.cache_index, nc_value_3.value_3_2);
}
table write_value_3_2 {
        actions {
                write_value_3_2_act;
        }
}
action write_value_3_3_act() {
        register_write(value_3_3_reg, meta.cache_index, nc_value_3.value_3_3);
}
table write_value_3_3 {
        actions {
                write_value_3_3_act;
        }
}
action write_value_3_4_act() {
        register_write(value_3_4_reg, meta.cache_index, nc_value_3.value_3_4);
}
table write_value_3_4 {
        actions {
                write_value_3_4_act;
        }
}

action write_value_4_1_act() { 
        register_write(value_4_1_reg, meta.cache_index, nc_value_4.value_4_1);
}
table write_value_4_1 {
        actions { 
                write_value_4_1_act; 
        } 
}
action write_value_4_2_act() {
        register_write(value_4_2_reg, meta.cache_index, nc_value_4.value_4_2);
}
table write_value_4_2 {
        actions {
                write_value_4_2_act;
        }
}
action write_value_4_3_act() {
        register_write(value_4_3_reg, meta.cache_index, nc_value_4.value_4_3);
}
table write_value_4_3 {
        actions {
                write_value_4_3_act;
        }
}
action write_value_4_4_act() {
        register_write(value_4_4_reg, meta.cache_index, nc_value_4.value_4_4);
}
table write_value_4_4 {
        actions {
                write_value_4_4_act;
        }
}

action write_value_5_1_act() { 
        register_write(value_5_1_reg, meta.cache_index, nc_value_5.value_5_1);
}
table write_value_5_1 {
        actions { 
                write_value_5_1_act; 
        } 
}
action write_value_5_2_act() {
        register_write(value_5_2_reg, meta.cache_index, nc_value_5.value_5_2);
}
table write_value_5_2 {
        actions {
                write_value_5_2_act;
        }
}
action write_value_5_3_act() {
        register_write(value_5_3_reg, meta.cache_index, nc_value_5.value_5_3);
}
table write_value_5_3 {
        actions {
                write_value_5_3_act;
        }
}
action write_value_5_4_act() {
        register_write(value_5_4_reg, meta.cache_index, nc_value_5.value_5_4);
}
table write_value_5_4 {
        actions {
                write_value_5_4_act;
        }
}

action write_value_6_1_act() { 
        register_write(value_6_1_reg, meta.cache_index, nc_value_6.value_6_1);
}
table write_value_6_1 {
        actions { 
                write_value_6_1_act; 
        } 
}
action write_value_6_2_act() {
        register_write(value_6_2_reg, meta.cache_index, nc_value_6.value_6_2);
}
table write_value_6_2 {
        actions {
                write_value_6_2_act;
        }
}
action write_value_6_3_act() {
        register_write(value_6_3_reg, meta.cache_index, nc_value_6.value_6_3);
}
table write_value_6_3 {
        actions {
                write_value_6_3_act;
        }
}
action write_value_6_4_act() {
        register_write(value_6_4_reg, meta.cache_index, nc_value_6.value_6_4);
}
table write_value_6_4 {
        actions {
                write_value_6_4_act;
        }
}

action write_value_7_1_act() { 
        register_write(value_7_1_reg, meta.cache_index, nc_value_7.value_7_1);
}
table write_value_7_1 {
        actions { 
                write_value_7_1_act; 
        } 
}
action write_value_7_2_act() {
        register_write(value_7_2_reg, meta.cache_index, nc_value_7.value_7_2);
}
table write_value_7_2 {
        actions {
                write_value_7_2_act;
        }
}
action write_value_7_3_act() {
        register_write(value_7_3_reg, meta.cache_index, nc_value_7.value_7_3);
}
table write_value_7_3 {
        actions {
                write_value_7_3_act;
        }
}
action write_value_7_4_act() {
        register_write(value_7_4_reg, meta.cache_index, nc_value_7.value_7_4);
}
table write_value_7_4 {
        actions {
                write_value_7_4_act;
        }
}

action write_value_8_1_act() { 
        register_write(value_8_1_reg, meta.cache_index, nc_value_8.value_8_1);
}
table write_value_8_1 {
        actions { 
                write_value_8_1_act; 
        } 
}
action write_value_8_2_act() {
        register_write(value_8_2_reg, meta.cache_index, nc_value_8.value_8_2);
}
table write_value_8_2 {
        actions {
                write_value_8_2_act;
        }
}
action write_value_8_3_act() {
        register_write(value_8_3_reg, meta.cache_index, nc_value_8.value_8_3);
}
table write_value_8_3 {
        actions {
                write_value_8_3_act;
        }
}
action write_value_8_4_act() {
        register_write(value_8_4_reg, meta.cache_index, nc_value_8.value_8_4);
}
table write_value_8_4 {
        actions {
                write_value_8_4_act;
        }
}


action remove_value_header_1_act() {
        subtract_from_field(ipv4.totalLen, 16);
        subtract_from_field(udp.len, 16);
	remove_header(nc_value_1);
}
table remove_value_header_1 {
	actions {
		remove_value_header_1_act;
        }
}

action remove_value_header_2_act() { 
        subtract_from_field(ipv4.totalLen, 16);
        subtract_from_field(udp.len, 16);
        remove_header(nc_value_2);
}
table remove_value_header_2 {
        actions { 
                remove_value_header_2_act;
        } 
}

action remove_value_header_3_act() { 
        subtract_from_field(ipv4.totalLen, 16);
        subtract_from_field(udp.len, 16);
        remove_header(nc_value_3);
}
table remove_value_header_3 {
        actions { 
                remove_value_header_3_act;
        } 
}

action remove_value_header_4_act() { 
        subtract_from_field(ipv4.totalLen, 16);
        subtract_from_field(udp.len, 16);
        remove_header(nc_value_4);
}
table remove_value_header_4 {
        actions { 
                remove_value_header_4_act;
        } 
}

action remove_value_header_5_act() { 
        subtract_from_field(ipv4.totalLen, 16);
        subtract_from_field(udp.len, 16);
        remove_header(nc_value_5);
}
table remove_value_header_5 {
        actions { 
                remove_value_header_5_act;
        } 
}

action remove_value_header_6_act() { 
        subtract_from_field(ipv4.totalLen, 16);
        subtract_from_field(udp.len, 16);
        remove_header(nc_value_6);
}
table remove_value_header_6 {
        actions { 
                remove_value_header_6_act;
        } 
}

action remove_value_header_7_act() { 
        subtract_from_field(ipv4.totalLen, 16);
        subtract_from_field(udp.len, 16);
        remove_header(nc_value_7);
}
table remove_value_header_7 {
        actions { 
                remove_value_header_7_act;
        } 
}

action remove_value_header_8_act() { 
        subtract_from_field(ipv4.totalLen, 16);
        subtract_from_field(udp.len, 16);
        remove_header(nc_value_8);
}
table remove_value_header_8 {
        actions { 
                remove_value_header_8_act;
        } 
}

     
control process_value {
    if (nc_hdr.op == NC_READ_REQUEST and meta.cache_valid == 1) {
        apply (reply_read_hit_before);
    }

    if (nc_hdr.op == NC_READ_REQUEST and meta.cache_valid == 1) {
	apply (add_value_header_1);
        apply (read_value_1_1);
        apply (read_value_1_2);
        apply (read_value_1_3);
        apply (read_value_1_4);
    }
    else if (nc_hdr.op == NC_UPDATE_REPLY and nc_cache_md.cache_exist == 1) {
	apply (write_value_1_1);
        apply (write_value_1_2);
        apply (write_value_1_3);
        apply (write_value_1_4);
        apply (remove_value_header_1);
    }

    if (nc_hdr.op == NC_READ_REQUEST and meta.cache_valid == 1) {
        apply (add_value_header_2);
        apply (read_value_2_1);
        apply (read_value_2_2);
        apply (read_value_2_3);
        apply (read_value_2_4);
    }
    else if (nc_hdr.op == NC_UPDATE_REPLY and nc_cache_md.cache_exist == 1) {
        apply (write_value_2_1);
        apply (write_value_2_2);
        apply (write_value_2_3);
        apply (write_value_2_4);
        apply (remove_value_header_2);
    }

    if (nc_hdr.op == NC_READ_REQUEST and meta.cache_valid == 1) {
        apply (add_value_header_3);
        apply (read_value_3_1);
        apply (read_value_3_2);
        apply (read_value_3_3);
        apply (read_value_3_4);
    }
    else if (nc_hdr.op == NC_UPDATE_REPLY and nc_cache_md.cache_exist == 1) {
        apply (write_value_3_1);
        apply (write_value_3_2);
        apply (write_value_3_3);
        apply (write_value_3_4);
        apply (remove_value_header_3);
    }

    if (nc_hdr.op == NC_READ_REQUEST and meta.cache_valid == 1) {
        apply (add_value_header_1);
        apply (read_value_4_1);
        apply (read_value_4_2);
        apply (read_value_4_3);
        apply (read_value_4_4);
    }
    else if (nc_hdr.op == NC_UPDATE_REPLY and nc_cache_md.cache_exist == 1) {
        apply (write_value_4_1);
        apply (write_value_4_2);
        apply (write_value_4_3);
        apply (write_value_4_4);
        apply (remove_value_header_4);
    }

    if (nc_hdr.op == NC_READ_REQUEST and meta.cache_valid == 1) {
        apply (add_value_header_5);
        apply (read_value_5_1);
        apply (read_value_5_2);
        apply (read_value_5_3);
        apply (read_value_5_4);
    }
    else if (nc_hdr.op == NC_UPDATE_REPLY and nc_cache_md.cache_exist == 1) {
        apply (write_value_5_1);
        apply (write_value_5_2);
        apply (write_value_5_3);
        apply (write_value_5_4);
        apply (remove_value_header_5);
    }

    if (nc_hdr.op == NC_READ_REQUEST and meta.cache_valid == 1) {
        apply (add_value_header_6);
        apply (read_value_6_1);
        apply (read_value_6_2);
        apply (read_value_6_3);
        apply (read_value_6_4);
    }
    else if (nc_hdr.op == NC_UPDATE_REPLY and nc_cache_md.cache_exist == 1) {
        apply (write_value_6_1);
        apply (write_value_6_2);
        apply (write_value_6_3);
        apply (write_value_6_4);
        apply (remove_value_header_6);
    }

    if (nc_hdr.op == NC_READ_REQUEST and meta.cache_valid == 1) {
        apply (add_value_header_7);
        apply (read_value_7_1);
        apply (read_value_7_2);
        apply (read_value_7_3);
        apply (read_value_7_4);
    }
    else if (nc_hdr.op == NC_UPDATE_REPLY and nc_cache_md.cache_exist == 1) {
        apply (write_value_7_1);
        apply (write_value_7_2);
        apply (write_value_7_3);
        apply (write_value_7_4);
        apply (remove_value_header_7);
    }

    if (nc_hdr.op == NC_READ_REQUEST and meta.cache_valid == 1) {
        apply (add_value_header_8);
        apply (read_value_8_1);
        apply (read_value_8_2);
        apply (read_value_8_3);
        apply (read_value_8_4);
    }
    else if (nc_hdr.op == NC_UPDATE_REPLY and nc_cache_md.cache_exist == 1) {
        apply (write_value_8_1);
        apply (write_value_8_2);
        apply (write_value_8_3);
        apply (write_value_8_4);
        apply (remove_value_header_8);
    }

    if (nc_hdr.op == NC_READ_REQUEST and meta.cache_valid == 1) {
        apply (reply_read_hit_after);
}



/* OLD DEFINITIONS USING C MACROS:
value headers -->
#define HEADER_VALUE(i) \
    header_type nc_value_##i##_t { \
        fields { \
            value_##i##_1: 32; \
            value_##i##_2: 32; \
            value_##i##_3: 32; \
            value_##i##_4: 32; \
        } \
    } \
    header nc_value_##i##_t nc_value_##i;

parser for nc_value fields in hdr -->
#define PARSER_VALUE(i, ip1) \
    parser parse_nc_value_##i { \
        extract (nc_value_##i); \
        return parse_nc_value_##ip1; \
    }
#define FINAL_PARSER(i) \
    parser parse_nc_value_##i { \
        return ingress; \
    }

reg arrays def -->
#define REGISTER_VALUE_SLICE(i, j) \
    register value_##i##_##j##_reg { \
        width: 32; \
        instance_count: NUM_CACHE; \
    }

#define REGISTER_VALUE(i) \
    REGISTER_VALUE_SLICE(i, 1) \
    REGISTER_VALUE_SLICE(i, 2) \
    REGISTER_VALUE_SLICE(i, 3) \
    REGISTER_VALUE_SLICE(i, 4)

action + table defs for read value -->
#define ACTION_READ_VALUE_SLICE(i, j) \
    action read_value_##i##_##j##_act() { \
        register_read(nc_value_##i.value_##i##_##j, value_##i##_##j##_reg, nc_cache_md.cache_index); \
    }

#define ACTION_READ_VALUE(i) \
    ACTION_READ_VALUE_SLICE(i, 1) \
    ACTION_READ_VALUE_SLICE(i, 2) \
    ACTION_READ_VALUE_SLICE(i, 3) \
    ACTION_READ_VALUE_SLICE(i, 4)

#define TABLE_READ_VALUE_SLICE(i, j) \
    table read_value_##i##_##j { \
        actions { \
            read_value_##i##_##j##_act; \
        } \
    }

#define TABLE_READ_VALUE(i) \
    TABLE_READ_VALUE_SLICE(i, 1) \
    TABLE_READ_VALUE_SLICE(i, 2) \
    TABLE_READ_VALUE_SLICE(i, 3) \
    TABLE_READ_VALUE_SLICE(i, 4)

action + table defs for add value headers -->
#define ACTION_ADD_VALUE_HEADER(i) \
    action add_value_header_##i##_act() { \
        add_to_field(ipv4.totalLen, 16);\
        add_to_field(udp.len, 16);\
        add_header(nc_value_##i); \
    }

#define TABLE_ADD_VALUE_HEADER(i) \
    table add_value_header_##i { \
        actions { \
            add_value_header_##i##_act; \
        } \
    }

write cache value to header -->
#define ACTION_WRITE_VALUE_SLICE(i, j) \
    action write_value_##i##_##j##_act() { \
        register_write(value_##i##_##j##_reg, nc_cache_md.cache_index, nc_value_##i.value_##i##_##j); \
    }

#define ACTION_WRITE_VALUE(i) \
    ACTION_WRITE_VALUE_SLICE(i, 1) \
    ACTION_WRITE_VALUE_SLICE(i, 2) \
    ACTION_WRITE_VALUE_SLICE(i, 3) \
    ACTION_WRITE_VALUE_SLICE(i, 4)

#define TABLE_WRITE_VALUE_SLICE(i, j) \
    table write_value_##i##_##j { \
        actions { \
            write_value_##i##_##j##_act; \
        } \
    }

#define TABLE_WRITE_VALUE(i) \
    TABLE_WRITE_VALUE_SLICE(i, 1) \
    TABLE_WRITE_VALUE_SLICE(i, 2) \
    TABLE_WRITE_VALUE_SLICE(i, 3) \
    TABLE_WRITE_VALUE_SLICE(i, 4)

remove value headers -->
#define ACTION_REMOVE_VALUE_HEADER(i) \
    action remove_value_header_##i##_act() { \
        subtract_from_field(ipv4.totalLen, 16);\
        subtract_from_field(udp.len, 16);\
        remove_header(nc_value_##i); \
    }

#define TABLE_REMOVE_VALUE_HEADER(i) \
    table remove_value_header_##i { \
        actions { \
            remove_value_header_##i##_act; \
        } \
    }


process_value control -->
#define CONTROL_PROCESS_VALUE(i) \
    control process_value_##i { \
        if (nc_hdr.op == NC_READ_REQUEST and nc_cache_md.cache_valid == 1) { \
            apply (add_value_header_##i); \
            apply (read_value_##i##_1); \
            apply (read_value_##i##_2); \
            apply (read_value_##i##_3); \
            apply (read_value_##i##_4); \
        } \
        else if (nc_hdr.op == NC_UPDATE_REPLY and nc_cache_md.cache_exist == 1) { \
            apply (write_value_##i##_1); \
            apply (write_value_##i##_2); \
            apply (write_value_##i##_3); \
            apply (write_value_##i##_4); \
            apply (remove_value_header_##i); \
        } \
    }




handling values -->
#define HANDLE_VALUE(i, ip1) \
    HEADER_VALUE(i) \
    PARSER_VALUE(i, ip1) \
    REGISTER_VALUE(i) \
    ACTION_READ_VALUE(i) \
    TABLE_READ_VALUE(i) \
    ACTION_ADD_VALUE_HEADER(i) \
    TABLE_ADD_VALUE_HEADER(i) \
    ACTION_WRITE_VALUE(i) \
    TABLE_WRITE_VALUE(i) \
    ACTION_REMOVE_VALUE_HEADER(i) \
    TABLE_REMOVE_VALUE_HEADER(i) \
    CONTROL_PROCESS_VALUE(i)

HANDLE_VALUE(1, 2)
HANDLE_VALUE(2, 3)
HANDLE_VALUE(3, 4)
HANDLE_VALUE(4, 5)
HANDLE_VALUE(5, 6)
HANDLE_VALUE(6, 7)
HANDLE_VALUE(7, 8)
HANDLE_VALUE(8, 9)
FINAL_PARSER(9)




*/
