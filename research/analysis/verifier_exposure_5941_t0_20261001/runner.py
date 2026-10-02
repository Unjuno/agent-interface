"""Finite provenance witness for Issue #5941; standard library only."""
import json
from itertools import product


def evaluate(case):
    # An exposed second verdict is never a second independent vote. Unknown
    # exposure provenance also receives no independence credit.
    votes = case["votes"]
    independent = []
    for v in votes:
        if v["exposure"] == "none" and v["commit_valid"]:
            independent.append(v["verdict"])
    raw_yes = sum(v["verdict"] == "PASS" for v in votes) >= 2
    scoped_yes = len(independent) >= 2 and sum(x == "PASS" for x in independent) >= 2
    if scoped_yes:
        disposition = "PASS_SCOPED"
    elif len(independent) >= 2 and sum(x == "FAIL" for x in independent) >= 2:
        disposition = "FAIL_SCOPED"
    else:
        disposition = "UNKNOWN_INDEPENDENCE"
    return {"raw_quorum_pass": raw_yes, "scoped_quorum_pass": scoped_yes,
            "independent_first_pass": independent, "disposition": disposition}


def cases():
    rows=[]
    # All triples over pass/fail, with V2 exposure and commitment validity.
    for a,b,c in product(("PASS","FAIL"), repeat=3):
        for exposure in ("none","peer_verdict","raw_observation","unknown"):
            for valid in (True,False):
                votes=[{"verdict":a,"exposure":"none","commit_valid":True},
                       {"verdict":b,"exposure":exposure,"commit_valid":valid},
                       {"verdict":c,"exposure":"none","commit_valid":True}]
                truth="PASS" if sum(x=="PASS" for x in (a,b,c))>=2 else "FAIL"
                row={"case_id":f"{len(rows):03d}","truth":truth,"votes":votes}
                row["result"]=evaluate(row)
                rows.append(row)
    # Omitted/forged exposure is represented by unknown provenance and must
    # not create credit for the second receipt.
    for mode in ("omitted_edge","forged_none"):
        row={"case_id":f"{len(rows):03d}","truth":"FAIL","mutation":mode,
             "votes":[{"verdict":"PASS","exposure":"none","commit_valid":True},
                      {"verdict":"PASS","exposure":"unknown","commit_valid":True},
                      {"verdict":"FAIL","exposure":"none","commit_valid":True}]}
        row["result"]=evaluate(row)
        rows.append(row)
    return rows


if __name__ == "__main__":
    out={"schema":"issue5941-finite-witness-v1","cases":cases()}
    print(json.dumps(out,sort_keys=True,separators=(",",":")))
