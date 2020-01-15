/* -*- P4_16 -*- */
#define HASH_BASE 10
#define HASH_MAX 1023


//#include <core.p4>
//#include <v1model.p4>

// Headers and Metadata definitions

header_type ethernet_t {
    fields {
    	dstAddr : 48;
    	srcAddr : 48;
    	etherType : 16;
    }
}

header ethernet_t ethernet;

header_type ipv4_t {
    fields {
    	version : 4;
    	ihl : 4;
    	diffserv : 8;
    	totalLen : 16;
    	identification : 16;
    	flags : 3;
    	fragOffset : 13;
    	ttl : 8;
    	protocol : 8;
    	hdrChecksum : 16;
    	srcAddr : 32;
    	dstAddr : 32;
    }
}

header ipv4_t ipv4;

header_type custom_metadata_t {
    fields {
	my_flowID : 64;
	my_estimated_count : 64;
	already_matched : 1;

	carry_min : 64;
	carry_min_plus_one : 64;
	min_stage : 8;
	do_recirculate : 1;
	orig_egr_port : 9;

        hashed_address_s1 : 32;
        hashed_address_s2 : 32;
        hashed_address_s3 : 32;
        hashed_address_s4 : 32;
        hashed_address_s5 : 32;
        hashed_address_s6 : 32;
        hashed_address_s7 : 32;
        hashed_address_s8 : 32;

	random_bits : 64;
	random_bits_short : 12;
	tmp_existing_flow_id : 64;
	tmp_existing_flow_count : 64;
    }
}

metadata custom_metadata_t meta;


// Standard IPv4 parser, dummy ingress processing

parser start {
	return parse_ethernet;
}

parser parse_ethernet {
	extract(ethernet);
	return select(latest.etherType) {
		0x800: parse_ipv4;
		default: ingress;
	}
}

parser parse_ipv4 {
	extract(ipv4);
	return ingress;
}


action repeater_a() {
	subtract(standard_metadata.egress_spec, 9, standard_metadata.ingress_port);
}
table repeater {
	actions {
		repeater_a;
	}
}

action drop_a() {
	drop();
}
table drop {
	actions {
		drop_a;
	}
}

control ingress {
	if (valid(ipv4)) apply(repeater);
	if (not valid(ipv4)) apply(drop);
}

// =========== Start implementation of PRECISION ============
// A brief introduction to Precision algorithm:
// 1. We maintain many (flow ID, packet count) tuples
// 2. When new packet comes and a tuple already exist for this flow, we increment the counter.
//    Otherwise, we simulate Space-Saving/RAP algorithm, find the approximate minimum counter and evict.
// 3. We use recirculation to evict entry and evict with probability 1/(min+1).
// In this example, we implement d=3 version of PRECISON, which maintain 3 pairs of flow tables.


// this is all defined in the egress pipeline

register flow_table_id_1 {
	width: 64;
	instance_count: 1024;
}
register flow_table_id_2 {
        width: 64;
        instance_count: 1024;
}
register flow_table_id_3 {
        width: 64;
        instance_count: 1024;
}
register flow_table_id_4 {
        width: 64;
        instance_count: 1024;
}
register flow_table_id_5 {
        width: 64;
        instance_count: 1024;
}
register flow_table_id_6 {
        width: 64;
        instance_count: 1024;
}
register flow_table_id_7 {
        width: 64;
        instance_count: 1024;
}
register flow_table_id_8 {
        width: 64;
        instance_count: 1024;
}

register flow_table_ctr_1 {
	width: 64;
	instance_count: 1024;
}

register flow_table_ctr_2 {
        width: 64;
        instance_count: 1024;
}
register flow_table_ctr_3 {
        width: 64;
        instance_count: 1024;
}
register flow_table_ctr_4 {
        width: 64;
        instance_count: 1024;
}
register flow_table_ctr_5 {
        width: 64;
        instance_count: 1024;
}
register flow_table_ctr_6 {
        width: 64;
        instance_count: 1024;
}
register flow_table_ctr_7 {
        width: 64;
        instance_count: 1024;
}
register flow_table_ctr_8 {
        width: 64;
        instance_count: 1024;
}

