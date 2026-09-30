#!/usr/bin/env python3
"""Copied-evidence mutations must all be rejected by the independent auditor."""
from __future__ import annotations

import copy
import json
import sys
import tempfile
from pathlib import Path

from audit import audit


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("usage: corruption_test.py dataset-dir predictions.json")
    root, source = Path(sys.argv[1]), Path(sys.argv[2])
    original = json.loads(source.read_text(encoding="utf-8"))
    mutations = {}

    def missing_row(x):
        x["rows"].pop()
    mutations["drop_denominator_row"] = missing_row

    def wrong_positive(x):
        x["rows"][0]["box_xyxy"] = [0, 0, 10, 10]
    mutations["wrong_positive_box"] = wrong_positive

    def guessed_absent(x):
        row = next(r for r in x["rows"] if r["id"] == "case-07-absent")
        row.update(status="PROPOSAL", box_xyxy=[300, 260, 356, 316])
    mutations["guessed_absent_control"] = guessed_absent

    def guessed_ambiguous(x):
        row = next(r for r in x["rows"] if r["id"] == "case-10-ambiguous-multiple")
        row.update(status="PROPOSAL", box_xyxy=[154, 254, 200, 300])
    mutations["guessed_ambiguous_control"] = guessed_ambiguous

    def altered_png_binding(x):
        x["rows"][0]["id"] = "case-12-ambiguous-multiple"
    mutations["altered_input_binding"] = altered_png_binding

    rejected = {}
    with tempfile.TemporaryDirectory() as temp:
        for name, mutate in mutations.items():
            altered = copy.deepcopy(original)
            mutate(altered)
            path = Path(temp) / f"{name}.json"
            path.write_text(json.dumps(altered), encoding="utf-8")
            errors = audit(root, path)["errors"]
            rejected[name] = bool(errors)
            if not errors:
                raise AssertionError(f"corruption accepted: {name}")
    print(json.dumps({"controls": rejected, "passed": sum(rejected.values()), "total": len(rejected)}, indent=2))


if __name__ == "__main__":
    main()
