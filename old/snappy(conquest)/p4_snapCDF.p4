action _nop() {
}
action _drop () {
    drop();
}
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
header_type magic_header_t {
    fields {
    data_1: 32;
    data_2: 32;
    data_3: 32;
    data_4: 32;
    data_5: 32;
    data_6: 32;
    data_7: 32;
    data_8: 32;
    }
}
#define IP_PROTOCOLS_TCP 6
#define IP_PROTOCOLS_UDP 17
#define MAGIC_UDP_PORT 233
parser start {
    return parse_ethernet;
}
header ethernet_t ethernet;
parser parse_ethernet {
    extract(ethernet);
    return select(latest.etherType) {
        0x800 : parse_ipv4;
        default: ingress;
    }
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
    return select(latest.dstPort) {
        MAGIC_UDP_PORT: parse_magic;
        default: ingress;
    }
}
header magic_header_t magic_header;
parser parse_magic {
    extract(magic_header);
    return ingress;
}
// ==== Parser end, actions start ====
action route_to_port(param){
    modify_field(ig_intr_md_for_tm.ucast_egress_port, param);
}
table tb_route_ipv4 {
    reads {
        ipv4.dstAddr : lpm;
    }
    actions {
        route_to_port;
        _drop;
    }
    default_action: _drop;
}
action magic_ingress () {
    // reflect
    modify_field(ig_intr_md_for_tm.ucast_egress_port, ig_intr_md.ingress_port);
    // set data_8 to 2333
    modify_field(magic_header.data_8,2333);
    // no checksum, thanks
    modify_field(udp.checksum,0);
}
// === Queue metadata test ===
register reg_enq_qdepth {
    width : 32;
    instance_count : 16;
}
register reg_deq_qdepth {
    width : 32;
    instance_count : 16;
}
register reg_deq_timedelta {
    width : 32;
    instance_count : 16;
}
register reg_pkt_length {
    width : 32;
    instance_count : 16;
}
blackbox stateful_alu save_enq_qdepth {
    reg: reg_enq_qdepth;
	update_lo_1_predicate: 1;
	update_lo_1_value: eg_intr_md.enq_qdepth;
}
blackbox stateful_alu save_deq_qdepth {
    reg: reg_deq_qdepth;
	update_lo_1_predicate: 1;
	update_lo_1_value: eg_intr_md.deq_qdepth;
}
blackbox stateful_alu save_deq_timedelta {
    reg: reg_deq_timedelta;
	update_lo_1_predicate: 1;
	update_lo_1_value: eg_intr_md.deq_timedelta;
}
blackbox stateful_alu save_pkt_length {
    reg: reg_pkt_length;
	update_lo_1_predicate: 1;
	update_lo_1_value: eg_intr_md.pkt_length;
}
action s1(){
    save_enq_qdepth.execute_stateful_alu(0);
}
action s2(){
    save_deq_qdepth.execute_stateful_alu(0);
}
action s3(){
    save_deq_timedelta.execute_stateful_alu(0);
}
action s4(){
    save_pkt_length.execute_stateful_alu(0);
}
//===== Start of Snappy logic =========
// ==== Constants ====
// Parameters for Snappy. CBF is 2x64
// we want smaller arrays, easy cleanup. (also, not that many flow, so we don't need large CBF)
#define SNAP_CBF_SIZE 64
#define SNAP_CBF_SIZE_BITS 6
// time duration per snapshot, let's make it 1024 microseconds.
// on simulator, it's 1024 packets; could be too long for experimenting stuff... use 128 here for princeton testbed.
// Changed to PKT interval, since Tofino deq_timedelta is problematic.
#define SNAP_PKT_INTERVAL 4096
#define SNAP_PKT_INTERVAL_BITS 12
#define STATUS_CLEAN 3
#define STATUS_WRITE 0
#define STATUS_READ_1 1
#define STATUS_READ_2 2
// 1,2: optional read, depending on tdiff size
// Safety check, guarantee integrity of constants
#if !(SNAP_PKT_INTERVAL ==1<< SNAP_PKT_INTERVAL_BITS)
	#error Need 2^SNAP_PKT_INTERVAL_BITS==SNAP_PKT_INTERVAL.
