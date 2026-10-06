#!/usr/bin/env python3
"""Audit published redactions and A01 STOP custody without rerunning A01."""
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    freeze = json.loads((ROOT / "freeze.json").read_text())
    result_record = json.loads((ROOT / "RESULT.json").read_text())
    redactions = json.loads((ROOT / "REDACTIONS.json").read_text())
    invocation = json.loads((ROOT / "raw" / "invocation.json").read_text())
    event_lines = (ROOT / "raw" / "events.jsonl").read_text().splitlines()
    events = [json.loads(line) for line in event_lines]
    stderr = (ROOT / "raw" / "stderr.txt").read_text(errors="replace")
    source_events = [json.loads(line) for line in (ROOT / "source_events.jsonl").read_text().splitlines()]

    published_hashes_match = True
    for relative, row in redactions["published_sha256"].items():
        if relative == "../audit.json":
            path = ROOT / "audit.json"
        elif relative == "source_events.jsonl":
            path = ROOT / relative
        else:
            path = ROOT / "raw" / relative
        published_hashes_match &= path.is_file() and sha(path) == row["sha256"]

    event_error = next((event for event in events if event.get("type") == "error"), {})
    event_message = event_error.get("message", "")
    public_text = "\n".join([
        (ROOT / "raw" / "events.jsonl").read_text(), stderr,
        (ROOT / "raw" / "invocation.json").read_text(),
        (ROOT / "audit.json").read_text(),
        (ROOT / "source_events.jsonl").read_text(),
    ])
    no_private_identifiers = (
        "/Users/" not in public_text
        and "C:/Users/" not in public_text
        and "C:\\Users\\" not in public_text
        and not re.search(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", public_text)
    )
    private = ROOT / "raw" / "private-local"
    original_hashes_match_locally = True
    for entry in redactions["original_sha256"].values():
        path = private / entry["private_copy"]
        original_hashes_match_locally &= path.is_file() and sha(path) == entry["sha256"]
    private_mode_ok = (private.stat().st_mode & 0o777) == 0o700 and all(
        (private / entry["private_copy"]).stat().st_mode & 0o777 == 0o600
        for entry in redactions["original_sha256"].values()
    )
    argv = invocation.get("argv", [])
    model_args_match = (
        "--model" in argv
        and argv[argv.index("--model") + 1] == freeze["candidate"]["model"]
        and "model_reasoning_effort=" + freeze["candidate"]["reasoning_effort"] in argv
        and "<PACKAGE>/source.png" in argv
        and "<PACKAGE>/output.schema.json" in argv
        and "<PACKAGE>/raw/final.txt" in argv
    )
    source_join_ok = (
        len(source_events) == 2
        and [row.get("event") for row in source_events] == ["typed_observation", "observation"]
        and all(row.get("sequence") == 200 for row in source_events)
        and source_events[0].get("image") is None
        and source_events[1].get("image") == "<SOURCE_IMAGE_PATH>/runtime/200.png"
        and source_events[0].get("frame_rgb_sha256") == source_events[1].get("frame_rgb_sha256") == freeze["input"]["decoded_rgb_sha256"]
        and source_events[0].get("signals", {}).get("health", {}).get("value") == 51
        and source_events[0].get("signals", {}).get("ammo", {}).get("value") == 38
    )
    checks = {
        "published_redacted_hashes_match": bool(published_hashes_match),
        "source_png_matches_freeze": sha(ROOT / "source.png") == freeze["input"]["png_sha256"],
        "original_source_event_hash_matches_freeze": redactions["original_sha256"].get("source_events.jsonl", {}).get("sha256") == freeze["input"]["source_events_sha256"],
        "sanitized_source_event_join_matches": source_join_ok,
        "prompt_and_stdin_match_freeze": sha(ROOT / "prompt.txt") == freeze["candidate"]["prompt_sha256"] and sha(ROOT / "raw" / "prompt.stdin.txt") == freeze["candidate"]["prompt_sha256"],
        "requested_model_and_effort_match": model_args_match,
        "local_original_raw_hashes_match": bool(original_hashes_match_locally),
        "local_private_permissions_match": bool(private_mode_ok),
        "private_paths_and_session_uuid_redacted": no_private_identifiers,
        "service_rejection_retained": "not supported when using Codex with a ChatGPT account" in event_message and "not supported when using Codex with a ChatGPT account" in stderr,
        "no_final_model_response": not (ROOT / "raw" / "final.txt").exists() and not any((event.get("item") or {}).get("type") == "agent_message" for event in events),
        "exit_code_and_disposition_match": (ROOT / "raw" / "exit-code.txt").read_text().strip() == "1" and result_record["status"] == "STOP_MODEL_UNSUPPORTED" and result_record["model_comprehension_gate"] == "NOT_EVALUATED",
    }
    output = {
        "audit": "redacted-raw-preservation-v4",
        "checks": checks,
        "passed": sum(checks.values()),
        "total": len(checks),
        "disposition": "PASS_REDACTION_AND_STOP_CUSTODY" if all(checks.values()) else "FAIL_AUDIT",
        "scope": "verifies public redactions and local original custody; does not rerun A01 or evaluate image comprehension",
    }
    (ROOT / "audit_redacted_v4.json").write_text(json.dumps(output, indent=2) + "\n")
    print(json.dumps(output, indent=2))
    return 0 if all(checks.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
