"""Independent raw-only gate scorer; does not import the formal runner or broker."""
import hashlib
import json
from pathlib import Path

ROOT = Path("/evidence")
rows = [json.loads(line) for line in (ROOT / "raw.jsonl").read_text(encoding="utf-8").splitlines()]
by_name = {row["case"]: row for row in rows}
errors = []
checks = {}

def check(name, condition):
    checks[name] = bool(condition)
    if not condition:
        errors.append(name)

check("exactly_seven_cases", len(rows) == 7 and len(by_name) == 7)
pre = json.loads((ROOT / "preflight.json").read_text(encoding="utf-8"))
check("preflight_pass", pre.get("result") == "PASS_PREFLIGHT")
check("fake_hash_matches_recorded", len(pre.get("fake_sha256", "")) == 64)
zero = by_name["exit_zero"]
zero_receipt = zero.get("receipts", {}).get("exit_zero.broker.json", {})
check("zero_receipt_is_zero", zero_receipt.get("returncode") == 0)
check("zero_process_exit_propagated", zero.get("process_returncode") == 0)
twenty_three = by_name["exit_23"]
rc23 = twenty_three.get("receipts", {}).get("exit_23.broker.json", {}).get("returncode")
check("exit_23_propagated", rc23 == 23 and twenty_three.get("process_returncode") == 23)
timeout_receipt = by_name["timeout"].get("receipts", {}).get("timeout.broker.json", {})
check("timeout_typed_non_success", timeout_receipt.get("stop_reason") == "HOST_BROKER_SUBPROCESS_TIMEOUT"
      and by_name["timeout"].get("process_returncode") not in (None, 0))
unavailable_receipt = by_name["unavailable"].get("receipts", {}).get("unavailable.broker.json", {})
check("unavailable_typed_non_success", unavailable_receipt.get("stop_reason") == "HOST_BROKER_EXECUTABLE_UNAVAILABLE"
      and by_name["unavailable"].get("process_returncode") not in (None, 0))
malformed = by_name["malformed_request"]
check("malformed_fails_closed", malformed.get("process_returncode") not in (None, 0)
      and not malformed.get("receipts") and not malformed.get("invocations"))
idle = by_name["idle_once"]
check("idle_externally_bounded", idle.get("external_timeout") is True and not idle.get("receipts"))
queued = by_name["two_queued"]
check("one_shot_processes_first_only", set(queued.get("receipts", {})) == {"a-first.broker.json"}
      and set(queued.get("responses", {})) == {"a-first.response.jsonl"}
      and len(queued.get("invocations", [])) == 1)
result = "PASS_BROKER_EXIT_CONTRACT" if not errors else ("FAIL_ZERO_EXIT_PROPAGATION" if "zero_process_exit_propagated" in errors else "FAIL_BROKER_EXIT_CONTRACT")
report = {"result": result, "rows": len(rows), "checks": checks, "errors": errors,
          "raw_sha256": hashlib.sha256((ROOT / "raw.jsonl").read_bytes()).hexdigest()}
(ROOT / "AUDIT.json").write_text(json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf-8")
print(json.dumps(report, sort_keys=True))
