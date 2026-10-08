"""Raw-only independent reconstruction; does not import candidate.py."""
from __future__ import annotations

import copy
import json
import sys
from decimal import Decimal, ROUND_HALF_EVEN, ROUND_HALF_UP
from pathlib import Path


ROUND = {"HALF_EVEN": ROUND_HALF_EVEN, "HALF_UP": ROUND_HALF_UP}


def _state(event, definitions, default_kind):
    app = event["app"]
    entered = event["entry"]
    if app["save"] is False:
        old = app["prior"]
        return (old["value"], old["unit"], old["dimension"], old["quantity_kind"],
                app["effect_count"], app["save_id"], True, True)
    definition = definitions.get(entered["unit_at_save"])
    if definition is None:
        return (entered["number"], entered["unit_at_save"], "unknown",
                app.get("quantity_kind", event["intent"].get("quantity_kind", default_kind)),
                app["effect_count"], app["save_id"], False, False)
    exact = Decimal(entered["number"]) * Decimal(definition["factor"])
    mode = app.get("rounding_mode")
    places = app.get("decimal_places")
    acceptable = mode is None or mode in ROUND
    if places is not None and acceptable:
        step = Decimal("1").scaleb(-places)
        exact = exact.quantize(step, rounding=ROUND[mode])
    kind = app.get("quantity_kind", event["intent"].get("quantity_kind", default_kind))
    return (str(exact) if acceptable else None, definition["canonical"],
            definition["dimension"], kind, app["effect_count"], app["save_id"], True, acceptable)


def _verdict(event, persisted, definitions, required_count, default_kind):
    if event["app"]["save"] is False:
        return "NO_EFFECT"
    if persisted[4] != required_count:
        return "WRONG_EFFECT_COUNT"
    if persisted[6] is False:
        return "UNKNOWN_CONVERSION"
    if persisted[7] is False:
        return "UNKNOWN_ROUNDING"
    if persisted[3] != event["intent"].get("quantity_kind", default_kind):
        return "WRONG_KIND"
    intended_unit = definitions.get(event["intent"]["unit"])
    if intended_unit is None:
        return "UNKNOWN_CONVERSION"
    if persisted[2] != intended_unit["dimension"]:
        return "WRONG_DIMENSION"
    expected = Decimal(event["intent"]["value"]) * Decimal(intended_unit["factor"])
    actual = Decimal(persisted[0])
    gap = abs(expected - actual)
    return "PASS" if gap <= Decimal(event["intent"]["tolerance"]) else "WRONG_MAGNITUDE"


def replay(fixture):
    contract = fixture["contract"]
    definitions = fixture["units"]
    reconstructed = []
    for event in fixture["cases"]:
        (value, unit, dimension, kind, count, effect_id,
         conversion_ok, rounding_ok) = _state(event, definitions, contract["quantity_kind"])
        reconstructed.append({
            "case_id": event["id"],
            "target_id": contract["target_id"],
            "bare_number_pass": Decimal(event["entry"]["number"]) == Decimal(event["intent"]["value"]),
            "typed_status": _verdict(
                event,
                (value, unit, dimension, kind, count, effect_id, conversion_ok, rounding_ok),
                definitions,
                contract["required_effect_count"],
                contract["quantity_kind"],
            ),
            "persisted_value": value,
            "persisted_unit": unit,
            "persisted_dimension": dimension,
            "persisted_kind": kind,
            "effect_count": count,
            "effect_id": effect_id,
            "conversion_known": conversion_ok,
            "rounding_known": rounding_ok,
        })
    return reconstructed


def audit(raw, fixture):
    expected = replay(fixture)
    errors = []
    if raw != expected:
        errors.append("raw-rows-do-not-match-independent-reconstruction")
    if len(expected) != 11 or len({row["case_id"] for row in raw}) != len(raw):
        errors.append("case-denominator-or-identity-mismatch")
    typed_passes = sum(row["typed_status"] == "PASS" for row in raw)
    false_positives = sum(
        row["bare_number_pass"] and row["typed_status"] != "PASS" for row in raw
    )
    if typed_passes != 2:
        errors.append("typed-pass-count-mismatch")
    if false_positives != 6:
        errors.append("bare-number-false-positive-count-mismatch")
    return {
        "errors": errors,
        "case_count": len(expected),
        "typed_passes": typed_passes,
        "bare_number_false_positives": false_positives,
        "status_counts": {
            label: sum(row["typed_status"] == label for row in raw)
            for label in sorted({row["typed_status"] for row in expected})
        },
    }


def corrupt(raw, field):
    result = copy.deepcopy(raw)
    row = result[0]
    if field == "case_id":
        row["case_id"] += "-mutated"
    elif field == "bare_number_pass":
        row[field] = not row[field]
    elif field == "typed_status":
        row[field] = "MUTATED"
    elif field == "persisted_value":
        row[field] = "999"
    elif field == "persisted_unit":
        row[field] = "kg"
    elif field == "persisted_dimension":
        row[field] = "mass"
    elif field == "persisted_kind":
        row[field] = "MUTATED"
    elif field == "effect_count":
        row[field] += 1
    elif field == "effect_id":
        row[field] = "mutated-effect"
    else:
        raise ValueError(field)
    return result


def main():
    if len(sys.argv) != 3:
        raise SystemExit("usage: auditor.py FIXTURE.json RAW.json")
    fixture = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    raw = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
    report = audit(raw, fixture)
    print(json.dumps(report, sort_keys=True, separators=(",", ":")))
    raise SystemExit(0 if not report["errors"] else 1)


if __name__ == "__main__":
    main()
