/*
P4 program using round-robin snapshots to estimate queue occupation.

Copyright 2018 Xiaoqi Chen, Princeton Cabernet Research Group
Questions should be directed to: xiaoqic@cs.princeton.edu
*/

// ==== Section 0. Constants, Macros ====

// Before the P4 code start, here we define some C preprocessor macros solely for the purpose of ease of programming.
// Mainly, we check the constants.
// This has nothing to do with P4; we happen to exploit the fact that P4 compilers use C preprocessor.

// Repeat the same macro 4 times; useful for repeat definition of registers etc. for each snapshot.
#define For4(FUN) FUN(0) FUN(1) FUN(2) FUN(3)

// One-action tables, for execute a single action.
#define _OAT(fn_name) table tb_## fn_name { \
	actions {fn_name;} \
	default_action: fn_name; \
}
//end _OAT

#define _OAT_Apply(fn_name) apply(tb_## fn_name)




// Counter size and register size allocation!
// Important: each Tofino stage has 48block*(16KBytes) memory, but you can use at most (8+1)*4 block per snap array if you want to fit 4. The +1 is due to Read/Write implementation (see doc).
// Maximum single-register size is (32+1)*16KBytes.
// (Feel free to abuse; the compiler will figure it out.)

// Define counters used in the Count-Min Sketch data structure.
// 32-bit counters are overkill. Use 16-bit is fine, just erase the lowest 8 bit in packet sizes.
#define SNAP_COUNTER_WIDTH 16
#define SNAP_COUNTER_SCALE_MINIMUM 8

// Define the interval (how many bytes of traffic) before switching to next snapshot.
// default: 1MB (chosen in original paper). Each snap remembers 1MB traffic on the wire.
#define SNAP_INTERVAL 1048576
#define SNAP_INTERVAL_BITS 20

// Maximum number of ports on the switch. Note that each register is partitioned into this many smaller "pages".
#define NUM_PORTS_TOTAL 64
#define NUM_PORTS_TOTAL_BITS 6

// Size of each memory "page". Requirement depends on how large the snap interval is, and how many flows/heavy flows are present.
// (How many counters does each data structure need? BTW, it's per-row. In total each snap uses 2x.)
#define REG_PAGE_SIZE 512
#define REG_PAGE_SIZE_BIT 9

// Multiply the above two, we get the total size per register. This number cannot be too large (per-stage memory constraint).
// (You'd better use less than 65536*16bit counter; this helps fit 4 snaps into 1 stage!)
#define REGISTER_TOTAL_SIZE 32768
#define REGISTER_TOTAL_SIZE_BITS 15

// Need two global counter registers, to save Snappy status for individual ports.
// This should be large enough, no need to change. As long as this is > #ports, we're good. (this may change in the future)
#define GLOBAL_COUNTER_REGISTER_SIZE NUM_PORTS_TOTAL
#define GLOBAL_COUNTER_REGISTER_SIZE_BITS NUM_PORTS_TOTAL_BITS
// BTW we always use 32 bits counters here; maximum supported by SALU


// Sanity check for all the above parameters......
#if !(SNAP_INTERVAL == 1<<SNAP_INTERVAL_BITS)
#error Need 2^SNAP_INTERVAL_BITS==SNAP_INTERVAL.
#endif

#if !(1<<(SNAP_COUNTER_WIDTH+SNAP_COUNTER_SCALE_MINIMUM) > SNAP_INTERVAL)
#error Counters in the snapshot registers (after scaling) are probably too small to save a flow sizes. Maximum flow size is equal to snapshot interval.
#endif

#if !(NUM_PORTS_TOTAL == 1<<NUM_PORTS_TOTAL_BITS)
#error Need 2^NUM_PORTS_TOTAL_BITS==NUM_PORTS_TOTAL.
#endif

#if !(REG_PAGE_SIZE == 1<<REG_PAGE_SIZE_BIT)
#error Need 2^REG_PAGE_SIZE_BIT==REG_PAGE_SIZE.
#endif

