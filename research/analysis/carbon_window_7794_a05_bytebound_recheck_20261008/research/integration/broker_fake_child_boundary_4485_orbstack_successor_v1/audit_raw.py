import copy
import hashlib
import json
from pathlib import Path
import sys


EXPECTED = ("exit_0", "exit_23", "timeout", "unavailable", "malformed", "idle", "queued")


def check(payload):
    errors = []
    rows = payload.get("rows") if isinstance(payload, dict) else None
    if payload.get("schema") != "broker-fake-child-result-v1" or not isinstance(rows, list):
        return ["schema"]
    if tuple(payload.get("case_ids", ())) != EXPECTED:
        errors.append("case_ids")
    if tuple(row.get("case_id") for row in rows) != EXPECTED:
        errors.append("row_order_or_count")
        return errors
    by_id = {row["case_id"]: row for row in rows}
    for name in ("exit_0", "exit_23"):
        row = by_id[name]
        code = 0 if name == "exit_0" else 23
        rid = "exit-0" if code == 0 else "exit-23"
        receipt = row.get("receipts", {}).get(rid)
        if row.get("broker_status") != code or not receipt or receipt.get("returncode") != code:
            errors.append(name + ":exit")
        if row.get("responses", {}).get(rid) != "fake-response\n":
            errors.append(name + ":response")
        if row.get("fake_invocation_count") != 1 or row.get("fake_invocation_log") != ["invoked"]:
            errors.append(name + ":child_call")
    timeout = by_id["timeout"]
    tr = timeout.get("receipts", {}).get("timeout", {})
    if (timeout.get("broker_status") != 1 or tr.get("returncode", "missing") is not None
            or tr.get("stop_reason") != "HOST_BROKER_SUBPROCESS_TIMEOUT"
            or timeout.get("responses", {}).get("timeout") != ""
            or timeout.get("fake_invocation_count") != 1):
        errors.append("timeout")
    unavailable = by_id["unavailable"]
    ur = unavailable.get("receipts", {}).get("unavailable", {})
    if (unavailable.get("broker_status") != 1 or ur.get("error_class") != "FileNotFoundError"
            or ur.get("stop_reason") != "HOST_BROKER_EXECUTABLE_UNAVAILABLE"
            or unavailable.get("responses", {}).get("unavailable") != ""
            or unavailable.get("fake_invocation_count") != 0):
        errors.append("unavailable")
    malformed = by_id["malformed"]
    mr = malformed.get("receipts", {}).get("malformed", {})
    if (malformed.get("broker_status") != 1 or mr.get("error_class") != "InvalidInstructions"
            or mr.get("stop_reason") != "HOST_MODEL_INSTRUCTIONS_REJECTED"
            or malformed.get("responses", {}).get("malformed") != ""
            or malformed.get("fake_invocation_count") != 0):
        errors.append("malformed")
    idle = by_id["idle"]
    if (idle.get("broker_status") is not None or idle.get("externally_timed_out") is not True
            or idle.get("receipts") != {} or idle.get("responses") != {}
            or idle.get("ipc_files") != [] or idle.get("fake_invocation_count") != 0):
        errors.append("idle")
    queued = by_id["queued"]
    if (queued.get("broker_status") != 0 or set(queued.get("receipts", {})) != {"a-first"}
            or set(queued.get("responses", {})) != {"a-first"}
            or queued.get("fake_invocation_count") != 1
            or queued["receipts"]["a-first"].get("returncode") != 0
            or not any(name == "z-last.request.json" for name in queued.get("ipc_files", []))):
        errors.append("queued")
    for row in rows:
        for receipt in row.get("receipts", {}).values():
            if receipt.get("authority_granted") is not False:
                errors.append(row["case_id"] + ":authority")
    return errors


