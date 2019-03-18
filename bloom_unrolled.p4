/* ethernet header, parsing, routing actions */
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
        bit<32> index1;
	bit<1> count1;
        bit<32> index2;
	bit<1> count2;
}

#define HASH_BASE 10w0
#define HASH_MAX 10w1023

control MyIngress(inout headers hdr,
                  inout custom_metadata_t meta,
                  inout standard_metadata_t standard_metadata) {

	register<bit<1>>(2048) bloom;

	bit<1> tmp_count;

	action hash1() {
                hash(meta.index1, HashAlgorithm.crc16, HASH_BASE,
                      {hdr.ipv4.srcAddr, hdr.ipv4.dstAddr, hdr.ipv4.protocol, 7w11}, HASH_MAX);
		
		bloom.read(meta.count1, meta.index1);
		tmp_count = (meta.count1 == 0)? 1 : meta.count1;		

		bloom.write(meta.index1,tmp_count);	
	}
        action hash2() {
                hash(meta.index2, HashAlgorithm.crc16, HASH_BASE,
                      {hdr.ipv4.srcAddr, hdr.ipv4.dstAddr, hdr.ipv4.protocol, 5w3}, HASH_MAX);

                bloom.read(meta.count2, meta.index2);
                tmp_count = (meta.count2 == 0)? 1 : meta.count2;     

                bloom.write(meta.index2,tmp_count);
        }
	
	apply {
		if(hdr.ipv4.isValid()) {
			hash1();
			hash2();
		}
	}
}


