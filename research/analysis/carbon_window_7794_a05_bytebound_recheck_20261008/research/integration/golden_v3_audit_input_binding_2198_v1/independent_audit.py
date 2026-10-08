#!/usr/bin/env python3
"""Reconstruct schema/result field evidence from bytes; no candidate-audit imports."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SCHEMA = ROOT / "research/integration/golden_v3_result_schema_2186_v1/schema.json"
REPORT = ROOT / "runtime/results/golden-desktop-app-server-v3-live-01/golden-report.json"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def classify(schema_bytes: bytes, report_bytes: bytes) -> dict:
    schema = json.loads(schema_bytes)
    report = json.loads(report_bytes)
    required = schema["required"]
    properties = schema["properties"]
    classifications = {}
    for name in required:
        if name not in report:
            classification = "ABSENT"
        elif name == "schema" and report[name] != properties[name].get("const"):
            classification = "EMITTED_VALUE_CONTRADICTION"
        else:
            classification = "EMITTED"
        classifications[name] = {
            "classification": classification,
            "actual_value_type": type(report.get(name)).__name__ if name in report else None,
            "required_schema_type": properties.get(name, {}).get("type"),
            "required_schema_const": properties.get(name, {}).get("const"),
            "required_schema_enum": properties.get(name, {}).get("enum"),
        }
    counts = {}
    for item in classifications.values():
        counts[item["classification"]] = counts.get(item["classification"], 0) + 1
    disposition = (
        "HOLD_GOLDEN_V3_SCHEMA_SOURCE_EVIDENCE_INCOMPLETE"
        if any(v["classification"] in {"ABSENT", "EMITTED_VALUE_CONTRADICTION"} for v in classifications.values())
        else "PASS_REQUIRED_FIELD_PRESENCE_ONLY_NOT_SOURCE_RECONCILIATION"
    )
    return {
        "disposition": disposition,
        "required_field_count": len(required),
        "counts": counts,
        "fields": classifications,
    }


def main() -> int:
    schema_bytes = SCHEMA.read_bytes()
    report_bytes = REPORT.read_bytes()
    schema = json.loads(schema_bytes)
    base_report = json.loads(report_bytes)
    schema_with_missing_field = {**schema, "required": [*schema["required"], "injected_field"], "properties": {**schema["properties"], "injected_field": {"type": "boolean"}}}
    prose_only = {"description": "injected_field exists in docs"}
    synthetic_valid = {"schema": "golden-v3-result-v1", "program_completed": True, "task_success": True, "authority_granted": False, "status": "success", "partial_effects": [], "cleanup_error": None, "lifecycle": [], "usage": {}}
    controls = {
        "unaltered": classify(schema_bytes, report_bytes)["disposition"],
        "renamed_field": classify(schema_bytes, json.dumps({k: v for k, v in base_report.items() if k != "usage"} | {"usage_renamed": base_report["usage"]}).encode())["disposition"],
        "prose_only_field_claim": classify(schema_bytes, json.dumps(prose_only).encode())["disposition"],
        "synthetic_schema_v1_report": classify(schema_bytes, json.dumps(synthetic_valid).encode())["disposition"],
        "injected_required_schema_field": classify(json.dumps(schema_with_missing_field).encode(), report_bytes)["disposition"],
        "mutated_schema_identity_value": classify(schema_bytes, json.dumps({**base_report, "schema": "golden-v3-result-v1"}).encode())["disposition"],
    }
    expected = {
        "unaltered": "HOLD_GOLDEN_V3_SCHEMA_SOURCE_EVIDENCE_INCOMPLETE",
        "renamed_field": "HOLD_GOLDEN_V3_SCHEMA_SOURCE_EVIDENCE_INCOMPLETE",
        "prose_only_field_claim": "HOLD_GOLDEN_V3_SCHEMA_SOURCE_EVIDENCE_INCOMPLETE",
        "synthetic_schema_v1_report": "PASS_REQUIRED_FIELD_PRESENCE_ONLY_NOT_SOURCE_RECONCILIATION",
        "injected_required_schema_field": "HOLD_GOLDEN_V3_SCHEMA_SOURCE_EVIDENCE_INCOMPLETE",
        "mutated_schema_identity_value": "HOLD_GOLDEN_V3_SCHEMA_SOURCE_EVIDENCE_INCOMPLETE",
    }
    controls_pass = all(controls[k] == v for k, v in expected.items())
    result = {
        "audit": "independent_raw_json_required_field_reconstruction_v1",
        **classify(schema_bytes, report_bytes),
        "artifact_sha256": {"schema": sha256(schema_bytes), "report": sha256(report_bytes)},
        "corruption_controls": controls,
        "corruption_controls_pass": controls_pass,
        "scope": "JSON required-field presence/value check only; no lineage or source-backed derivation is inferred.",
    }
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0 if controls_pass else 1


if __name__ == "__main__":
    sys.exit(main())