#if !(REGISTER_TOTAL_SIZE == 1<<REGISTER_TOTAL_SIZE_BITS)
#error Need 2^REGISTER_TOTAL_SIZE_BITS==REGISTER_TOTAL_SIZE.
#endif
// We need snapshot bit width be large enough to count large flows
#if !(REGISTER_TOTAL_SIZE_BITS==(REG_PAGE_SIZE_BIT+NUM_PORTS_TOTAL_BITS))
#error The register address size should be equal to (#pages * size per page). The lower address bits are in-page address, higher address bits are page ID.
#endif
// We need snapshot (pages) to be small enough to be cleaned thoroughly by cyclic cleaning
#if !(REG_PAGE_SIZE < SNAP_INTERVAL / 1600)
#error The register page is too large for cyclic cleaning in one interval; assuming maximum 1600 bytes packets, you only have (SNAP_INTERVAL / 1600) packets per inteval.
#endif

// Now, the start of actual P4 program.

// ==== Section 1. includes, headers, parsers (not relevant to snappy) ====


#include <tofino/intrinsic_metadata.p4>
#include <tofino/constants.p4>
#include <tofino/stateful_alu_blackbox.p4>

header_type ethernet_t {
    fields {
        dstAddr : 48;
        srcAddr : 48;
        etherType : 16;
    }
}

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
        dstAddr: 32;
    }
}

header_type tcp_t {
    fields {
        srcPort : 16;
        dstPort : 16;
        seqNo : 32;
        ackNo : 32;
        dataOffset : 4;
        res : 3;
        ecn : 3;
        ctrl : 6;
        window : 16;
        checksum : 16;
        urgentPtr : 16;
    }
}

header_type udp_t {
    fields {
        srcPort : 16;
        dstPort : 16;
        hdr_length : 16;
        checksum : 16;
    }
}

#define IP_PROTOCOLS_TCP 6
#define IP_PROTOCOLS_UDP 17

header_type sampled_dummy_header_t {
	// A "dummy" header added to the original packet; desirable if we want to sample&submit some packets to CPU or a collector for deeper analysis.
	// IPv4+UDP!
    fields {
		// IPv4
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
        dstAddr: 32;

		// UDP
        srcPort : 16;
        dstPort : 16;
        hdr_length : 16;
        checksum : 16;

		// Data
		data_1: 32;
		data_2: 32;
    }
}
header sampled_dummy_header_t sampled_dummy_header;



parser start {
    return parse_ethernet;
}

header ethernet_t ethernet;

parser parse_ethernet {
    extract(ethernet);
    return select(latest.etherType) {
		0x000: parse_sampled_dummy_header;
        0x800 : parse_ipv4;
        default: ingress;
    }
}

parser parse_sampled_dummy_header {
	extract(sampled_dummy_header);
    return parse_ipv4;
}



header ipv4_t ipv4;

parser parse_ipv4 {
    extract(ipv4);
    return select(latest.fragOffset, latest.protocol) {
        IP_PROTOCOLS_TCP : parse_tcp;
        IP_PROTOCOLS_UDP : parse_udp;
        default: ingress;
    }
}

header tcp_t tcp;

parser parse_tcp {
    extract(tcp);
    return ingress;
}

header udp_t udp;

parser parse_udp {
    extract(udp);
    return ingress;
}


// ==== Section 2. Register programs ====
// Here we define the registers and the register access programs for Snappy's snapshot operations.
// Note that the memory index of register access is computed separately, independent of the access itself.

// We first define some temporary variables (using metadata in P4). To match hardware model closely, most variables are only written once.
// (Special case: the register access index, which will be "overwritten" if register is in cyclic cleaning mode.)

#define reg_indexvar_name(SNAPID, ROWID)  md_reg_index_s ## SNAPID ## _r ## ROWID


#define loop_define_metadata_per_snapshot(SNAPID)  \
reg_indexvar_name(SNAPID, 0): REGISTER_TOTAL_SIZE_BITS; \
reg_indexvar_name(SNAPID, 1): REGISTER_TOTAL_SIZE_BITS; \
snap_round_robin_action_s##SNAPID : 2;
//end loop_define_metadata_per_snapshot
// Round-robin variable: 1=write 2=read 3=clean (default: 0=nop)


