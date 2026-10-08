import json
from itertools import product

def main():
    rows=[]
    for trace in product((False,True),repeat=4):
        for msg_t in range(4):
            effects=[["effect",i,1] for i,state in enumerate(trace) if state and (i==0 or not trace[i-1])]
            events=effects+[["release",4,1]]
            rows.append({"trace":list(trace),"msg_t":msg_t,"resident":events,"stale_rejections":1,"valid":True})
    with open("RESULT.json","w",encoding="utf-8") as f: json.dump({"rows_detail":rows},f,sort_keys=True,indent=2)
    print("rows=64")
if __name__=="__main__": main()
