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

header udp_t {
    bit<16>   srcPort;
    bit<16>   dstPort;
    bit<16>   len;
    bit<16>   checksum;
} 

header nc_hdr_t {
    bit<8>    op;
    bit<128>  key;
}

header nc_value_1_t {
    bit<32>   value_1_1;
    bit<32>   value_1_2;
    bit<32>   value_1_3;
    bit<32>   value_1_4;
}

header nc_value_2_t {
    bit<32>   value_2_1;
    bit<32>   value_2_2;
    bit<32>   value_2_3;
    bit<32>   value_2_4;
}
header nc_value_3_t {
    bit<32>   value_3_1;
    bit<32>   value_3_2;
    bit<32>   value_3_3;
    bit<32>   value_3_4;
}
header nc_value_4_t {
    bit<32>   value_4_1;
    bit<32>   value_4_2;
    bit<32>   value_4_3;
    bit<32>   value_4_4;
}
header nc_value_5_t {
    bit<32>   value_5_1;
    bit<32>   value_5_2;
    bit<32>   value_5_3;
    bit<32>   value_5_4;
}
header nc_value_6_t {
    bit<32>   value_6_1;
    bit<32>   value_6_2;
    bit<32>   value_6_3;
    bit<32>   value_6_4;
}
header nc_value_7_t {
    bit<32>   value_7_1;
    bit<32>   value_7_2;
    bit<32>   value_7_3;
    bit<32>   value_7_4;
}
header nc_value_8_t {
    bit<32>   value_8_1;
    bit<32>   value_8_2;
    bit<32>   value_8_3;
    bit<32>   value_8_4;
}

struct headers {
    ipv4_t       ipv4;
    udp_t	 udp;
    nc_hdr_t	 nc_hdr;
    nc_value_1_t nc_value_1;
    nc_value_2_t nc_value_2;
    nc_value_3_t nc_value_3;
    nc_value_4_t nc_value_4;
    nc_value_5_t nc_value_5;
    nc_value_6_t nc_value_6;
    nc_value_7_t nc_value_7;
    nc_value_8_t nc_value_8;
}

struct custom_metadata_t {
        bit<1>  cache_exist;
        bit<14> cache_index;
        bit<1>  cache_valid;
	bit<32> ipv4_srcAddr;
	bit<32> ipv4_dstAddr;
}

parser MyParser(packet_in packet, out headers hdr, inout custom_metadata_t meta, inout standard_metadata_t standard_metadata) {
        state parse_ipv4 {
                packet.extract(hdr.ipv4);
                transition parse_udp;
        }

        state parse_udp {
                packet.extract(hdr.udp);
                transition parse_nc_hdr;
        }
        state parse_nc_hdr {
                packet.extract(hdr.nc_hdr);
                transition select(latest.op) {
			NC_READ_REQUEST: accept;
			NC_READ_REPLY: parse_value;
			NC_UPDATE_REQUEST: accept;
			NC_UPDATE_REPLY: parse_value;
			default: accept;
		}
        }
	state parse_value {
		transition parse_value_1;
	}
        state parse_value_1 {
		packet.extract(nc_value_1);
                transition parse_value_2;
        }
        state parse_value_2 {
                packet.extract(nc_value_2);
                transition parse_value_3;
        }
        state parse_value_3 {
                packet.extract(nc_value_3);
                transition parse_value_4;
        }
        state parse_value_4 {
                packet.extract(nc_value_4);
                transition parse_value_5;
        }
        state parse_value_5 {
                packet.extract(nc_value_5);
                transition parse_value_6;
        }
        state parse_value_6 {
                packet.extract(nc_value_6);
                transition parse_value_7;
        }
        state parse_value_7 {
                packet.extract(nc_value_7);
                transition parse_value_8;
        }
        state parse_value_8 {
                packet.extract(nc_value_8);
                transition parse_value_9;
        }
        state parse_value_9 {
                transition accept;
        }
}

control MyVerifyChecksum(inout headers hdr, inout custom_metadata_t meta) {
        apply { }
}


