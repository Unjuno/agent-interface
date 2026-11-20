"""Write the one-shot A02 source and decision freeze before invocation."""
import hashlib
import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parent
TARGET_COMMIT = "719ef679c977a925db3a6d1fe15f9cd93cf2b42c"
EXPERIMENT_ID = "v39-application-consumption-audit-integrity-7662-a02-20261005"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def blob(path):
    spec = f"{TARGET_COMMIT}:research/doom/v39_application_consumption_conflict_59_a01_20261005/{path}"
    return subprocess.check_output(["git", "rev-parse", spec], cwd=ROOT.parents[2], text=True).strip()


def main():
    frozen_files = sorted(path for path in (ROOT / "frozen").rglob("*") if path.is_file())
    frozen_hashes = {path.relative_to(ROOT / "frozen").as_posix(): sha(path) for path in frozen_files}
    source_hashes = {
        "experiment.py": sha(ROOT / "experiment.py"),
        "independent_audit_v2.py": sha(ROOT / "independent_audit_v2.py"),
        "test_independent_audit_v2.py": sha(ROOT / "test_independent_audit_v2.py"),
        "make_freeze.py": sha(ROOT / "make_freeze.py"),
    }
    main_ref = subprocess.check_output(["git", "ls-remote", "origin", "refs/heads/main"], cwd=ROOT.parents[2], text=True).split()[0]
    freeze = {
        "schema": "v39-saved-result-audit-integrity-freeze-v1",
        "experiment_id": EXPERIMENT_ID,
        "issue": 59,
        "reviewed_pull_request": 7662,
        "current_main_observed_at_freeze": main_ref,
        "audited_source_commit": TARGET_COMMIT,
        "audited_source_branch": "fix/59-v39-app-consumption-contradiction-20261005",
        "question": "Does the saved-result auditor independently verify interval order from the down/up intervals, or can its declared expected_ordered labels be changed in a count-preserving swap without detection?",
        "H": "The saved-result auditor may accept a changed chronology classification if expected_ordered is treated as its own oracle and one true/false pair is swapped while preserving the 15/85 totals.",
        "T": "Run the exact frozen audit_a01.py once on the unchanged saved A01 raw and once on a copy where sweep rows 4 and 15 have their expected_ordered labels swapped, statuses and interval outputs updated consistently to those labels in both baseline and candidate sweeps. Independently derive chronology only from down[1] < up[0].",
        "D": "Reproduce only if the original auditor passes both arms while independent chronology finds exactly four expected_ordered mismatches (two rows for each of two implementations). Otherwise record HOLD/NOT_REPRODUCED.",
        "C": "Synthetic saved-JSON mutation; no candidate, game, model, GUI, input, X server, GPU, container, WSLc, or allocation invocation.",
        "U": ["One count-preserving label swap tests this specific oracle-independence gap only.", "No physical key timing, app consumption, useful feedback, recovery, or gameplay conclusion follows."],
        "mutation": {"ordered_index": 4, "unordered_index": 15, "implementations": ["baseline", "candidate"], "fields": ["expected_ordered", "status", "down_edge_interval_ns", "up_edge_interval_ns"], "preserve": ["raw source identities", "application-flag mutation matrix", "candidate false-accept count", "15 paired / 85 incomplete summary counts"]},
        "invocation_rule": "Exactly one frozen-auditor invocation per arm; no retry. Independent audit is a separate posthoc read of saved raw and output.",
        "frozen_sha256": frozen_hashes,
        "frozen_git_blobs": {
            "audit_a01.py": blob("audit_a01.py"),
            "raw/A01.json": blob("raw/A01.json"),
            "FREEZE.json": blob("FREEZE.json"),
            "CANDIDATE_SOURCE.py.txt": blob("CANDIDATE_SOURCE.py.txt"),
        },
        "source_sha256": source_hashes,
        "source_raw_sha256": frozen_hashes["raw/A01.json"],
    }
    (ROOT / "FREEZE.json").write_text(json.dumps(freeze, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"experiment_id": EXPERIMENT_ID, "current_main_observed_at_freeze": main_ref, "audited_source_commit": TARGET_COMMIT, "frozen_files": len(frozen_hashes), "freeze_written": True}, sort_keys=True))


if __name__ == "__main__":
    main()
