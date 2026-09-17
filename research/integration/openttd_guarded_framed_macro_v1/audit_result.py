#!/usr/bin/env python3
import argparse, hashlib, json, pathlib, sys

def sha_bytes(b): return hashlib.sha256(b).hexdigest()
def load(p): return json.loads(pathlib.Path(p).read_text(encoding="utf-8"))

def audit(fixture, result):
    errors=[]
    if result.get("formal_invocations") != 1: errors.append("formal_invocations")
    if result.get("formal_reruns") != 0: errors.append("formal_reruns")
    if result.get("source_blobs") != fixture.get("source_blobs"): errors.append("source_blobs")
    rows=result.get("rows",[])
    if len(rows)!=10: errors.append("row_count")
    source=fixture["source_procedure"]
    by={(r.get("state"),r.get("arm")):r for r in rows}
    for state in fixture["states"]:
        for arm in ("LITERAL_RAW_REPLAY","GUARDED_FRAMED_MACRO"):
            if (state["id"],arm) not in by: errors.append(f"missing:{state['id']}:{arm}")
        if state["kind"]=="ordinary":
            g=by[(state["id"],"GUARDED_FRAMED_MACRO")]
            l=by[(state["id"],"LITERAL_RAW_REPLAY")]
            if not (g.get("first_path_match") and g.get("continuation_path_match") and g.get("branch_match") and g.get("chrome_unchanged")):
                errors.append(f"guarded_mismatch:{state['id']}")
            if l.get("first_path_match") or l.get("continuation_path_match") or not l.get("chrome_unchanged"):
                errors.append(f"literal_discriminator:{state['id']}")
        else:
            g=by[(state["id"],"GUARDED_FRAMED_MACRO")]
            if g.get("fault_refusal_match") is not True or g["output"].get("pointer_target_emitted") is not False:
                errors.append("binding_fault")
    if any(r.get("output",{}).get("authority") != "none" or r.get("output",{}).get("task_input_granted") is not False for r in rows):
        errors.append("authority")
    expected_gates={
      "candidate_path_match_4of4", "candidate_branch_match_4of4", "candidate_chrome_unchanged_4of4",
      "literal_content_mismatch_4of4", "literal_chrome_unchanged_4of4", "candidate_binding_fault_refusal",
      "candidate_no_authority_all_rows", "row_count_10"}
    gates=result.get("gates",{})
    if set(gates)!=expected_gates or not all(gates.values()): errors.append("gates")
    expected_decision="PASS_OPENTTD_GUARDED_MACRO_TRANSFER_SCOPED" if not errors else result.get("decision")
    if not errors and result.get("decision")!=expected_decision: errors.append("decision")
    return {"audit":"PASS" if not errors else "FAIL", "errors":errors,
            "decision":result.get("decision"), "result_sha256":sha_bytes((json.dumps(result, indent=2, sort_keys=True)+"\n").encode())}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("fixture"); ap.add_argument("result"); ap.add_argument("--output")
    a=ap.parse_args(); out=audit(load(a.fixture),load(a.result)); text=json.dumps(out,indent=2,sort_keys=True)+"\n"
    if a.output: pathlib.Path(a.output).write_text(text,encoding="utf-8",newline="\n")
    else: sys.stdout.write(text)
    raise SystemExit(0 if out["audit"]=="PASS" else 1)
if __name__=="__main__": main()
