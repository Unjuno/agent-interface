import json, os, subprocess, sys, tempfile, time
from pathlib import Path
from bridge import extract_schema_payload

ROOT = Path(__file__).resolve().parents[2]
def main():
    ipc = Path(tempfile.mkdtemp(prefix="ipc-schema-v2-")); rid = "schema-bridge-2818-v2-01"
    request = {"request_id": rid, "schema": str(ROOT / "research/live_control/compiled_form_grounding_schema_v1.json"), "working": str(ROOT), "prompt": "Return a minimal object satisfying the supplied schema.", "authority_granted": False}
    env = dict(os.environ); env["CODEX_EXE"] = env.get("CODEX_EXE", "codex.exe")
    p = subprocess.Popen([sys.executable, str(ROOT / "runtime/host_model_ipc_broker_v1.py"), "--ipc", str(ipc), "--repo", str(ROOT), "--once"], env=env)
    (ipc / (rid + ".request.json")).write_text(json.dumps(request), encoding="utf-8")
    response = None; raw = ""; deadline = time.monotonic() + 120
    while time.monotonic() < deadline:
        f = ipc / (rid + ".response.jsonl")
        if f.exists() and f.read_text(encoding="utf-8").strip(): raw = f.read_text(encoding="utf-8"); break
        time.sleep(.1)
    try:
        response = extract_schema_payload(raw)
        decision = {"decision": "PASS_DOCKER_IPC_SCHEMA_BRIDGE_PREFLIGHT", "authority_granted": False, "payload": response}
    except ValueError as exc:
        decision = {"decision": "STOP_SCHEMA_RESPONSE_UNNORMALIZED", "authority_granted": False, "reason": str(exc), "raw_event_types": [json.loads(x).get("type") for x in raw.splitlines() if x.strip()]}
    print(json.dumps(decision, indent=2, sort_keys=True)); p.wait(timeout=10)
    return 0 if decision["decision"].startswith("PASS") else 1
if __name__ == "__main__": raise SystemExit(main())
