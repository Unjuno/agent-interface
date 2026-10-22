import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
freeze = json.loads((ROOT / "FREEZE.json").read_text(encoding="utf-8"))
source_manifest = json.loads((ROOT / "source_hashes.json").read_text(encoding="utf-8"))
stdout = (ROOT / "results/wslc.stdout.txt").read_text(encoding="utf-8-sig")
exit_code = int((ROOT / "results/exit.txt").read_text(encoding="utf-8").strip())
receipt = json.loads((ROOT / "results/result.json").read_text(encoding="utf-8"))

source_checks = []
for name, expected in freeze["sources"].items():
    data = (ROOT / name).read_bytes()
    oid = hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()
    source_checks.append({
        "source": name,
        "git_blob_matches": oid == expected["git_blob"] == source_manifest[name]["git_blob"],
        "sha256_matches": hashlib.sha256(data).hexdigest() == expected["sha256"] == source_manifest[name]["sha256"],
        "bytes_match": len(data) == expected["bytes"] == source_manifest[name]["bytes"],
    })

test_ok = hashlib.sha256((ROOT / "test_a10_cancel_composition.py").read_bytes()).hexdigest() == freeze["test_sha256"]
container_ok = hashlib.sha256((ROOT / "Containerfile").read_bytes()).hexdigest() == freeze["containerfile_sha256"]
match = re.search(r"A10_RESULT=(\{[^\r\n]+\})", stdout)
raw_receipt = json.loads(match.group(1)) if match else None
transcript_ok = (exit_code == 0 and "Ran 1 test in " in stdout and
                 "OK" in stdout.splitlines()[-1] and raw_receipt == receipt)
assertions_ok = (
    receipt["invalidation"] == "health:below_hard_minimum" and
    receipt["timeline"] == ["executor_cancel_write", "executor_flush",
                            "planner_interrupt_request", "planner_interrupt_ack"] and
    receipt["planner_result"] == {"status": "completed", "cancellation_requested": True,
                                  "answer_eligible": False, "answer": None} and
    receipt["terminal_release"] == {"verified": True, "keys_down": [], "buttons_down": []})
all_sources_ok = all(all(row[k] for k in ("git_blob_matches", "sha256_matches", "bytes_match"))
                     for row in source_checks)
passed = (all_sources_ok and test_ok and container_ok and transcript_ok and assertions_ok)
result = {
    "audit_status": "PASS_SCOPED" if passed else "HOLD_AUDIT_MISMATCH",
    "audit_method": "Non-executing source identity, WSLc transcript, and structured receipt audit; test not rerun.",
    "main_commit": freeze["main_commit"],
    "source_checks": source_checks,
    "test_hash_matches": test_ok,
    "containerfile_hash_matches": container_ok,
    "transcript_exit_zero_and_receipt_matches": transcript_ok,
    "composition_order_and_terminal_assertions_match": assertions_ok,
    "receipt_classification": receipt["classification"],
    "limits": ["fake planner client", "fake executor", "synthetic typed observations and release receipt",
               "no physical key release or live-game outcome"]
}
(ROOT / "results/audit.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps(result, indent=2, sort_keys=True))
raise SystemExit(0 if passed else 1)