action compute_flow_id_a() {
	// should use mask here
	modify_field(meta.my_flowID, ipv4.srcAddr);
	modify_field(meta.my_flowID, ipv4.dstAddr);
}

table compute_flow_id {
	actions {
		compute_flow_id_a;
	}
}

field_list hash_1 {
        ipv4.srcAddr;
        7;
        ipv4.dstAddr;
}
field_list_calculation hashcalc_1 {
        input {hash_1;}
        algorithm: crc16;
        output_width: 32;
}

action compute_reg_index_a_1() {
	modify_field_with_hash_based_offset(meta.hashed_address_s1, HASH_BASE, hashcalc_1, 32);
}
table compute_reg_index_1 {
	actions {
		compute_reg_index_a_1;
	}
}

field_list hash_2 {
	3;
        ipv4.srcAddr;
        5;
        ipv4.dstAddr;
}
field_list_calculation hashcalc_2 {
        input {hash_2;}
        algorithm: crc16;
        output_width: 32;
}
action compute_reg_index_a_2() {
	modify_field_with_hash_based_offset(meta.hashed_address_s2, HASH_BASE, hashcalc_2, 32);
}
table compute_reg_index_2 {
        actions {
                compute_reg_index_a_2;
        }
}

field_list hash_3 {
	2;
        ipv4.srcAddr;
        1;
        ipv4.dstAddr;
}
field_list_calculation hashcalc_3 {
        input {hash_3;}
        algorithm: crc16;
        output_width: 32;
}
action compute_reg_index_a_3() {
	modify_field_with_hash_based_offset(meta.hashed_address_s3, HASH_BASE, hashcalc_3, 32);
}
table compute_reg_index_3 {
        actions {
                compute_reg_index_a_3;
        }
}

field_list hash_4 {
	3;
        ipv4.srcAddr;
        7;
        ipv4.dstAddr;
}
field_list_calculation hashcalc_4 {
        input {hash_4;}
        algorithm: crc16;
        output_width: 32;
}
action compute_reg_index_a_4() {
	modify_field_with_hash_based_offset(meta.hashed_address_s4, HASH_BASE, hashcalc_4, 32);
}
table compute_reg_index_4 {
        actions {
                compute_reg_index_a_4;
        }
}

field_list hash_5 {
        ipv4.srcAddr;
        13;
        ipv4.dstAddr;
}
field_list_calculation hashcalc_5 {
        input {hash_5;}
        algorithm: crc16;
        output_width: 32;
}
action compute_reg_index_a_5() {
	modify_field_with_hash_based_offset(meta.hashed_address_s5, HASH_BASE, hashcalc_5, 32);
}
table compute_reg_index_5 {
        actions {
                compute_reg_index_a_5;
        }
}

field_list hash_6 {
        ipv4.srcAddr;
        11;
        ipv4.dstAddr;
}
field_list_calculation hashcalc_6 {
        input {hash_6;}
        algorithm: crc16;
        output_width: 32;
}
action compute_reg_index_a_6() {
	modify_field_with_hash_based_offset(meta.hashed_address_s6, HASH_BASE, hashcalc_6, 32);
}
table compute_reg_index_6 {
        actions {
                compute_reg_index_a_6;
        }
}

field_list hash_7 {
        ipv4.srcAddr;
        5;
        ipv4.dstAddr;
}
field_list_calculation hashcalc_7 {
        input {hash_7;}
        algorithm: crc16;
        output_width: 32;
}
action compute_reg_index_a_7() {
	modify_field_with_hash_based_offset(meta.hashed_address_s7, HASH_BASE, hashcalc_7, 32);
}
table compute_reg_index_7 {
        actions {
                compute_reg_index_a_7;
        }
}

