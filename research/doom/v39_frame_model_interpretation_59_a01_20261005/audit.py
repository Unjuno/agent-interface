#!/usr/bin/env python3
"""Deterministically audit the single saved-frame model response."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
EXPECTED = {
    "visible_hostile": True,
    "health": 51,
    "ammo": 38,
}
ALLOWED_RECOMMENDATIONS = {"CONTINUE", "STOP_OR_SWITCH", "UNCERTAIN"}


def main() -> int:
    freeze = json.loads((ROOT / "freeze.json").read_text())
    source = ROOT / "source.png"
    source_sha = hashlib.sha256(source.read_bytes()).hexdigest()
    source_matches = source_sha == freeze["input"]["png_sha256"]
    frozen_assets_match = all(
        (ROOT / rel).is_file()
        and hashlib.sha256((ROOT / rel).read_bytes()).hexdigest() == digest
        for rel, digest in [
            ("source_events.jsonl", freeze["input"]["source_events_sha256"]),
            ("prompt.txt", freeze["candidate"]["prompt_sha256"]),
            ("output.schema.json", freeze["candidate"]["output_schema_sha256"]),
            ("run_once.py", freeze["candidate"]["runner_sha256"]),
            ("audit.py", freeze["candidate"]["auditor_sha256"]),
        ]
    )
    exit_path = ROOT / "raw" / "exit-code.txt"
    try:
        exit_code = int(exit_path.read_text().strip()) if exit_path.exists() else None
    except ValueError:
        exit_code = None
    invocation_path = ROOT / "raw" / "invocation.json"
    try:
        invocation = json.loads(invocation_path.read_text()) if invocation_path.exists() else {}
    except Exception:
        invocation = {}
    stdin_path = ROOT / "raw" / "prompt.stdin.txt"
    stdin_sha = hashlib.sha256(stdin_path.read_bytes()).hexdigest() if stdin_path.exists() else None
    invocation_matches = (
        invocation.get("allocation") == freeze["allocation"]
        and invocation.get("model") == freeze["candidate"]["model"]
        and invocation.get("reasoning_effort") == freeze["candidate"]["reasoning_effort"]
        and invocation.get("image_sha256") == source_sha
        and stdin_sha == freeze["candidate"]["prompt_sha256"]
        and invocation.get("status") == "finished"
        and invocation.get("exit_code") == exit_code
    )
    expected_argv = [
        "codex", "exec", "--ephemeral", "--json", "--skip-git-repo-check",
        "--sandbox", "read-only", "--model", freeze["candidate"]["model"],
        "-c", f"model_reasoning_effort={freeze['candidate']['reasoning_effort']}",
        "--image", str((ROOT / "source.png").resolve()),
        "--output-schema", str((ROOT / "output.schema.json").resolve()),
        "--output-last-message", str((ROOT / "raw" / "final.txt").resolve()),
        "--cd", "/tmp", "-",
    ]
    invocation_matches = invocation_matches and invocation.get("argv") == expected_argv
    event_path = ROOT / "raw" / "events.jsonl"
    event_file_present = event_path.is_file()
    tool_events = []
    event_parse_errors = 0
    if event_path.exists():
        for line_number, line in enumerate(event_path.read_text(errors="replace").splitlines(), 1):
            try:
                event = json.loads(line)
            except Exception:
                event_parse_errors += 1
                continue
            item = event.get("item")
            if isinstance(item, dict) and item.get("type") not in {"reasoning", "agent_message"}:
                tool_events.append({"line": line_number, "item_type": item.get("type")})

    final_path = ROOT / "raw" / "final.txt"
    response = None
    parse_error = None
    try:
        response = json.loads(final_path.read_text())
    except Exception as exc:  # Retain parse failure as an audit result.
        parse_error = f"{type(exc).__name__}: {exc}"

    expected_keys = {
        "visible_hostile", "health", "ammo", "cover_recommendation", "rationale"
    }
    schema_valid = (
        isinstance(response, dict)
        and set(response) == expected_keys
        and isinstance(response.get("visible_hostile"), bool)
        and (response.get("health") is None or type(response.get("health")) is int)
        and (response.get("ammo") is None or type(response.get("ammo")) is int)
        and response.get("cover_recommendation") in ALLOWED_RECOMMENDATIONS
        and isinstance(response.get("rationale"), str)
    )
    field_matches = {
        key: bool(schema_valid and response.get(key) == value)
        for key, value in EXPECTED.items()
    }
    result = {
        "audit": "v1-independent-deterministic",
        "source_png_sha256": source_sha,
        "source_matches_freeze": source_matches,
        "frozen_assets_match": frozen_assets_match,
        "cli_exit_code": exit_code,
        "invocation_status": invocation.get("status"),
        "invocation_matches_freeze": invocation_matches,
        "stdin_sha256": stdin_sha,
        "jsonl_event_parse_errors": event_parse_errors,
        "jsonl_file_present": event_file_present,
        "non_message_items": tool_events,
        "response_parse_error": parse_error,
        "schema_valid": schema_valid,
        "field_matches": field_matches,
        "unscored_cover_recommendation": (
            response.get("cover_recommendation") if schema_valid else None
        ),
        "gate": (
            "PASS"
            if source_matches and frozen_assets_match and invocation_matches and event_file_present and exit_code == 0 and schema_valid and not tool_events and not event_parse_errors and all(field_matches.values())
            else "FAIL"
            if source_matches and frozen_assets_match and invocation_matches and event_file_present and exit_code == 0 and schema_valid and not tool_events and not event_parse_errors
            else "STOP"
        ),
        "scope": "one saved frame and one model call; no controller or game action",
    }
    (ROOT / "audit.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