// Metadata, for temp variables
header_type md_t {
    fields {
		// Global counters, read from two global registers
		global_per_port_pkt_counter: 32;
		global_per_port_byte_counter: 32;
		// Translate to local counters
		my_packet_size_for_cms: SNAP_COUNTER_WIDTH; //(real pkt size / 2^SNAP_COUNTER_SCALE_MINIMUM).
		snap_epoch: 32; // byte coutner / snap interval
		snap_roundrobin_epoch: 2; // assume 4 snaps for now, lowest 2 bit of epoch
		cyclic_clean_epoch: REG_PAGE_SIZE_BIT; //lowest bits of pkt counter


		// Now we compute the hashes and get the register access locations... this may need many more stages than necessary; I love P4_16.
		port_number_lower: NUM_PORTS_TOTAL_BITS;
		hashed_in_page_addr_r0: REG_PAGE_SIZE_BIT;
		hashed_in_page_addr_r1: REG_PAGE_SIZE_BIT;
		// For each snap, we set addr=port*page_size + hashed_in_page_addr
		// If in cleaning mode, we add cyclic_clean_epoch instead.


		// Define register access indexes. We need to pre-populate these index, since the actual stage only allows one index variable when executing blackbox
		For4(loop_define_metadata_per_snapshot)

	}
}
metadata md_t md;

// Global register arrays, act as accumulator/counter
register reg_global_packet_counter
{ width : 32; instance_count : GLOBAL_COUNTER_REGISTER_SIZE; }

register reg_global_bytes_counter
{ width : 32; instance_count : GLOBAL_COUNTER_REGISTER_SIZE; }

blackbox stateful_alu salu_update_packet_count {
	reg: 					reg_global_packet_counter;
	update_lo_1_value: 		register_lo + 1;
	update_lo_1_predicate: 	1;
	output_dst: 			md.global_per_port_pkt_counter;
	output_value: 			register_lo;
}

blackbox stateful_alu salu_update_bytes_count {
	reg: 					reg_global_bytes_counter;
	update_lo_1_value: 		register_lo + eg_intr_md.pkt_length;
	update_lo_1_predicate: 	1;
	output_dst: 			md.global_per_port_byte_counter;
	output_value: 			register_lo;
}
action prepare_port_number_lower(){
	//to make sure we're not accessing the regiset out-of-bound, we only use lower bits of port number value.
	modify_field(md.port_number_lower,eg_intr_md.egress_port);
}
_OAT(prepare_port_number_lower)
action update_packet_count(){
	salu_update_packet_count.execute_stateful_alu(md.port_number_lower);
}
_OAT(update_packet_count)
action update_bytes_count(){
	salu_update_bytes_count.execute_stateful_alu(md.port_number_lower);
}
_OAT(update_bytes_count)

// After acquiring global count, we get lower bits for our snapshot epoch
action prepare_interval_and_epoch(){
	shift_right(md.snap_epoch, md.global_per_port_byte_counter, SNAP_INTERVAL_BITS); //not used, for debug only; lower bits should equal snap_roundrobin_epoch
	shift_right(md.snap_roundrobin_epoch, md.global_per_port_byte_counter, SNAP_INTERVAL_BITS);

	shift_right(md.my_packet_size_for_cms, eg_intr_md.pkt_length, SNAP_COUNTER_SCALE_MINIMUM);

	modify_field(md.cyclic_clean_epoch, md.global_per_port_pkt_counter);
}
_OAT(prepare_interval_and_epoch)

action prepare_individual_epoch_stage(){
	#define add_offset_each_snap_rr(SNAPID) add(md.snap_round_robin_action_s## SNAPID, SNAPID, md.snap_roundrobin_epoch);
	//For4(add_offset_each_snap_rr)
	add_offset_each_snap_rr(0)
}
_OAT(prepare_individual_epoch_stage)

// Now we also compute hash locations for each row; these are shared among snapshots.
// Location are for in-page offset; thus location address length is REG_PAGE_SIZE_BIT
	// we need two hash functions for two different rows...
