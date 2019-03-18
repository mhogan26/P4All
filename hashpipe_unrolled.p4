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

struct headers {
    ipv4_t       ipv4;
}


struct custom_metadata_t {
        bit<32> mKeyInTable;
        bit<32> mCountInTable;
        bit<32> mIndex;
        bit<1> mValid;
        bit<32> mKeyCarried;
        bit<32> mCountCarried;
        bit<32> mDiff;
}

#define HASH_BASE 10w0
#define HASH_MAX 10w1023

control MyIngress(inout headers hdr,
                  inout custom_metadata_t meta,
                  inout standard_metadata_t standard_metadata) {

	register<bit<32>>(32) flow_tracker_stage1;
	register<bit<32>>(32) packet_counter_stage1;
	register<bit<1>>(32) valid_bit_stage1;

	bit<32> tmp_count;

	action do_stage1(){
    		// first table stage
    		meta.mKeyCarried = hdr.ipv4.srcAddr;
    		meta.mCountCarried = 0;

    		// hash using my custom function
                hash(meta.mIndex, HashAlgorithm.crc16, HASH_BASE,
                      {meta.mKeyCarried, 7w11}, HASH_MAX);

		// read the key and value at that location
		flow_tracker_stage1.read(meta.mKeyInTable, meta.mIndex);
		packet_counter_stage1.read(meta.mCountInTable, meta.mIndex);
		valid_bit_stage1.read(meta.mValid, meta.mIndex);

		// check if location is empty or has a differentkey in there
		meta.mKeyInTable = (meta.mValid == 0)? meta.mKeyCarried : meta.mKeyInTable;
		meta.mDiff = (meta.mValid == 0)? 0 : meta.mKeyInTable - meta.mKeyCarried;

		// update hash table
		flow_tracker_stage1.write(meta.mIndex, hdr.ipv4.srcAddr);
		tmp_count = (meta.mDiff == 0)? meta.mCountInTable + 1 : 1;
		packet_counter_stage1.write(meta.mIndex, tmp_count);
		valid_bit_stage1.write(meta.mIndex, 1);

		// update metadata carried to the next table stage
		meta.mKeyCarried = ((meta.mDiff == 0) ? 0: meta.mKeyInTable);
		meta.mCountCarried = ((meta.mDiff == 0) ? 0: meta.mCountInTable);
	}

/********************** table stage 2 **************************/

        register<bit<32>>(32) flow_tracker_stage2;
        register<bit<32>>(32) packet_counter_stage2;
        register<bit<1>>(32) valid_bit_stage2;

        bit<32> tmp_flow_count;
        bit<32> tmp_pkt_count;
        bit<1> tmp_valid;

	action do_stage2(){
    		// hash using my custom function 
                hash(meta.mIndex, HashAlgorithm.crc16, HASH_BASE,
                      {meta.mKeyCarried, 5w3}, HASH_MAX);

    		// read the key and value at that location
                flow_tracker_stage2.read(meta.mKeyInTable, meta.mIndex);
                packet_counter_stage2.read(meta.mCountInTable, meta.mIndex);
                valid_bit_stage2.read(meta.mValid, meta.mIndex);

		// check if location is empty or has a differentkey in there
    		meta.mKeyInTable = (meta.mValid == 0)? meta.mKeyCarried : meta.mKeyInTable;
    		meta.mDiff = (meta.mValid == 0)? 0 : meta.mKeyInTable - meta.mKeyCarried;

		// update hash table
		tmp_flow_count = ((meta.mDiff == 0)? meta.mKeyInTable : ((meta.mCountInTable < meta.mCountCarried) ? 
				meta.mKeyCarried : meta.mKeyInTable));
		flow_tracker_stage2.write(meta.mIndex, tmp_flow_count);
		tmp_pkt_count = ((meta.mDiff == 0)? meta.mCountInTable + meta.mCountCarried : 
				((meta.mCountInTable < meta.mCountCarried) ? meta.mCountCarried : meta.mCountInTable));
		packet_counter_stage2.write(meta.mIndex, tmp_pkt_count);
		tmp_valid = ((meta.mValid == 0) ? ((meta.mKeyCarried == 0) ? (bit<1>)0 : 1) : (bit<1>)1);
		valid_bit_stage2.write(meta.mIndex, tmp_valid);

		// update metadata carried to the next table stage
		meta.mKeyCarried = ((meta.mDiff == 0) ? 0: meta.mKeyInTable);
		meta.mCountCarried = ((meta.mDiff == 0) ? 0: meta.mCountInTable);  
	}

	apply {
		if(hdr.ipv4.isValid()) {
			do_stage1();
			do_stage2();
		}
	}

}
       
