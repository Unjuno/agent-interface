"""Mutation controls for the Issue #5236 raw-only auditor."""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

from .audit import audit


def mutation_controls(raw: dict, wrapper: dict) -> dict:
    mutations = (
        ("omitted_row", lambda value: value.update(rows=value["rows"][:-1])),
        ("swapped_direction", lambda value: value["rows"].__setitem__(slice(1, 3), value["rows"][2:0:-1])),
        ("wrong_expected_bytes", lambda value: value["rows"][1].update(expected_effect_hex="00")),
        ("missing_actor_receipt", lambda value: value["rows"][1].update(actor_receipt=None)),
        ("missing_post_save_wait", lambda value: value["rows"][1].update(post_save_wait=None)),
        ("changed_raw_output", lambda value: value["rows"][1].update(
            saved_effect_hex="7b227361766564223a20747275652c202274657874223a20226129227d0a")),
    )
    outcomes = []
    for name, mutate in mutations:
        candidate = copy.deepcopy(raw)
        mutate(candidate)
        outcomes.append({"name": name, "decision": audit(candidate, wrapper)["decision"]})
    clean = {"NO_STALE_EFFECT_OBSERVED", "PASS_MIDPROGRAM_REMAP_FAIL_CLOSED"}
    rejected = all(row["decision"] not in clean for row in outcomes)
    return {"all_rejected": rejected, "controls": outcomes}


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) != 2:
        print("usage: corruptions.py RAW.json WRAPPER.json", file=sys.stderr)
        return 2
    try:
        raw = json.loads(Path(args[0]).read_text(encoding="utf-8"))
        wrapper = json.loads(Path(args[1]).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"STOP_CORRUPTION_INPUT: {exc}", file=sys.stderr)
        return 2
    report = mutation_controls(raw, wrapper)
    print(json.dumps(report, sort_keys=True))
    return 0 if report["all_rejected"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

