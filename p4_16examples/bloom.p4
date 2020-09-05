/* ethernet, ipv4 headers, parsing, routing functions */

/* this is a membership bloom filter */
// M = 2048 (num bits in filter)
// K = 2 (num of hash functions)

#include "core.p4"
#include "v1model.p4"

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
        bit<32> index0;
        bit<1> member0;
        bit<32> index1;
        bit<1> member1;
        bit<32> index2;
        bit<1> member2;
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

control MyIngress(inout headers hdr,
                  inout custom_metadata_t meta,
                  inout standard_metadata_t standard_metadata) {

        register<bit<1>>(2048) bloom0;
	register<bit<1>>(2048) bloom1;
	register<bit<1>>(2048) bloom2;


        action hash0() {
                hash(meta.index0, HashAlgorithm.crc16, HASH_BASE,
                      {hdr.ipv4.srcAddr, hdr.ipv4.dstAddr, hdr.ipv4.protocol, 7w11}, HASH_MAX);

                bloom0.read(meta.member0, meta.index0);
                meta.member0 = 1;

                bloom0.write(meta.index0,meta.member0);
        }

	action hash1() {
                hash(meta.index1, HashAlgorithm.crc16, HASH_BASE,
                      {hdr.ipv4.srcAddr, hdr.ipv4.dstAddr, hdr.ipv4.protocol, 5w3}, HASH_MAX);

                bloom1.read(meta.member1, meta.index1);
                meta.member1 = 1;

                bloom1.write(meta.index1,meta.member1);
        }

        action hash2() {
                hash(meta.index1, HashAlgorithm.crc16, HASH_BASE,
                      {hdr.ipv4.srcAddr, hdr.ipv4.dstAddr, hdr.ipv4.protocol, 3w5}, HASH_MAX);

                bloom2.read(meta.member2, meta.index2);
                meta.member1 = 1;

                bloom2.write(meta.index2,meta.member2);
        }

        apply {
	        hash0();
                hash1();
		hash2();

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







