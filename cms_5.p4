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
        bit<32> index4;
        bit<32> current_count4;
}


control ingress(inout headers hdr,
                  inout custom_metadata_t meta,
                  inout standard_metadata_t standard_metadata) {

	register<bit<32>>(2048) counter0;
	register<bit<32>>(2048) counter1;
        register<bit<32>>(2048) counter2;
        register<bit<32>>(2048) counter3;
        register<bit<32>>(2048) counter4;

	action hash_increment0() {
        	/* compute hash index */
        	/* increment counter stored in counter0 */
		/* write to metadata */
	}

	action hash_increment1() {
                /* compute hash index */
                /* increment counter stored in counter1 */
                /* write to metadata */
	}

        action hash_increment2() {
                /* compute hash index */
                /* increment counter stored in counter2 */
                /* write to metadata */
        }   

        action hash_increment3() {
                /* compute hash index */
                /* increment counter stored in counter3 */
                /* write to metadata */
        }   

        action hash_increment4() {
                /* compute hash index */
                /* increment counter stored in counter4 */
                /* write to metadata */
        }

	action set_min0(){
        	meta.count_min = meta.current_count0;
	}

	action set_min1(){
        	meta.count_min = meta.current_count1;
	}

        action set_min2(){
                meta.count_min = meta.current_count2;
        }

        action set_min3(){
                meta.count_min = meta.current_count3;
        }

        action set_min4(){
                meta.count_min = meta.current_count4;
        }

	apply {
		hash_increment0();
		hash_increment1();
                hash_increment2();
                hash_increment3();
                hash_increment4();

                if (meta.current_count0 < meta.count_min) {
    			set_min0();
		}
		if (meta.current_count1 < meta.count_min) {
	    		set_min1();
		}
                if (meta.current_count2 < meta.count_min) {
                        set_min2();
                }
                if (meta.current_count3 < meta.count_min) {
                        set_min3();
                }
                if (meta.current_count4 < meta.count_min) {
                        set_min4();
                }	
	}

}



