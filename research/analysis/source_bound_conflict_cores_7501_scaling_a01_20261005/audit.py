#!/usr/bin/env python3
"""Independent audit: mask-ordered exhaustive truth-table oracle for completed rows."""
import itertools, json, platform, sys
from pathlib import Path

def make_case(k, ident, budget):
    clauses=[]
    for i in range(k):
        clauses += [{"id":f"x{i}_pos","source_span":f"r1#{2*i+1}","kind":"relaxable","literals":[f"x{i}"]},{"id":f"x{i}_neg","source_span":f"r1#{2*i+2}","kind":"relaxable","literals":[f"!x{i}"]}]
    return {"id":ident,"vars":[f"x{i}" for i in range(k)],"clauses":clauses,"compiled_revision":"r1","current_revision":"r1","budget":budget,"expected_full_subsets":(4**k)-1,"expected_core_count":k}

def formula_true(subset, bits, variables):
    assignment={name:bool(bits & (1 << index)) for index,name in enumerate(variables)}
    return all(any((assignment[lit[1:]] == False) if lit.startswith("!") else assignment[lit] for lit in clause["literals"]) for clause in subset)

def oracle(case):
    clauses=case["clauses"]
    valuations=range(1 << len(case["vars"]))
    unsat=[]
    # Different enumeration order from candidate: integer masks rather than combinations by cardinality.
    for mask in range(1, 1 << len(clauses)):
        subset=[clause for i,clause in enumerate(clauses) if mask & (1 << i)]
        if not any(formula_true(subset,bits,case["vars"]) for bits in valuations):
            unsat.append(tuple(sorted(clause["id"] for clause in subset)))
    minimal=[core for core in unsat if not any(set(other)<set(core) for other in unsat)]
    return sorted(minimal)

def verify(fixture, candidate):
    if candidate.get("format") != "mus-scaling-candidate-v1": return False, []
    rows=candidate.get("rows")
    if not isinstance(rows,list) or len(rows)!=len(fixture["cases"]): return False, []
    audit_rows=[]
    for cfg,row in zip(fixture["cases"],rows):
        case=make_case(cfg["k"],cfg["id"],cfg["budget"])
        if row.get("id") != case["id"]: return False, audit_rows
        core_sets=[tuple(sorted(c)) for c in row.get("cores",[])]
        if len(core_sets)!=len(set(core_sets)): return False,audit_rows
        for core in core_sets:
            selected=[c for c in case["clauses"] if c["id"] in core]
            if len(selected)!=len(core): return False,audit_rows
            if any(formula_true(selected,bits,case["vars"]) for bits in range(1 << len(case["vars"]))): return False,audit_rows
            for removed in core:
                reduced=[c for c in selected if c["id"]!=removed]
                if not any(formula_true(reduced,bits,case["vars"]) for bits in range(1 << len(case["vars"]))): return False,audit_rows
        if case["budget"] == case["expected_full_subsets"]:
            expected=oracle(case)
            if row.get("status")!="CONFLICT_CORE_COMPLETE" or row.get("complete") is not True or row.get("dispatch_allowed") is not False or core_sets!=expected or row.get("work_units")!=case["expected_full_subsets"]: return False,audit_rows
            expected_count=case["expected_core_count"]
        else:
            if row.get("status")!="INCOMPLETE" or row.get("complete") is not False or row.get("dispatch_allowed") is not False or row.get("work_units")!=case["budget"] or case["budget"]>=case["expected_full_subsets"]: return False,audit_rows
            expected_count=case["expected_core_count"]
        audit_rows.append({"id":case["id"],"status":row["status"],"work_units":row["work_units"],"full_subset_count":case["expected_full_subsets"],"cores_emitted":len(core_sets),"oracle_core_count":expected_count,"partial_cores_valid":True})
    return True,audit_rows

def mutations(fixture,candidate):
    outcomes={}
    def run(name,change):
        altered=json.loads(json.dumps(candidate)); change(altered); outcomes[name]=not verify(fixture,altered)[0]
    run("drop_complete_core",lambda c:c["rows"][0]["cores"].pop())
    run("mark_budgeted_complete",lambda c:c["rows"][6].update(status="CONFLICT_CORE_COMPLETE",complete=True))
    run("dispatch_from_incomplete",lambda c:c["rows"][7].update(dispatch_allowed=True))
    run("inflate_work_beyond_budget",lambda c:c["rows"][6].update(work_units=1025))
    return outcomes

def main():
    fixture=json.loads(Path(sys.argv[1]).read_text(encoding="utf-8-sig")); candidate=json.loads(Path(sys.argv[2]).read_text(encoding="utf-8-sig"))
    passed,rows=verify(fixture,candidate); controls=mutations(fixture,candidate)
    result={"oracle_match":passed,"rows":rows,"mutation_controls_rejected":controls,"all_mutations_rejected":all(controls.values()),"python":platform.python_version(),"implementation":platform.python_implementation(),"machine":platform.machine()}
    Path(sys.argv[3]).write_text(json.dumps(result,sort_keys=True,separators=(",",":"))+"\n",encoding="utf-8")
    Path(sys.argv[4]).write_text(json.dumps(result,sort_keys=True,separators=(",",":"))+"\n",encoding="utf-8")
    print(json.dumps(result,sort_keys=True))
    if not (passed and result["all_mutations_rejected"]): raise SystemExit(1)

if __name__ == "__main__": main()
