"""Single-shot, lease-gated launcher. No retry path exists by design."""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

from protocol import (ALLOCATION, IMAGE_ID, SEEDS, canonical, docker_argv,
                      exact_argv_matches, sha256_bytes)

HERE = Path(__file__).resolve().parent
ROOT = HERE
ISSUE = 5085
LEASE_SCHEMA = "needle-docker-owner-lease-v1"
CLEANUP_RESERVE_SECONDS = 20
CLEANUP_TIMEOUT_SECONDS = 8
SELF_STOP_MARGIN_SECONDS = 30
REQUIRED_LEASE_FIELDS = ("allocation", "owner_comment_url", "docker_context",
                         "main_sha", "branch", "expires_at_utc", "lease_id",
                         "slot_start_utc", "slot_end_utc")
LEASE_COMMENT_PATTERN = re.compile(
    r"<!-- needle-docker-owner-lease-v1\n(\{.*?\})\n-->", re.DOTALL)


def stop(reason: str):
    raise SystemExit("STOP_" + reason)


def unique_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate_json_key")
        result[key] = value
    return result


def read_json(path: Path):
    try:
        return json.loads(path.read_bytes(), object_pairs_hook=unique_pairs)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        stop("INVALID_JSON:" + str(exc))


def fetch_owner_comment(owner_comment_url: str) -> dict:
    match = re.fullmatch(
        r"https://github\.com/Unjuno/agent-interface/issues/5085#issuecomment-(\d+)",
        owner_comment_url)
    if not match:
        stop("LEASE_OWNER_COMMENT_URL_INVALID")
    request = urllib.request.Request(
        "https://api.github.com/repos/Unjuno/agent-interface/issues/comments/" + match.group(1),
        headers={"Accept": "application/vnd.github+json", "User-Agent": "agent-interface-research"})
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            record = json.loads(response.read(), object_pairs_hook=unique_pairs)
    except (OSError, urllib.error.URLError, json.JSONDecodeError, ValueError):
        stop("LEASE_OWNER_COMMENT_FETCH_FAILED")
    if not isinstance(record, dict):
        stop("LEASE_OWNER_COMMENT_RECORD_INVALID")
    if type(record.get("id")) is not int or record["id"] != int(match.group(1)):
        stop("LEASE_OWNER_COMMENT_ID_MISMATCH")
    return record


