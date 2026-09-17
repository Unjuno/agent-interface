import hashlib, json, random, time
from pathlib import Path
import baseline, candidate
from common import fixed_cases, make_case, state_tuple, strip_samples

ROOT=Path(__file__).resolve().parent
FREEZE=json.loads((ROOT/'FREEZE.json').read_text())

def digest_update(h, idx, equal, order_ok):
    h.update(f"{idx}:{int(equal)}:{int(order_ok)}\n".encode())

def check_order(case, trace):
    names=[r[0] for r in trace]
    if case.op=="down":
        if "sample_pre" not in names:
            # rejected before sampling is allowed
            return not any(x in names for x in ("KeyPress","sample_post"))
        if names.index("sample_pre") <= names.index("admitted_clock"):
            return False
        if "KeyPress" not in names or names.index("sample_pre") >= names.index("KeyPress"):
            return False
        if "sync" in names and names.index("sync") < names.index("KeyPress"):
            return False
        if "sample_post" in names:
            return "sync" in names and names.index("sample_post") > names.index("sync")
        return True
    if case.op=="up":
        if "sample_pre" not in names:
            return "held_owner_check" in names and (case.held_relation=="other" or not case.key_available)
        if names.index("sample_pre") <= names.index("held_owner_check"):
            return False
        if case.held_relation=="self":
            if "KeyRelease" not in names or names.index("sample_pre") >= names.index("KeyRelease"):
                return False
            if "sample_post" in names:
                return "sync" in names and names.index("sample_post") > names.index("sync") and "held_del" in names and names.index("sample_post") > names.index("held_del")
        else:
            return "KeyRelease" not in names and "sample_post" in names and names.index("sample_post") > names.index("sample_pre")
        return True
    return False

def compare(case):
    bs,bo=baseline.execute(case); cs,co=candidate.execute(case)
    eq=(bo.semantic()==co.semantic() and strip_samples(cs.trace)==bs.trace and state_tuple(cs)==state_tuple(bs))
    return eq, check_order(case,cs.trace), bs,bo,cs,co

def main():
    started=time.perf_counter_ns()
    errors=[]; fixed=[]
    for name,case in fixed_cases():
        eq,order,bs,bo,cs,co=compare(case)
        fixed.append({"name":name,"equal":eq,"order_ok":order,"baseline_outcome":bo.semantic(),"candidate_outcome":co.semantic(),"baseline_trace":bs.trace,"candidate_trace":cs.trace,"state_equal":state_tuple(bs)==state_tuple(cs)})
        if not eq or not order: errors.append(f"fixed:{name}:eq={eq}:order={order}")
    rng=random.Random(FREEZE['random_seed']); h=hashlib.sha256(); mismatches=order_errors=0
    sample_fail_cases=sample_fail_semantic_changes=0
    for i in range(FREEZE['random_cases']):
        case=make_case(rng)
        eq,order,bs,bo,cs,co=compare(case)
        if not eq: mismatches+=1
        if not order: order_errors+=1
        if (not case.sample_pre_ok) or (not case.sample_post_ok):
            sample_fail_cases+=1
            if bo.semantic()!=co.semantic() or strip_samples(cs.trace)!=bs.trace or state_tuple(cs)!=state_tuple(bs): sample_fail_semantic_changes+=1
        digest_update(h,i,eq,order)
    result={
      "task":FREEZE['task'],"decision":"PASS_OWNER_PHYSICAL_SAMPLE_SEQUENCING_SCOPED" if not errors and mismatches==0 and order_errors==0 and sample_fail_semantic_changes==0 else "FAIL_CONSTRUCTION",
      "fixed":fixed,"random_cases":FREEZE['random_cases'],"random_mismatches":mismatches,"order_errors":order_errors,
      "sample_fail_cases":sample_fail_cases,"sample_fail_semantic_changes":sample_fail_semantic_changes,"case_digest":h.hexdigest(),
      "forbidden_claims":{"actuation_id":False,"physical_interval":False,"authority":False,"application_consumption":False},
      "errors":errors,"elapsed_ns":time.perf_counter_ns()-started,
    }
    (ROOT/'RESULT.json').write_text(json.dumps(result,indent=2,sort_keys=True))
    print(json.dumps({k:result[k] for k in ('decision','random_cases','random_mismatches','order_errors','sample_fail_cases','sample_fail_semantic_changes','case_digest','elapsed_ns')},sort_keys=True))

if __name__=='__main__': main()
