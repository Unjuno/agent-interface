"""Independent raw-only structural, accounting, and decision auditor."""
from __future__ import annotations

import copy
import hashlib
import json
import sys
from pathlib import Path

ALLOCATION = "typed-mode-4844-successor-20260928-03"
SCHEMA = "typed-mode-4844-successor-raw-v1"
BLOCKS = ("COMPLETE", "SINGLE_MISSING", "MULTI_MISSING", "COMPOSITION_HOLDOUT", "NUISANCE_SHIFT")
PRIMARY = ("SINGLE_MISSING", "MULTI_MISSING", "COMPOSITION_HOLDOUT")
DISPOSITIONS = (0, 0, 1, 2, 2)
NAMES = ("REBIND", "WAIT_OBSERVE", "REOBSERVE")
EXPECTED = {
    "schema": SCHEMA,
    "allocation": ALLOCATION,
    "train_seed": 484431,
    "test_seed": 484432,
    "n_train": 2000,
    "n_test": 4800,
    "alpha": 1.0,
    "threshold": 0.65,
    "flip_p": 0.08,
    "drop_p": 0.20,
    "blocks": list(BLOCKS),
    "primary_blocks": list(PRIMARY),
    "disposition_names": list(NAMES),
}


def _fail(errors: list[str], code: str) -> None:
    errors.append(code)


