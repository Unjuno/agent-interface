"""Finite successor fixture for Issue #1979 / idea #1941."""
from itertools import product
import hashlib,json

OBS=("current_causal","older_causal","older_irrelevant","unexpected")
META={"current_causal":(1,3),"older_causal":(1,2),
      "older_irrelevant":(0,1),"unexpected":(0,0)}

def oracle(stream):
    return sorted(range(len(stream)),
                  key=lambda i:(META[stream[i]][0],i),reverse=True)

def recency(stream): return list(reversed(range(len(stream))))

def causal_then_recency(stream):
    return sorted(range(len(stream)),
                  key=lambda i:(META[stream[i]][0],i),reverse=True)

def reconstruct(stream,order): return tuple(stream[i] for i in order)

def run():
    rows=[]
    for n in range(1,6):
        for stream in product(OBS,repeat=n):
            oracle_order=oracle(stream)
            causal_order=causal_then_recency(stream)
            recency_order=recency(stream)
            rows.append({
                "stream":stream,"oracle":oracle_order,
                "causal":causal_order,"recency":recency_order,
                "causal_exact":causal_order==oracle_order,
                "recency_exact":recency_order==oracle_order,
                "raw_sha":hashlib.sha256(
                    json.dumps(stream).encode()).hexdigest()})
    return rows

if __name__=="__main__":
    rows=run()
    assert all(x["causal_exact"] for x in rows)
    counter=[x for x in rows if not x["recency_exact"]]
    assert counter
    assert all(reconstruct(x["stream"],x["causal"]) ==
               reconstruct(x["stream"],x["oracle"]) for x in rows)
    print("streams",len(rows),
          "causal_exact",sum(x["causal_exact"] for x in rows),
          "recency_counterexamples",len(counter))
    print("first_counterexample",counter[0])
