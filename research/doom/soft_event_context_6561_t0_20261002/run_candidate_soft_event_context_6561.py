"""Run the finite Issue #6561 construction fixture once to a new raw packet."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import research_soft_event_context_6561 as target


def build_packet() -> dict:
    binding, rows, _fixture_binding = target.fixture()
    cases = []
    for case_id, state, count, event, current_sequence, _want, raw_events in rows:
        context = target.candidate_context(
            state, count, event, current_sequence, binding)
        cases.append({
            "case_id": case_id,
            "history_state": state,
            "current_sequence": current_sequence,
            "binding": binding,
            "raw_events": raw_events,
            "context": context,
            "prompt": target.render_prompt_context(context),
        })
    return {"cases": cases}


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: run_candidate_soft_event_context_6561.py NEW_RAW_PACKET.json", file=sys.stderr)
        return 2
    output = Path(argv[1])
    if output.exists():
        print("STOP_OUTPUT_ALREADY_EXISTS", file=sys.stderr)
        return 2
    try:
        packet = build_packet()
        output.write_text(json.dumps(packet, sort_keys=True, separators=(",", ":")) + "\n",
                          encoding="utf-8")
    except (OSError, ValueError, TypeError) as exc:
        print(f"FAIL_CANDIDATE: {exc}", file=sys.stderr)
        return 1
    print("CANDIDATE_CONSTRUCTION_COMPLETE cases=6")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
