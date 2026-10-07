#!/usr/bin/env python3
"""Audit the one A02 CLI response against the frozen image labels."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
EXPECTED = {"visible_hostile": True, "health": 51, "ammo": 38}
RECOMMENDATIONS = {"CONTINUE", "STOP_OR_SWITCH", "UNCERTAIN"}
PACKAGE = "@openai/codex@0.160.0"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    freeze = json.loads((ROOT / "freeze.json").read_text())
    source_ok = sha(ROOT / "source.png") == freeze["input"]["png_sha256"]
    assets_ok = all(
        (ROOT / relative).is_file() and sha(ROOT / relative) == digest
        for relative, digest in [
            ("source_events.jsonl", freeze["input"]["source_events_public_sha256"]),
            ("prompt.txt", freeze["candidate"]["prompt_sha256"]),
            ("output.schema.json", freeze["candidate"]["output_schema_sha256"]),
            ("run_once.py", freeze["candidate"]["runner_sha256"]),
            ("audit.py", freeze["candidate"]["auditor_sha256"]),
        ]
    )
    raw = ROOT / "raw"
    try:
        invocation = json.loads((raw / "invocation.json").read_text())
        version_preflight = json.loads((raw / "version-preflight.json").read_text())
        exit_code = int((raw / "exit-code.txt").read_text().strip())
    except Exception:
        invocation, version_preflight, exit_code = {}, {}, None
    expected_argv = [
        "npm", "exec", "--yes", "--package", PACKAGE, "--",
        "codex", "exec", "--ephemeral", "--json", "--skip-git-repo-check",
        "--sandbox", "read-only", "--model", freeze["candidate"]["model"],
        "-c", f"model_reasoning_effort={freeze['candidate']['reasoning_effort']}",
        "--image", str((ROOT / "source.png").resolve()),
        "--output-schema", str((ROOT / "output.schema.json").resolve()),
        "--output-last-message", str((raw / "final.txt").resolve()),
        "--cd", "/tmp", "-",
    ]
    prompt_hash = sha(ROOT / "prompt.txt")
    invocation_ok = (
        invocation.get("allocation") == freeze["allocation"]
        and invocation.get("status") == "finished"
        and invocation.get("argv") == expected_argv
        and invocation.get("stdin_sha256") == prompt_hash
        and invocation.get("image_sha256") == sha(ROOT / "source.png")
        and invocation.get("package") == PACKAGE
        and invocation.get("cli_version") == freeze["candidate"]["cli_version"]
        and invocation.get("model") == freeze["candidate"]["model"]
        and invocation.get("reasoning_effort") == freeze["candidate"]["reasoning_effort"]
        and invocation.get("exit_code") == exit_code
    )
    preflight_ok = (
        version_preflight.get("exit_code") == 0
        and version_preflight.get("stdout") == freeze["candidate"]["cli_version"]
        and version_preflight.get("argv") == ["npm", "exec", "--yes", "--package", PACKAGE, "--", "codex", "--version"]
    )
    launcher_error = (raw / "launcher-error.txt").exists()
    events_path = raw / "events.jsonl"
    events = []
    parse_errors = 0
    if events_path.is_file():
        for line in events_path.read_text(errors="replace").splitlines():
            try:
                events.append(json.loads(line))
            except Exception:
                parse_errors += 1
    tool_items = []
    for event in events:
        item = event.get("item")
        if isinstance(item, dict) and item.get("type") not in {"reasoning", "agent_message", "error"}:
            tool_items.append(item.get("type"))
    final_path = raw / "final.txt"
    parse_error = None
    try:
        response = json.loads(final_path.read_text())
    except Exception as exc:
        response = None
        parse_error = f"{type(exc).__name__}: final response absent or invalid"
    expected_keys = {"visible_hostile", "health", "ammo", "cover_recommendation", "rationale"}
    schema_valid = (
        isinstance(response, dict)
        and set(response) == expected_keys
        and isinstance(response.get("visible_hostile"), bool)
        and (response.get("health") is None or type(response.get("health")) is int)
        and (response.get("ammo") is None or type(response.get("ammo")) is int)
        and response.get("cover_recommendation") in RECOMMENDATIONS
        and isinstance(response.get("rationale"), str)
    )
    matches = {key: bool(schema_valid and response.get(key) == value) for key, value in EXPECTED.items()}
    failed_turn = any(
        event.get("type") in {"error", "turn.failed"}
        or (isinstance(event.get("item"), dict) and event["item"].get("type") == "error")
        for event in events
    )
    evidence_complete = all((raw / name).is_file() for name in ["events.jsonl", "stderr.txt", "exit-code.txt", "invocation.json", "version-preflight.json", "prompt.stdin.txt"])
    gate = (
        "STOP"
        if not (source_ok and assets_ok and invocation_ok and preflight_ok and evidence_complete and exit_code == 0 and schema_valid and not tool_items and not parse_errors and not failed_turn and not launcher_error)
        else "PASS"
        if all(matches.values())
        else "FAIL"
    )
    audit = {
        "audit": "a02-frozen-response-v1",
        "source_png_matches_freeze": source_ok,
        "frozen_assets_match": assets_ok,
        "version_preflight_matches": preflight_ok,
        "invocation_matches_freeze": invocation_ok,
        "candidate_exit_code": exit_code,
        "event_json_parse_errors": parse_errors,
        "non_message_items": tool_items,
        "turn_error_event": failed_turn,
        "launcher_error": launcher_error,
        "response_parse_error": parse_error,
        "schema_valid": schema_valid,
        "field_matches": matches,
        "unscored_cover_recommendation": response.get("cover_recommendation") if schema_valid else None,
        "gate": gate,
        "scope": "one retained frame, one CLI 0.160.0 inference attempt; no game or controller action",
    }
    (ROOT / "audit.json").write_text(json.dumps(audit, indent=2) + "\n")
    print(json.dumps(audit, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
