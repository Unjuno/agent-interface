"""Build the deterministic, non-sensitive T0 fixture for Issue #6492."""
from __future__ import annotations

import json
from pathlib import Path


ARMS = (
    "immediate_modal",
    "timing_only",
    "preserved_view",
    "preserved_view_optional_cue",
)

SCENARIOS = (
    ("stable_cue_written", False, False, True, "user", "Finish row 3, then verify total."),
    ("stable_cue_unused", False, False, False, "none", ""),
    ("changed_external_state", True, False, True, "user", "Finish row 3, then verify total."),
    ("urgent_release", False, True, True, "user", "Finish row 3, then verify total."),
    ("simple_no_cue", False, False, False, "none", ""),
    ("duplicate_effect_guard", True, False, True, "user", "Verify whether row 3 was already saved."),
)


def make_fixture() -> dict:
    rows = []
    for scenario, changed, urgent, cue_written, cue_author, cue_text in SCENARIOS:
        for arm in ARMS:
            rows.append(
                {
                    "row_id": f"{scenario}::{arm}",
                    "scenario_id": scenario,
                    "arm": arm,
                    "task": {
                        "task_id": "synthetic-ledger-07",
                        "facts": ["row 3 amount is 12", "row 4 amount is 8"],
                        "pending_step": "Finish row 3, then verify total.",
                        "independent_correct_return_action": "inspect row 3 status before any save",
                        "question_id": "agent-question-01",
                        "question_text": "Should the agent include the optional note?",
                        "answer_choices": ["include", "omit", "defer"],
                        "answer_facts": ["note is optional", "no save is requested by this question"],
                    },
                    "interrupt": {
                        "eligible_deferrable": not urgent,
                        "urgent_release": urgent,
                        "warning_interval_ms": 0,
                        "question_duration_ms": 6000,
                        "question_content_digest": "synthetic-sha256:question-content-v1",
                    },
                    "state": {
                        "changed_while_interrupted": changed,
                        "change_receipt": "fixture-change-01" if changed else None,
                        "duplicate_effect_risk": scenario == "duplicate_effect_guard",
                    },
                    "source_view": {
                        "task_id": "synthetic-ledger-07",
                        "window_id": "synthetic-window-07",
                        "session_id": "synthetic-session-07",
                        "state_version": "v2" if changed else "v1",
                        "visible_locator": "sheet:Ledger!A1:D8",
                        "contains_hidden_content": False,
                    },
                    "cue": {
                        "offer": arm == "preserved_view_optional_cue",
                        "author": cue_author if cue_written else "none",
                        "text": cue_text if cue_written else "",
                    },
                }
            )
    return {"schema": "human-return-resumption-fixture-v1", "rows": rows}


if __name__ == "__main__":
    path = Path(__file__).with_name("fixture.json")
    path.write_text(json.dumps(make_fixture(), sort_keys=True, indent=2) + "\n", encoding="utf-8")
