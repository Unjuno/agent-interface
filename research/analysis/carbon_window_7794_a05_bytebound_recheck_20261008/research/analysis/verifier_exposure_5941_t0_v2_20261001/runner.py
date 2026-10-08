"""Fresh, deterministic Issue #5941 successor T0; standard library only."""
import json
from itertools import product

EXPOSURES = ("none", "peer_verdict", "raw_observation", "unknown")

def score(votes):
    eligible = [v["verdict"] for v in votes if v["exposure"] == "none" and v["commit_valid"] is True]
    p, f = eligible.count("PASS"), eligible.count("FAIL")
    disposition = "PASS_SCOPED" if p >= 2 else "FAIL_SCOPED" if f >= 2 else "UNKNOWN_INDEPENDENCE"
    return {"raw_quorum_pass": sum(v["verdict"] == "PASS" for v in votes) >= 2,
            "scoped_quorum_pass": disposition == "PASS_SCOPED",
            "independent_first_pass": eligible, "disposition": disposition}

def generate():
    rows=[]
    for truth_index,(a,b,c) in enumerate(product(("PASS", "FAIL"), repeat=3)):
        for exposure in EXPOSURES:
            for commit_valid in (True, False):
                votes=[{"verifier":"V1","domain":"A","verdict":a,"exposure":"none","commit_valid":True},
                       {"verifier":"V2","domain":"B","verdict":b,"exposure":exposure,"commit_valid":commit_valid},
                       {"verifier":"V3","domain":"C","verdict":c,"exposure":"none","commit_valid":True}]
                # Ground truth is a separately preassigned balanced factor,
                # not derived from the verifier votes being evaluated.
                truth="PASS" if truth_index % 2 == 0 else "FAIL"
                row={"case_id":f"{len(rows):03d}","truth":truth,"votes":votes}
                row["result"]=score(votes); rows.append(row)
    for mutation in ("omitted_edge","forged_none"):
        votes=[{"verifier":"V1","domain":"A","verdict":"PASS","exposure":"none","commit_valid":True},
               {"verifier":"V2","domain":"B","verdict":"PASS","exposure":"unknown","commit_valid":True},
               {"verifier":"V3","domain":"C","verdict":"FAIL","exposure":"none","commit_valid":True}]
        row={"case_id":f"{len(rows):03d}","truth":"FAIL","mutation":mutation,"votes":votes}
        row["result"]=score(votes); rows.append(row)
    return {"schema":"issue5941-finite-witness-v2","cases":rows}

if __name__ == "__main__":
    print(json.dumps(generate(),sort_keys=True,separators=(",",":")))