field_list hash_8 {
        ipv4.srcAddr;
        3;
        ipv4.dstAddr;
}
field_list_calculation hashcalc_8 {
        input {hash_8;}
        algorithm: crc16;
        output_width: 32;
}
action compute_reg_index_a_8() {
	modify_field_with_hash_based_offset(meta.hashed_address_s8, HASH_BASE, hashcalc_8, 32);
}
table compute_reg_index_8 {
        actions {
                compute_reg_index_a_8;
        }
}


action set_est_count_a() {
	modify_field(meta.my_estimated_count,0);
}
table set_est_count {
	actions {
		set_est_count_a;
	}
}

action read_id_a_1() {
	register_read(meta.tmp_existing_flow_id, flow_table_id_1, meta.hashed_address_s1);
}
table read_id_1 {
	actions {
		read_id_a_1;
	}
}

action read_c_a_1() {
	register_read(meta.tmp_existing_flow_count, flow_table_ctr_1, meta.hashed_address_s1); 
}
table read_c_1 {
        actions {
                read_c_a_1;
        }
}

action read_id_a_2() {
        register_read(meta.tmp_existing_flow_id, flow_table_id_2, meta.hashed_address_s2);
}
table read_id_2 {
        actions {
                read_id_a_2;
        }
}

action read_c_a_2() {
        register_read(meta.tmp_existing_flow_count, flow_table_ctr_2, meta.hashed_address_s2);
}
table read_c_2 {
        actions {
                read_c_a_2;
        }
}

action read_id_a_3() {
        register_read(meta.tmp_existing_flow_id, flow_table_id_3, meta.hashed_address_s3);
}
table read_id_3 {
        actions {
                read_id_a_3;
        }
}

action read_c_a_3() {
        register_read(meta.tmp_existing_flow_count, flow_table_ctr_3, meta.hashed_address_s3);
}
table read_c_3 {
        actions {
                read_c_a_3;
        }
}

action read_id_a_4() {
        register_read(meta.tmp_existing_flow_id, flow_table_id_4, meta.hashed_address_s4);
}
table read_id_4 {
        actions {
                read_id_a_4;
        }
}

action read_c_a_4() {
        register_read(meta.tmp_existing_flow_count, flow_table_ctr_4, meta.hashed_address_s4);
}
table read_c_4 {
        actions {
                read_c_a_4;
        }
}

action read_id_a_5() {
        register_read(meta.tmp_existing_flow_id, flow_table_id_5, meta.hashed_address_s5);
}
table read_id_5 {
        actions {
                read_id_a_5;
        }
}

action read_c_a_5() {
        register_read(meta.tmp_existing_flow_count, flow_table_ctr_5, meta.hashed_address_s5);
}
table read_c_5 {
        actions {
                read_c_a_5;
        }
}

action read_id_a_6() {
        register_read(meta.tmp_existing_flow_id, flow_table_id_6, meta.hashed_address_s6);
}
table read_id_6 {
        actions {
                read_id_a_6;
        }
}

action read_c_a_6() {
        register_read(meta.tmp_existing_flow_count, flow_table_ctr_6, meta.hashed_address_s6);
}
table read_c_6 {
        actions {
                read_c_a_6;
        }
}

action read_id_a_7() {
        register_read(meta.tmp_existing_flow_id, flow_table_id_7, meta.hashed_address_s7);
}
table read_id_7 {
        actions {
                read_id_a_7;
        }
}

action read_c_a_7() {
        register_read(meta.tmp_existing_flow_count, flow_table_ctr_7, meta.hashed_address_s7);
}
table read_c_7 {
        actions {
                read_c_a_7;
        }
}

action read_id_a_8() {
        register_read(meta.tmp_existing_flow_id, flow_table_id_8, meta.hashed_address_s8);
}
table read_id_8 {
        actions {
                read_id_a_8;
        }
}

action read_c_a_8() {
        register_read(meta.tmp_existing_flow_count, flow_table_ctr_8, meta.hashed_address_s8);
}
table read_c_8 {
        actions {
                read_c_a_8;
        }
}

