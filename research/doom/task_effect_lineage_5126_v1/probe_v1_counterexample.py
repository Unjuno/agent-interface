"""Recheck the known #5126 whitespace-lineage mutant without touching v1 files."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
V1 = ROOT / "research" / "doom" / "map01_task_effect_contract_1839_v1"


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    result_path = V1 / "result.json"
    result = json.loads(result_path.read_text(encoding="utf-8"))
    row = next(r for r in result["cases"] if r["case_id"] == "positive_bound_effect")
    raw = copy.deepcopy(row["raw"])
    raw["session_id"] = raw["plan_id"] = raw["actuation_id"] = " "
    physical = raw["physical"]
    physical["owner_id"] = " "
    for edge in (physical["down"], physical["up"]):
        edge["session_id"] = edge["plan_id"] = edge["actuation_id"] = " "
        edge["owner_id"] = " "
    for effect in raw["task_effects"]:
        effect["session_id"] = effect["plan_id"] = effect["actuation_id"] = " "
        effect["effect_id"] = " "

    candidate = load("lineage_v1_candidate", V1 / "contract.py")
    oracle = load("lineage_v1_oracle", V1 / "oracle.py")
    auditor = load("lineage_v1_auditor", V1 / "audit.py")
    candidate_out = candidate.classify(raw)
    oracle_out = oracle.oracle(raw)

    mutated = copy.deepcopy(result)
    for case in mutated["cases"]:
        case["raw"] = copy.deepcopy(raw)
        case["candidate"] = candidate.classify(raw)
        case["oracle"] = oracle.oracle(raw)
        case["expected_task_effect"] = case["candidate"]["task_effect"]
    with tempfile.TemporaryDirectory(prefix="issue5126-v1-mutant-") as temp:
        path = Path(temp) / "mutated.json"
        path.write_text(json.dumps(mutated), encoding="utf-8")
        audit_out = auditor.audit(path)

    schema_keys = {
        "physical_down": sorted(raw["physical"]["down"]),
        "physical_up": sorted(raw["physical"]["up"]),
        "task_effect": sorted(raw["task_effects"][0]),
    }
    out = {
        "schema": "issue5126-v1-counterexample-recheck-v1",
        "current_main": "611962d32477f8a86096431227a819418ceef994",
        "mutated_result_sha256": sha(result_path),
        "candidate": candidate_out,
        "oracle": oracle_out,
        "audit": audit_out,
        "schema_keys": schema_keys,
        "source_identity_fields_present": {
            "physical_edges": any(k in schema_keys["physical_down"] for k in
                                   ("event_id", "event_sequence", "source_event_ref")),
            "task_effect": any(k in schema_keys["task_effect"] for k in
                                ("event_id", "event_sequence", "source_event_ref")),
        },
    }
    print(json.dumps(out, sort_keys=True, indent=2))
    return 0 if (candidate_out == oracle_out
                 and candidate_out["physical_actuation"] == "PHYSICAL_ACTUATION_SCOPED"
                 and candidate_out["task_effect"] == "TASK_EFFECT_SCOPED"
                 and audit_out["status"] == "PASS_MAP01_TASK_EFFECT_CONTRACT_SCOPED"
                 and not audit_out["errors"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
