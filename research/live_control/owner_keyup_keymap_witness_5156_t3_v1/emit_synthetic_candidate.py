"""Emit deterministic synthetic raw rows to exercise the file/CLI boundary only."""
import json
import sys
from pathlib import Path

from test_audit_formal_x11 import fixture_rows


def runner_order_rows():
    rows = fixture_rows()

    def select(event, case=None, stage=None, key=None):
        return next(r for r in rows if r.get("event") == event
                    and (case is None or r.get("case") == case)
                    and (stage is None or r.get("stage") == stage)
                    and (key is None or r.get("key") == key))

    ordered = [select("fixture")]
    for case, admits, terminal_stage in (
        ("single_explicit", ["a"], "post_release"),
        ("two_key_explicit", ["a", "b"], "post_release"),
        ("partial_cancel", ["a"], "post_cleanup"),
    ):
        ordered.append(select("keymap_snapshot", case, "pre_down"))
        ordered.extend(select("admission", case, key=key) for key in admits)
        ordered.append(select("keymap_snapshot", case, "post_down"))
        ordered.append(select("keymap_snapshot", case, terminal_stage))
        ordered.append(select("case_terminal", case))
    used = {id(row) for row in ordered}
    ordered.extend(row for row in rows if id(row) not in used)
    return ordered


def main(raw_path):
    records = runner_order_rows()
    Path(raw_path).write_text(
        "".join(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n" for row in records),
        encoding="utf-8")
    print(json.dumps({"status": "SYNTHETIC_CANDIDATE_EXIT_0", "rows": len(records)}))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: emit_synthetic_candidate.py RAW.jsonl")
    main(sys.argv[1])
