#!/usr/bin/env python3
"""Frozen bounded candidate: enumerate every clause subset in cardinality order."""
import itertools, json, platform, sys
from pathlib import Path

def fixture_case(k, ident, budget):
    clauses=[]
    for i in range(k):
        clauses.extend([
            {"id":f"x{i}_pos","source_span":f"r1#{2*i+1}","kind":"relaxable","literals":[f"x{i}"]},
            {"id":f"x{i}_neg","source_span":f"r1#{2*i+2}","kind":"relaxable","literals":[f"!x{i}"]}
        ])
    return {"id":ident,"vars":[f"x{i}" for i in range(k)],"clauses":clauses,"compiled_revision":"r1","current_revision":"r1","budget":budget,"expected_full_subsets":(1 << (2*k))-1,"expected_core_count":k}

def assignments(names):
    return [dict(zip(names, bits)) for bits in itertools.product((False, True), repeat=len(names))]

def sat(clauses, valuation):
    for clause in clauses:
        if not any((not valuation[literal[1:]]) if literal.startswith("!") else valuation[literal] for literal in clause["literals"]):
            return False
    return True

def solve(case):
    vals=assignments(case["vars"])
    clauses=case["clauses"]
    cores=[]
    work=0
    for size in range(1, len(clauses)+1):
        for subset in itertools.combinations(clauses, size):
            if work >= case["budget"]:
                return {"id":case["id"],"status":"INCOMPLETE","complete":False,"dispatch_allowed":False,"cores":cores,"work_units":work}
            work += 1
            if not any(sat(subset, v) for v in vals):
                ids=[c["id"] for c in subset]
                if not any(set(core).issubset(ids) for core in cores):
                    cores.append(ids)
    status="CONFLICT_CORE_COMPLETE" if cores else "SAT"
    return {"id":case["id"],"status":status,"complete":True,"dispatch_allowed":status=="SAT","cores":cores,"work_units":work}

def main():
    fixture=json.loads(Path(sys.argv[1]).read_text(encoding="utf-8-sig"))
    out=Path(sys.argv[2]); stdout=Path(sys.argv[3])
    rows=[solve(fixture_case(c["k"], c["id"], c["budget"])) for c in fixture["cases"]]
    result={"format":"mus-scaling-candidate-v1","rows":rows}
    summary={"case_count":len(rows),"statuses":{s:sum(r["status"]==s for r in rows) for s in sorted({r["status"] for r in rows})},"python":platform.python_version(),"implementation":platform.python_implementation(),"machine":platform.machine()}
    out.write_text(json.dumps(result,sort_keys=True,separators=(",",":"))+"\n",encoding="utf-8")
    stdout.write_text(json.dumps(summary,sort_keys=True,separators=(",",":"))+"\n",encoding="utf-8")
    print(json.dumps(summary,sort_keys=True))

if __name__ == "__main__": main()