def _unique_object(pairs: list[tuple[str, object]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate_json_key:" + key)
        result[key] = value
    return result


def _canonical(data: object) -> bytes:
    return (json.dumps(data, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode("utf-8")


def validate(data: object, expected_train_seed: int = 484431, expected_test_seed: int = 484432) -> list[str]:
    errors: list[str] = []
    if type(data) is not dict:
        return ["root_type"]
    expected_values = dict(EXPECTED, train_seed=expected_train_seed, test_seed=expected_test_seed)
    for key, value in expected_values.items():
        if data.get(key) != value or (key in ("train_seed", "test_seed", "n_train", "n_test") and type(data.get(key)) is not int):
            _fail(errors, key)
    rows = data.get("rows")
    if type(rows) is not list or len(rows) != 4800:
        return errors + ["rows_denominator"]
    counts = {block: 0 for block in BLOCKS}
    modes = {block: [0] * 5 for block in BLOCKS}
    totals = {block: {"direct_wrong": 0, "typed_wrong": 0, "direct_covered": 0, "typed_covered": 0, "direct_unsafe": 0, "typed_unsafe": 0} for block in BLOCKS}
    for index, row in enumerate(rows):
        if type(row) is not dict:
            _fail(errors, f"row_type:{index}")
            continue
        block, mode = row.get("block"), row.get("mode")
        if block not in BLOCKS:
            _fail(errors, f"row_block:{index}")
            continue
        if type(mode) is not int or not 0 <= mode < 5:
            _fail(errors, f"row_mode:{index}")
            continue
        truth = row.get("truth")
        if type(truth) is not int or truth != DISPOSITIONS[mode]:
            _fail(errors, f"row_truth:{index}")
        for arm in ("direct", "typed"):
            emitted = row.get(arm)
            if emitted is not None and (type(emitted) is not int or emitted not in (0, 1, 2)):
                _fail(errors, f"row_action:{index}:{arm}")
            wrong = type(emitted) is int and emitted != DISPOSITIONS[mode]
            if row.get(f"{arm}_wrong") is not wrong:
                _fail(errors, f"row_wrong:{index}:{arm}")
            if row.get(f"{arm}_covered") is not (emitted is not None):
                _fail(errors, f"row_coverage:{index}:{arm}")
            unsafe = row.get(f"{arm}_unsafe")
            if type(unsafe) is not bool or unsafe:
                _fail(errors, f"row_unsafe:{index}:{arm}")
            totals[block][f"{arm}_wrong"] += int(wrong)
            totals[block][f"{arm}_covered"] += int(emitted is not None)
            totals[block][f"{arm}_unsafe"] += int(unsafe is True)
        counts[block] += 1
        modes[block][mode] += 1
    for block in BLOCKS:
        if counts[block] != 960 or modes[block] != [192] * 5:
            _fail(errors, f"denominator:{block}")
    summary = data.get("summary")
    if type(summary) is not dict or set(summary) != set(BLOCKS):
        _fail(errors, "summary_keys")
    else:
        for block in BLOCKS:
            item = summary.get(block)
            if type(item) is not dict:
                _fail(errors, f"summary_type:{block}")
                continue
            if item.get("n") != counts[block]:
                _fail(errors, f"summary_n:{block}")
            for arm in ("direct", "typed"):
                if item.get(f"{arm}_wrong") != totals[block][f"{arm}_wrong"]:
                    _fail(errors, f"summary_wrong:{block}:{arm}")
                actual_coverage = totals[block][f"{arm}_covered"] / max(1, counts[block])
                if type(item.get(f"{arm}_coverage")) not in (int, float) or abs(item[f"{arm}_coverage"] - actual_coverage) > 1e-12:
                    _fail(errors, f"summary_coverage:{block}:{arm}")
                if item.get(f"{arm}_unsafe") != totals[block][f"{arm}_unsafe"]:
                    _fail(errors, f"summary_unsafe:{block}:{arm}")
    full = data.get("full_observation")
    if type(full) is not list or len(full) != 5:
        _fail(errors, "full_denominator")
    else:
        for mode, item in enumerate(full):
            if type(item) is not dict or item.get("mode") != mode or item.get("truth") != DISPOSITIONS[mode] or item.get("direct") != DISPOSITIONS[mode] or item.get("typed") != DISPOSITIONS[mode]:
                _fail(errors, f"full_control:{mode}")
    for control in ("unknown", "contradictory"):
        item = data.get(control)
        if type(item) is not dict or item.get("direct") is not None or item.get("typed") is not None:
            _fail(errors, f"control:{control}")
    return errors


def mutation_controls(data: dict, expected_train_seed: int = 484431, expected_test_seed: int = 484432) -> dict[str, bool]:
    cases = {}
    mutations = {
        "allocation": lambda d: d.update(allocation="wrong"),
        "train_seed": lambda d: d.update(train_seed=True),
        "test_seed": lambda d: d.update(test_seed=484402),
        "train_denominator": lambda d: d.update(n_train=1999),
        "test_denominator": lambda d: d.update(n_test=4799),
        "threshold": lambda d: d.update(threshold=0.70),
        "block_denominator": lambda d: d["rows"].pop(),
        "unknown_action": lambda d: d["unknown"].update(direct=0),
        "contradictory_action": lambda d: d["contradictory"].update(typed=2),
        "full_control": lambda d: d["full_observation"][0].update(typed=2),
        "wrong_truth": lambda d: d["rows"][0].update(truth=2),
        "wrong_flag": lambda d: d["rows"][0].update(direct_wrong=not d["rows"][0]["direct_wrong"]),
        "coverage_flag": lambda d: d["rows"][0].update(typed_covered=not d["rows"][0]["typed_covered"]),
        "unsafe_emission": lambda d: d["rows"][0].update(typed_unsafe=True),
        "summary_count": lambda d: d["summary"]["COMPLETE"].update(n=959),
        "summary_coverage": lambda d: d["summary"]["NUISANCE_SHIFT"].update(direct_coverage=2.0),
    }
    for name, mutate in mutations.items():
        candidate = copy.deepcopy(data)
        mutate(candidate)
        cases[name] = bool(validate(candidate, expected_train_seed, expected_test_seed))
    return cases


def audit_bytes(raw: bytes, expected_sha256: str, expected_train_seed: int = 484431, expected_test_seed: int = 484432) -> dict:
    actual_sha = hashlib.sha256(raw).hexdigest()
    if actual_sha != expected_sha256:
        return {"accepted": False, "errors": ["raw_sha256"]}
    try:
        data = json.loads(raw, object_pairs_hook=_unique_object)
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        return {"accepted": False, "errors": ["json:" + str(exc)]}
    if raw != _canonical(data):
        return {"accepted": False, "errors": ["noncanonical_json"]}
    errors = validate(data, expected_train_seed, expected_test_seed)
    controls = mutation_controls(data, expected_train_seed, expected_test_seed) if type(data) is dict and not errors else {}
    if len(controls) != 16 or not all(controls.values()):
        errors.append("mutation_controls")
    summary = data.get("summary", {}) if type(data) is dict else {}
    gates = {}
    if not errors and type(summary) is dict:
        for block in PRIMARY:
            item = summary[block]
            direct_wrong, typed_wrong = item["direct_wrong"], item["typed_wrong"]
            reduction = (direct_wrong - typed_wrong) / direct_wrong if direct_wrong else 0.0
            coverage_loss = item["direct_coverage"] - item["typed_coverage"]
            gates[block] = {"wrong_reduction": reduction, "coverage_loss": coverage_loss, "pass": reduction >= 0.25 and coverage_loss <= 0.05 and item["direct_unsafe"] == 0 and item["typed_unsafe"] == 0}
    if errors:
        decision = "STOP_PROVENANCE_OR_AUDIT"
    elif any(summary[block]["direct_unsafe"] or summary[block]["typed_unsafe"] for block in BLOCKS):
        decision = "FAIL_MODE_MISROUTES_RECOVERY"
    elif any(not gate["pass"] for gate in gates.values()):
        coverage_tradeoff = any(gate["wrong_reduction"] > 0 and gate["coverage_loss"] > 0.05 for gate in gates.values())
        any_benefit = any(gate["wrong_reduction"] >= 0.25 and gate["coverage_loss"] <= 0.05 for gate in gates.values())
        decision = "HOLD_COVERAGE_TRADEOFF" if coverage_tradeoff else ("HOLD_MIXED_PARTIAL_RESULT" if any_benefit else "FAIL_DIAGNOSIS_STILL_REDUNDANT")
    else:
        decision = "PASS_TYPED_MODE_GENERALIZATION_SCOPED"
    return {"accepted": not errors, "errors": errors, "decision": decision, "primary_gates": gates, "raw_sha256": actual_sha, "rows": len(data.get("rows", [])) if type(data) is dict else 0, "mutation_controls": controls}


if __name__ == "__main__":
    raw_path = Path(sys.argv[1])
    receipt_path = Path(sys.argv[2])
    result = audit_bytes(raw_path.read_bytes(), sys.argv[3])
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    print(json.dumps({"accepted": result["accepted"], "errors": result["errors"], "rows": result["rows"], "mutation_controls_rejected": sum(result["mutation_controls"].values())}, sort_keys=True))
    raise SystemExit(0 if result["accepted"] else 2)
