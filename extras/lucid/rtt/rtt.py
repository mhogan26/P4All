

import pickle


collisions = [0]
timeouts = [0]
samples = [0]

def log_collision():
    collisions[0] += 1
    with open('collisions.txt','wb') as f:
        pickle.dump(collisions[0],f)

def log_timeout(t):
    if t:
        timeouts[0] += 1
        with open('timeouts.txt','wb') as f:
            pickle.dump(timeouts[0],f)

def log_rttsample(sample):
    samples[0]+=1
    with open('numsamples.txt','wb') as f:
        pickle.dump(samples[0],f)


