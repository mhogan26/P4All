/* With this implementation, it won't matter if we have multiple arrays in the same stage. Those can run in parallel because we're not comparing values to find a global min until the end, after we've already done all the hashing. */

/* ethernet, ipv4 headers, parsing, routing functions */

// N = 2
// DEPTH = 2048

#include <core.p4>
#include <v1model.p4>

typedef bit<32> ip4Addr_t;

header ipv4_t {
    bit<4>    version;
    bit<4>    ihl;
    bit<8>    diffserv;
    bit<16>   totalLen;
    bit<16>   identification;
    bit<3>    flags;
    bit<13>   fragOffset;
    bit<8>    ttl;
    bit<8>    protocol;
    bit<16>   hdrChecksum;
    ip4Addr_t srcAddr;
    ip4Addr_t dstAddr;
}

struct custom_metadata_t {
	bit<32> count_min;
	bit<32> index0;
        bit<32> current_count0;
        bit<32> index1;
        bit<32> current_count1;
}

struct headers {
    ipv4_t       ipv4;
}


parser MyParser(packet_in packet, out headers hdr, inout custom_metadata_t meta, inout standard_metadata_t standard_metadata) {
        state start {
                transition parse_ipv4;
        }
        state parse_ipv4 {
                packet.extract(hdr.ipv4);
                transition accept;
        }
}

control MyVerifyChecksum(inout headers hdr, inout custom_metadata_t meta) {
        apply { }
}




#define HASH_BASE 10w0
#define HASH_MAX 10w1023


/* for simplicity, we don't include tables and apply actions directly in control */
control MyIngress(inout headers hdr,
                  inout custom_metadata_t meta,
                  inout standard_metadata_t standard_metadata) {

	register<bit<32>>(2048) counter0;
	register<bit<32>>(2048) counter1;

	bit<32> tmp_count;

	action count0() {
        	/* compute hash index */
		hash(meta.index0, HashAlgorithm.crc16, HASH_BASE,
                      {hdr.ipv4.srcAddr, hdr.ipv4.dstAddr, hdr.ipv4.protocol, 7w11}, HASH_MAX);


        	/* increment counter  - read, increment, write*/
		counter0.read(tmp_count, meta.index0);
		meta.current_count0 = tmp_count + 1;
        	counter0.write(meta.index0, meta.current_count0);
	}

	table count_0 {
		actions = { count0; }
	}

	action count1() {
        	/* compute hash index */
                hash(meta.index1, HashAlgorithm.crc16, HASH_BASE,
                      {hdr.ipv4.srcAddr, hdr.ipv4.dstAddr, hdr.ipv4.protocol, 5w3}, HASH_MAX);

        	/* increment counter  - read, increment, write*/
		counter1.read(tmp_count, meta.index1);
		meta.current_count1 = tmp_count + 1;
        	counter1.write(meta.index1, meta.current_count1);
	}

	table count_1 {
		actions = { count1; }
	}

	action set_min0(){
        	meta.count_min = meta.current_count0;
	}

	table set_min_0 {
		actions = { set_min0; }
	}

	action set_min1(){
        	meta.count_min = meta.current_count1;
	}

	table set_min_1 {
		actions = { set_min1; }
	}


	apply {
		count_0.apply();
		count_1.apply();

    		// finding min - conditions
    		// first stage is always the same - put 1st count as min
    		set_min_0.apply();
		if (meta.current_count1 < meta.count_min) {
	    		set_min_1.apply();
		}
    		
	}

    	/* apply forwarding logic */
}

control MyEgress(inout headers hdr, inout custom_metadata_t meta, inout standard_metadata_t standard_metadata) {
        apply { }
}

control MyComputeChecksum(inout headers hdr, inout custom_metadata_t meta) {
        apply { }
}

control MyDeparser(packet_out packet, in headers hdr) {
        apply {
                packet.emit(hdr.ipv4);
        }
}



V1Switch(
MyParser(),
MyVerifyChecksum(),
MyIngress(),
MyEgress(),
MyComputeChecksum(),
MyDeparser()
) main;
