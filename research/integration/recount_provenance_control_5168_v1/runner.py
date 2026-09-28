"""One-shot synthetic Git-object/working-tree provenance control."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

ALLOCATION = "recount-provenance-control-5168-20260928-01"
MAIN = "43a8f58c126a8d54cb84f2f4fcd2299b9028b380"
PR_HEAD = "d14bc0abfcab3dc8572d4716c73cf3e460c3a5e2"
CANDIDATE_BLOB = "a0cd1db94c3c4204f7dfd0e3b88a702f1c1e50b1"
EVIDENCE = Path("research/live_control/results/integrated-efficiency-live-01")
V1_FREEZE = Path("research/live_control/integrated_efficiency_live_audit_20260928/FREEZE.json")
ARMS = ("plain", "ephemeral", "persistent")


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def run(args: list[str], *, cwd: Path | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(args, cwd=cwd, text=True, capture_output=True, check=True)


def expected_paths() -> list[str]:
    paths = [V1_FREEZE.as_posix()]
    paths.extend((EVIDENCE / name).as_posix() for name in
                 ("preregistration.json", "trace.json", "report.json", "audit.json"))
    result_count = {"plain": 5, "ephemeral": 5, "persistent": 4}
    for arm in ARMS:
        paths.extend([
            (EVIDENCE / "preflight" / arm / "gate" / "gate-report.json").as_posix(),
            (EVIDENCE / "arms" / arm / "task-details.json").as_posix(),
            (EVIDENCE / "arms" / arm / "runtime" / "submission-history.jsonl").as_posix(),
        ])
        paths.extend((EVIDENCE / "model-calls" / arm / f"task-{i}" / "anchor" / "result.json").as_posix()
                     for i in range(1, result_count[arm] + 1))
    return sorted(paths)


def main(output: Path) -> int:
    package = Path(__file__).resolve().parent
    freeze = json.loads((package / "FREEZE.json").read_text(encoding="utf-8"))
    candidate = package / "freeze_inputs_candidate.py"
    if freeze["allocation"] != ALLOCATION or freeze["source_main"] != MAIN:
        raise RuntimeError("freeze identity mismatch")
    if freeze["candidate_pr_head"] != PR_HEAD or freeze["candidate_freeze_inputs_blob"] != CANDIDATE_BLOB:
        raise RuntimeError("candidate provenance mismatch")
    if sha(candidate.read_bytes()) != freeze["candidate_copy_sha256"]:
        raise RuntimeError("candidate source hash mismatch")
    for name, key in (("runner.py", "runner_sha256"), ("audit.py", "auditor_sha256"),
                      ("test_contract.py", "contract_test_sha256")):
        if sha((package / name).read_bytes()) != freeze[key]:
            raise RuntimeError("frozen source hash mismatch: " + name)
    if output.exists():
        raise FileExistsError("refusing to overwrite frozen result")
    if len(expected_paths()) != 28 or len(set(expected_paths())) != 28:
        raise RuntimeError("synthetic fixture inventory is not exactly 28 unique paths")

    root = Path(tempfile.mkdtemp(prefix="recount-provenance-control-5168-01-"))
    (root / ".git").exists() and (_ for _ in ()).throw(RuntimeError("unexpected pre-existing Git directory"))
    run(["git", "init", "-q", str(root)])
    run(["git", "-C", str(root), "config", "user.name", "Probe"])
    run(["git", "-C", str(root), "config", "user.email", "probe@example.invalid"])
    for rel in expected_paths():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        if rel.endswith("result.json"):
            index = sum(1 for item in expected_paths() if item.endswith("result.json") and item <= rel)
            payload = {"call_id": f"synthetic-call-{index:02d}", "usage": {"input": index}}
        elif rel.endswith("task-details.json"):
            payload = {"trusted": True, "arm": rel.split("/")[5]}
        elif rel.endswith(".json"):
            payload = {"synthetic": True, "path": rel}
        else:
            payload = {"synthetic": True, "path": rel}
        path.write_text(json.dumps(payload, sort_keys=True) + "\n", encoding="utf-8")
    run(["git", "-C", str(root), "add", "--all"])
    run(["git", "-C", str(root), "commit", "-qm", "trusted synthetic input snapshot"])
    commit = run(["git", "-C", str(root), "rev-parse", "HEAD"]).stdout.strip()

    target_rel = (EVIDENCE / "arms" / "plain" / "task-details.json").as_posix()
    target = root / target_rel
    trusted_bytes = target.read_bytes()
    pinned_blob = run(["git", "-C", str(root), "rev-parse", f"{commit}:{target_rel}"]).stdout.strip()
    target.write_bytes(trusted_bytes + b"synthetic-working-tree-mutation\n")
    mutated_bytes = target.read_bytes()
    candidate_run = subprocess.run([sys.executable, str(candidate), str(root), commit],
                                   text=True, capture_output=True)
    manifest = json.loads(candidate_run.stdout) if candidate_run.stdout.strip() else None
    entry = next((item for item in manifest["files"] if item["path"] == target_rel), None) if manifest else None
    output.parent.mkdir(parents=True, exist_ok=True)
    pinned_bytes = subprocess.run(["git", "-C", str(root), "cat-file", "blob", pinned_blob],
                                  capture_output=True, check=True).stdout
    raw = {
        "schema": "recount_provenance_control_5168_raw_v1",
        "allocation": ALLOCATION,
        "source_main": MAIN,
        "candidate_pr_head": PR_HEAD,
        "candidate_freeze_inputs_blob": CANDIDATE_BLOB,
        "synthetic_commit": commit,
        "fixture_id": root.name,
        "inventory_count": len(expected_paths()),
        "candidate_exit_code": candidate_run.returncode,
        "candidate_stderr_sha256": sha(candidate_run.stderr.encode()),
        "candidate_manifest": manifest,
        "target_path": target_rel,
        "trusted_bytes_sha256": sha(trusted_bytes),
        "mutated_working_bytes_sha256": sha(mutated_bytes),
        "pinned_git_blob": pinned_blob,
        "pinned_git_bytes_sha256": sha(pinned_bytes),
        "candidate_target_entry": entry,
        "status": "CONFIRM_DEFECT" if candidate_run.returncode == 0 and entry and
                  entry["sha256"] == sha(mutated_bytes) and entry["git_blob"] == pinned_blob and
                  sha(mutated_bytes) != sha(trusted_bytes) else "NOT_REPRODUCED",
        "effects": {"model": 0, "gui": 0, "network": 0, "docker": 0, "historical_inputs": 0},
    }
    output.write_text(json.dumps(raw, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": raw["status"], "candidate_exit_code": candidate_run.returncode,
                      "inventory_count": len(expected_paths()), "target_manifest_emitted": entry is not None,
                      "mutated_sha_matches_pinned_blob": bool(entry and entry["sha256"] == raw["pinned_git_bytes_sha256"]),
                      "synthetic_root_name": root.name}))
    return 0 if raw["status"] == "CONFIRM_DEFECT" else 1


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: runner.py RAW.json")
    raise SystemExit(main(Path(sys.argv[1])))
