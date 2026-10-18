#!/usr/bin/env python3
"""Run the frozen terminal-status × release-state construction matrix."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import platform
import subprocess
from datetime import datetime, timezone
from pathlib import Path


HERE = Path(__file__).resolve().parent
ADAPTER_PATH = HERE / "candidate_adapter.py"
ACTION_ID = "composition-a01-action"
SOURCE_PATH = (
    "research/integration/mindustry_three_arm_economics_20260928/"
    "target_socket_submit_v1.py"
)
MAIN_SHA = "c99d93a2c81945f0946173e48247bdd49e32a02a"
STATUS_HEAD = "bd0ba260acf885d7b859d665571b2c3260666642"
RELEASE_HEAD = "1d7bb20bcde67333f58e41a24f8dce68f8561ffd"

STATUS_CASES = [
    ("completed", "completed"),
    ("failed", "failed"),
    ("cancelled", "cancelled"),
    ("needs_decision", "needs_decision"),
    ("explicit_null", None),
    ("missing", "__MISSING__"),
    ("boolean_true", True),
    ("uppercase", "COMPLETED"),
]


def release_cases() -> list[tuple[str, object]]:
    return [
        ("minimal_empty", {"verified": True, "keys_down": [], "buttons_down": []}),
        ("source_owner_release", {
            "event": "owner_release", "reason": "release", "verified": True,
            "keys_down": [], "buttons_down": [], "verified_ns": 123, "valid_until_ns": 456,
        }),
        ("held_key", {"verified": True, "keys_down": ["LEFT"], "buttons_down": []}),
        ("held_button", {"verified": True, "keys_down": [], "buttons_down": ["left"]}),
        ("missing_keys", {"verified": True, "buttons_down": []}),
        ("missing_buttons", {"verified": True, "keys_down": []}),
        ("unverified", {"verified": False, "keys_down": [], "buttons_down": []}),
        ("missing_release", "__MISSING__"),
        ("unknown_field", {
            "verified": True, "keys_down": [], "buttons_down": [], "future": "unknown",
        }),
        ("malformed_metadata", {
            "event": "terminal", "verified": True, "keys_down": [],
            "buttons_down": [], "verified_ns": True,
        }),
    ]


def source_blob_sha(revision: str) -> str:
    return subprocess.check_output(
        ["git", "rev-parse", f"{revision}:{SOURCE_PATH}"], cwd=HERE, text=True
    ).strip()


def build_response(status: object, release: object) -> dict:
    terminal = {"event": "terminal", "id": ACTION_ID}
    if status != "__MISSING__":
        terminal["status"] = status
    if release != "__MISSING__":
        terminal["release"] = release
    return {
        "status": "boundary",
        "records": [terminal],
        "cursor": 1,
        "authority": "none",
        "acknowledgement": "not implied",
        "command_receipt": {
            "request_id": ACTION_ID, "replayed": False, "state": "stdin_flushed",
        },
    }


def load_adapter():
    spec = importlib.util.spec_from_file_location("composition_candidate", ADAPTER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load candidate adapter")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> None:
    started_utc = datetime.now(timezone.utc).isoformat()
    candidate_bytes = ADAPTER_PATH.read_bytes()
    candidate_sha = hashlib.sha256(candidate_bytes).hexdigest()
    module = load_adapter()
    rows = []
    for status_label, status_value in STATUS_CASES:
        for release_label, release_value in release_cases():
            response = build_response(status_value, release_value)
            submitter = module.TargetSocketSubmitter(
                "/not-used.sock", trace_sink=lambda _record: None,
            )
            submitter._exchange = lambda _request, value=response: value
            try:
                result = submitter({"op": "submit", "id": ACTION_ID})
                observed = "accepted"
                receipt = result
            except module.SocketSubmitStop as error:
                observed = "rejected"
                receipt = None
                error_type = type(error).__name__
            row = {
                "status_case": status_label,
                "release_case": release_label,
                "observed": observed,
                "receipt": receipt,
            }
            if observed == "rejected":
                row["error_type"] = error_type
            rows.append(row)

    raw = {
        "schema": "mindustry_terminal_release_composition_raw_v1",
        "started_utc": started_utc,
        "finished_utc": datetime.now(timezone.utc).isoformat(),
        "argv": ["python3", "run.py"],
        "main_sha": MAIN_SHA,
        "status_pr_head": STATUS_HEAD,
        "release_pr_head": RELEASE_HEAD,
        "status_source_blob": source_blob_sha(STATUS_HEAD),
        "release_source_blob": source_blob_sha(RELEASE_HEAD),
        "candidate_sha256": candidate_sha,
        "python": platform.python_version(),
        "case_count": len(rows),
        "accepted": sum(row["observed"] == "accepted" for row in rows),
        "rejected": sum(row["observed"] == "rejected" for row in rows),
        "rows": rows,
        "environment_scope": "in-memory callbacks only; no socket, GUI, game, model, Docker, or OS input",
    }
    raw_bytes = json.dumps(raw, indent=2, sort_keys=True).encode("utf-8") + b"\n"
    (HERE / "RAW.json").write_bytes(raw_bytes)
    print(json.dumps({
        "case_count": raw["case_count"], "accepted": raw["accepted"],
        "rejected": raw["rejected"],
        "raw_sha256": hashlib.sha256(raw_bytes).hexdigest(),
        "candidate_sha256": candidate_sha,
    }, sort_keys=True))


if __name__ == "__main__":
    main()
