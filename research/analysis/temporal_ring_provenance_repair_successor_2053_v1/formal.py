import hashlib, json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RESULT_PATH = ROOT / "result.json"

def admissible(obs, request):
    if not isinstance(obs, dict) or not isinstance(request, dict):
        return "UNKNOWN"
    if obs.get("status") != "AVAILABLE":
        return "UNKNOWN"
    if obs.get("surface") != request.get("surface") or obs.get("session") != request.get("session"):
        return "UNKNOWN"
    if obs.get("role") != request.get("role"):
        return "UNKNOWN"
    if not isinstance(obs.get("time"), int) or not isinstance(obs.get("label"), str):
        return "UNKNOWN"
    if not (request["lo"] <= obs["time"] <= request["hi"]):
        return "UNKNOWN"
    return obs["label"]

def main():
    request = {"surface":"s1","session":"x1","role":"CURRENT","lo":10,"hi":20}
    cases = [
        ({"status":"AVAILABLE","surface":"s1","session":"x1","role":"CURRENT","time":15,"label":"resolved"}, "resolved"),
        ({"status":"AVAILABLE","surface":"s1","session":"x1","role":"HISTORICAL","time":15,"label":"wrong-role"}, "UNKNOWN"),
        ({"status":"AVAILABLE","surface":"s1","session":"x1","role":"CURRENT","time":9,"label":"old"}, "UNKNOWN"),
        ({"status":"AVAILABLE","surface":"s2","session":"x1","role":"CURRENT","time":15,"label":"leak"}, "UNKNOWN"),
        ({"status":"AVAILABLE","surface":"s1","session":"x2","role":"CURRENT","time":15,"label":"other"}, "UNKNOWN"),
        ({"status":"DROPPED","surface":"s1","session":"x1","role":"CURRENT","time":15,"label":"missing"}, "UNKNOWN"),
        ({"status":"AVAILABLE","surface":"s1","session":"x1","role":"MISLABELED","time":15,"label":"bad"}, "UNKNOWN"),
        ({"status":"AVAILABLE","surface":"s1","session":"x1","role":"CURRENT","label":"missing-time"}, "UNKNOWN"),
        ({"status":"AVAILABLE","surface":"s1","session":"x1","role":"CURRENT","time":15}, "UNKNOWN"),
        ({"status":"AVAILABLE","surface":"s1","session":"x1","role":"CURRENT","time":20,"label":"boundary"}, "boundary"),
    ]
    rows = [{"case": i, "expected": expected, "actual": admissible(obs, request), "ok": admissible(obs, request) == expected}
            for i, (obs, expected) in enumerate(cases)]
    assert len(rows) == 10 and all(row["ok"] for row in rows)
    raw = json.dumps(rows, sort_keys=True, separators=(",", ":")).encode()
    result = {
        "decision": "PASS_TEMPORAL_RING_PROVENANCE_REPAIR_SCOPED",
        "cases": len(rows),
        "unknown_cases": sum(row["actual"] == "UNKNOWN" for row in rows),
        "mismatches": sum(not row["ok"] for row in rows),
        "result_path": str(RESULT_PATH),
        "model_gui_network_runtime_task_input": 0,
        "sha256": hashlib.sha256(raw).hexdigest(),
    }
    RESULT_PATH.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))

if __name__ == "__main__":
    main()
