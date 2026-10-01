"""Independent raw-only audit; does not import or invoke the broker."""
import hashlib
import json
from pathlib import Path

ROOT = Path("/evidence/formal")
cases = ["exit0", "exit23", "timeout", "unavailable", "malformed", "one-shot-idle", "two-queued"]
errors = []
rows = []
for name in cases:
    folder = ROOT / name
    process = json.loads((folder / "process.json").read_text())
    request_files = sorted(folder.glob("*.request.json"))
    broker_files = sorted(folder.glob("*.broker.json"))
    response_files = sorted(folder.glob("*.response.jsonl"))
    fake_files = sorted(folder.glob("invocation-*.json"))
    if name == "one-shot-idle":
        if not process["killed_by_harness"] or broker_files or response_files or fake_files:
            errors.append(f"{name}: idle bounds mismatch")
    elif name == "malformed":
        if process["killed_by_harness"] or process["returncode"] != 1:
            errors.append("malformed request process outcome mismatch")
        if len(request_files) != 1 or request_files[0].name != "malformed.request.json":
            errors.append("malformed request bytes missing")
        if broker_files or response_files:
            errors.append("malformed request emitted broker outputs")
    elif name == "two-queued":
        if len(request_files) != 2 or len(broker_files) != 1 or len(response_files) != 1 or len(fake_files) != 1:
            errors.append("one-shot cardinality not exactly one")
        elif json.loads(broker_files[0].read_text())["request_id"] != "queued-a":
            errors.append("sorted first request did not own the sole receipt")
        elif response_files[0].name != "queued-a.response.jsonl" or process["returncode"] != 1:
            errors.append("one-shot response/process result mismatch")
    else:
        if len(request_files) != 1 or len(broker_files) != 1 or len(response_files) != 1:
            errors.append(f"{name}: missing/duplicate broker response")
        else:
            receipt = json.loads(broker_files[0].read_text())
            expected_id = name
            if receipt.get("request_id") != expected_id:
                errors.append(f"{name}: receipt ID mismatch")
            if broker_files[0].name != f"{expected_id}.broker.json" or response_files[0].name != f"{expected_id}.response.jsonl":
                errors.append(f"{name}: response/receipt filenames do not match request ID")
            if name in ("exit0", "exit23", "timeout", "unavailable"):
                if not fake_files and name not in ("unavailable",):
                    errors.append(f"{name}: fake invocation missing")
            if name == "exit0" and process["returncode"] != 1:
                errors.append("zero-exit hypothesis not reproduced")
            if name == "exit0" and receipt.get("returncode") != 0:
                errors.append("successful fake exit missing from receipt")
            if name == "exit0" and response_files[0].read_text() != '{"ok":true}':
                errors.append("successful fake response bytes mismatch")
            if name == "exit0" and (not fake_files or json.loads(fake_files[0].read_text())["stdin"] != "fake\n"):
                errors.append("successful fake argv/stdin record mismatch")
            if name == "exit23" and (receipt.get("returncode") != 23 or process["returncode"] != 23):
                errors.append("nonzero code mismatch")
            if name == "timeout" and (receipt.get("returncode") is not None or process["returncode"] != 1):
                errors.append("timeout process outcome mismatch")
            if name == "timeout" and receipt.get("stop_reason") != "HOST_BROKER_SUBPROCESS_TIMEOUT":
                errors.append("timeout was not typed")
            if name == "unavailable" and (receipt.get("returncode") is not None or process["returncode"] != 1):
                errors.append("unavailable process outcome mismatch")
            if name == "unavailable" and receipt.get("stop_reason") != "HOST_BROKER_EXECUTABLE_UNAVAILABLE":
                errors.append("unavailable executable was not typed")
            rows.append({"case": name, "broker_rc": process["returncode"], "receipt": receipt})
hashes = {}
for path in sorted(ROOT.rglob("*")):
    if path.is_file() and path.name != "AUDIT.json":
        hashes[str(path.relative_to(ROOT))] = hashlib.sha256(path.read_bytes()).hexdigest()
report = {"decision": "FAIL_ZERO_EXIT_PROPAGATION" if not errors else "HOLD_AUDIT_ERRORS",
          "errors": errors, "cases": rows, "sha256": hashes}
(ROOT / "AUDIT.json").write_text(json.dumps(report, sort_keys=True, indent=2)+"\n")
print(f"INDEPENDENT_AUDIT decision={report['decision']} errors={len(errors)} files_hashed={len(hashes)}")
if errors: raise SystemExit(2)
