struct custom_metadata_t {
	bit<32> count_min;
	bit<32> index0;
        bit<32> current_count0;
        bit<32> index1;
        bit<32> current_count1;
        bit<32> index2;
        bit<32> current_count2;
        bit<32> index3;
        bit<32> current_count3;
}


#define REGISTER_COUNTER(i) \
    register<bit<32>>(2048) counter##i;

#define ACTION_HASH_INCREMENT(i) \
    action hash_increment##i() { \
	/* compute hash index */
	/* increment counter stored in counter##i */
	/* write to metadata */
    }

#define ACTION_SET_MIN(i) \
    action set_min_##i() { \
        meta.count_min = meta.current_count##i;
    }


ACTION_SET_MIN(0)
ACTION_SET_MIN(1)
ACTION_SET_MIN(2)
ACTION_SET_MIN(3)

ACTION_SET_MIN(0)
ACTION_SET_MIN(1)
ACTION_SET_MIN(2)
ACTION_SET_MIN(3)

control ingress(inout headers hdr,
                  inout custom_metadata_t meta,
                  inout standard_metadata_t standard_metadata) {

	REGISTER_COUNTER(0)
        REGISTER_COUNTER(1)
        REGISTER_COUNTER(2)
        REGISTER_COUNTER(3)

	apply {
		hash_increment0();
		hash_increment1();
                hash_increment2();
                hash_increment3();

                if (meta.current_count0 < meta.count_min) {
    			set_min_0();
		}
		if (meta.current_count1 < meta.count_min) {
	    		set_min_1();
		}
                if (meta.current_count2 < meta.count_min) {
                        set_min_2();
                }
                if (meta.current_count3 < meta.count_min) {
                        set_min_3();
                }
    		
	}

}



