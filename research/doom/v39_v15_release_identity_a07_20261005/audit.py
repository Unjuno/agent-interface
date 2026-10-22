"""Independent audit of one-to-one admission/release identity binding."""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any


IDENTITY_FIELDS = ("id", "intent_token", "owner_id", "step", "key")


def _identity(row: dict[str, Any]) -> tuple[Any, ...] | None:
    values = tuple(row.get(field) for field in IDENTITY_FIELDS)
    if not (
        all(isinstance(values[i], str) and values[i] for i in (0, 1, 2, 4))
        and isinstance(values[3], int)
        and not isinstance(values[3], bool)
    ):
        return None
    return values


def evaluate(raw: dict[str, Any]) -> dict[str, Any]:
    case_results = []
    for case_index, case in enumerate(raw.get("cases", [])):
        errors: list[str] = []
        rows = case.get("rows")
        if not isinstance(rows, list):
            rows = []
            errors.append("rows_not_array")
        admissions = [r for r in rows if isinstance(r, dict) and r.get("event") == "input_admission"]
        releases = [r for r in rows if isinstance(r, dict) and r.get("event") == "input_release_transition"]

        admitted_by_identity: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
        for row in admissions:
            identity = _identity(row)
            if identity is None:
                errors.append("admission_identity_invalid")
            else:
                admitted_by_identity[identity].append(row)
        if any(len(matches) != 1 for matches in admitted_by_identity.values()):
            errors.append("admission_identity_not_unique")

        seen_releases: set[tuple[Any, ...]] = set()
        matched_admissions: set[tuple[Any, ...]] = set()
        for row in releases:
            identity = _identity(row)
            if identity is None:
                errors.append("release_identity_invalid")
                continue
            matches = admitted_by_identity.get(identity, [])
            if len(matches) != 1:
                errors.append("release_has_no_unique_matching_admission")
            if identity in seen_releases:
                errors.append("duplicate_release_for_admission")
            seen_releases.add(identity)
            if len(matches) == 1:
                matched_admissions.add(identity)

            receipt = row.get("owner_thread_keyup_receipt")
            if not isinstance(receipt, dict) or any(
                receipt.get(field) != row.get(field)
                for field in ("intent_token", "owner_id", "key")
            ):
                errors.append("release_receipt_identity_mismatch")

        if set(admitted_by_identity) != matched_admissions:
            errors.append("admission_release_pairing_incomplete")
        case_results.append({
            "case_index": case_index,
            "case": case.get("case"),
            "admission_count": len(admissions),
            "release_count": len(releases),
            "matched_count": len(matched_admissions),
            "passed": not errors,
            "errors": errors,
        })

    if not case_results:
        errors = ["no_cases"]
    else:
        errors = []
    passed = bool(case_results) and all(case["passed"] for case in case_results) and not errors
    return {
        "schema": "v39-v15-release-identity-a07-audit-v1",
        "scope": "retained synthetic raw admission-to-release identity only",
        "identity_fields": list(IDENTITY_FIELDS),
        "passed": passed,
        "case_count": len(case_results),
        "cases": case_results,
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    raw = json.loads(Path(args.input).read_text(encoding="utf-8"))
    result = evaluate(raw)
    Path(args.output).write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"passed": result["passed"], "case_count": result["case_count"],
                      "error_count": sum(len(case["errors"]) for case in result["cases"])}, sort_keys=True))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