field_list tcp_hash_field_list_0 {
    ipv4.protocol;
    ipv4.srcAddr;
    ipv4.dstAddr;
	tcp.srcPort;
	tcp.dstPort;
}
field_list_calculation tcp_hash_field_list_calc_0 {
    input {
        tcp_hash_field_list_0;
    }
    algorithm : crc_32;
    output_width : REG_PAGE_SIZE_BIT;
}
field_list tcp_hash_field_list_1 {
    ipv4.dstAddr;
	tcp.dstPort;
    ipv4.protocol;
    ipv4.srcAddr;
	tcp.srcPort;
}
field_list_calculation tcp_hash_field_list_calc_1 {
    input {
        tcp_hash_field_list_1;
    }
    algorithm : crc_32q;
    output_width : REG_PAGE_SIZE_BIT;
}

field_list udp_hash_field_list_0 {
    ipv4.protocol;
    ipv4.srcAddr;
    ipv4.dstAddr;
	udp.srcPort;
	udp.dstPort;
}
field_list_calculation udp_hash_field_list_calc_0 {
    input {
        udp_hash_field_list_0;
    }
    algorithm : crc_32;
    output_width : REG_PAGE_SIZE_BIT;
}
field_list udp_hash_field_list_1 {
    ipv4.dstAddr;
	udp.dstPort;
    ipv4.protocol;
    ipv4.srcAddr;
	udp.srcPort;
}
field_list_calculation udp_hash_field_list_calc_1 {
    input {
        udp_hash_field_list_1;
    }
    algorithm : crc_32q;
    output_width : REG_PAGE_SIZE_BIT;
}


action prepare_tcp_hash_loc(){
	modify_field_with_hash_based_offset(md.hashed_in_page_addr_r0,0,tcp_hash_field_list_calc_0,REG_PAGE_SIZE);
	modify_field_with_hash_based_offset(md.hashed_in_page_addr_r1,0,tcp_hash_field_list_calc_1,REG_PAGE_SIZE);
}
_OAT(prepare_tcp_hash_loc)
action prepare_udp_hash_loc(){
	modify_field_with_hash_based_offset(md.hashed_in_page_addr_r0,0,udp_hash_field_list_calc_0,REG_PAGE_SIZE);
	modify_field_with_hash_based_offset(md.hashed_in_page_addr_r1,0,udp_hash_field_list_calc_1,REG_PAGE_SIZE);
}
_OAT(prepare_udp_hash_loc)

// Now we prepare the register access addresses. First, we multiply port number to get page's base addr
action prepare_base_addr_for_all_snaps(){
	#define assign_page_base_by_multiply(SNAPID) \
	shift_left(md.reg_indexvar_name(SNAPID, 0), md.port_number_lower, REG_PAGE_SIZE_BIT); \
	shift_left(md.reg_indexvar_name(SNAPID, 1), md.port_number_lower, REG_PAGE_SIZE_BIT);
	For4(assign_page_base_by_multiply)
}
_OAT(prepare_base_addr_for_all_snaps)

action calculate_reg_addr_regular_s0(){
	add_to_field(md.reg_indexvar_name(0, 0), md.hashed_in_page_addr_r0);
	add_to_field(md.reg_indexvar_name(0, 1), md.hashed_in_page_addr_r1);
}
action calculate_reg_addr_cleaning_s0(){
	add_to_field(md.reg_indexvar_name(0, 0), md.cyclic_clean_epoch);
	add_to_field(md.reg_indexvar_name(0, 1), md.cyclic_clean_epoch);
}
table tb_calculate_reg_addr_s0 {
	reads {
		md.snap_round_robin_action_s0 : exact;
	}
	actions {
		calculate_reg_addr_regular_s0;
		calculate_reg_addr_cleaning_s0;
	}
	size: 4;
}


// Snapshot Count-Min Sketch registers;  slightly more complicated programs.
// A count-min sketch will "count" the packet into different rows, while also compute the "min" out of all rows.
// In read phase we do read-only count; in clean phase we simply set 0.
// Row 0 always write output; Row 1 will compare and min



