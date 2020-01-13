/* With this implementation, it DOES matter if we have multiple arrays in the same stage. If they're in the same stage, they'd both be accessing the global metadata at the same time because we compare values to global min as we go. */

/* ethernet, ipv4 headers, parsing, routing functions */
 
// what's the right number of counts to store in metadata? = to the total number of accesses we have across all stages or just the max number of accesses in a single stage?
/* you can have counts = # accesses across all stages, but with this implementation, that's excessive. we only have 1 access per stage, so we only need 1 count */

// N = 2
// DEPTH = 2048

//#include <core.p4>
//#include <v1model.p4>

header_type ipv4_t {
    fields {
	version	: 4;
	ihl	: 4;
	diffserv	: 8;
	totalLen	: 16;
	identification	: 16;
	flags	: 3;
	fragOffset	: 13;
	ttl	: 8;
	protocol	: 8;
	hdrChecksum	: 16;
	srcAddr	: 32;
	dstAddr	: 32;
    }
}

header ipv4_t ipv4;

header_type ingress_metadata_t {
    fields {
	count_min	: 32;
	index	: 32;
	current_count	: 32;
    }
}

metadata ingress_metadata_t meta;


field_list hash {
	ipv4.srcAddr;
	ipv4.dstAddr;
	ipv4.protocol;
}

field_list_calculation hashcalc {
	input	{ hash; }
	algorithm	: crc32;
	output_width	: 32;
}



// how many times can you write to the same metadata value in a stage? - still need at least 2 index/counts if more than one access in same stage
// ^ you can only really do this once, because operations run in parallel in a stage

parser start {
	extract(ipv4);
	return ingress;	
}

#define HASH_MAX 10w1023

register counter0 {
	width: 32;
	instance_count: 2048;
}

register counter1 {
	width: 32;
	instance_count: 2048;
}

action count0() {
	/* compute hash index */
	modify_field_with_hash_based_offset(meta.index, 0, hashcalc, 32);

        /* increment counter  - read, increment, write*/
        register_read(meta.index, counter0, meta.current_count);
        modify_field(meta.current_count,meta.current_count + 1);
        register_write(counter0,meta.index, meta.current_count);
}

table count_0 {
	actions { count0; }
}


action count1() {
	/* compute hash index */
	modify_field_with_hash_based_offset(meta.index, 0, hashcalc, 32);

        /* increment counter  - read, increment, write*/ 
        register_read(meta.index, counter1, meta.current_count);
        modify_field(meta.current_count,meta.current_count + 1);
        register_write(counter1,meta.index, meta.current_count);
}


table count_1 {
	actions { count1; }
}


action set_min() {
	modify_field(meta.count_min,meta.current_count);
}

table set_min_0 {
	actions { set_min; }
}

table set_min_1 {
	actions { set_min; }
}


/* for simplicity, we don't include tables and apply actions directly in control */
control ingress {
	apply(count_0);
	apply(set_min_0);
	apply(count_1);
	if ((meta.count_min - meta.current_count) > 0) {
		apply(set_min_1);
	}

}