control MyIngress(inout headers hdr,
                  inout custom_metadata_t meta,
                  inout standard_metadata_t standard_metadata) {
	register<bit<32>>(NUM_CACHE) value_1_1_reg;
        register<bit<32>>(NUM_CACHE) value_1_2_reg;
        register<bit<32>>(NUM_CACHE) value_1_3_reg;
        register<bit<32>>(NUM_CACHE) value_1_4_reg;

        register<bit<32>>(NUM_CACHE) value_2_1_reg;
        register<bit<32>>(NUM_CACHE) value_2_2_reg;
        register<bit<32>>(NUM_CACHE) value_2_3_reg;
        register<bit<32>>(NUM_CACHE) value_2_4_reg;

        register<bit<32>>(NUM_CACHE) value_3_1_reg;
        register<bit<32>>(NUM_CACHE) value_3_2_reg;
        register<bit<32>>(NUM_CACHE) value_3_3_reg;
        register<bit<32>>(NUM_CACHE) value_3_4_reg;

        register<bit<32>>(NUM_CACHE) value_4_1_reg;
        register<bit<32>>(NUM_CACHE) value_4_2_reg;
        register<bit<32>>(NUM_CACHE) value_4_3_reg;
        register<bit<32>>(NUM_CACHE) value_4_4_reg;

        register<bit<32>>(NUM_CACHE) value_5_1_reg;
        register<bit<32>>(NUM_CACHE) value_5_2_reg;
        register<bit<32>>(NUM_CACHE) value_5_3_reg;
        register<bit<32>>(NUM_CACHE) value_5_4_reg;

        register<bit<32>>(NUM_CACHE) value_6_1_reg;
        register<bit<32>>(NUM_CACHE) value_6_2_reg;
        register<bit<32>>(NUM_CACHE) value_6_3_reg;
        register<bit<32>>(NUM_CACHE) value_6_4_reg;

        register<bit<32>>(NUM_CACHE) value_7_1_reg;
        register<bit<32>>(NUM_CACHE) value_7_2_reg;
        register<bit<32>>(NUM_CACHE) value_7_3_reg;
        register<bit<32>>(NUM_CACHE) value_7_4_reg;

        register<bit<32>>(NUM_CACHE) value_8_1_reg;
        register<bit<32>>(NUM_CACHE) value_8_2_reg;
        register<bit<32>>(NUM_CACHE) value_8_3_reg;
        register<bit<32>>(NUM_CACHE) value_8_4_reg;


	// store src and dst addresses in metadata (if we have a read request and cache valid)
	action reply_read_hit_before() {
		meta.ipv4_srcAddr = hdr.ipv4.srcAddr;
		meta.ipv4_dstAddr = hdr.ipv4.dstAddr;
	}

	// send reply back - swap src and dst addresses (if read request and cache valid)
	action reply_read_hit_after() {
		hdr.ipv4.srcAddr = meta.ipv4_dstAddr;
		hdr.ipv4.dstAddr = meta.ipv4_srcAddr;
		hdr.nc_hdr.op = NC_READ_REPLY;
	}

	action read_value_1_1() {
		value_1_1_reg.read(hdr.nc_value_1.value_1_1, meta.cache_index);
	}
        action read_value_1_2() {
                value_1_2_reg.read(hdr.nc_value_1.value_1_2, meta.cache_index);
        }
        action read_value_1_3() {
                value_1_3_reg.read(hdr.nc_value_1.value_1_3, meta.cache_index);
        }
        action read_value_1_4() {
                value_1_4_reg.read(hdr.nc_value_1.value_1_4, meta.cache_index);
        }

        action read_value_2_1() {
                value_2_1_reg.read(hdr.nc_value_2.value_2_1, meta.cache_index);
        }
        action read_value_2_2() {
                value_2_2_reg.read(hdr.nc_value_2.value_2_2, meta.cache_index);
        }
        action read_value_2_3() {
                value_2_3_reg.read(hdr.nc_value_2.value_2_3, meta.cache_index);
        }
        action read_value_2_4() {
                value_2_4_reg.read(hdr.nc_value_2.value_2_4, meta.cache_index);
        }

        action read_value_3_1() {
                value_3_1_reg.read(hdr.nc_value_3.value_3_1, meta.cache_index);
        }
        action read_value_3_2() {
                value_3_2_reg.read(hdr.nc_value_3.value_3_2, meta.cache_index);
        }
        action read_value_3_3() {
                value_3_3_reg.read(hdr.nc_value_3.value_3_3, meta.cache_index);
        }
        action read_value_3_4() {
                value_3_4_reg.read(hdr.nc_value_3.value_3_4, meta.cache_index);
        }

        action read_value_4_1() {
                value_4_1_reg.read(hdr.nc_value_4.value_4_1, meta.cache_index);
        }
        action read_value_4_2() {
                value_4_2_reg.read(hdr.nc_value_4.value_4_2, meta.cache_index);
        }
        action read_value_4_3() {
                value_4_3_reg.read(hdr.nc_value_4.value_4_3, meta.cache_index);
        }
        action read_value_4_4() {
                value_4_4_reg.read(hdr.nc_value_4.value_4_4, meta.cache_index);
        }

        action read_value_5_1() {
                value_5_1_reg.read(hdr.nc_value_5.value_5_1, meta.cache_index);
        }
        action read_value_5_2() {
                value_5_2_reg.read(hdr.nc_value_5.value_5_2, meta.cache_index);
        }
        action read_value_5_3() {
                value_5_3_reg.read(hdr.nc_value_5.value_5_3, meta.cache_index);
        }
        action read_value_5_4() {
                value_5_4_reg.read(hdr.nc_value_5.value_5_4, meta.cache_index);
        }

        action read_value_6_1() {
                value_6_1_reg.read(hdr.nc_value_6.value_6_1, meta.cache_index);
        }
        action read_value_6_2() {
                value_6_2_reg.read(hdr.nc_value_6.value_6_2, meta.cache_index);
        }
        action read_value_6_3() {
                value_6_3_reg.read(hdr.nc_value_6.value_6_3, meta.cache_index);
        }
        action read_value_6_4() {
                value_6_4_reg.read(hdr.nc_value_6.value_6_4, meta.cache_index);
        }

        action read_value_7_1() {
                value_7_1_reg.read(hdr.nc_value_7.value_7_1, meta.cache_index);
        }
        action read_value_7_2() {
                value_7_2_reg.read(hdr.nc_value_7.value_7_2, meta.cache_index);
        }
        action read_value_7_3() {
                value_7_3_reg.read(hdr.nc_value_7.value_7_3, meta.cache_index);
        }
        action read_value_7_4() {
                value_7_4_reg.read(hdr.nc_value_7.value_7_4, meta.cache_index);
        }

        action read_value_8_1() {
                value_8_1_reg.read(hdr.nc_value_8.value_8_1, meta.cache_index);
        }
        action read_value_8_2() {
                value_8_2_reg.read(hdr.nc_value_8.value_8_2, meta.cache_index);
        }
        action read_value_8_3() {
                value_8_3_reg.read(hdr.nc_value_8.value_8_3, meta.cache_index);
        }
        action read_value_8_4() {
                value_8_4_reg.read(hdr.nc_value_8.value_8_4, meta.cache_index);
        }


	action add_value_header_1() {
		hdr.ipv4.totalLen += 16;
		hdr.udp.len += 16		
		hdr.nc_value_1.setValid();
	}
        action add_value_header_2() {
                hdr.ipv4.totalLen += 16;
                hdr.udp.len += 16
                hdr.nc_value_2.setValid();
        }
        action add_value_header_3() {
                hdr.ipv4.totalLen += 16;
                hdr.udp.len += 16
                hdr.nc_value_3.setValid();
        }
        action add_value_header_4() {
                hdr.ipv4.totalLen += 16;
                hdr.udp.len += 16
                hdr.nc_value_4.setValid();
        }
        action add_value_header_5() {
                hdr.ipv4.totalLen += 16;
                hdr.udp.len += 16
                hdr.nc_value_5.setValid();
        }
        action add_value_header_6() {
                hdr.ipv4.totalLen += 16;
                hdr.udp.len += 16
                hdr.nc_value_6.setValid();
        }
        action add_value_header_7() {
                hdr.ipv4.totalLen += 16;
                hdr.udp.len += 16
                hdr.nc_value_7.setValid();
        }
        action add_value_header_8() {
                hdr.ipv4.totalLen += 16;
                hdr.udp.len += 16
                hdr.nc_value_8.setValid();
        }


	action write_value_1_1() {
		value_1_1_reg.write(meta.cache_index, hdr.nc_value_1.value_1_1);
	}
        action write_value_1_2() {
                value_1_2_reg.write(meta.cache_index, hdr.nc_value_1.value_1_2);
        }
        action write_value_1_3() {
                value_1_3_reg.write(meta.cache_index, hdr.nc_value_1.value_1_3);
        }
        action write_value_1_4() {
                value_1_4_reg.write(meta.cache_index, hdr.nc_value_1.value_1_4);
        }

        action write_value_2_1() {
                value_2_1_reg.write(meta.cache_index, hdr.nc_value_2.value_2_1);
        }
        action write_value_2_2() {
                value_2_2_reg.write(meta.cache_index, hdr.nc_value_2.value_2_2);
        }
        action write_value_2_3() {
                value_2_3_reg.write(meta.cache_index, hdr.nc_value_2.value_2_3);
        }
        action write_value_2_4() {
                value_2_4_reg.write(meta.cache_index, hdr.nc_value_2.value_2_4);
        }

        action write_value_3_1() {
                value_3_1_reg.write(meta.cache_index, hdr.nc_value_3.value_3_1);
        }
        action write_value_3_2() {
                value_3_2_reg.write(meta.cache_index, hdr.nc_value_3.value_3_2);
        }
        action write_value_3_3() {
                value_3_3_reg.write(meta.cache_index, hdr.nc_value_3.value_3_3);
        }
        action write_value_3_4() {
                value_3_4_reg.write(meta.cache_index, hdr.nc_value_3.value_3_4);
        }

        action write_value_4_1() {
                value_4_1_reg.write(meta.cache_index, hdr.nc_value_4.value_4_1);
        }
        action write_value_4_2() {
                value_4_2_reg.write(meta.cache_index, hdr.nc_value_4.value_4_2);
        }
        action write_value_4_3() {
                value_4_3_reg.write(meta.cache_index, hdr.nc_value_4.value_4_3);
        }
        action write_value_4_4() {
                value_4_4_reg.write(meta.cache_index, hdr.nc_value_4.value_4_4);
        }

        action write_value_5_1() {
                value_5_1_reg.write(meta.cache_index, hdr.nc_value_5.value_5_1);
        }
        action write_value_5_2() {
                value_5_2_reg.write(meta.cache_index, hdr.nc_value_5.value_5_2);
        }
        action write_value_5_3() {
                value_5_3_reg.write(meta.cache_index, hdr.nc_value_5.value_5_3);
        }
        action write_value_5_4() {
                value_5_4_reg.write(meta.cache_index, hdr.nc_value_5.value_5_4);
        }

        action write_value_6_1() {
                value_6_1_reg.write(meta.cache_index, hdr.nc_value_6.value_6_1);
        }
        action write_value_6_2() {
                value_6_2_reg.write(meta.cache_index, hdr.nc_value_6.value_6_2);
        }
        action write_value_6_3() {
                value_6_3_reg.write(meta.cache_index, hdr.nc_value_6.value_6_3);
        }
        action write_value_6_4() {
                value_6_4_reg.write(meta.cache_index, hdr.nc_value_6.value_6_4);
        }

        action write_value_7_1() {
                value_7_1_reg.write(meta.cache_index, hdr.nc_value_7.value_7_1);
        }
        action write_value_7_2() {
                value_7_2_reg.write(meta.cache_index, hdr.nc_value_7.value_7_2);
        }
        action write_value_7_3() {
                value_7_3_reg.write(meta.cache_index, hdr.nc_value_7.value_7_3);
        }
        action write_value_7_4() {
                value_7_4_reg.write(meta.cache_index, hdr.nc_value_7.value_7_4);
        }

        action write_value_8_1() {
                value_8_1_reg.write(meta.cache_index, hdr.nc_value_8.value_8_1);
        }
        action write_value_8_2() {
                value_8_2_reg.write(meta.cache_index, hdr.nc_value_8.value_8_2);
        }
        action write_value_8_3() {
                value_8_3_reg.write(meta.cache_index, hdr.nc_value_8.value_8_3);
        }
        action write_value_8_4() {
                value_8_4_reg.write(meta.cache_index, hdr.nc_value_8.value_8_4);
        }


	action remove_value_header_1() {
		hdr.ipv4.totalLen = hdr.ipv4.totalLen - 16;
		hdr.udp.len = hdr.udp.len - 16;
		hdr.nc_value_1.setInvalid();
	}
        action remove_value_header_2() {
                hdr.ipv4.totalLen = hdr.ipv4.totalLen - 16;
                hdr.udp.len = hdr.udp.len - 16;
                hdr.nc_value_2.setInvalid();
        }

        action remove_value_header_3() {
                hdr.ipv4.totalLen = hdr.ipv4.totalLen - 16;
                hdr.udp.len = hdr.udp.len - 16;
                hdr.nc_value_3.setInvalid();
        }

        action remove_value_header_4() {
                hdr.ipv4.totalLen = hdr.ipv4.totalLen - 16;
                hdr.udp.len = hdr.udp.len - 16;
                hdr.nc_value_4.setInvalid();
        }

        action remove_value_header_5() {
                hdr.ipv4.totalLen = hdr.ipv4.totalLen - 16;
                hdr.udp.len = hdr.udp.len - 16;
                hdr.nc_value_5.setInvalid();
        }

        action remove_value_header_6() {
                hdr.ipv4.totalLen = hdr.ipv4.totalLen - 16;
                hdr.udp.len = hdr.udp.len - 16;
                hdr.nc_value_6.setInvalid();
        }

        action remove_value_header_7() {
                hdr.ipv4.totalLen = hdr.ipv4.totalLen - 16;
                hdr.udp.len = hdr.udp.len - 16;
                hdr.nc_value_7.setInvalid();
        }

        action remove_value_header_8() {
                hdr.ipv4.totalLen = hdr.ipv4.totalLen - 16;
                hdr.udp.len = hdr.udp.len - 16;
                hdr.nc_value_8.setInvalid();
        }


	apply {
		if (hdr.nc_hdr.op == NC_READ_REQUEST and meta.cache_valid == 1) {
			reply_read_hit_before();
		}

		if (hdr.nc_hdr.op == NC_READ_REQUEST and meta.cache_valid == 1) {
			add_value_eader_1();
			read_value_1_1();
			read_value_1_2();
			read_value_1_3();
			read_value_1_4();
		}
		else if (hdr.nc_hdr.op == NC_UPDATE_REPLY and meta.cache_exist == 1) {
			write_value_1_1();
			write_value_1_2();
			write_value_1_3();
			write_value_1_4();
			remove_value_header_1();
		}

                if (hdr.nc_hdr.op == NC_READ_REQUEST and meta.cache_valid == 1) {
                        add_value_header_2();
                        read_value_2_1();
                        read_value_2_2();
                        read_value_2_3();
                        read_value_2_4();
                }
                else if (hdr.nc_hdr.op == NC_UPDATE_REPLY and meta.cache_exist == 1) {
                        write_value_2_1();
                        write_value_2_2();
                        write_value_2_3();
                        write_value_2_4();
                        remove_value_header_2();
                }

                if (hdr.nc_hdr.op == NC_READ_REQUEST and meta.cache_valid == 1) {
                        add_value_header_3();
                        read_value_3_1();
                        read_value_3_2();
                        read_value_3_3();
                        read_value_3_4();
                }
                else if (hdr.nc_hdr.op == NC_UPDATE_REPLY and meta.cache_exist == 1) {
                        write_value_3_1();
                        write_value_3_2();
                        write_value_3_3();
                        write_value_3_4();
                        remove_value_header_3();
                }

                if (hdr.nc_hdr.op == NC_READ_REQUEST and meta.cache_valid == 1) {
                        add_value_header_4();
                        read_value_4_1();
                        read_value_4_2();
                        read_value_4_3();
                        read_value_4_4();
                }
                else if (hdr.nc_hdr.op == NC_UPDATE_REPLY and meta.cache_exist == 1) {
                        write_value_4_1();
                        write_value_4_2();
                        write_value_4_3();
                        write_value_4_4();
                        remove_value_header_4();
                }

                if (hdr.nc_hdr.op == NC_READ_REQUEST and meta.cache_valid == 1) {
                        add_value_header_5();
                        read_value_5_1();
                        read_value_5_2();
                        read_value_5_3();
                        read_value_5_4();
                }
                else if (hdr.nc_hdr.op == NC_UPDATE_REPLY and meta.cache_exist == 1) {
                        write_value_5_1();
                        write_value_5_2();
                        write_value_5_3();
                        write_value_5_4();
                        remove_value_header_5();
                }

                if (hdr.nc_hdr.op == NC_READ_REQUEST and meta.cache_valid == 1) {
                        add_value_header_6();
                        read_value_6_1();
                        read_value_6_2();
                        read_value_6_3();
                        read_value_6_4();
                }
                else if (hdr.nc_hdr.op == NC_UPDATE_REPLY and meta.cache_exist == 1) {
                        write_value_6_1();
                        write_value_6_2();
                        write_value_6_3();
                        write_value_6_4();
                        remove_value_header_6();
                }

                if (hdr.nc_hdr.op == NC_READ_REQUEST and meta.cache_valid == 1) {
                        add_value_header_7();
                        read_value_7_1();
                        read_value_7_2();
                        read_value_7_3();
                        read_value_7_4();
                }
                else if (hdr.nc_hdr.op == NC_UPDATE_REPLY and meta.cache_exist == 1) {
                        write_value_7_1();
                        write_value_7_2();
                        write_value_7_3();
                        write_value_7_4();
                        remove_value_header_7();
                }

                if (hdr.nc_hdr.op == NC_READ_REQUEST and meta.cache_valid == 1) {
                        add_value_header_8();
                        read_value_8_1();
                        read_value_8_2();
                        read_value_8_3();
                        read_value_8_4();
                }
                else if (hdr.nc_hdr.op == NC_UPDATE_REPLY and meta.cache_exist == 1) {
                        write_value_8_1();
                        write_value_8_2();
                        write_value_8_3();
                        write_value_8_4();
                        remove_value_header_8();
                }

		if (hdr.nc_hdr.op == NC_READ_REQUEST and meta.cache_valid == 1) {
			reply_read_hit_after();
		}
	}


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
