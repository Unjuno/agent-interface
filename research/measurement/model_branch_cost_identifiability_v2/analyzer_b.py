#!/usr/bin/env python3
import argparse, collections, json
from pathlib import Path

KEYS=("run","i","img","input","cached","output","reasoning","model_ns","effect","state","primary","branches","session")

def rec(v):
    return dict(zip(KEYS,v))

def frozen(x):
    return json.dumps(x,sort_keys=True,separators=(",",":"))

def fingerprint(r):
    return frozen({
        "img":r["img"],
        "effect":r["effect"],
        "state":r["state"],
        "primary":r["primary"],
        "input":r["input"],
        "cached":r["cached"],
        "session":r["session"],
    })

def analyze(path):
    data=json.loads(Path(path).read_text())
    rows=[rec(x) for x in data["rows"]]
    g=[x for x in rows if x["run"]=="grouped"]
    u=[x for x in rows if x["run"]=="ungrouped"]
    gi=collections.defaultdict(list)
    ui=collections.defaultdict(list)
    gimg=collections.Counter()
    uimg=collections.Counter()
    for r in g:
        gi[fingerprint(r)].append(r)
        gimg[r["img"]]+=1
    for r in u:
        ui[fingerprint(r)].append(r)
        uimg[r["img"]]+=1
    admissible=[]
    fully_matched_pairs=0
    for key in sorted(set(gi)&set(ui)):
        for a in gi[key]:
            for b in ui[key]:
                fully_matched_pairs+=1
                if a["branches"] != b["branches"]:
                    admissible.append([a["i"],b["i"]])
    same_image=sum(gimg[k]*uimg[k] for k in set(gimg)&set(uimg))
    return {
        "analyzer":"B_fingerprint_index",
        "rows":len(rows),
        "grouped_rows":len(g),
        "ungrouped_rows":len(u),
        "candidate_pairs":len(g)*len(u),
        "same_image_pairs":same_image,
        "fully_matched_prebranch_pairs":fully_matched_pairs,
        "admissible_pairs":sorted(admissible),
        "admissible_pair_count":len(admissible),
        "all_pairs_fail_at_least_one_required_gate":fully_matched_pairs==0,
        "causal_per_branch_estimate":None
    }

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("ledger")
    p.add_argument("out")
    a=p.parse_args()
    Path(a.out).write_text(json.dumps(analyze(a.ledger),indent=2,sort_keys=True)+"\n")
