"""Audit A04's retained post-run failure without rerunning the candidate."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent

def _sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))

def _frozen_source_matches(expected: str, working: bytes, committed: bytes) -> bool:
    # Git normalizes text while the frozen SHA identifies the exact Windows
    # worktree bytes used by the candidate. Prefer that exact retained checkout;
    # for post-run-edited docs, also accept the immutable committed blob.
    if _sha_bytes(working) == expected or _sha_bytes(committed) == expected:
        return True
    variants = {committed, committed.replace(b"\r\n", b"\n"), committed.replace(b"\n", b"\r\n")}
    return any(_sha_bytes(variant) == expected for variant in variants)

def _repo_root() -> Path:
    result = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=ROOT,
                            check=True, capture_output=True, text=True)
    return Path(result.stdout.strip())

def _committed_file(repo: Path, commit: str, relative: str) -> bytes:
    path = (ROOT / relative).relative_to(repo).as_posix()
    return subprocess.run(["git", "show", f"{commit}:{path}"], cwd=repo,
                          check=True, capture_output=True).stdout

def classify_candidate(exit_code: int, stdout_size: int, stderr: str, fetch_head: str) -> str:
    cleanup_error = "PermissionError" in stderr and "WinError 32" in stderr and "FETCH_HEAD" in stderr
    plugin_fetch = "https://github.com/openai/plugins" in fetch_head
    if exit_code != 0 and stdout_size == 0 and cleanup_error and plugin_fetch:
        return "PARTIAL_OR_UNVERIFIABLE"
    return "UNVERIFIABLE"

def audit() -> dict:
    frozen = _load(ROOT / "FROZEN.json")
    command = _load(ROOT / "results" / "candidate.command.json")
    started = _load(ROOT / "results" / "candidate.started.json")
    repo = _repo_root()
    source_commit = command["source_checkout_head"]
    errors = []
    source_errors = []
    committed_freeze = _committed_file(repo, source_commit, "FROZEN.json")
    if _sha_bytes(committed_freeze) != _sha_bytes((ROOT / "FROZEN.json").read_bytes()):
        source_errors.append("working FROZEN.json differs from the candidate source commit")
    for relative, expected in frozen["source_sha256"].items():
        try:
            committed = _committed_file(repo, source_commit, relative)
            working = (ROOT / relative).read_bytes()
        except (subprocess.CalledProcessError, OSError):
            source_errors.append(f"frozen source missing from candidate checkout: {relative}")
            continue
        if not _frozen_source_matches(expected, working, committed):
            source_errors.append(f"frozen source hash mismatch at candidate checkout: {relative}")
    if source_errors:
        errors.extend(source_errors)

    stdout_path = ROOT / "results" / "candidate.stdout.json"
    stderr_path = ROOT / "results" / "candidate.stderr.txt"
    exit_code = int((ROOT / "results" / "candidate.exit").read_text(encoding="utf-8").strip())
    stdout_size = stdout_path.stat().st_size
    stderr = stderr_path.read_text(encoding="utf-8", errors="replace")
    fetch_head = (ROOT / "results" / "candidate.plugin-fetch-head.txt").read_text(encoding="utf-8")
    hashes = _load(ROOT / "results" / "postrun-artifact-hashes.json")
    rollout = _load(ROOT / "results" / "candidate.rollout-summary.json")
    temp_state = _load(ROOT / "results" / "candidate-temp-state.json")
    candidate_class = classify_candidate(exit_code, stdout_size, stderr, fetch_head)
    checks = {
        "one_shot_identity_and_exit_match": (command.get("run_id") == started.get("run_id")
            and command.get("candidate_runs") == started.get("candidate_runs") == 1
            and command.get("retries") == started.get("retries") == 0
            and exit_code == started.get("exit_code") == 1),
        "raw_candidate_stdout_empty": stdout_size == 0,
        "teardown_lock_error_retained": ("PermissionError" in stderr and "WinError 32" in stderr
            and ".git" in stderr and "FETCH_HEAD" in stderr),
        "external_plugin_fetch_retained": ("https://github.com/openai/plugins" in fetch_head
            and hashes["observed_plugin_FETCH_HEAD"]["sha256"] == _sha_bytes((ROOT / "results" / "candidate.plugin-fetch-head.txt").read_bytes())),
        "supplemental_rollout_hash_matches_metadata": (rollout["raw_log_sha256"] == hashes["candidate_codex_rollout"]["sha256"]
            and rollout["raw_log_bytes"] == hashes["candidate_codex_rollout"]["bytes"]),
        "supplemental_rollout_scope_limited": (rollout["raw_http_responses_request_bodies_retained"] is False
            and rollout["raw_app_server_rpc_replies_retained"] is False
            and rollout["raw_turn_completed_protocol_notification_retained"] is False
            and rollout["same_logged_turn_id_for_observation_items"] is True),
        "temporary_process_and_lock_check_recorded": (temp_state["matching_active_process_count"] == 0
            and temp_state["fetch_head_exclusive_read_open_succeeded"] is True
            and temp_state["temp_root_retained"] is True),
    }
    if not checks["one_shot_identity_and_exit_match"]:
        errors.append("candidate run identity or exit receipt mismatch")
    if not checks["raw_candidate_stdout_empty"]:
        errors.append("expected the documented empty candidate stdout")
    if not checks["teardown_lock_error_retained"]:
        errors.append("teardown failure signature is incomplete")
    if not checks["external_plugin_fetch_retained"]:
        errors.append("external plugin fetch evidence is incomplete")
    if source_errors:
        verdict = "FAIL_A04_AUDIT"
    elif candidate_class != "PARTIAL_OR_UNVERIFIABLE" or not all(checks.values()):
        verdict = "FAIL_A04_AUDIT"
        errors.append("post-run evidence does not support the partial/unverifiable disposition")
    else:
        verdict = "FAIL_A04_CANDIDATE_PARTIAL_RAW_AND_ISOLATION_DEVIATION"
    return {
        "audit_verdict": verdict,
        "delivery_class": candidate_class,
        "candidate_exit": exit_code,
        "candidate_stdout_bytes": stdout_size,
        "frozen_base_commit": frozen["base_commit"],
        "candidate_source_commit": source_commit,
        "one_candidate_run": True,
        "retry_count": 0,
        "external_network_contact": {"host":"github.com","path":"/openai/plugins",
            "commit":"5fd93af4cd0c623e020d0cc7e9ce178b4ac1f70f",
            "separate_from_loopback_responses_mock": True},
        "supplemental_rollout": {"local_only": True, "sha256": rollout["raw_log_sha256"],
            "bytes": rollout["raw_log_bytes"],
            "same_turn_observation_items": rollout["same_logged_turn_id_for_observation_items"],
            "does_not_classify_http_coalescing": True},
        "checks": checks,
        "integrity_errors": errors,
        "scope": "failure audit only; no HTTP delivery classification, model inference, or computer-control effect",
    }

def main() -> int:
    result = audit()
    path = ROOT / "results" / "POSTRUN_AUDIT_FINAL.json"
    path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["audit_verdict"] == "FAIL_A04_CANDIDATE_PARTIAL_RAW_AND_ISOLATION_DEVIATION" else 1

if __name__ == "__main__":
    raise SystemExit(main())
