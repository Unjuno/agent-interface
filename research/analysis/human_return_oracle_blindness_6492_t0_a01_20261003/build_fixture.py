#!/usr/bin/env python3
"""Build the public candidate fixture and separate auditor-only truth file."""

import argparse
import json
from pathlib import Path


SCHEMA = "human-return-oracle-blindness-fixture-v1"


def public_view(checkpoint, **overrides):
    row = {
        "view": {"window": "task-board", "visible_checkpoint": checkpoint},
        "cue": None,
        "current_epoch": 4,
        "view_epoch": 4,
        "window_matches_task": True,
        "emergency_release_required": False,
    }
    row.update(overrides)
    return row


def build():
    rows = []
    truth_rows = []
    pairs = []

    for pair_number, checkpoint in enumerate(("row-blue", "row-green", "row-amber", "row-violet")):
        first = len(rows)
        rows.extend([public_view(checkpoint), public_view(checkpoint)])
        pairs.append({"pair_id": f"eq-{pair_number + 1}", "ordinals": [first, first + 1]})
        truth_rows.extend(
            [
                {
                    "ordinal": first,
                    "case_role": "observational_equivalence",
                    "pair_id": f"eq-{pair_number + 1}",
                    "correct_return_label": f"task-{pair_number + 1}-step-left",
                },
                {
                    "ordinal": first + 1,
                    "case_role": "observational_equivalence",
                    "pair_id": f"eq-{pair_number + 1}",
                    "correct_return_label": f"task-{pair_number + 1}-step-right",
                },
            ]
        )

    controls = [
        (
            public_view(
                "row-blue",
                cue={"text": "Resume at the blue row", "origin": "USER", "epoch": 4},
            ),
            "valid_fresh_user_cue",
            "user-cued-step",
        ),
        (
            public_view(
                "row-blue",
                cue={"text": "Old cue before the edit", "origin": "USER", "epoch": 4},
                current_epoch=5,
                view_epoch=4,
                external_app_change=True,
            ),
            "stale_user_cue_after_external_change",
            "post-edit-step",
        ),
        (
            public_view(
                "row-blue",
                cue={"text": "Agent guessed this step", "origin": "AGENT", "epoch": 4},
            ),
            "agent_authored_cue",
            "agent-guess-step",
        ),
        (
            public_view("row-blue", window_matches_task=False),
            "wrong_window_view",
            "other-window-step",
        ),
        (
            public_view("row-blue", cue_offer_accepted=True),
            "offered_but_unused_cue",
            "unwritten-cue-step",
        ),
        (
            public_view("row-blue", emergency_release_required=True),
            "emergency_release_obligation",
            "release-before-return",
        ),
    ]

    for public, role, correct_label in controls:
        ordinal = len(rows)
        rows.append(public)
        truth_rows.append(
            {
                "ordinal": ordinal,
                "case_role": role,
                "correct_return_label": correct_label,
            }
        )

    public_document = {"schema": SCHEMA, "rows": rows}
    truth_document = {
        "schema": SCHEMA,
        "rows": truth_rows,
        "equivalence_pairs": pairs,
    }
    return public_document, truth_document


def write_json(path, document):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(document, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", required=True)
    args = parser.parse_args()
    root = Path(args.output_root)
    if root.exists() and any(root.iterdir()):
        raise FileExistsError(f"refusing to overwrite nonempty fixture root: {root}")

    public_document, truth_document = build()
    write_json(root / "candidate-input" / "public.json", public_document)
    write_json(root / "auditor-input" / "truth.json", truth_document)


if __name__ == "__main__":
    main()
