import json
import sys

POLICIES=("NO_RESTORE","SUMMARY_ONLY","RESTORE_ONLY","RESTORE_PLUS_DIFF")


def diff(a,b):
    return {k:{"before":a.get(k),"after":b.get(k)} for k in sorted(set(a)|set(b)) if a.get(k)!=b.get(k)}


def evaluate(cases, rows, oracle):
    lookup={(r["case"],r["policy"]):r for r in rows}
    checks=[]
    for case in cases:
        for policy in POLICIES:
            row=lookup.get((case["id"],policy))
            if row is None:
                checks.append({"case":case["id"],"policy":policy,"valid":False,"success":False})
                continue
            mismatches=sum(row["context_after"].get(k)!=v for k,v in case["next_requires"].items())
            effects_ok=all(row["effects_after"].get(k)==v for k,v in oracle[case["id"]].items())
            external_ok=all(row["context_after"].get(k)==case["terminal"].get(k) for k in case["external_fields"])
            artifacts_ok=all(v in row["context_after"].values() for v in case["required_artifacts"])
            unknown_ok=all(row["context_after"].get(k)==case["terminal"].get(k) for k in case["unknown_fields"])
            residual_ok=(row["residual_state_diff"]==diff(case["initial"],row["context_after"]) if policy=="RESTORE_PLUS_DIFF" else
                         row["residual_state_diff"]==(diff(case["initial"],row["context_after"]) if policy=="SUMMARY_ONLY" else {}))
            safe_flags=(row["effects_lost"] == (not effects_ok) and row["external_overwrite"] == (not external_ok) and
                        row["artifacts_lost"] == (not artifacts_ok) and row["unresolved_cleared"] == (not unknown_ok))
            valid=(row["modeled_context_mismatches"]==mismatches and residual_ok and safe_flags)
            checks.append({"case":case["id"],"policy":policy,"valid":valid,"success":mismatches==0,
                           "mismatches_recomputed":mismatches,"mismatches_reported":row["modeled_context_mismatches"]})
    totals={p:{"successes":sum(c["success"] for c in checks if c["policy"]==p),
               "mismatch_total":sum(c["mismatches_recomputed"] for c in checks if c["policy"]==p)} for p in POLICIES}
    rpd=totals["RESTORE_PLUS_DIFF"]["successes"]
    summary=totals["SUMMARY_ONLY"]["successes"]
    valid=len(checks)==len(cases)*len(POLICIES) and all(c["valid"] for c in checks)
    plus=[lookup[(case["id"],"RESTORE_PLUS_DIFF")] for case in cases]
    rpd_safe=all(not r["effects_lost"] and all(r["effects_after"].get(k)==v for k,v in oracle[r["case"]].items()) and
                 not r["external_overwrite"] and not r["artifacts_lost"] and not r["unresolved_cleared"] for r in plus)
    return {"audited_rows":len(checks),"all_rows_valid":valid,"rows":checks,"totals":totals,
            "restore_plus_diff_not_worse_than_summary":rpd>=summary,
            "restore_plus_diff_safety_invariants":rpd_safe,
            "decision":"PASS_METHOD_SCOPED" if valid and rpd_safe and rpd>=summary and rpd>summary else "UNCERTAIN_OR_FAIL"}


def main(fixture_path, candidate_path, oracle_path):
    fixture=json.load(open(fixture_path,encoding="utf-8"))
    candidate=json.load(open(candidate_path,encoding="utf-8"))
    oracle=json.load(open(oracle_path,encoding="utf-8"))["expected_case_safety"]
    return evaluate(fixture["cases"],candidate,oracle)


if __name__=="__main__":
    print(json.dumps(main(*sys.argv[1:]),sort_keys=True,separators=(",",":")))
