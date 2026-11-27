import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
freeze = json.loads((ROOT / "FREEZE.json").read_text(encoding="utf-8"))
observed = json.loads((ROOT / "source_hashes.json").read_text(encoding="utf-8"))
stdout = (ROOT / "results/wslc.stdout.txt").read_text(encoding="utf-8")
exit_code = int((ROOT / "results/exit.txt").read_text(encoding="utf-8").strip())
checks = []
for name, metadata in freeze["sources"].items():
    data = (ROOT / name).read_bytes()
    git_oid = hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()
    checks.append({
        "source": name,
        "git_blob_matches_freeze": git_oid == metadata["git_blob"] == observed[name]["git_blob"],
        "sha256_matches_freeze": hashlib.sha256(data).hexdigest() == metadata["sha256"] == observed[name]["sha256"],
        "byte_count_matches": len(data) == metadata["bytes"] == observed[name]["bytes"],
    })
test = (ROOT / "test_a09_pair_monitor.py").read_bytes()
test_hash_ok = hashlib.sha256(test).hexdigest() == freeze["test_sha256"]
case_names = re.findall(r"^(test_[a-z0-9_]+) \(test_a09_pair_monitor\.[^)]+\) \.\.\. ok$", stdout, re.M)
transcript_ok = (exit_code == 0 and len(case_names) == 4 and
                 "Ran 4 tests in " in stdout and stdout.rstrip().endswith("OK"))
identity_ok = test_hash_ok and all(all(c[k] for k in ("git_blob_matches_freeze",
                                                        "sha256_matches_freeze",
                                                        "byte_count_matches")) for c in checks)
passed = identity_ok and transcript_ok
result = {
    "audit_status": "PASS_SCOPED" if passed else "HOLD_AUDIT_MISMATCH",
    "audit_method": "Non-executing source identity and retained WSLc transcript audit; unittest was not rerun.",
    "main_commit": freeze["main_commit"],
    "source_checks": checks,
    "test_sha256_matches_freeze": test_hash_ok,
    "wslc_transcript_exit_zero": exit_code == 0,
    "passing_case_names": case_names,
    "four_cases_present": len(case_names) == 4,
    "scope": freeze["scope"],
    "limitations": ["synthetic signal values", "AST-extracted controller functions", "no live cancel/release or game-control claim"],
}
(ROOT / "results/audit.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps(result, indent=2, sort_keys=True))
raise SystemExit(0 if passed else 1)