action write_id_a_1() {
	register_write(flow_table_id_1, meta.hashed_address_s1, meta.my_flowID);
}
table write_id_1 {
	actions {
		write_id_a_1;
	}
}

action write_id_a_2() {
        register_write(flow_table_id_2, meta.hashed_address_s2, meta.my_flowID);
}
table write_id_2 {
        actions {
                write_id_a_2;
        }
}

action write_id_a_3() {
        register_write(flow_table_id_3, meta.hashed_address_s3, meta.my_flowID);
}
table write_id_3 {
        actions {
                write_id_a_3;
        }
}

action write_id_a_4() {
        register_write(flow_table_id_4, meta.hashed_address_s4, meta.my_flowID);
}
table write_id_4 {
        actions {
                write_id_a_4;
        }
}

action write_id_a_5() {
        register_write(flow_table_id_5, meta.hashed_address_s5, meta.my_flowID);
}
table write_id_5 {
        actions {
                write_id_a_5;
        }
}

action write_id_a_6() {
        register_write(flow_table_id_6, meta.hashed_address_s6, meta.my_flowID);
}
table write_id_6 {
        actions {
                write_id_a_6;
        }
}

action write_id_a_7() {
        register_write(flow_table_id_7, meta.hashed_address_s7, meta.my_flowID);
}
table write_id_7 {
        actions {
                write_id_a_7;
        }
}

action write_id_a_8() {
        register_write(flow_table_id_8, meta.hashed_address_s8, meta.my_flowID);
}
table write_id_8 {
        actions {
                write_id_a_8;
        }
}

action add_count_a() {
	add_to_field(meta.tmp_existing_flow_count, 1);
}
table add_count {
	actions {
		add_count_a;
	}
}
table add_count_2 {
        actions {
                add_count_a;
        }
}
table add_count_3 {
        actions {
                add_count_a;
        }
}
table add_count_4 {
        actions {
                add_count_a;
        }
}
table add_count_5 {
        actions {
                add_count_a;
        }
}
table add_count_6 {
        actions {
                add_count_a;
        }
}
table add_count_7 {
        actions {
                add_count_a;
        }
}
table add_count_8 {
        actions {
                add_count_a;
        }
}


action write_c_a_1() {
	register_write(flow_table_ctr_1, meta.hashed_address_s1, meta.tmp_existing_flow_count);
}
table write_c_1 {
	actions {
		write_c_a_1;
	}
}

action write_c_a_2() {
        register_write(flow_table_ctr_2, meta.hashed_address_s2, meta.tmp_existing_flow_count);
}
table write_c_2 {
        actions {
                write_c_a_2;
        }
}

action write_c_a_3() {
        register_write(flow_table_ctr_3, meta.hashed_address_s3, meta.tmp_existing_flow_count);
}
table write_c_3 {
        actions {
                write_c_a_3;
        }
}

action write_c_a_4() {
        register_write(flow_table_ctr_4, meta.hashed_address_s4, meta.tmp_existing_flow_count);
}
table write_c_4 {
        actions {
                write_c_a_4;
        }
}

action write_c_a_5() {
        register_write(flow_table_ctr_5, meta.hashed_address_s5, meta.tmp_existing_flow_count);
}
table write_c_5 {
        actions {
                write_c_a_5;
        }
}

action write_c_a_6() {
        register_write(flow_table_ctr_6, meta.hashed_address_s6, meta.tmp_existing_flow_count);
}
table write_c_6 {
        actions {
                write_c_a_6;
        }
}

action write_c_a_7() {
        register_write(flow_table_ctr_7, meta.hashed_address_s7, meta.tmp_existing_flow_count);
}
table write_c_7 {
        actions {
                write_c_a_7;
        }
}

action write_c_a_8() {
        register_write(flow_table_ctr_8, meta.hashed_address_s8, meta.tmp_existing_flow_count);
}
table write_c_8 {
        actions {
                write_c_a_8;
        }
}

