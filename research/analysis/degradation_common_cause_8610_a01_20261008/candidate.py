"""Candidate degradation-mode enumerator; it never dispatches task actions."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def service_state(spec: dict, case: dict) -> dict[str, bool]:
    failed = set(case["failed_dependencies"])
    corrupted = set(case["corrupted_dependencies"])
    return {
        service: not bool(set(dependencies) & (failed | corrupted))
        for service, dependencies in spec["components"].items()
    }


def evidence_current(case: dict, operation: dict) -> bool:
    return all(case["evidence"].get(name) is True for name in operation["evidence"])


def contract_rows(spec: dict, case: dict, services: dict[str, bool]) -> list[dict]:
    rows = []
    for operation in spec["operations"]:
        if all(services.get(name, False) for name in operation["requires"]) and evidence_current(case, operation):
            rows.append({
                "operation": operation["id"],
                "source": operation["source"],
                "claim": operation["claim"],
                "freshness": "CURRENT",
            })
    return rows


def evaluate(spec: dict) -> dict:
    cases = []
    for case in spec["scenarios"]:
        services = service_state(spec, case)
        contract = contract_rows(spec, case, services)
        binary_ready = all(services.get(name, False) for name in spec["binary_full_route"])
        binary_ready = binary_ready and all(value is True for value in case["evidence"].values())
        silent = list(contract)
        raw_inspection_available = (
            services.get("raw_observation", False)
            and services.get("authority", False)
            and services.get("release", False)
            and case["evidence"].get("raw_fresh") is True
            and case["evidence"].get("raw_intact") is True
        )
        semantic_operation_available = any(row["operation"] == "present_semantics" for row in contract)
        if raw_inspection_available and not semantic_operation_available:
            silent.append({
                "operation": "present_semantics",
                "source": "raw_observation",
                "claim": "SEMANTIC_VERIFIED",
                "freshness": "CURRENT",
            })
        cases.append({
            "case_id": case["id"],
            "binary": contract if binary_ready else [],
            "contract": contract,
            "silent_substitution": silent,
            "release_obligation": "MANDATORY_RELEASE",
        })
    return {"schema": "8610-candidate-v1", "cases": cases}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    spec = json.loads(Path(args.spec).read_text(encoding="utf-8"))
    result = evaluate(spec)
    with Path(args.output).open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(result, handle, ensure_ascii=False, sort_keys=True, indent=2)
        handle.write("\n")
    print(f"CANDIDATE_COMPLETE cases={len(result['cases'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