/*

// 131072 is too large for 64 bit; maximum register size is 35*128Kbit
#define reg_bloom_name(SNAPID, ROWID)  bloom_filter_s ## SNAPID ## _r ## ROWID
#define reg_bloom_filter_def(SNAPID, ROWID) register reg_bloom_name(SNAPID, ROWID) \
{ width : SNAP_COUNTER_WIDTH; instance_count : REG_SIZE; }

#define loop_define_registers(X) reg_bloom_filter_def(X,0) reg_bloom_filter_def(X,1)
For4(loop_define_registers)
// This macro defines 4*2=8 registers.

// These macros defines all register programs. For now, the programs are empty.
#define reg_blackbox_name(SNAPID, ROWID, PROGRAM)  blackbox_s ## SNAPID ## _r ## ROWID ##_##PROGRAM

#define template_blackbox_programs(SNAPID, ROWID) \
blackbox stateful_alu reg_blackbox_name(SNAPID, ROWID, WRITE){ \
	reg: reg_bloom_name(SNAPID, ROWID); \
} \
blackbox stateful_alu reg_blackbox_name(SNAPID, ROWID, READ){ \
	reg: reg_bloom_name(SNAPID, ROWID); \
} \
blackbox stateful_alu reg_blackbox_name(SNAPID, ROWID, CLEAN){ \
	reg: reg_bloom_name(SNAPID, ROWID); \
} \
//done template_blackbox_programs

// define blackboxes, two rows per "snapshot"
#define loop_define_snapshot_CMS_program(SNAPID) template_blackbox_programs(SNAPID,0) template_blackbox_programs(SNAPID,1)
// define 4 snapshots
For4(loop_define_snapshot_CMS_program)



// We cannot combine two rows in a single action; thus, need two tables.
#define template_blackbox_actions(SNAPID, ROWID) \
action execute_read_s ## SNAPID ## _r ## ROWID ()\
{ reg_blackbox_name(SNAPID, ROWID, READ).execute_stateful_alu(md.reg_indexvar_name(SNAPID, ROWID)); } \
action execute_write_s ## SNAPID ## _r ## ROWID ()\
{ reg_blackbox_name(SNAPID, ROWID, WRITE).execute_stateful_alu(md.reg_indexvar_name(SNAPID, ROWID)); } \
action execute_clean_s ## SNAPID ## _r ## ROWID ()\
{ reg_blackbox_name(SNAPID, ROWID, CLEAN).execute_stateful_alu(md.reg_indexvar_name(SNAPID, ROWID)); }
//done template_blackbox_actions

// define actions for register access, two rows per "snapshot"
#define loop_define_blackbox_actions(SNAPID) template_blackbox_actions(SNAPID,0) template_blackbox_actions(SNAPID,1)
For4(loop_define_blackbox_actions)
action _nop(){}


#define template_table_reg_access(SNAPID, ROWID) \
table tb_access_reg_s## SNAPID ##_r ## ROWID { \
	reads {\
		md.snap_round_robin_action_s##SNAPID : exact; \
	}\
	actions {\
		execute_read_s## SNAPID ##_r ## ROWID;\
		execute_write_s## SNAPID ##_r ## ROWID;\
		execute_clean_s## SNAPID ##_r ## ROWID;\
		_nop; \
	}\
	default_action: _nop; \
	size: 4; \
}
//end template_table_reg_access
// ======= TODO: variable-length read? how to express this in Match part? ========

#define loop_define_regaccess_tables(SNAPID) template_table_reg_access(SNAPID,0) template_table_reg_access(SNAPID,1)
For4(loop_define_regaccess_tables)




// High-level logic in snapshot round-robin:
// 0.  Global counters are maintained in several global "utility" register (32-bit ints, runs in "++i" fashion). Indexed by egress_port.
	// Each snapshot is also "partitioned" into per-port area; size=(REG_SIZE_PER_PORT*Total_Ports).
// 1. We use packet length bytes to increment md.round_robin_byte_counter; md.total_pkt_counter is incremented.
// 2. Snap_RR_ID=((md.round_robin_byte_counter / SNAP_INTERVAL) % 4), and cyclic register loc=(md.total_pkt_counter%REG_SIZE)
// 3. Given Snap_RR_ID, we copy cyclic register loc to appropriate #snap for cleaning (overwrite existing hash-based address, which is prepared much earlier).
// 4. Finally, we can start going through register access tables.
// -. If you give me queue length, methodologically I should use floor(qlen/SNAP_INTERVAL) as #snap to read.
	//-> This translates to: Read#0 always read, Read#1 read only if qlen>SNAP_INTERVAL, Read#2 if qlen>2*SNAP_INTERVAL
	//   Whenever Read happens, increment est_interval_len and est_threshold (=0.7*est_interval_len; but can't multiply)






field_list tcp_hash_field_list {
    ipv4.srcAddr;
    ipv4.dstAddr;

	tcp.srcPort;
	tcp.dstPort;

}
field_list_calculation tcp_hash_field_list_calc {
    input {
        tcp_hash_field_list;
    }
    algorithm : crc_32;
    output_width : 32;
}


field_list udp_hash_field_list {
    ipv4.protocol;
    ipv4.srcAddr;
    ipv4.dstAddr;

    ipv4.totalLen;
    ipv4.identification;
	ipv4.hdrChecksum;

	udp.srcPort;
	udp.dstPort;
	udp.checksum;
}
field_list_calculation udp_hash_field_list_calc {
    input {
        udp_hash_field_list;
    }
    algorithm : crc_32;
    output_width : 32;
}
// Some short, same-content UDP packets will confuse our measurement.
// (Future: we could ignore all short UDP packets.)
// (Or: drop all short UDP packets with no checksum.)



// Temp/intermediate variables


field_list register_hash_fields {
    md.my_packet_signature;
}
field_list_calculation register_access_hash_calc {
    input { register_hash_fields; }
    algorithm: crc32;
    output_width: 16;
}



// Define stateful registers
#define REG_SIZE 65536
// 131072 is too large for 64 bit; maximum register size is 35*128Kbit
register cached_packet_table_1 {
    width : 64;
    instance_count : REG_SIZE;
}
//used in paired mode, so each entry is 64 bits?
// Lo: packet ID
// Hi: timestamp
#define TIMEOUT 500000
//arbitrary threshold, for now; (well, what's the unit of time?)

// possible register actions:
blackbox stateful_alu cp1_ing_packet_write {
	//logic: if entry empty or timestamp expired, put myself in
    reg: cached_packet_table_1;
	condition_lo: register_lo == 0;
	condition_hi: register_hi + TIMEOUT - md.current_timestamp < 0;

	update_lo_1_predicate: condition_lo or condition_hi;
	update_lo_1_value: md.my_packet_signature;
	update_hi_1_predicate: condition_lo or condition_hi;
	update_hi_1_value: md.current_timestamp;


	update_lo_2_predicate: not condition_lo and not condition_hi;
	update_lo_2_value: register_lo;
	update_hi_2_predicate: not condition_lo and not condition_hi;
	update_hi_2_value: register_hi;

	//output_dst: md.salu_result_predicate;
	//output_value: predicate;
}


blackbox stateful_alu cp1_egr_packet_read {
	//logic: if entry matched,  calc timestamp diff & clear ID; otherwise leave everything intact
    reg: cached_packet_table_1;
	condition_lo: register_lo == md.my_packet_signature;

	update_lo_1_predicate: condition_lo;
	update_lo_1_value: 0;
	update_hi_1_predicate: condition_lo;
	update_hi_1_value: 0;

	update_lo_2_predicate: not condition_lo;
	update_lo_2_value: register_lo;
	update_hi_2_predicate: not condition_lo;
	update_hi_2_value: register_hi;

	output_dst: md.my_matched_prev_timestamp;
	output_value: register_hi;
	output_predicate: condition_lo;
}




// actual actions

action _nop() {
}
action _drop () {
    drop();
}

action mark_useless_bit() {
	modify_field(md.is_useless,1);
}

table tb_mark_useless_packets {
	reads {
        ethernet   : valid;
        ipv4.dstAddr : lpm;
    }
    actions {
      _nop;
	  mark_useless_bit;
    }
	default_action: _nop;
}

action get_timestamp() {
	modify_field(md.current_timestamp, ig_intr_md_from_parser_aux.ingress_global_tstamp);
}


action prepare_packet_tcp() {
	modify_field_with_hash_based_offset(md.my_packet_signature,
		0,tcp_hash_field_list_calc, 0x100000000);
	get_timestamp();
}

action prepare_packet_udp() {
	modify_field_with_hash_based_offset(md.my_packet_signature,
		0,udp_hash_field_list_calc, 0x100000000);
	get_timestamp();
}


table tb_prepare_packet_tcp {
	actions {
		prepare_packet_tcp;
	}
	default_action: prepare_packet_tcp;
}
table tb_prepare_packet_udp {
	actions {
		prepare_packet_udp;
	}

	default_action: prepare_packet_udp;
}

action prepare_register_index(){
	modify_field_with_hash_based_offset(md.my_register_location,
		0,register_access_hash_calc, REG_SIZE);
}

table tb_prepare_register_index{
	actions {
		prepare_register_index;
	}
	default_action: prepare_register_index;
}


action reg_access_input_packets(){
	cp1_ing_packet_write.execute_stateful_alu(md.my_register_location);
}
action reg_access_output_packets(){
	cp1_egr_packet_read.execute_stateful_alu(md.my_register_location);
}

table tb_execute_register{
	reads {
		ig_intr_md.ingress_port : exact;
	}
	actions {
		reg_access_input_packets;
		reg_access_output_packets;
	}
}

action compute_timediff(){
	// calculate time diff, put in somewhere
	subtract(md.my_computed_timediff,md.current_timestamp,md.my_matched_prev_timestamp);
}
#define SAMPLER_COLLECTING_PORT 5
action prepare_sampled_result(){
	// Add a simple IP+UDP header
	add_header(sampled_dummy_header);
	modify_field(sampled_dummy_header.data_1, md.my_matched_prev_timestamp);
	modify_field(sampled_dummy_header.data_2, md.my_computed_timediff);

	modify_field(sampled_dummy_header.version, 4);
	modify_field(sampled_dummy_header.ihl, 5);
	modify_field(sampled_dummy_header.ttl, 64);
	modify_field(sampled_dummy_header.protocol, IP_PROTOCOLS_UDP);


	// write output to dummy header's IP header field, for easy debug only
	modify_field(sampled_dummy_header.srcAddr, 0);
	modify_field(sampled_dummy_header.dstAddr, 0xffffffff);

	// send to a collector port
	modify_field(ig_intr_md_for_tm.ucast_egress_port, SAMPLER_COLLECTING_PORT);
}

table tb_cleanse_result{
	actions {
		_drop;//for all input packets; for output packets without matching timestamp;
	}
	default_action: _drop;
}

table tb_compute_timediff{
	actions {
		compute_timediff;
	}
	default_action:compute_timediff;
}
table tb_prepare_sampled_result{
	actions {
		prepare_sampled_result;//route to collector, add a UDP header in front...
	}
	default_action: prepare_sampled_result;
}
*/

