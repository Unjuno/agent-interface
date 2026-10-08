#!/usr/bin/env python3
"""Run one bounded synthetic cleanup-event identity candidate."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
import tempfile

PACKAGE = Path(__file__).resolve().parent
ROOT = PACKAGE.parents[3]
SOURCE = ROOT / "research/doom/doom_controller_failure_cleanup_v1.py"
sys.path.insert(0, str(SOURCE.parent))
from doom_controller_failure_cleanup_v1 import ControllerFailureCleanup  # noqa: E402


class Planner:
    def close(self, timeout=1):
        return None


class RetiredReader:
    def join(self, timeout=None):
        return None

    def is_alive(self):
        return False


def accepted(identifier, token):
    row = {"event": "accepted", "id": identifier}
    if token is not None:
        row["intent_token"] = token
    return row


def terminal(identifier, verified, token=...):
    release = {"verified": verified,
               "keys_down": [] if verified else [38],
               "buttons_down": []}
    if token is not ...:
        release["intent_token"] = token
    return {"event": "terminal", "id": identifier, "release": release}


def cases():
    return [
        ("valid_single", [accepted("one", "lease-one"),
                          terminal("one", True, "lease-one")]),
        ("legacy_tokenless", [accepted("one", "lease-one"),
                               terminal("one", True)]),
        ("mismatched_token", [accepted("one", "lease-one"),
                               terminal("one", True, "other-lease")]),
        ("distinct_pair", [accepted("one", "lease-one"),
                            accepted("two", "lease-two"),
                            terminal("one", True, "lease-one"),
                            terminal("two", True, "lease-two")]),
        ("duplicate_accept_one_terminal", [accepted("one", "lease-a"),
                                            accepted("one", "lease-b"),
                                            terminal("one", True, "lease-b")]),
        ("duplicate_terminal_verified_then_failed", [accepted("one", "lease-one"),
                                                      terminal("one", True, "lease-one"),
                                                      terminal("one", False)]),
        ("duplicate_terminal_failed_then_verified", [accepted("one", "lease-one"),
                                                      terminal("one", False),
                                                      terminal("one", True, "lease-one")]),
    ]


def run_case(name, events):
    with tempfile.TemporaryDirectory(prefix="cleanup-identity-a02-") as directory:
        output = Path(directory)
        scope = ControllerFailureCleanup(Planner(), output)
        scope.observe_output(events, RetiredReader(), lambda predicate, timeout: None,
                             None, [])
        try:
            with scope:
                scope.set_stage("synthetic_event_reconstruction")
                raise RuntimeError("synthetic candidate boundary")
        except RuntimeError as error:
            if str(error) != "synthetic candidate boundary":
                raise
        receipt = json.loads((output / "controller-failure.json").read_text())
    return {
        "name": name,
        "events": events,
        "receipt": {key: receipt.get(key) for key in (
            "input_terminals_complete", "input_releases_verified_empty",
            "input_release_verified_empty", "event_identity_ambiguous",
            "accepted_duplicate_ids", "terminal_duplicate_ids")},
    }


def main():
    freeze = json.loads((PACKAGE / "FREEZE.json").read_text(encoding="utf-8"))
    source_sha = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    if source_sha != freeze["source_sha256"]:
        raise SystemExit("frozen source hash mismatch")
    raw = {
        "schema": "issue8681-cleanup-identity-a02-raw-v1",
        "allocation_id": freeze["allocation_id"],
        "base_main_sha": freeze["base_main_sha"],
        "source_sha256": source_sha,
        "cases": [run_case(name, rows) for name, rows in cases()],
        "claims": {
            "production_duplicate_occurrence": False,
            "runtime_or_game_behavior": False,
            "model_behavior": False,
            "gui_or_os_input": False,
            "physical_release": False,
        },
    }
    (PACKAGE / "RAW.json").write_text(
        json.dumps(raw, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": "CANDIDATE_RETAINED",
                      "allocation_id": raw["allocation_id"],
                      "case_count": len(raw["cases"]),
                      "source_sha256": source_sha}, sort_keys=True))


if __name__ == "__main__":
    main()