def validate_lease(lease: dict, main_sha: str, branch: str, current_context: str,
                   owner_comment_record: dict | None = None):
    if not isinstance(lease, dict) or lease.get("schema") != LEASE_SCHEMA:
        stop("NO_EXPLICIT_OWNER_LEASE")
    if any(not isinstance(lease.get(key), str) or not lease[key].strip()
           for key in REQUIRED_LEASE_FIELDS):
        stop("LEASE_FIELD_MISSING")
    if (type(lease.get("issue")) is not int or lease["issue"] != ISSUE
            or lease["allocation"] != ALLOCATION
            or lease["main_sha"] != main_sha or lease["branch"] != branch
            or lease["docker_context"] != current_context):
        stop("LEASE_SCOPE_MISMATCH")
    if not re.fullmatch(r"[0-9a-f]{40}", lease["main_sha"]):
        stop("LEASE_MAIN_SHA_INVALID")
    if lease["lease_id"] in ("none", "unknown", "pending"):
        stop("LEASE_ID_INVALID")
    try:
        expiry = datetime.fromisoformat(lease["expires_at_utc"].replace("Z", "+00:00"))
        slot_start = datetime.fromisoformat(lease["slot_start_utc"].replace("Z", "+00:00"))
        slot_end = datetime.fromisoformat(lease["slot_end_utc"].replace("Z", "+00:00"))
    except ValueError:
        stop("LEASE_EXPIRY_INVALID")
    now = datetime.now(timezone.utc)
    if any(value.tzinfo is None for value in (expiry, slot_start, slot_end)):
        stop("LEASE_TIME_UNZONED")
    if not (slot_start <= now < slot_end and now < expiry <= slot_end):
        stop("LEASE_SLOT_NOT_ACTIVE")
    comment = owner_comment_record or fetch_owner_comment(lease["owner_comment_url"])
    match = re.fullmatch(
        r"https://github\.com/Unjuno/agent-interface/issues/5085#issuecomment-(\d+)",
        lease["owner_comment_url"])
    if (not match or type(comment.get("id")) is not int
            or comment.get("id") != int(match.group(1))):
        stop("LEASE_OWNER_COMMENT_ID_MISMATCH")
    if (comment.get("html_url") != lease["owner_comment_url"]
            or comment.get("issue_url") != "https://api.github.com/repos/Unjuno/agent-interface/issues/5085"):
        stop("LEASE_OWNER_COMMENT_URL_MISMATCH")
    author = comment.get("user")
    if not isinstance(author, dict) or author.get("login") != "Unjuno":
        stop("LEASE_OWNER_COMMENT_AUTHOR")
    body = comment.get("body")
    blocks = LEASE_COMMENT_PATTERN.findall(body) if isinstance(body, str) else []
    if len(blocks) != 1:
        stop("LEASE_OWNER_COMMENT_PAYLOAD_MISSING")
    try:
        payload = json.loads(blocks[0], object_pairs_hook=unique_pairs)
    except (json.JSONDecodeError, ValueError):
        stop("LEASE_OWNER_COMMENT_PAYLOAD_INVALID")
    expected_payload = {key: lease[key] for key in (
        "schema", "allocation", "issue", "main_sha", "branch", "docker_context",
        "lease_id", "slot_start_utc", "slot_end_utc", "expires_at_utc")}
    if payload != expected_payload:
        stop("LEASE_OWNER_COMMENT_PAYLOAD_MISMATCH")
    return {"id": comment["id"], "html_url": comment["html_url"], "issue_url": comment["issue_url"],
            "user_login": comment["user"]["login"], "body": body}


def lease_window_active(lease: dict, now=None) -> bool:
    """Recheck the complete owner-granted window immediately before each Docker call."""
    try:
        expiry = datetime.fromisoformat(lease["expires_at_utc"].replace("Z", "+00:00"))
        slot_start = datetime.fromisoformat(lease["slot_start_utc"].replace("Z", "+00:00"))
        slot_end = datetime.fromisoformat(lease["slot_end_utc"].replace("Z", "+00:00"))
    except (KeyError, TypeError, ValueError):
        return False
    if any(value.tzinfo is None for value in (expiry, slot_start, slot_end)):
        return False
    current = now or datetime.now(timezone.utc)
    return slot_start <= current < min(slot_end, expiry)


def lease_seconds_remaining(lease: dict, now=None) -> float:
    try:
        expiry = datetime.fromisoformat(lease["expires_at_utc"].replace("Z", "+00:00"))
        slot_end = datetime.fromisoformat(lease["slot_end_utc"].replace("Z", "+00:00"))
    except (KeyError, TypeError, ValueError):
        return 0.0
    current = now or datetime.now(timezone.utc)
    if expiry.tzinfo is None or slot_end.tzinfo is None:
        return 0.0
    return max(0.0, (min(expiry, slot_end) - current).total_seconds())


def lease_hard_stop_utc(lease: dict) -> str:
    expiry = datetime.fromisoformat(lease["expires_at_utc"].replace("Z", "+00:00"))
    slot_end = datetime.fromisoformat(lease["slot_end_utc"].replace("Z", "+00:00"))
    if expiry.tzinfo is None or slot_end.tzinfo is None:
        stop("LEASE_TIME_UNZONED")
    hard_stop = min(expiry, slot_end).astimezone(timezone.utc) - timedelta(
        seconds=SELF_STOP_MARGIN_SECONDS)
    return hard_stop.isoformat().replace("+00:00", "Z")


