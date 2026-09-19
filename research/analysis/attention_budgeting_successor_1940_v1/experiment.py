"""Finite attention-budget allocation fixture for Issue #1940."""
import hashlib,json
ITEMS=(("target",8,10),("effect",6,7),("history",5,5),
       ("context",4,4),("static",3,1),("decorative",2,0))
BUDGETS=range(18)
def oracle(b):
    best=(0,())
    for mask in range(1<<len(ITEMS)):
        chosen=tuple(i for i in range(len(ITEMS)) if mask>>i&1)
        cost=sum(ITEMS[i][1] for i in chosen)
        value=sum(ITEMS[i][2] for i in chosen)
        if cost<=b and (value>best[0] or (value==best[0] and chosen<best[1])):
            best=(value,chosen)
    return best
def run():
    rows=[]
    for b in BUDGETS:
        value,chosen=oracle(b)
        raw=[{"name":n,"cost":c,"priority":v} for n,c,v in ITEMS]
        rows.append({"budget":b,"value":value,"chosen":chosen,
                     "raw_sha":hashlib.sha256(
                         json.dumps(raw,sort_keys=True).encode()).hexdigest()})
    return rows
if __name__=="__main__":
    rows=run()
    assert rows and rows[-1]["value"]==19
    assert all(r["value"]==oracle(r["budget"])[0] for r in rows)
    print("budgets",len(rows),"items",len(ITEMS),"max_value",rows[-1]["value"])
    print("rows_sha",hashlib.sha256(
        json.dumps(rows,sort_keys=True).encode()).hexdigest())
