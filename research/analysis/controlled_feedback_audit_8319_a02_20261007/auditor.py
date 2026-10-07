"""Independent raw-only audit for the retained Issue #8319 A01 record.

This module is implemented from the written factorial protocol. It imports no
candidate or auditor module and never writes to the input artifact.
"""
from __future__ import annotations

import copy
import hashlib
import json
import sys
from pathlib import Path

EXPECTED_INPUT_SHA256 = "ecffd8121a289d3533c94373c8f7aba50d9c349ffd5db534e46db16522897e9d"
EXPECTED_ROWS = 400
PATCHES = tuple([*(f"case:{slot}" for slot in range(8)), *(f"stratum:{band}" for band in range(4))])
MODES = ("FULL", "CONTROLLED")
RULES = ("CASE_PATCH", "STRATUM_PATCH")


def _cases(seed: int, cohort: str) -> list[tuple[str, int, bool]]:
    marker = "F" if cohort == "fresh" else "D"
    return [
        (f"{marker}{seed:03d}-{slot:02d}", (seed + slot) % 4,
         (seed + 3 * slot) % 5 not in (0, 1))
        for slot in range(32)
    ]


def _applies(case: tuple[str, int, bool], patch: str) -> bool:
    identity, band, _base = case
    kind, value = patch.split(":", 1)
    if kind == "case":
        return identity.startswith("D") and int(identity.rsplit("-", 1)[1]) == int(value)
    return band == int(value)


def _correct_count(cases: list[tuple[str, int, bool]], chosen: list[str]) -> int:
    return sum(base or any(_applies(case, patch) for patch in chosen)
               for case in cases for identity, band, base in [case])


def _response(mode: str, cases: list[tuple[str, int, bool]], chosen: list[str]) -> dict:
    wrong = [(identity, band) for identity, band, base in cases
             if not base and not any(_applies((identity, band, base), patch) for patch in chosen)]
    record = {"kind": mode, "aggregate_correct": len(cases) - len(wrong),
              "aggregate_total": len(cases)}
    if mode == "FULL":
        record["error_ids"] = [identity for identity, _ in wrong]
        record["error_by_stratum"] = {
            str(band): sum(found_band == band for _, found_band in wrong)
            for band in range(4)
        }
    else:
        record["improvement_over_previous"] = None
        record["threshold_met"] = False
    return record


def _next_patch(rule: str, feedback: dict, chosen: list[str], round_no: int) -> str:
    remaining = [patch for patch in PATCHES if patch not in chosen]
    if rule == "CASE_PATCH":
        preferred = [f"case:{int(identity.rsplit('-', 1)[1])}"
                     for identity in feedback.get("error_ids", [])]
    else:
        counts = feedback.get("error_by_stratum", {})
        preferred = [f"stratum:{band}" for band in sorted(
            range(4), key=lambda band: (-int(counts.get(str(band), 0)), band))]
    rotation = list(PATCHES[round_no:]) + list(PATCHES[:round_no])
    return next(patch for patch in preferred + rotation if patch in remaining)


def _expected(seed: int, mode: str, rule: str) -> dict:
    development = _cases(seed, "development")
    fresh = _cases(seed, "fresh")
    chosen: list[str] = []
    trace: list[dict] = []
    previous = _correct_count(development, chosen)
    feedback = _response(mode, development, chosen)
    starting_feedback = copy.deepcopy(feedback)

    for round_no in range(4):
        if round_no == 2:
            trace.append({"round": round_no, "proposal": "safety_regression",
                          "safety_event": True, "disclosed_exactly": True,
                          "veto": True, "fresh_read": False})
            continue
        patch = _next_patch(rule, feedback, chosen, round_no)
        chosen.append(patch)
        updated = _correct_count(development, chosen)
        disclosure = _response(mode, development, chosen)
        if mode == "CONTROLLED":
            disclosure["improvement_over_previous"] = updated - previous
            disclosure["threshold_met"] = updated - previous >= 1
            disclosure.pop("error_ids", None)
            disclosure.pop("error_by_stratum", None)
        previous, feedback = updated, disclosure
        trace.append({"round": round_no, "proposal": patch, "feedback": disclosure,
                      "safety_event": False, "veto": False, "fresh_read": False})

    dev_correct = _correct_count(development, chosen)
    fresh_correct = _correct_count(fresh, chosen)
    return {
        "seed": seed, "feedback": mode, "updater": rule, "query_count": 5,
        "patches": chosen, "trace": trace,
        "candidate_locked_before_fresh": True,
        "initial_feedback": starting_feedback,
        "dev_correct": dev_correct, "dev_total": len(development),
        "fresh_correct": fresh_correct, "fresh_total": len(fresh),
        "optimism": dev_correct / len(development) - fresh_correct / len(fresh),
        "safety_veto_count": sum(int(item["veto"]) for item in trace),
        "raw_released_after_lock": True,
    }