#endif
#if !(SNAP_CBF_SIZE == 1<< SNAP_CBF_SIZE_BITS)
	#error Need 2^SNAP_CBF_SIZE_BITS==SNAP_CBF_SIZE.
#endif
// ==== FlowID Hash ====
//tcp
field_list tcp_flowid_hash_field_list {
    ipv4.protocol;
    ipv4.srcAddr;
    ipv4.dstAddr;
	tcp.srcPort;
	tcp.dstPort;
}
// use different polynomials as different hash
field_list_calculation tcp_flowid_hash_field_list_calc_1 {
    input {
        tcp_flowid_hash_field_list;
    }
    algorithm : crc_32c;
    output_width : 16;
}
field_list_calculation tcp_flowid_hash_field_list_calc_2 {
    input {
        tcp_flowid_hash_field_list;
    }
    algorithm : crc_16_dnp;
    output_width : 16;
}
//udp
field_list udp_flowid_hash_field_list {
    ipv4.protocol;
    ipv4.srcAddr;
    ipv4.dstAddr;
	udp.srcPort;
	udp.dstPort;
}
// use different polynomials as different hash
field_list_calculation udp_flowid_hash_field_list_calc_1 {
    input {
        udp_flowid_hash_field_list;
    }
    algorithm : crc_32d;
    output_width : 16;
}
field_list_calculation udp_flowid_hash_field_list_calc_2 {
    input {
        udp_flowid_hash_field_list;
    }
    algorithm : crc_16_dnp;
    output_width : 16;
}
header_type md_t {
    fields {
		//current_timestamp: 32; // original is 48 bit, choose the lower 32 bit.
		//my_packet_size_bytes: 32;
		my_flowid_hashed_1: 16;
		my_flowid_hashed_2: 16;
    }
}
metadata md_t md;
header_type sp_t {
    fields {
		global_pkt_count: 32;
		cyclic_clean_idx: SNAP_CBF_SIZE_BITS;
		hash_addr_r_0: 32;//SNAP_CBF_SIZE_BITS;
		hash_addr_r_1: 32;//SNAP_CBF_SIZE_BITS;
		//status_cycle: 2;
		//time_diff_scaled_down: 4;//gateway supports at most 12 bit comparison; however we only care about this value is 0,1,2,or >2 (hopefully not too large, like 10)
		// this is already time_diff/time_interval_per_snap, meaning how many snapshot to read. If it's 0, we only write. 1/2 means one or two additional reads.
        enq_qdepth_scaled_down: 4;
		addr_s_0_r_0: SNAP_CBF_SIZE_BITS;
		addr_s_0_r_1: SNAP_CBF_SIZE_BITS;
		addr_s_1_r_0: SNAP_CBF_SIZE_BITS;
		addr_s_1_r_1: SNAP_CBF_SIZE_BITS;
		addr_s_2_r_0: SNAP_CBF_SIZE_BITS;
		addr_s_2_r_1: SNAP_CBF_SIZE_BITS;
		addr_s_3_r_0: SNAP_CBF_SIZE_BITS;
		addr_s_3_r_1: SNAP_CBF_SIZE_BITS;
		read_result_s_0_r_0: 32;
		read_result_s_0_r_1: 32;
		read_result_s_1_r_0: 32;
		read_result_s_1_r_1: 32;
		read_result_s_2_r_0: 32;
		read_result_s_2_r_1: 32;
		read_result_s_3_r_0: 32;
		read_result_s_3_r_1: 32;
		read_min_s_0: 32;
		read_min_s_1: 32;
		read_min_s_2: 32;
		read_min_s_3: 32;
		read_result_sum_p1: 32;
		read_result_sum_p2: 32;
		read_result_sum: 32;
    }
}
metadata sp_t sp;
header_type spst_t {
    fields {
		status_s_0: 2;
		status_s_1: 2;
		status_s_2: 2;
		status_s_3: 2;
		current_pktcount_scaled_down_SIT: 32;
	}
}
metadata spst_t spst;
register global_pkt_counter {
	width: 32;
	instance_count: 16;
}
blackbox stateful_alu global_pkt_count_incr {
	reg: global_pkt_counter;
	update_lo_1_predicate: 1;
	update_lo_1_value: register_lo + 1;
	output_value: register_lo;
	output_dst: sp.global_pkt_count;
}
// ===== Start Snapshots ===
#define regname(sid, rid) snap_##sid##_r_##rid
#define reg_def(sid, rid) register regname(sid,rid) {\
    width : 32;\
    instance_count : SNAP_CBF_SIZE;\
}
reg_def(0,0) reg_def(0,1)
reg_def(1,0) reg_def(1,1)
reg_def(2,0) reg_def(2,1)
reg_def(3,0) reg_def(3,1)
action copy_addr_r_0() {
	// A CROSS-CONTAINER COPY.
	modify_field_with_hash_based_offset(sp.hash_addr_r_0, 0,copy_addr_1_calc,SNAP_CBF_SIZE);
}
action copy_addr_r_1() {
	modify_field_with_hash_based_offset(sp.hash_addr_r_1, 0,copy_addr_2_calc,SNAP_CBF_SIZE);
}
action choose_addr_s_0_clean() {
	modify_field(sp.addr_s_0_r_0,sp.cyclic_clean_idx);
	modify_field(sp.addr_s_0_r_1,sp.cyclic_clean_idx);
}
action choose_addr_s_1_clean() {
	modify_field(sp.addr_s_1_r_0,sp.cyclic_clean_idx);
	modify_field(sp.addr_s_1_r_1,sp.cyclic_clean_idx);
}
action choose_addr_s_2_clean() {
	modify_field(sp.addr_s_2_r_0,sp.cyclic_clean_idx);
	modify_field(sp.addr_s_2_r_1,sp.cyclic_clean_idx);
}
action choose_addr_s_3_clean() {
	modify_field(sp.addr_s_3_r_0,sp.cyclic_clean_idx);
	modify_field(sp.addr_s_3_r_1,sp.cyclic_clean_idx);
}
action choose_addr_s_0_regular() {
	modify_field(sp.addr_s_0_r_0, sp.hash_addr_r_0);
	modify_field(sp.addr_s_0_r_1, sp.hash_addr_r_1);
}
action choose_addr_s_1_regular() {
	modify_field(sp.addr_s_1_r_0, sp.hash_addr_r_0);
	modify_field(sp.addr_s_1_r_1, sp.hash_addr_r_1);
}
action choose_addr_s_2_regular() {
	modify_field(sp.addr_s_2_r_0, sp.hash_addr_r_0);
	modify_field(sp.addr_s_2_r_1, sp.hash_addr_r_1);
}
action choose_addr_s_3_regular() {
	modify_field(sp.addr_s_3_r_0, sp.hash_addr_r_0);
	modify_field(sp.addr_s_3_r_1, sp.hash_addr_r_1);
}
//#define COUNT_BYTE
#ifdef COUNT_BYTE
	#define VAR_TO_ADD md.my_packet_size_bytes