action mod_count_a() {
	modify_field(meta.my_estimated_count, meta.tmp_existing_flow_count);
}
table mod_count {
	actions {
		mod_count_a;
	}
}

action mod_match_a() {
	modify_field(meta.already_matched,1);
}
table mod_match {
	actions {
		mod_match_a;
	}
}

action mod_min_a() {
	modify_field(meta.carry_min, meta.tmp_existing_flow_count);
}
table mod_min {
	actions {
		mod_min_a;
	}
}

action mod_stg_a_1() {
	modify_field(meta.min_stage,1);
}
table mod_stg_1 {
	actions {
		mod_stg_a_1;
	}
}
action mod_stg_a_2() {
        modify_field(meta.min_stage,2);
}
table mod_stg_2 {
        actions {
                mod_stg_a_2;
        }
}
action mod_stg_a_3() {
        modify_field(meta.min_stage,3);
}
table mod_stg_3 {
        actions {
                mod_stg_a_3;
        }
}
action mod_stg_a_4() {
        modify_field(meta.min_stage,4);
}
table mod_stg_4 {
        actions {
                mod_stg_a_4;
        }
}
action mod_stg_a_5() {
        modify_field(meta.min_stage,5);
}
table mod_stg_5 {
        actions {
                mod_stg_a_5;
        }
}
action mod_stg_a_6() {
        modify_field(meta.min_stage,6);
}
table mod_stg_6 {
        actions {
                mod_stg_a_6;
        }
}
action mod_stg_a_7() {
        modify_field(meta.min_stage,7);
}
table mod_stg_7 {
        actions {
                mod_stg_a_7;
        }
}
action mod_stg_a_8() {
        modify_field(meta.min_stage,8);
}
table mod_stg_8 {
        actions {
                mod_stg_a_8;
        }
}


field_list cln {
        meta.my_flowID;
        meta.my_estimated_count;
        meta.already_matched;

        meta.carry_min;
        meta.carry_min_plus_one;
        meta.min_stage;
        meta.do_recirculate;
        meta.orig_egr_port;

        meta.hashed_address_s1;
        meta.hashed_address_s2;
        meta.hashed_address_s3;
        meta.hashed_address_s4;
        meta.hashed_address_s5;
        meta.hashed_address_s6;
        meta.hashed_address_s7;
        meta.hashed_address_s8;

        meta.random_bits;
        meta.random_bits_short;
        meta.tmp_existing_flow_id;
        meta.tmp_existing_flow_count;
}

action clone_and_recirc_replace_entry(){
	clone_egress_pkt_to_egress(0, cln);
}

action none() {
	no_op();
}

table better_approximation {
	reads {
		meta.carry_min_plus_one : ternary;
		meta.random_bits : ternary;
		meta.random_bits_short : range;
	}
        actions {
                clone_and_recirc_replace_entry;
		none;
        }
        size : 128;
}


action rands_a() {
	modify_field(meta.random_bits, 64);
	modify_field(meta.random_bits_short, 12); 
}
table rands {
	actions {
		rands_a;
	}
}

action min_plus_a() {
	modify_field(meta.carry_min_plus_one, meta.carry_min);
	add_to_field(meta.carry_min_plus_one, 1);
}
table min_plus {
	actions {
		min_plus_a;
	}
}

action dst_mod_a() {
	modify_field(ethernet.dstAddr, 0xffffffffffff);
}
table dst_mod {
	actions {
		dst_mod_a;
	}
}

action src_mod_a() {
	// should use mask
	modify_field(ethernet.srcAddr, meta.my_estimated_count);
}
table src_mod {
	actions {
		src_mod_a;
	}
}

