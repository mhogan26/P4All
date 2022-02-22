# track number of rtt samples we get and record how many inserts happen during each sample
import pickle
samples = [0]
insert_measure = []

# insrtdiff is the number of pkts inserted in fridge between seq and ack
def log_rttsample(rtt, insrtdiff):
    samples[0]+=1
    insert_measure.append(insrtdiff)
    with open('numsamples.txt','w') as f:
        f.write(str(samples[0]))
    with open('insertdiffs.txt','wb') as f:
        pickle.dump(insert_measure,f)

