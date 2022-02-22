
collisions = [0]
timeouts = [0]
samples = [0]

def log_collision():
    collisions[0] += 1
    with open('collisions.txt','w') as f:
        f.write(str(collisions[0]))

def log_timeout(t):
    if t:
        timeouts[0] += 1
        with open('timeouts.txt','w') as f:
            f.write(str(timeouts[0]))

def log_rttsample(sample):
    samples[0]+=1
    with open('numsamples.txt','w') as f:
        f.write(str(samples[0]))