def lease_hard_stop_seconds(lease: dict, now=None) -> float:
    expiry = datetime.fromisoformat(lease["expires_at_utc"].replace("Z", "+00:00"))
    slot_end = datetime.fromisoformat(lease["slot_end_utc"].replace("Z", "+00:00"))
    current = now or datetime.now(timezone.utc)
    if expiry.tzinfo is None or slot_end.tzinfo is None:
        return 0.0
    return (min(expiry, slot_end) - current).total_seconds() - SELF_STOP_MARGIN_SECONDS


def _read_container_id(cidfile: Path) -> str | None:
    try:
        value = cidfile.read_text(encoding="ascii").strip()
    except OSError:
        return None
    return value if re.fullmatch(r"[0-9a-f]{64}", value) else None


def _text_output(value) -> str | None:
    if value is None:
        return None
    return value.decode("utf-8", errors="replace") if isinstance(value, bytes) else str(value)


def run_lease_bounded(argv: list[str], cidfile: Path, lease: dict,
                      docker_context: str, hard_stop_utc: str):
    """Bound execution before lease end; container watchdog remains the final stop."""
    run_timeout = lease_seconds_remaining(lease) - CLEANUP_RESERVE_SECONDS
    if run_timeout <= 0:
        stop("LEASE_WINDOW_TOO_SHORT_FOR_CLEANUP")
    try:
        proc = subprocess.run(argv, check=False, capture_output=True, text=True,
                              timeout=run_timeout)
        return proc, {"timed_out": False, "cleanup_exit_code": None,
                "cleanup_stderr": None, "container_id": _read_container_id(cidfile),
                "hard_stop_utc": hard_stop_utc}
    except subprocess.TimeoutExpired as exc:
        container_id = _read_container_id(cidfile)
        cleanup_code, cleanup_stderr = None, None
        if container_id and lease_seconds_remaining(lease) > 1:
            cleanup_timeout = min(CLEANUP_TIMEOUT_SECONDS,
                                  max(1.0, lease_seconds_remaining(lease) - 1.0))
            try:
                cleanup = subprocess.run(["docker", "--context", docker_context,
                                          "rm", "--force", container_id],
                                          check=False, capture_output=True, text=True,
                                          timeout=cleanup_timeout)
                cleanup_code, cleanup_stderr = cleanup.returncode, cleanup.stderr
            except (OSError, subprocess.SubprocessError) as cleanup_error:
                cleanup_stderr = str(cleanup_error)
        return subprocess.CompletedProcess(argv, 124,
                                           stdout=_text_output(exc.stdout),
                                           stderr=_text_output(exc.stderr)), {
            "timed_out": True, "cleanup_exit_code": cleanup_code,
            "cleanup_stderr": cleanup_stderr, "container_id": container_id,
            "hard_stop_utc": hard_stop_utc}


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    if args == ["--preflight"]:
        print(json.dumps({"allocation": ALLOCATION, "formal_docker_calls": 0,
                          "lease_required": True, "result": "PREFLIGHT_ONLY"}, sort_keys=True))
        return 0
    if len(args) != 7 or args[0] != "--formal":
        stop("USAGE:formal LEASE.json MAIN_SHA BRANCH DOCKER_CONTEXT SOURCE_DIR OUTPUT_DIR")
    lease_path, main_sha, branch, expected_context, source_text, output_text = args[1:]
    lease = read_json(Path(lease_path))
    try:
        source, output = Path(source_text).resolve(strict=True), Path(output_text).resolve(strict=True)
    except OSError as exc:
        stop("MOUNT_PATH_INVALID:" + str(exc))
    if source != HERE.resolve(strict=True):
        stop("SOURCE_PATH_NOT_EXPERIMENT_DIRECTORY")
    if not output.is_dir() or any(output.iterdir()):
        stop("OUTPUT_NOT_EMPTY")
    owner_comment = validate_lease(lease, main_sha, branch, expected_context)
    try:
        actual_branch = subprocess.run(["git", "branch", "--show-current"], cwd=ROOT,
                                       check=True, capture_output=True, text=True, timeout=10).stdout.strip()
        current_main = subprocess.run(["git", "rev-parse", "refs/remotes/origin/main"], cwd=ROOT,
                                      check=True, capture_output=True, text=True, timeout=10).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        stop("GIT_MAIN_OR_BRANCH_UNVERIFIABLE")
    if actual_branch != branch or current_main != main_sha:
        stop("STALE_MAIN_OR_BRANCH")
    if not lease_window_active(lease):
        stop("LEASE_SLOT_EXPIRED_BEFORE_DOCKER")
    context_timeout = min(10.0, lease_seconds_remaining(lease))
    if context_timeout <= 0:
        stop("LEASE_SLOT_EXPIRED_BEFORE_DOCKER")
    context_result = subprocess.run(["docker", "context", "show"], check=False,
                                    capture_output=True, text=True, timeout=context_timeout)
    if context_result.returncode != 0:
        stop("DOCKER_CONTEXT_UNAVAILABLE")
    current_context = context_result.stdout.strip()
    if current_context != expected_context:
        stop("DOCKER_CONTEXT_CHANGED")
    hard_stop = lease_hard_stop_utc(lease)
    hard_stop_seconds = lease_hard_stop_seconds(lease)
    if hard_stop_seconds <= 0:
        stop("LEASE_WINDOW_TOO_SHORT_FOR_SELF_STOP")
    argv = docker_argv(source, output, current_context, hard_stop, hard_stop_seconds)
    canonical_argv = list(argv)
    receipt = {
        "schema": "needle-role-skill-joint-retention-formal-receipt-v1",
        "allocation": ALLOCATION, "issue": 5081, "lease_id": lease["lease_id"],
        "owner_comment_url": lease["owner_comment_url"], "main_sha": main_sha,
        "lease_issue": lease["issue"], "slot_start_utc": lease["slot_start_utc"],
        "slot_end_utc": lease["slot_end_utc"], "expires_at_utc": lease["expires_at_utc"],
        "branch": branch, "docker_context": current_context,
        "hard_stop_utc": hard_stop,
        "hard_stop_seconds": hard_stop_seconds,
        "owner_lease_comment": owner_comment,
        "source_path": str(source), "output_path": str(output),
        "image_id": IMAGE_ID, "seeds": list(SEEDS), "formal_invocations": 1,
        "retries": 0, "command_argv": canonical_argv,
        "command_argv_sha256": sha256_bytes(canonical(canonical_argv)),
        "started_at_ns": time.time_ns(),
        "started_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    receipt_path = output / "formal_receipt.json"
    # This one invocation is deliberate. There is no retry or partial rerun.
    if not lease_window_active(lease):
        stop("LEASE_SLOT_EXPIRED_BEFORE_DOCKER_RUN")
    proc, bounded = run_lease_bounded(argv, output / "container.id", lease,
                                      current_context, hard_stop)
    raw_path = output / "formal_result.json"
    raw_sha = sha256_bytes(raw_path.read_bytes()) if raw_path.is_file() else None
    watchdog_path = output / "watchdog_receipt.json"
    watchdog_sha = sha256_bytes(watchdog_path.read_bytes()) if watchdog_path.is_file() else None
    completed = {**receipt, "exit_code": proc.returncode,
                 "finished_at_ns": time.time_ns(),
                 "finished_at_utc": datetime.now(timezone.utc).isoformat(),
                 "stdout": proc.stdout, "stderr": proc.stderr,
                 "container_timed_out": bounded["timed_out"],
                 "container_cleanup_exit_code": bounded["cleanup_exit_code"],
                 "container_cleanup_stderr": bounded["cleanup_stderr"],
                 "container_id": bounded["container_id"],
                 "watchdog_receipt_sha256": watchdog_sha,
                 "raw_result_sha256": raw_sha,
                 "formal_result_present": raw_path.is_file()}
    with receipt_path.open("xb") as stream:
        stream.write(canonical(completed) + b"\n")
    print(json.dumps({"allocation": ALLOCATION, "exit_code": proc.returncode,
                      "formal_invocations": 1, "retries": 0,
                      "raw_result_sha256": raw_sha}, sort_keys=True))
    return 0 if proc.returncode == 0 and raw_sha else 2


if __name__ == "__main__":
    raise SystemExit(main())
