#!/usr/bin/env python3
"""Independent raw-only T1 audit; does not import candidate code."""
import hashlib, json, sys
from pathlib import Path

STRATA = ("easy", "hard")
EXPECTED = {"composition_stable":"TRANSPORT_METHOD_CONTROL_PASS","mechanism_shift":"HOLD_NONTRANSPORTABLE","support_failure":"HOLD_NONTRANSPORTABLE","endpoint_mismatch":"HOLD_NONCOMPARABLE"}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def rate(cell):
    good, total = cell
    if not isinstance(good,int) or not isinstance(total,int) or total <= 0 or good < 0 or good > total:
        return None
    return good / total


def reconstruct(case):
    st=sum(case["source_population"].get(s,0) for s in STRATA)
    tt=sum(case["target_population"].get(s,0) for s in STRATA)
    if st <= 0 or tt <= 0:
        return None
    sw={s:case["source_population"].get(s,0)/st for s in STRATA}
    tw={s:case["target_population"].get(s,0)/tt for s in STRATA}
    se,te={},{}
    for s in STRATA:
        sa,sb=rate(case["source_outcomes"][s]["A"]),rate(case["source_outcomes"][s]["B"])
        ta,tb=rate(case["target_outcomes"][s]["A"]),rate(case["target_outcomes"][s]["B"])
        se[s]=None if sa is None or sb is None else sb-sa
        te[s]=None if ta is None or tb is None else tb-ta
    support=all(case["source_population"].get(s,0)>0 and case["target_population"].get(s,0)>0 and se[s] is not None and te[s] is not None for s in STRATA)
    comparable=case["source_endpoint"]==case["target_endpoint"]
    invariant=support and all(se[s]==te[s] for s in STRATA)
    source=None if any(se[s] is None for s in STRATA) else sum(sw[s]*se[s] for s in STRATA)
    target=None if any(te[s] is None for s in STRATA) else sum(tw[s]*te[s] for s in STRATA)
    naive=None if not support else sum(tw[s]*se[s] for s in STRATA)
    if not comparable:
        return ("HOLD_NONCOMPARABLE","endpoint_contract_mismatch",source,target,se,te,support,comparable,invariant,None,None)
    if not support:
        return ("HOLD_NONTRANSPORTABLE","positivity_or_cell_support_missing",source,target,se,te,support,comparable,invariant,None,None)
    if not invariant:
        return ("HOLD_NONTRANSPORTABLE","conditional_route_effect_changed",source,target,se,te,support,comparable,invariant,None,naive)
    return ("TRANSPORT_METHOD_CONTROL_PASS","support_and_conditional_effects_match",source,target,se,te,support,comparable,invariant,naive,None)


def expected(case):
    r=reconstruct(case)
    status,reason,src,tgt,se,te,sup,cmp,inv,trans,diag=r
    return {"status":status,"reason":reason,"source_direct_effect":src,"target_direct_effect":tgt,
            "conditional_effects_source":se,"conditional_effects_target":te,"common_support":sup,
            "endpoint_comparable":cmp,"conditional_effect_invariant":inv,"transported_effect":trans,
            "diagnostic_only_naive_standardization":diag}


def audit(result,doc,candidate_path):
    errors=[]; freeze=json.loads((Path(__file__).parent/"FREEZE.json").read_text(encoding="utf-8")); errors += (["auditor_source_sha256"] if sha(__file__)!=freeze.get("sha256",{}).get("auditor_sha256") else []); errors += (["base_main_sha"] if result.get("base_main_sha")!=freeze.get("base_main_sha") else []); errors += (["container_image_ref"] if result.get("container_image_ref")!=freeze.get("container_image_ref") else []); errors += (["frozen_candidate_sha256"] if result.get("candidate_sha256")!=freeze.get("sha256",{}).get("candidate_sha256") else []); errors += (["frozen_input_sha256"] if result.get("input_sha256")!=freeze.get("sha256",{}).get("input_sha256") else [])
    if result.get("schema")!="selection-transport-t1-result-v1": errors.append("schema")
    if result.get("allocation")!="SELECTION-TRANSPORT-5663-T1-20261002-01": errors.append("allocation")
    if result.get("input_sha256")!=sha(Path(__file__).parent/"inputs"/"fixture.json"): errors.append("input_sha256")
    if result.get("candidate_sha256")!=sha(candidate_path): errors.append("candidate_sha256")
    got=result.get("scenarios")
    if not isinstance(got,dict) or set(got)!=set(EXPECTED): return errors+["scenario_set"]
    for name in EXPECTED:
        exp,obs=expected(doc["scenarios"][name]),got[name]
        for key,val in exp.items():
            if key not in obs: errors.append(name+":"+key+":missing")
            elif isinstance(val,float):
                if not isinstance(obs[key],(int,float)) or abs(obs[key]-val)>1e-12: errors.append(name+":"+key+":mismatch")
            elif obs[key]!=val: errors.append(name+":"+key+":mismatch")
    return errors


def main():
    raw=json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    doc=json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
    errors=audit(raw,doc,Path(__file__).parent/"candidate.py")
    print(json.dumps({"auditor":"selection-transport-t1-independent-auditor-v1","result":"PASS_METHOD_SCOPED" if not errors else "FAIL_AUDIT","scenario_count":len(raw.get("scenarios",{})),"errors":errors},sort_keys=True))
    raise SystemExit(0 if not errors else 1)


if __name__ == "__main__":
    main()