#!/usr/bin/env python3
"""Audit public redactions and the preserved unsupported-model STOP packet."""
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
    prompt_hash = sha(ROOT / "prompt.txt")
    image_hash = sha(ROOT / "source.png")
    event_digest_matches = all(
        sha((ROOT / relative).resolve()) == row["sha256"]
        for relative, row in redactions["published_sha256"].items()
    )
    event_error = next((e for e in events if e.get("type") == "error"), {})
    event_message = event_error.get("message", "")
    public_text = "\n".join([
        (ROOT / "raw" / "events.jsonl").read_text(), stderr,
        (ROOT / "raw" / "invocation.json").read_text(),
        (ROOT / "audit.json").read_text(),
    ])
    private_patterns_absent = (
        "/Users/" not in public_text
        and not re.search(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", public_text)
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
    checks = {
        "redacted_public_hashes_match": event_digest_matches,
        "source_png_matches_freeze": image_hash == freeze["input"]["png_sha256"],
        "source_events_match_freeze": sha(ROOT / "source_events.jsonl") == freeze["input"]["source_events_sha256"],
        "prompt_matches_freeze": prompt_hash == freeze["candidate"]["prompt_sha256"],
        "prompt_stdin_matches": sha(ROOT / "raw" / "prompt.stdin.txt") == prompt_hash,
        "requested_model_and_effort_match": model_args_match,
        "thread_identifier_redacted": any(e.get("thread_id") == "<REDACTED_LOCAL_THREAD_ID>" for e in events),
        "private_paths_and_uuid_absent": private_patterns_absent,
        "service_rejection_retained": "not supported when using Codex with a ChatGPT account" in event_message and "not supported when using Codex with a ChatGPT account" in stderr,
        "no_final_model_response": not (ROOT / "raw" / "final.txt").exists() and not any((e.get("item") or {}).get("type") == "agent_message" for e in events),
        "exit_code_and_disposition_match": (ROOT / "raw" / "exit-code.txt").read_text().strip() == "1" and result_record["status"] == "STOP_MODEL_UNSUPPORTED" and result_record["model_comprehension_gate"] == "NOT_EVALUATED",
        "original_hashes_recorded": all(len(row["sha256"]) == 64 for row in redactions["original_sha256"].values()),
    }
    output = {
        "audit": "redacted-raw-preservation-v2",
        "checks": checks,
        "passed": sum(checks.values()),
        "total": len(checks),
        "disposition": "PASS_REDACTION_AND_STOP_CUSTODY" if all(checks.values()) else "FAIL_AUDIT",
        "scope": "audits public redactions and retained service rejection; does not rerun A01 or evaluate model comprehension",
    }
    (ROOT / "audit_redacted_v2.json").write_text(json.dumps(output, indent=2) + "\n")
    print(json.dumps(output, indent=2))
    return 0 if all(checks.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