def reconstruct(rows: list[dict]) -> list[str]:
    expected_keys = [(seed, mode, rule) for seed in range(100)
                     for mode in MODES for rule in RULES]
    if not isinstance(rows, list) or len(rows) != EXPECTED_ROWS:
        return [f"row_count:{len(rows) if isinstance(rows, list) else 'non-list'}!={EXPECTED_ROWS}"]
    mismatches = []
    for index, (seed, mode, rule) in enumerate(expected_keys):
        if rows[index] != _expected(seed, mode, rule):
            mismatches.append(f"row_{index}_does_not_match_protocol")
    return mismatches


def _mutated(rows: list[dict]) -> list[tuple[str, list[dict]]]:
    probes: list[tuple[str, list[dict]]] = []
    def alter(name: str, edit) -> None:
        changed = copy.deepcopy(rows)
        edit(changed[0])
        probes.append((name, changed))
    alter("feedback_swap", lambda row: row.__setitem__("feedback", "CONTROLLED"))
    alter("updater_identity", lambda row: row.__setitem__("updater", "STRATUM_PATCH"))
    alter("fresh_before_lock", lambda row: row.__setitem__("candidate_locked_before_fresh", False))
    alter("omitted_safety_disclosure",
          lambda row: row["trace"][2].__setitem__("disclosed_exactly", False))
    alter("changed_fresh_marginal", lambda row: row.__setitem__("fresh_total", row["fresh_total"] - 1))
    alter("forged_response", lambda row: row["trace"][0]["feedback"].__setitem__("aggregate_correct", -1))
    return probes


def undetected_mutations(rows: list[dict]) -> list[str]:
    return [name for name, changed in _mutated(rows) if not reconstruct(changed)]


def gate_status(row_count: int, errors: list[str], undetected: list[str]) -> str:
    """Return PASS only when every reconstruction and negative control passes."""
    if row_count == EXPECTED_ROWS and not errors and not undetected:
        return "PASS"
    return "FAIL"


def audit(input_path: Path, output_path: Path) -> int:
    input_hash = hashlib.sha256(input_path.read_bytes()).hexdigest()
    errors: list[str] = []
    rows: object = None
    if input_hash != EXPECTED_INPUT_SHA256:
        errors.append("input_sha256_mismatch")
    try:
        rows = json.loads(input_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        errors.append(f"input_parse_error:{type(exc).__name__}")
    if isinstance(rows, list):
        errors.extend(reconstruct(rows))
        undetected = undetected_mutations(rows) if len(rows) == EXPECTED_ROWS else ["mutation_controls_not_run"]
    else:
        undetected = ["mutation_controls_not_run"]
    row_count = len(rows) if isinstance(rows, list) else 0
    status = gate_status(row_count, errors, undetected)
    record = {
        "status": status,
        "input_sha256": input_hash,
        "rows_observed": row_count,
        "rows_reconstructed": EXPECTED_ROWS if row_count == EXPECTED_ROWS and not errors else 0,
        "reconstruction_errors": errors,
        "mutation_controls": len(_mutated(rows)) if isinstance(rows, list) and row_count == EXPECTED_ROWS else 6,
        "mutations_rejected": 6 - len(undetected),
        "mutations_not_rejected": undetected,
        "gate_contract": "PASS iff 400 rows, zero reconstruction errors, and zero undetected mutations",
    }
    output_path.write_text(json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n",
                           encoding="utf-8")
    return 0 if status == "PASS" else 1


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print("usage: auditor.py IMMUTABLE_RAW.json AUDIT.json", file=sys.stderr)
        return 2
    return audit(Path(argv[1]), Path(argv[2]))


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