#else
	#define VAR_TO_ADD 1
#endif
//note: write phase can choose to output or not.
// to output: use
//	output_dst: sp.read_result_s_##sid##_r_##rid; \
//	output_value: alu_lo;\
#define reg_bb_def(sid, rid) \
blackbox stateful_alu salu_incr_s_##sid##_r_##rid { \
	reg: regname(sid, rid); \
	update_lo_1_predicate: 1;\
	update_lo_1_value: register_lo + VAR_TO_ADD ;\
}\
blackbox stateful_alu salu_read_s_##sid##_r_##rid {\
	reg: regname(sid, rid);\
	update_lo_1_predicate: 1;\
	update_lo_1_value: register_lo;\
	output_dst: sp.read_result_s_##sid##_r_##rid;\
	output_value: alu_lo;\
}\
blackbox stateful_alu salu_clean_s_##sid##_r_##rid {\
	reg: regname(sid, rid);\
	update_lo_1_predicate: 1;\
	update_lo_1_value: 0;\
}\
action snap_s_##sid##_r_##rid##_clean(){\
	salu_clean_s_##sid##_r_##rid .execute_stateful_alu(sp.addr_s_##sid##_r_##rid );\
}\
action snap_s_##sid##_r_##rid##_write(){\
	salu_incr_s_##sid##_r_##rid .execute_stateful_alu( sp.addr_s_##sid##_r_##rid );\
}\
action snap_s_##sid##_r_##rid##_read(){\
	salu_read_s_##sid##_r_##rid .execute_stateful_alu( sp.addr_s_##sid##_r_##rid );\
}
reg_bb_def(0,0) reg_bb_def(0,1)
reg_bb_def(1,0) reg_bb_def(1,1)
reg_bb_def(2,0) reg_bb_def(2,1)
reg_bb_def(3,0) reg_bb_def(3,1)
// ===== Prepare addresses =====
action prepare_tcp_flowID_1(){
	modify_field_with_hash_based_offset(md.my_flowid_hashed_1,
		0,tcp_flowid_hash_field_list_calc_1,65536);
}
action prepare_tcp_flowID_2(){
	modify_field_with_hash_based_offset(md.my_flowid_hashed_2,
		0,tcp_flowid_hash_field_list_calc_2,65536);
}
action prepare_udp_flowID_1(){
	modify_field_with_hash_based_offset(md.my_flowid_hashed_1,
		0,udp_flowid_hash_field_list_calc_1,65536);
}
action prepare_udp_flowID_2(){
	modify_field_with_hash_based_offset(md.my_flowid_hashed_2,
		0,udp_flowid_hash_field_list_calc_2,65536);
}
field_list copy_addr_1 {
	md.my_flowid_hashed_1;
}
field_list_calculation copy_addr_1_calc {
    input {
        copy_addr_1;
    }
    algorithm : identity_lsb;
    output_width : 32;//SNAP_CBF_SIZE_BITS;
}
field_list copy_addr_2 {
	md.my_flowid_hashed_2;
}
field_list_calculation copy_addr_2_calc {
    input {
        copy_addr_2;
    }
    algorithm : identity_lsb;
    output_width : 32;//SNAP_CBF_SIZE_BITS;
}
// ===== Sum Results from Read =====
action collect_min_from_read_01(){
	min(sp.read_min_s_0, sp.read_result_s_0_r_0, sp.read_result_s_0_r_1);
	min(sp.read_min_s_1, sp.read_result_s_1_r_0, sp.read_result_s_1_r_1);
}
action collect_min_from_read_23(){
	min(sp.read_min_s_2, sp.read_result_s_2_r_0, sp.read_result_s_2_r_1);
	min(sp.read_min_s_3, sp.read_result_s_3_r_0, sp.read_result_s_3_r_1);
}
action collect_sum_01(){
	add(sp.read_result_sum_p1,sp.read_min_s_0,sp.read_min_s_1);
}
action collect_sum_23(){
	add(sp.read_result_sum_p2,sp.read_min_s_2,sp.read_min_s_3);
}
action collect_sum_all(){
	add(sp.read_result_sum,sp.read_result_sum_p1,sp.read_result_sum_p2);
}
action init_reads_to_zero(){
	modify_field(sp.read_result_s_0_r_0, 0);
	modify_field(sp.read_result_s_0_r_1, 0);
	modify_field(sp.read_result_s_1_r_0, 0);
	modify_field(sp.read_result_s_1_r_1, 0);
	modify_field(sp.read_result_s_2_r_0, 0);
	modify_field(sp.read_result_s_2_r_1, 0);
	modify_field(sp.read_result_s_3_r_0, 0);
	modify_field(sp.read_result_s_3_r_1, 0);
}
// ======== Snappy Control Flow ==========
// Start of SNAPPY logic
action update_pkt_count(){ global_pkt_count_incr.execute_stateful_alu(0); }
/*
action prepare_snap_status_interval(){
    shift_right(spst.current_pktcount_scaled_down_SIT, sp.global_pkt_count, SNAP_PKT_INTERVAL_BITS);
}
field_list cross_container_copy__current_pktcount_scaled_down_SIT {
	spst.current_pktcount_scaled_down_SIT;
}
field_list_calculation cross_container_copy_id_hash__current_pktcount_scaled_down_SIT {
    input {
        cross_container_copy__current_pktcount_scaled_down_SIT;
    }
    algorithm : identity_lsb;
    output_width : 32;
}
action prepare_snap_status_1(){
	modify_field(sp.cyclic_clean_idx, sp.global_pkt_count);
	modify_field_with_hash_based_offset(spst.status_s_0,
		0,cross_container_copy_id_hash__current_pktcount_scaled_down_SIT, 0x04);//only 4 snaps, so cycle=0..3
}*/
action prepare_snap_status_1(){
    modify_field(sp.cyclic_clean_idx, sp.global_pkt_count);
    shift_right(spst.status_s_0, sp.global_pkt_count, SNAP_PKT_INTERVAL_BITS);
}
action prepare_snap_status_2(){
	//add(spst.status_s_0, sp.status_cycle, 0);
	add(spst.status_s_1, spst.status_s_0, 1);
	add(spst.status_s_2, spst.status_s_0, 2);
	add(spst.status_s_3, spst.status_s_0, 3);
}
action prepare_snap_how_many_to_read(){
	shift_right(sp.enq_qdepth_scaled_down, eg_intr_md.enq_qdepth, SNAP_PKT_INTERVAL_BITS);
}
// ======= End of main program, debugging follow ====
//for debugging, read by magic
blackbox stateful_alu read_enq_qdepth {
    reg: reg_enq_qdepth;
    output_dst: magic_header.data_1;
    output_value: register_lo;
}
blackbox stateful_alu read_deq_qdepth {
    reg: reg_deq_qdepth;
    output_dst: magic_header.data_2;
    output_value: register_lo;
}
blackbox stateful_alu read_deq_timedelta {
    reg: reg_deq_timedelta;
    output_dst: magic_header.data_3;
    output_value: register_lo;
}
blackbox stateful_alu read_pkt_length {
    reg: reg_pkt_length;
    output_dst: magic_header.data_4;
    output_value: register_lo;
}
action m1(){
    read_enq_qdepth.execute_stateful_alu(0);
}
action m2(){
    read_deq_qdepth.execute_stateful_alu(0);
}
action m3(){
    read_deq_timedelta.execute_stateful_alu(0);
}
action m4(){
    read_pkt_length.execute_stateful_alu(0);
}
//==== CC copy for Debugging (magic output) only ====
field_list cross_container_copy__enq_qdepth_scaled_down {
	sp.enq_qdepth_scaled_down;
}
field_list_calculation cross_container_copy_id_hash__enq_qdepth_scaled_down {
    input {
        cross_container_copy__enq_qdepth_scaled_down;
    }
    algorithm : identity_lsb;
    output_width : 32;
}
field_list cross_container_copy__global_pkt_count {
	sp.global_pkt_count;
}
field_list_calculation cross_container_copy_id_hash__global_pkt_count {
    input {
        cross_container_copy__global_pkt_count;
    }
    algorithm : identity_lsb;
    output_width : 32;
}
field_list cross_container_copy__hash_addr_r_0 {
	sp.hash_addr_r_0;
}
field_list_calculation cross_container_copy_id_hash__hash_addr_r_0 {
    input {
        cross_container_copy__hash_addr_r_0;
    }
    algorithm : identity_lsb;
    output_width : 32;
}
field_list cross_container_copy__cyclic_clean_idx {
	sp.cyclic_clean_idx;
}
field_list_calculation cross_container_copy_id_hash__cyclic_clean_idx {
    input {
        cross_container_copy__cyclic_clean_idx;
    }
    algorithm : identity_lsb;
    output_width : 32;
}
field_list cross_container_copy__status_s_0 {
	spst.status_s_0;
}
field_list_calculation cross_container_copy_id_hash__status_s_0 {
    input {
        cross_container_copy__status_s_0;
    }
    algorithm : identity_lsb;
    output_width : 32;
}
action mc1(){
	modify_field_with_hash_based_offset(magic_header.data_1,
		0,cross_container_copy_id_hash__enq_qdepth_scaled_down, 4294967296);
}
action mc2(){
	modify_field_with_hash_based_offset(magic_header.data_2,
		0,cross_container_copy_id_hash__global_pkt_count, 4294967296);
}
action mc3(){
	modify_field_with_hash_based_offset(magic_header.data_3,
		0,cross_container_copy_id_hash__hash_addr_r_0, 4294967296);
}
action mc4(){
	modify_field_with_hash_based_offset(magic_header.data_4,
		0,cross_container_copy_id_hash__cyclic_clean_idx, 4294967296);
}
action mc5(){
	modify_field_with_hash_based_offset(magic_header.data_5,
		0,cross_container_copy_id_hash__status_s_0, 4294967296);
}
action magic_egress_inline () {
    modify_field(magic_header.data_7, sp.read_result_sum);
}
/* Main control flow */
control ingress {
    if(valid(magic_header)){
        _OAT(magic_ingress);
    }else{
        apply(tb_route_ipv4);
    }
}
#define RUN_ON_PORT 180
control egress {
    if(valid(magic_header)){
        //_OAT(m1);
        //_OAT(m2);
        //_OAT(m3);
        //_OAT(m4);
    }
    if(eg_intr_md.egress_port== RUN_ON_PORT){
        // prepare signature
        if(valid(tcp)){
            _OAT(prepare_tcp_flowID_1);
            _OAT(prepare_tcp_flowID_2);
        }
        else if(valid(udp)){
            _OAT(prepare_udp_flowID_1);
            _OAT(prepare_udp_flowID_2);
        }
        _OAT(update_pkt_count);
        //_OAT(prepare_snap_status_interval);
        _OAT(prepare_snap_status_1);
        _OAT(prepare_snap_status_2);
        _OAT(copy_addr_r_0);
        _OAT(copy_addr_r_1);
        _OAT(init_reads_to_zero);
        _OAT(prepare_snap_how_many_to_read);
        // Start the real snappy!
        if(spst.status_s_0!=STATUS_CLEAN){ _OAT(choose_addr_s_0_regular);}
		else 							{_OAT(choose_addr_s_0_clean);}
		if(spst.status_s_1!=STATUS_CLEAN){_OAT(choose_addr_s_1_regular);}
		else 							{ _OAT(choose_addr_s_1_clean);}
        #define Gateway_conditions(sid)  \
                if(spst.status_s_##sid ==STATUS_CLEAN){ \
                    _OAT(snap_s_##sid##_r_## 0 ##_clean); \
                    _OAT(snap_s_##sid##_r_## 1 ##_clean); \
                }else if(spst.status_s_##sid ==STATUS_WRITE){ \
                    _OAT(snap_s_##sid##_r_## 0 ##_write); \
                    _OAT(snap_s_##sid##_r_## 1 ##_write); \
                }else if(spst.status_s_##sid ==STATUS_READ_1 and sp.enq_qdepth_scaled_down != 0){ \
                    _OAT(snap_s_##sid##_r_## 0 ##_read); \
                    _OAT(snap_s_##sid##_r_## 1 ##_read); \
                }else if(spst.status_s_##sid ==STATUS_READ_2 and sp.enq_qdepth_scaled_down != 0 and sp.enq_qdepth_scaled_down != 1){ \
                    _OAT(snap_s_##sid##_r_## 0 ##_read); \
                    _OAT(snap_s_##sid##_r_## 1 ##_read); \
                }
        Gateway_conditions(0)
        if(spst.status_s_2==STATUS_CLEAN){ _OAT(choose_addr_s_2_clean); }
        else 							{_OAT(choose_addr_s_2_regular);}
        if(spst.status_s_3==STATUS_CLEAN){ _OAT(choose_addr_s_3_clean); }
        else 							{_OAT(choose_addr_s_3_regular);}
        Gateway_conditions(1)
        _OAT(collect_min_from_read_01);
        // == Stage 6 ====
        Gateway_conditions(2)
        _OAT(collect_sum_01);
        Gateway_conditions(3)
        //collect MIN, sum stuff
        _OAT(collect_min_from_read_23);
        _OAT(collect_sum_23);
        // Stage 10 (second to last)
        _OAT(collect_sum_all);
        // Stage 11
        // TODO: Action!
        // End of control flow. Debugging follows.
        if(valid(magic_header)){
			_OAT(mc1);
			_OAT(mc2);
			_OAT(mc3);
			_OAT(mc4);
			_OAT(mc5);
            _OAT(magic_egress_inline);
        }
    }
}