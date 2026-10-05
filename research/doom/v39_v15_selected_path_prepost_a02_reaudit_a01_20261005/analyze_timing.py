import hashlib, json
from pathlib import Path

ROOT=Path(__file__).resolve().parent
SOURCE=ROOT/"inputs"/"pr-7926"/"run"/"candidate.stdout"
d=json.loads(SOURCE.read_text(encoding="utf-8"))
out=[]
for case in d["cases"]:
    bykey={r["key"]:r for r in case["rows"] if r.get("event")=="input_admission"}
    releases={r["key"]:r for r in case["rows"] if r.get("event")=="input_release_transition"}
    receipts={r["key"]:r for r in case["owner_records"]}
    for key in ("F8","space"):
        a=bykey[key]; rel=releases[key]; rec=receipts[key]
        assert (a["id"],a["owner_id"],a["intent_token"])==(rel["id"],rel["owner_id"],rel["intent_token"])
        assert (rel["owner_id"],rel["intent_token"])==(rec["owner_id"],rec["intent_token"])
        start=rec["owner_keyrelease_started_ns"]; sync=rec["owner_sync_returned_ns"]
        assert a["admitted_ns"] <= a["input_ack_ns"] <= start <= sync
        trace=case["trace"]
        down=[e for e in trace if e.get("kind")=="xtest_key_down" and e.get("keycode")==rec["keycode"]]
        up=[e for e in trace if e.get("kind")=="xtest_key_up_delivered" and e.get("keycode")==rec["keycode"]]
        suppressed=[e for e in trace if e.get("kind")=="xtest_key_up_suppressed" and e.get("keycode")==rec["keycode"]]
        assert len(down)==1 and len(up)+len(suppressed)==1
        assert next(i for i,e in enumerate(trace) if e is down[0]) < next(i for i,e in enumerate(trace) if e.get("kind")=="telemetry_emit" and e.get("event")=="input_admission" and e.get("key")==key)
        delivered=bool(up)
        out.append({
          "case":case["case"],"key":key,"keycode":rec["keycode"],"owner_id":rec["owner_id"],"intent_token":rec["intent_token"],
          "admitted_ns":a["admitted_ns"],"input_ack_ns":a["input_ack_ns"],
          "explicit_up_call_started_ns":start,"owner_sync_returned_ns":sync,
          "admission_to_up_call_start_ms":(start-a["admitted_ns"])/1e6,
          "input_ack_to_up_call_start_ms":(start-a["input_ack_ns"])/1e6,
          "up_call_bracket_ms":(sync-start)/1e6,
          "up_delivery":"delivered" if delivered else "suppressed",
          "observed_post_keymap_down":rec["keycode"] in case["post_sample"]["keycodes_down"],
          "bounds":"Monotonic timing joins the candidate's admission/ack record to its owner key-up receipt. KeyDown event precedes admission telemetry in trace but has no timestamp; admission→UP start is a lower bound on server-side hold, not exact occupancy. XSync end is not proof of physical or application release."
        })
result={"schema":"v39-v15-prepost-a02-timing-reanalysis-a01-v1","source_pr_head":"6bbdc0a70","source_base":"81a59aed13492ba1d52ea80e03d48c3d8de7b2c5","candidate_stdout_sha256":hashlib.sha256(SOURCE.read_bytes()).hexdigest(),"candidate_invocations":0,"rows":out,"conclusion":"All four admission-to-UP receipt brackets reconcile by key/owner/intent. The fake server delivers three key releases; the intentionally suppressed SPACE UP remains in the post sample and final server keymap. This supplies per-key server-call timing bounds for the preserved synthetic construction only.","scope":"No timestamped key-down, physical occupancy, application consumption, live Doom, useful feedback, recovery efficacy, threat response, or MAP01 task result."}
dest=ROOT/"results"/"reaudit-a02"/"TIMING.json"
dest.parent.mkdir(parents=True,exist_ok=True)
dest.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
print(json.dumps({"rows":len(out),"status":"PASS" if len(out)==4 else "FAIL","delivery":[(r["case"],r["key"],r["up_delivery"],r["admission_to_up_call_start_ms"],r["up_call_bracket_ms"]) for r in out]},sort_keys=True))