control read_1 {
	apply(read_id_1);
	apply(read_c_1);
}
control read_2 {
        apply(read_id_2);
        apply(read_c_2);
}
control read_3 {
        apply(read_id_3);
        apply(read_c_3);
}
control read_4 {
        apply(read_id_4);
        apply(read_c_4);
}
control read_5 {
        apply(read_id_5);
        apply(read_c_5);
}
control read_6 {
        apply(read_id_6);
        apply(read_c_6);
}
control read_7 {
        apply(read_id_7);
        apply(read_c_7);
}
control read_8 {
        apply(read_id_8);
        apply(read_c_8);
}


control write_1_mod {
	apply(write_id_1);
	apply(add_count);
	apply(write_c_1);
	apply(mod_count);
	apply(mod_match);
}
control write_2_mod {
        apply(write_id_2);
        apply(add_count_2);
        apply(write_c_2);
        apply(mod_count);
        apply(mod_match);
}
control write_3_mod {
        apply(write_id_3);
        apply(add_count_3);
        apply(write_c_3);
        apply(mod_count);
        apply(mod_match);
}
control write_4_mod {
        apply(write_id_4);
        apply(add_count_4);
        apply(write_c_4);
        apply(mod_count);
        apply(mod_match);
}
control write_5_mod {
        apply(write_id_5);
        apply(add_count_5);
        apply(write_c_5);
        apply(mod_count);
        apply(mod_match);
}
control write_6_mod {
        apply(write_id_6);
        apply(add_count_6);
        apply(write_c_6);
        apply(mod_count);
        apply(mod_match);
}
control write_7_mod {
        apply(write_id_7);
        apply(add_count_7);
        apply(write_c_7);
        apply(mod_count);
        apply(mod_match);
}
control write_8_mod {
        apply(write_id_8);
        apply(add_count_8);
        apply(write_c_8);
        apply(mod_count);
        apply(mod_match);
}


control mod_s_1 {
	apply(mod_min);
	apply(mod_stg_1);
}
control mod_s_2 {
        apply(mod_min);
        apply(mod_stg_2);
}
control mod_s_3 {
        apply(mod_min);
        apply(mod_stg_3);
}
control mod_s_4 {
        apply(mod_min);
        apply(mod_stg_4);
}
control mod_s_5 {
        apply(mod_min);
        apply(mod_stg_5);
}
control mod_s_6 {
        apply(mod_min);
        apply(mod_stg_6);
}
control mod_s_7 {
        apply(mod_min);
        apply(mod_stg_7);
}
control mod_s_8 {
        apply(mod_min);
        apply(mod_stg_8);
}

control already_2 {
	read_2();
	if(meta.tmp_existing_flow_count==0 or meta.tmp_existing_flow_id==meta.my_flowID)
		write_2_mod();
	if (meta.tmp_existing_flow_count!= 0 and meta.tmp_existing_flow_id!=meta.my_flowID and meta.carry_min>meta.tmp_existing_flow_count)
		mod_s_2();
}

control already_3 {
read_3();
                        if(meta.tmp_existing_flow_count==0 or meta.tmp_existing_flow_id==meta.my_flowID)
                                write_3_mod();
			if (meta.tmp_existing_flow_count!= 0 and meta.tmp_existing_flow_id!=meta.my_flowID and meta.carry_min>meta.tmp_existing_flow_count)
                                        mod_s_3(); 
}

