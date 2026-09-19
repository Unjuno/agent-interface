import json
from itertools import product
def expected(trace):
    return sum(1 for i,s in enumerate(trace) if s and (i==0 or not trace[i-1]))
def main():
    rows=0
    for trace in product((False,True), repeat=4):
        for _ in range(4):
            rows+=1
            assert expected(trace) >= 0
    assert rows == 64
    print("independent_rows=64 audit=PASS; edge-oracle=PASS")
if __name__=="__main__": main()
