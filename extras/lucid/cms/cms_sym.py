# keep track of measurements from interpreter
import pickle

interp_measure = {}

def update_count(src, dst, count):
    interp_measure[str(src)+str(dst)] = count
    with open("test.txt",'wb') as f:
        pickle.dump(interp_measure, f)


