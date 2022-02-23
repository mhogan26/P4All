# python code to track output of starflow during interpreter sim
# starflow flushes records from cache on eviction/when ring buffer is full
# these are exact counts, bc hash table instead of sketch
# we can measure eviction ratio - ratio of evicted GPVs to pkts
# we keep a counter of # pkts we've seen, and counter of GPVs evicted
# we know how many pkts we see when we gen json file, so don't need to count that here
# just count # evictions (every time cache is flushed)

import pickle

cache_short = [0]
cache_long = [0]
cache_total = [0]

def cache_flush_short():
    cache_short[0] += 1
    cache_total[0] += 1
    with open('total.txt','wb') as f:
        pickle.dump(cache_total[0],f)
    '''
    cache_short += 1
    with open('short.txt','w') as f:
        f.write(str(cache_short))
    '''

def cache_flush_long():
    cache_long[0] += 1
    cache_total[0] += 1
    with open('total.txt','wb') as f:
        pickle.dump(cache_total[0],f)
    '''
    cache_long += 1
    with open('long.txt','w') as f:
        f.write(str(cache_long))
    '''


