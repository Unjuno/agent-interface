"""Raw-only independent auditor. Does not import or invoke the broker/fake."""
import hashlib
import json
from pathlib import Path

ROOT = Path("/evidence/formal")
STUDY = Path("/study")
REPO = Path("/repo")
FREEZE = json.loads((STUDY / "FREEZE.json").read_text())
contract_errors = []
provenance_errors = []
rows = []
zero_exit_mismatch = False
for key, path in (("broker_sha256", REPO / "runtime/host_model_ipc_broker_v1.py"),
                  ("existing_test_sha256", REPO / "runtime/test_host_model_ipc_broker_v1.py")):
    if hashlib.sha256(path.read_bytes()).hexdigest() != FREEZE["source"][key]:
        provenance_errors.append(f"source hash mismatch: {path.name}")
if hashlib.sha256((STUDY / "fake_codex.py").read_bytes()).hexdigest() != FREEZE["fake_sha256"]:
    provenance_errors.append("fake executable hash mismatch")

for name in FREEZE["formal_matrix"]:
    folder = ROOT / name
    try:
        process = json.loads((folder / "process.json").read_text())
    except Exception as exc:
        provenance_errors.append(f"{name}: process record missing/invalid: {type(exc).__name__}")
        continue
    requests = sorted(folder.glob("*.request.json"))
    responses = sorted(folder.glob("*.response.jsonl"))
    receipts = sorted(folder.glob("*.broker.json"))
    invocations = sorted(folder.glob("invocation-*.json"))
    receipt = json.loads(receipts[0].read_text()) if len(receipts) == 1 else None
    request_ids = [json.loads(p.read_text())["request_id"] for p in requests]

    if name == "one-shot-idle":
        if process["returncode"] != -9 or not process["killed_by_harness"]:
            contract_errors.append("one-shot-idle: broker did not remain idle to external bound")
        if requests or responses or receipts or invocations:
            provenance_errors.append("one-shot-idle: unexpected request/response/receipt/fake evidence")
    elif name == "malformed":
        if len(requests) != 1 or request_ids != ["malformed"]:
            provenance_errors.append("malformed: exact raw request missing")
        if process["returncode"] != 1 or process["killed_by_harness"]:
            contract_errors.append("malformed: expected fail-closed process exit 1")
        if responses or receipts or invocations:
            contract_errors.append("malformed: unexpected response/receipt/fake invocation")
        if "KeyError" not in process["stderr"]:
            provenance_errors.append("malformed: exception record absent")
    elif name == "two-queued":
        if request_ids != ["queued-a", "queued-b"]:
            provenance_errors.append("two-queued: expected exact pair of retained requests")
        if len(receipts) != 1 or len(responses) != 1 or len(invocations) != 1 or receipt is None:
            provenance_errors.append("two-queued: expected exactly one receipt/response/fake invocation")
        else:
            if receipt.get("request_id") != "queued-a" or receipts[0].name != "queued-a.broker.json":
                contract_errors.append("two-queued: wrong first request selected")
            if responses[0].name != "queued-a.response.jsonl" or process["returncode"] != 1:
                contract_errors.append("two-queued: response or one-shot process result mismatch")
            invocation = json.loads(invocations[0].read_text())
            if invocation.get("configured_exit") != 0 or invocation.get("stdin") != "fake\n":
                provenance_errors.append("two-queued: fake invocation record mismatch")
    else:
        if len(requests) != 1 or request_ids != [name]:
            provenance_errors.append(f"{name}: exact raw request missing")
        if len(receipts) != 1 or len(responses) != 1 or receipt is None:
            provenance_errors.append(f"{name}: expected one receipt and response")
            rows.append({"case": name, "broker_exit": process["returncode"], "request_ids": request_ids})
            continue
        if receipt.get("request_id") != name or receipts[0].name != f"{name}.broker.json" or responses[0].name != f"{name}.response.jsonl":
            provenance_errors.append(f"{name}: request/response/receipt IDs do not reconcile")
        if receipt.get("boundary") != "host-local-codex-exe" or receipt.get("authority_granted") is not False:
            provenance_errors.append(f"{name}: broker authority/boundary metadata mismatch")

        if name == "exit0":
            if receipt.get("returncode") != 0:
                contract_errors.append("exit0: successful fake returncode missing from receipt")
            if process["returncode"] != receipt.get("returncode"):
                zero_exit_mismatch = True
            if responses[0].read_bytes() != b'{"ok":true}':
                provenance_errors.append("exit0: fake response bytes mismatch")
            if len(invocations) != 1:
                provenance_errors.append("exit0: expected exactly one fake invocation")
            else:
                invocation = json.loads(invocations[0].read_text())
                if invocation.get("configured_exit") != 0 or invocation.get("stdin") != "fake\n":
                    provenance_errors.append("exit0: argv/stdin/exit fake record mismatch")
        elif name == "exit23":
            if receipt.get("returncode") != 23 or process["returncode"] != 23:
                contract_errors.append("exit23: exact nonzero propagation mismatch")
            if len(invocations) != 1 or json.loads(invocations[0].read_text()).get("configured_exit") != 23:
                provenance_errors.append("exit23: expected one recorded fake exit-23 invocation")
        elif name == "timeout":
            if receipt.get("returncode") is not None or receipt.get("stop_reason") != "HOST_BROKER_SUBPROCESS_TIMEOUT" or process["returncode"] != 1:
                contract_errors.append("timeout: typed non-success outcome mismatch")
            if len(invocations) != 1 or json.loads(invocations[0].read_text()).get("sleep_s") != 0.3:
                provenance_errors.append("timeout: expected recorded sleeping fake invocation")
        elif name == "unavailable":
            if receipt.get("returncode") is not None or receipt.get("stop_reason") != "HOST_BROKER_EXECUTABLE_UNAVAILABLE" or process["returncode"] != 1:
                contract_errors.append("unavailable: typed non-success outcome mismatch")
            if invocations:
                provenance_errors.append("unavailable: intentional missing executable unexpectedly ran fake")
        rows.append({"case": name, "broker_exit": process["returncode"], "receipt": receipt,
                     "response_sha256": hashlib.sha256(responses[0].read_bytes()).hexdigest()})

hashes = {}
for path in sorted(ROOT.rglob("*")):
    if path.is_file() and path.name != "AUDIT.json":
        hashes[str(path.relative_to(ROOT))] = hashlib.sha256(path.read_bytes()).hexdigest()

if provenance_errors:
    decision = "STOP_AUDIT_PROVENANCE"
elif contract_errors:
    decision = "FAIL_BROKER_EXIT_CONTRACT"
elif zero_exit_mismatch:
    decision = "FAIL_ZERO_EXIT_PROPAGATION"
else:
    decision = "PASS_BROKER_EXIT_CONTRACT"

report = {"allocation": FREEZE["allocation"], "decision": decision,
          "provenance_errors": provenance_errors, "contract_errors": contract_errors,
          "rows": rows, "files_hashed": len(hashes), "sha256": hashes}
(ROOT / "AUDIT.json").write_text(json.dumps(report, sort_keys=True, indent=2) + "\n")
print(f"INDEPENDENT_AUDIT allocation={FREEZE['allocation']} decision={decision} provenance_errors={len(provenance_errors)} contract_errors={len(contract_errors)} files_hashed={len(hashes)}")
if provenance_errors or contract_errors:
    raise SystemExit(2)