action bouncer(){
	    modify_field(ig_intr_md_for_tm.ucast_egress_port, ig_intr_md.ingress_port);
}
_OAT(bouncer)


/* Main control flow */
control ingress {

	//Give me some basic routing...
	_OAT_Apply(bouncer);
}

field_list resubmit_fields {
    md.reg_indexvar_name(0, 0);
    md.reg_indexvar_name(0, 1);
}
action dummy_foo(){
	//avoid dead-code elim
	//clone_egress_pkt_to_egress(2, resubmit_fields);
	//modify_field(udp.dstPort, md.reg_indexvar_name(0, 0));
	modify_field(udp.dstPort, md.snap_round_robin_action_s0);
	modify_field(udp.srcPort, md.cyclic_clean_epoch);
	modify_field(udp.checksum, md.my_packet_size_for_cms);
}
_OAT(dummy_foo)

control egress {
	_OAT_Apply(prepare_port_number_lower);
	_OAT_Apply(prepare_base_addr_for_all_snaps);

	_OAT_Apply(update_packet_count);
	_OAT_Apply(update_bytes_count);

	_OAT_Apply(prepare_interval_and_epoch);
	_OAT_Apply(prepare_individual_epoch_stage);

	if(valid(tcp)){
		_OAT_Apply(prepare_tcp_hash_loc);
	}
	else if(valid(udp)){
		_OAT_Apply(prepare_udp_hash_loc);
	}// TODO: Else we ignore this flow; or set it to special flow ID

	//apply(prepare_base_addr_for_all_snaps);
	// apply(tb_calculate_reg_addr_s0);


	_OAT_Apply(dummy_foo);
}
