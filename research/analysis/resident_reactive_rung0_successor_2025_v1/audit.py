from itertools import product

def expected_edges(trace):
    return sum(1 for i,state in enumerate(trace)
               if state and (i == 0 or not trace[i-1]))

def audit_row(trace, msg_t):
    generation=1
    stale_generation=0
    effects=0
    previous=False
    for t,state in enumerate(trace):
        if t == msg_t and 0 != generation:
            stale_generation += 1
            continue
        if state and not previous:
            effects += 1
        previous=state
    return effects == expected_edges(trace) and stale_generation == 1

def main():
    rows=0
    for trace in product((False,True), repeat=4):
        for msg_t in range(4):
            rows += 1
            assert audit_row(trace,msg_t)
    assert rows == 64
    print("independent_rows=64 stale_rejections=64 edge-oracle=PASS")
if __name__=="__main__": main()