def mutations(payload):
    variants = []
    x = copy.deepcopy(payload); x["rows"].pop(); variants.append(("missing_row", x))
    x = copy.deepcopy(payload); x["rows"][0]["broker_status"] = 9; variants.append(("exit_status", x))
    x = copy.deepcopy(payload); x["rows"][1]["receipts"]["exit-23"]["returncode"] = 0; variants.append(("receipt_code", x))
    x = copy.deepcopy(payload); x["rows"][0]["receipts"]["exit-0"]["authority_granted"] = True; variants.append(("authority", x))
    x = copy.deepcopy(payload); x["rows"][0]["responses"]["exit-0"] = "forged"; variants.append(("response", x))
    x = copy.deepcopy(payload); x["rows"][0]["fake_invocation_count"] = 0; variants.append(("child_call", x))
    x = copy.deepcopy(payload); x["rows"][5]["ipc_files"] = ["idle.broker.json"]; variants.append(("idle_artifact", x))
    x = copy.deepcopy(payload); x["rows"][6]["receipts"]["z-last"] = {"returncode": 0}; variants.append(("queued_duplicate", x))
    return variants


def main(result_path, freeze_path):
    root = Path(result_path).parent
    payload = json.loads(Path(result_path).read_text(encoding="utf-8"))
    errors = check(payload)
    for row in payload.get("rows", []):
        case_root = root / "cases" / row.get("case_id", "__invalid__")
        saved = json.loads((case_root / "RESULT.json").read_text(encoding="utf-8"))
        if saved != row:
            errors.append("case_result_copy:" + row["case_id"])
        ipc = case_root / "ipc"
        actual_ipc = sorted(p.name for p in ipc.iterdir())
        if actual_ipc != row.get("ipc_files"):
            errors.append("ipc_paths:" + row["case_id"])
        requests = sorted(ipc.glob("*.request.json"))
        actual_hashes = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in requests}
        if actual_hashes != row.get("request_sha256"):
            errors.append("request_hashes:" + row["case_id"])
        actual_receipts = {p.name.removesuffix(".broker.json"): json.loads(p.read_text())
                           for p in sorted(ipc.glob("*.broker.json"))}
        actual_responses = {p.name.removesuffix(".response.jsonl"): p.read_text(encoding="utf-8")
                            for p in sorted(ipc.glob("*.response.jsonl"))}
        if actual_receipts != row.get("receipts") or actual_responses != row.get("responses"):
            errors.append("ipc_content:" + row["case_id"])
    environment = json.loads((root / "ENVIRONMENT.json").read_text(encoding="utf-8"))
    freeze = json.loads(Path(freeze_path).read_text(encoding="utf-8"))
    if environment.get("broker_sha256") != freeze.get("broker_sha256"):
        errors.append("broker_source_hash")
    if environment.get("machine") not in ("aarch64", "arm64"):
        errors.append("architecture")
    if not environment.get("python", "").startswith("3.12.14 "):
        errors.append("python_version")
    manifest = json.loads((root / "FILE_MANIFEST.json").read_text(encoding="utf-8"))
    entries = manifest.get("files", {})
    actual_paths = sorted(str(p.relative_to(root)) for p in root.rglob("*") if p.is_file() and p.name != "FILE_MANIFEST.json")
    if sorted(entries) != actual_paths:
        errors.append("manifest_paths")
    for rel, meta in entries.items():
        data = (root / rel).read_bytes()
        if hashlib.sha256(data).hexdigest() != meta.get("sha256") or len(data) != meta.get("bytes"):
            errors.append("manifest_hash:" + rel)
    controls = {name: bool(check(mutant)) for name, mutant in mutations(payload)}
    if len(controls) != 8 or not all(controls.values()):
        errors.append("corruption_controls")
    result = {
        "status": "PASS_BROKER_EXIT_CONTRACT_SCOPED" if not errors else "FAIL_AUDIT",
        "rows": len(payload.get("rows", [])),
        "errors": errors,
        "corruption_controls_rejected": sum(controls.values()),
        "corruption_controls": controls,
    }
    print(json.dumps(result, sort_keys=True))
    return 0 if not errors else 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1], sys.argv[2]))