control already_4 {
read_4();
                        if(meta.tmp_existing_flow_count==0 or meta.tmp_existing_flow_id==meta.my_flowID)
                                write_4_mod();
			if (meta.tmp_existing_flow_count!= 0 and meta.tmp_existing_flow_id!=meta.my_flowID and meta.carry_min>meta.tmp_existing_flow_count)
                                        mod_s_4();
}
control already_5 {
read_5();
                        if(meta.tmp_existing_flow_count==0 or meta.tmp_existing_flow_id==meta.my_flowID)
                                write_5_mod();
			if (meta.tmp_existing_flow_count!= 0 and meta.tmp_existing_flow_id!=meta.my_flowID and meta.carry_min>meta.tmp_existing_flow_count)
                                        mod_s_5();
}
control already_6 {
read_6();
                        if(meta.tmp_existing_flow_count==0 or meta.tmp_existing_flow_id==meta.my_flowID)
                                write_6_mod();
			if (meta.tmp_existing_flow_count!= 0 and meta.tmp_existing_flow_id!=meta.my_flowID and meta.carry_min>meta.tmp_existing_flow_count)
                                        mod_s_6();
}
control already_7 {
read_7();
                        if(meta.tmp_existing_flow_count==0 or meta.tmp_existing_flow_id==meta.my_flowID)
                                write_7_mod();
			if (meta.tmp_existing_flow_count!= 0 and meta.tmp_existing_flow_id!=meta.my_flowID and meta.carry_min>meta.tmp_existing_flow_count)
                                        mod_s_7();
}
control already_8 {
read_8();
                        if(meta.tmp_existing_flow_count==0 or meta.tmp_existing_flow_id==meta.my_flowID)
                                write_8_mod();
			if (meta.tmp_existing_flow_count!= 0 and meta.tmp_existing_flow_id!=meta.my_flowID and meta.carry_min>meta.tmp_existing_flow_count)
                                        mod_s_8();
}
control already_approx {
apply(rands);
                        apply(min_plus);
                        apply(better_approximation);
}

control type_0 {
read_1();
                if(meta.tmp_existing_flow_count==0 or meta.tmp_existing_flow_id==meta.my_flowID)
                        write_1_mod();
                if(meta.tmp_existing_flow_count!=0 and meta.tmp_existing_flow_id!=meta.my_flowID) 
                        mod_s_1();  

                if(meta.already_matched==0)
                        already_2();

                if(meta.already_matched==0)
                        already_3();
 
                if(meta.already_matched==0)
                        already_4();
 
                if(meta.already_matched==0)
                        already_5();

                if(meta.already_matched==0)
                        already_6();

                if(meta.already_matched==0)
                        already_7();

                if(meta.already_matched==0)
                        already_8();


                if(meta.already_matched==0)
                        already_approx();
}

control w_1 {
apply(write_id_1);
                        apply(add_count);
                        apply(write_c_1);
}
control w_2 {
apply(write_id_2);
                        apply(add_count_2);
                        apply(write_c_2);
}
control w_3 {
apply(write_id_3);
                        apply(add_count_3);
                        apply(write_c_3);
}
control w_4 {
apply(write_id_4);
                        apply(add_count_4);
                        apply(write_c_4);
}
control w_5 {
apply(write_id_5);
                        apply(add_count_5);
                        apply(write_c_5);
}
control w_6 {
apply(write_id_6);
                        apply(add_count_6);
                        apply(write_c_6);
}
control w_7 {
apply(write_id_7);
                        apply(add_count_7);
                        apply(write_c_7);
}
control w_8 {
apply(write_id_8);
                        apply(add_count_8);
                        apply(write_c_8);
}

control not_type_0 {
apply(drop);
                if(meta.min_stage==1)
                        w_1();
                if(meta.min_stage==2)
                        w_2();
                if(meta.min_stage==3)
                        w_3();
                if(meta.min_stage==4)
                        w_4();
                if(meta.min_stage==5)
                        w_5();
                if(meta.min_stage==6)
                        w_6();
                if(meta.min_stage==7)
                        w_7();
                if(meta.min_stage==8)
                        w_8();
}

control egress {
	apply(compute_flow_id);
	apply(compute_reg_index_1);
        apply(compute_reg_index_2);
        apply(compute_reg_index_3);
        apply(compute_reg_index_4);
        apply(compute_reg_index_5);
        apply(compute_reg_index_6);
        apply(compute_reg_index_7);
        apply(compute_reg_index_8);

	apply(set_est_count);

	//if(standard_metadata.instance_type==0)
	//	type_0();
	if(standard_metadata.instance_type!=0)
		not_type_0();

	
	apply(dst_mod);
	apply(src_mod);

}


// =========== End implementation of PRECISION ===========




