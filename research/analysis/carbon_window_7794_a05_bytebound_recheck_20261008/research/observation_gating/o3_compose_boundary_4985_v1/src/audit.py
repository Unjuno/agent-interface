from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

EXPECTED_HASHES = {
    "gate.py": "042df7f03687680a0133cfe5ad0a208ec05d5dc27afa7e4e60543560dde9eb1a",
    "source_window_verifier.py": "182292735cd58f19e5d4a0784194f2c9320efd77cbaa5f6cab24e65f66a66545",
    "adapter.py": "aee2508f2bc2cbbad58df06c8fd035fb781b61c2b2d5ad2f20813106a6a4f222",
    "transport.py": "7e14fc38d0c7c93b3cb5c2df179db662395770283390ae7b23fd5b1df4d40eb9",
}
SOURCE_PATHS = {
    "gate.py": "research/observation_gating/o3_relevant_region_successor_v1/gate.py",
    "source_window_verifier.py": "research/observation_gating/o3_relevant_region_3131_v1/source_window_verifier.py",
    "adapter.py": "research/observation_gating/o3_live_receipt_transport_2692_v1/adapter.py",
    "transport.py": "research/observation_gating/o3_live_receipt_transport_2692_v1/transport.py",
}
CASES = [
    ("same_int", 2097155, 2097155, True, True, True, "admitted"),
    ("same_string", "2097155", "2097155", True, True, True, "admitted"),
    ("mixed_int_receipt_string_trusted", 2097155, "2097155", True, True, False, "source_window_mismatch"),
    ("mixed_string_receipt_int_trusted", "2097155", 2097155, True, True, False, "source_window_mismatch"),
    ("unequal_int", 2097155, 2097156, False, False, False, "source_window_mismatch;gate:source_window_mismatch"),
    ("unequal_string", "2097155", "02097155", False, False, False, "source_window_mismatch;gate:source_window_mismatch"),
    ("bool_equals_int", True, 1, False, False, False, "gate:source_window_mismatch"),
    ("float_equals_int", 1.0, 1, False, False, False, "gate:source_window_mismatch"),
]

def check(data, src):
    errors = []
    if data.get("schema") != "o3-compose-boundary-4985-raw-v1" or data.get("issue") != 4985:
        errors.append("schema_or_issue")
    if data.get("main_commit") != "7d1208cf323408897983ef2b5c75fd34f54d6815":
        errors.append("main_commit")
    if data.get("source_hashes") != EXPECTED_HASHES:
        errors.append("source_hashes_payload")
    for name, rel in SOURCE_PATHS.items():
        try:
            actual = hashlib.sha256((src / rel).read_bytes()).hexdigest()
        except OSError:
            actual = None
        if actual != EXPECTED_HASHES[name]:
            errors.append("source_file:" + name)
    rows = data.get("rows")
    if not isinstance(rows, list) or len(rows) != len(CASES):
        errors.append("row_count")
        return errors
    for expected, row in zip(CASES, rows):
        case_id, receipt_xid, trusted_xid, gate_ok, verifier_ok, adapter_ok, adapter_reason = expected
        if row.get("case_id") != case_id or row.get("receipt_xid") != receipt_xid or type(row.get("receipt_xid")) is not type(receipt_xid):
            errors.append("case_identity:" + case_id)
        if row.get("trusted_xid") != trusted_xid or type(row.get("trusted_xid")) is not type(trusted_xid):
            errors.append("trusted_identity:" + case_id)
        gate = row.get("direct_gate", {})
        verifier = row.get("source_verifier", {})
        adapter = row.get("adapter", {})
        if gate.get("admitted") is not gate_ok:
            errors.append("gate_decision:" + case_id)
        if gate.get("reason") != ("admitted" if gate_ok else "source_window_mismatch"):
            errors.append("gate_reason:" + case_id)
        if verifier.get("admitted") is not verifier_ok:
            errors.append("verifier_decision:" + case_id)
        if verifier.get("reason") != ("source_window_bound" if verifier_ok else "source_window_mismatch"):
            errors.append("verifier_reason:" + case_id)
        if adapter.get("admitted") is not adapter_ok or adapter.get("action_emissions") != 0:
            errors.append("adapter_decision_or_emission:" + case_id)
        if adapter.get("reason") != adapter_reason:
            errors.append("adapter_reason:" + case_id)
        if adapter.get("model_escalation_eligible") is not (not adapter_ok):
            errors.append("escalation:" + case_id)
    if data.get("action_emissions_total") != 0 or data.get("gui_calls") != 0 or data.get("model_calls") != 0 or data.get("authority_grants") != 0:
        errors.append("side_effect_counts")
    if data.get("interpretation") != "HOLD_CALLER_TYPE_CONTRACT":
        errors.append("interpretation")
    return errors

def main(raw_path, src):
    data = json.loads(Path(raw_path).read_text(encoding="utf-8"))
    errors = check(data, Path(src))
    probes = []
    mutations = [
        lambda x: x["rows"].pop(),
        lambda x: x["rows"][2]["adapter"].update(admitted=True),
        lambda x: x["rows"][2]["adapter"].update(reason="admitted"),
        lambda x: x["source_hashes"].update(adapter="0" * 64),
        lambda x: x.update(action_emissions_total=1),
    ]
    for mutate in mutations:
        changed = json.loads(json.dumps(data))
        mutate(changed)
        probes.append(bool(check(changed, Path(src))))
    summary = {"audit": "PASS_COMPOSITION_BOUNDARY_SCOPED" if not errors and all(probes) else "FAIL_AUDIT",
               "rows": len(data.get("rows", [])), "errors": errors,
               "mutation_controls_rejected": sum(probes), "mutation_controls_total": len(probes)}
    print(json.dumps(summary, sort_keys=True))
    if summary["audit"] != "PASS_COMPOSITION_BOUNDARY_SCOPED":
        raise SystemExit(1)

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
