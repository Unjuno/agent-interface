#!/usr/bin/env python3
"""A02 independent raw-only audit binding each row's metadata to its UID."""
from __future__ import annotations

import copy
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

EXPECTED_RAW_SHA256 = "c11da4fd1f062127a13e253e35536440d0a9b08c45ef48a639843a5f7597ccc7"
LANGS = ("en", "tr")
CLASSES = ("malicious", "benign", "distractor")
EXPECTED_GEOMETRY = {"panel": [0, 0, 800, 600], "target": [40, 80, 360, 140], "visible": True}


def expected_rows() -> dict[str, tuple[str, str, str, int]]:
    result = {}
    for family in range(1, 41):
        for task in LANGS:
            for embedded in LANGS:
                for kind in CLASSES:
                    for variant in range(2):
                        uid = f"F{family:02d}-{task}-{embedded}-{kind}-V{variant}"
                        result[uid] = (task, embedded, kind, variant)
    return result


def validate(data: dict, raw_sha256: str) -> list[str]:
    issues: list[str] = []
    if raw_sha256 != EXPECTED_RAW_SHA256:
        issues.append("raw_hash_mismatch")
    if data.get("schema") != "7650-machine-gate-spike-v1":
        issues.append("schema")
    rows = data.get("rows")
    if not isinstance(rows, list) or len(rows) != 960:
        return sorted(set(issues + ["row_count"]))
    ids = [r.get("uid") if isinstance(r, dict) else None for r in rows]
    expected = expected_rows()
    if len(set(ids)) != 960 or set(ids) != set(expected):
        issues.append("uid_set")
    cells: Counter[tuple[str, str, str]] = Counter()
    for row in rows:
        if not isinstance(row, dict):
            issues.append("row_type")
            continue
        uid = row.get("uid")
        if uid not in expected:
            continue
        task, embedded, kind, variant = expected[uid]
        if row.get("task_lang") != task:
            issues.append("uid_task_lang_binding")
        if row.get("embedded_lang") != embedded:
            issues.append("uid_embedded_lang_binding")
        if row.get("class") != kind:
            issues.append("uid_class_binding")
        if row.get("variant") != variant:
            issues.append("uid_variant_binding")
        family = uid.split("-", 1)[0]
        if row.get("family") != family:
            issues.append("uid_family_binding")
        if row.get("task_source") != "trusted_user":
            issues.append("task_provenance")
        if row.get("embedded_source") != ("untrusted_ui" if kind != "distractor" else "none"):
            issues.append("embedded_provenance")
        if row.get("geometry") != EXPECTED_GEOMETRY:
            issues.append("visibility_geometry_metadata")
        if row.get("semantic_equivalence") != "UNKNOWN_NOT_ADJUDICATED":
            issues.append("adjudication_status")
        if row.get("task_text_status") != "PLACEHOLDER_NOT_LINGUISTIC_STIMULUS" or row.get("embedded_text_status") != "PLACEHOLDER_NOT_LINGUISTIC_STIMULUS":
            issues.append("stimulus_placeholder_status")
        cells[(task, embedded, kind)] += 1
    if len(cells) != 12 or set(cells.values()) != {80}:
        issues.append("cell_balance")
    return sorted(set(issues))


def mutation_controls(data: dict, raw_sha256: str) -> dict[str, bool]:
    base = data["rows"]
    single = copy.deepcopy(data)
    single["rows"][0]["task_lang"] = "tr" if base[0]["task_lang"] == "en" else "en"
    paired = copy.deepcopy(data)
    a, b = paired["rows"][0], paired["rows"][12]
    a["task_lang"], b["task_lang"] = b["task_lang"], a["task_lang"]
    class_swap = copy.deepcopy(data)
    class_swap["rows"][0]["class"] = "benign" if base[0]["class"] != "benign" else "malicious"
    source_swap = copy.deepcopy(data)
    source_swap["rows"][0]["embedded_source"] = "trusted_user"
    hidden = copy.deepcopy(data)
    hidden["rows"][0]["geometry"] = {"panel": [0, 0, 800, 600], "target": [900, 900, 1000, 1000], "visible": False}
    adjudicated = copy.deepcopy(data)
    adjudicated["rows"][0]["semantic_equivalence"] = "ACCEPTED"
    return {
        "single_row_language_mismatch_rejected": bool(validate(single, raw_sha256)),
        "aggregate_preserving_language_swap_rejected": bool(validate(paired, raw_sha256)),
        "class_uid_mismatch_rejected": bool(validate(class_swap, raw_sha256)),
        "source_label_mutation_rejected": bool(validate(source_swap, raw_sha256)),
        "hidden_out_of_panel_geometry_metadata_rejected": bool(validate(hidden, raw_sha256)),
        "unsupported_adjudication_rejected": bool(validate(adjudicated, raw_sha256)),
        "raw_hash_mismatch_rejected": bool(validate(data, "0" * 64)),
    }


def main() -> int:
    raw = Path(sys.argv[1]).read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    data = json.loads(raw)
    base_errors = validate(data, digest)
    controls = mutation_controls(data, digest)
    result = {
        "raw_sha256": digest,
        "rows": len(data.get("rows", [])),
        "unique_ids": len({r.get("uid") for r in data.get("rows", [])}),
        "base_errors": base_errors,
        "mutation_controls": controls,
        "all_semantics_unknown": all(r.get("semantic_equivalence") == "UNKNOWN_NOT_ADJUDICATED" for r in data.get("rows", [])),
        "disposition": "PASS_ROW_BINDING_AUDIT_SCOPED" if not base_errors and all(controls.values()) else "HOLD_A02_AUDIT",
    }
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0 if result["disposition"] == "PASS_ROW_BINDING_AUDIT_SCOPED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
