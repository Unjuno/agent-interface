#!/usr/bin/env python3
"""Independent raw-only reconstruction and seeded corruption checks."""
from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

LANGS = ("en", "tr")
CLASSES = ("malicious", "benign", "distractor")
EXPECTED_GEOMETRY = {"panel": [0, 0, 800, 600], "target": [40, 80, 360, 140], "visible": True}


def expected_uid_set() -> set[str]:
    return {
        f"F{family:02d}-{task}-{embedded}-{kind}-V{variant}"
        for family in range(1, 41)
        for task in LANGS
        for embedded in LANGS
        for kind in CLASSES
        for variant in range(2)
    }


def errors(rows: list[dict]) -> list[str]:
    issues = []
    ids = [r.get("uid") for r in rows]
    if len(rows) != 960 or len(set(ids)) != 960 or set(ids) != expected_uid_set():
        issues.append("row_identity_or_coverage")
    for row in rows:
        if row.get("task_source") != "trusted_user":
            issues.append("task_provenance")
        expected_source = "untrusted_ui" if row.get("class") != "distractor" else "none"
        if row.get("embedded_source") != expected_source:
            issues.append("embedded_provenance")
        if row.get("task_lang") not in LANGS or row.get("embedded_lang") not in LANGS:
            issues.append("language_cell")
        geo = row.get("geometry")
        if geo != EXPECTED_GEOMETRY:
            issues.append("visibility_geometry")
        if row.get("semantic_equivalence") != "UNKNOWN_NOT_ADJUDICATED":
            issues.append("adjudication_status")
        if row.get("task_text_status") != "PLACEHOLDER_NOT_LINGUISTIC_STIMULUS" or row.get("embedded_text_status") != "PLACEHOLDER_NOT_LINGUISTIC_STIMULUS":
            issues.append("stimulus_status")
    return sorted(set(issues))


def main() -> int:
    raw = Path(sys.argv[1]).read_bytes()
    data = json.loads(raw)
    rows = data["rows"]
    base_errors = errors(rows)
    provenance_mutant = json.loads(json.dumps(rows))
    provenance_mutant[0]["embedded_source"] = "trusted_user"
    hidden_mutant = json.loads(json.dumps(rows))
    hidden_mutant[0]["geometry"]["visible"] = False
    hidden_mutant[0]["geometry"]["target"] = [900, 900, 1000, 1000]
    mutation_results = {
        "provenance_swap_rejected": bool(errors(provenance_mutant)),
        "hidden_target_rejected": bool(errors(hidden_mutant)),
    }
    coverage = Counter((r["task_lang"], r["embedded_lang"], r["class"]) for r in rows)
    result = {
        "raw_sha256": hashlib.sha256(raw).hexdigest(),
        "rows": len(rows),
        "unique_ids": len({r.get("uid") for r in rows}),
        "cells": {"|".join(k): v for k, v in sorted(coverage.items())},
        "base_errors": base_errors,
        "mutations": mutation_results,
        "all_semantics_unknown": all(r.get("semantic_equivalence") == "UNKNOWN_NOT_ADJUDICATED" for r in rows),
        "disposition": "PASS_MACHINE_GATE_SCOPED" if not base_errors and all(mutation_results.values()) else "HOLD_MACHINE_GATE",
    }
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0 if result["disposition"] == "PASS_MACHINE_GATE_SCOPED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
