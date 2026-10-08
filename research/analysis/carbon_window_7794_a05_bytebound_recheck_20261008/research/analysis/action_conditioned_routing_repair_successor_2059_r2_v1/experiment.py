import hashlib, json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RESULT_PATH = ROOT / "result.json"

def route(intent, raw):
    if not isinstance(intent, dict) or not isinstance(raw, dict):
        return {"decision":"UNKNOWN","reason":"MALFORMED","regions":[],"raw":None,"authority":False}
    kind = intent.get("kind")
    if not isinstance(kind, str) or kind not in ("save","move"):
        return {"decision":"UNKNOWN","reason":"UNKNOWN_INTENT","regions":[],"raw":raw,"authority":False}
    if not isinstance(intent.get("target"), str) or not intent["target"]:
        return {"decision":"UNKNOWN","reason":"MALFORMED_TARGET","regions":[],"raw":raw,"authority":False}
    regions = ["save_button","status_region"] if kind == "save" else ["canvas","destination_marker"]
    return {"decision":"ROUTE","reason":"VALID","regions":regions,"raw":raw,"authority":False}

def main():
    raw = {"frame_id":"f1","surface":"s1","pixels_sha256":"abc"}
    cases = [
        ({"kind":"save","target":"button"}, "ROUTE"),
        ({"kind":"move","target":"marker"}, "ROUTE"),
        ({"kind":"delete","target":"button"}, "UNKNOWN"),
        ({"kind": ["save"], "target":"button"}, "UNKNOWN"),
        ({"kind":"save","target":None}, "UNKNOWN"),
        ({"kind":"save"}, "UNKNOWN"),
        (["save"], "UNKNOWN"),
        ({"kind":"move","target":"marker","extra":{"bad":True}}, "ROUTE"),
    ]
    rows = []
    for i, (intent, expected) in enumerate(cases):
        out = route(intent, raw)
        rows.append({"case":i,"expected":expected,"actual":out["decision"],"output":out,
                     "ok":out["decision"] == expected})
    assert len(rows) == 8 and all(r["ok"] for r in rows)
    assert all(r["output"]["authority"] is False for r in rows)
    serialized = json.dumps(rows, sort_keys=True, separators=(",", ":")).encode()
    result = {
        "decision":"PASS_ACTION_CONDITIONED_ROUTING_REPAIR_SCOPED",
        "cases":len(rows),
        "mismatches":sum(not r["ok"] for r in rows),
        "malformed_or_unknown":sum(r["actual"] == "UNKNOWN" for r in rows),
        "raw_retained_rows":sum(r["output"]["raw"] == raw for r in rows),
        "raw_sha256":hashlib.sha256(json.dumps(raw,sort_keys=True,separators=(",",":")).encode()).hexdigest(),
        "rows_sha256":hashlib.sha256(serialized).hexdigest(),
        "authority_true":sum(r["output"]["authority"] for r in rows),
        "model_gui_network_runtime_task_input":0,
    }
    RESULT_PATH.write_text(json.dumps(result, sort_keys=True, indent=2)+"
", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
if __name__ == "__main__":
    main()
