"""Model-free typed quantity-effect oracle for the frozen synthetic fixture."""
from __future__ import annotations

import json
import sys
from decimal import Decimal, ROUND_HALF_EVEN, ROUND_HALF_UP
from pathlib import Path


ROUNDING = {"HALF_EVEN": ROUND_HALF_EVEN, "HALF_UP": ROUND_HALF_UP}


def load_fixture():
    return json.loads(Path(__file__).with_name("fixture.json").read_text(encoding="utf-8"))


def _persist(case, fixture):
    app = case["app"]
    entry = case["entry"]
    if not app["save"]:
        prior = app["prior"]
        return {
            "present": True,
            "value": prior["value"],
            "unit": prior["unit"],
            "dimension": prior["dimension"],
            "quantity_kind": prior["quantity_kind"],
            "effect_count": app["effect_count"],
            "effect_id": app["save_id"],
            "conversion_known": True,
            "rounding_known": True,
        }

    unit = entry["unit_at_save"]
    try:
        spec = fixture["units"][unit]
    except KeyError:
        return {
            "present": True,
            "value": entry["number"],
            "unit": unit,
            "dimension": "unknown",
            "quantity_kind": app.get("quantity_kind", fixture["contract"]["quantity_kind"]),
            "effect_count": app["effect_count"],
            "effect_id": app["save_id"],
            "conversion_known": False,
            "rounding_known": False,
        }
    value = Decimal(entry["number"]) * Decimal(spec["factor"])
    places = app.get("decimal_places")
    round_name = app.get("rounding_mode")
    known_round = round_name is None or round_name in ROUNDING
    if places is not None and known_round:
        quantum = Decimal(1).scaleb(-places)
        value = value.quantize(quantum, rounding=ROUNDING[round_name])
    return {
        "present": True,
        "value": str(value) if known_round else None,
        "unit": spec["canonical"],
        "dimension": spec["dimension"],
        "quantity_kind": app.get(
            "quantity_kind",
            case["intent"].get("quantity_kind", fixture["contract"]["quantity_kind"]),
        ),
        "effect_count": app["effect_count"],
        "effect_id": app["save_id"],
        "conversion_known": True,
        "rounding_known": known_round,
    }


def _judge(case, fixture, persisted):
    app = case["app"]
    intent = case["intent"]
    if not app["save"]:
        return "NO_EFFECT"
    if app["effect_count"] != fixture["contract"]["required_effect_count"]:
        return "WRONG_EFFECT_COUNT"
    if not persisted["conversion_known"]:
        return "UNKNOWN_CONVERSION"
    if not persisted["rounding_known"]:
        return "UNKNOWN_ROUNDING"
    wanted_unit = fixture["units"].get(intent["unit"])
    if wanted_unit is None:
        return "UNKNOWN_CONVERSION"
    wanted_kind = intent.get("quantity_kind", fixture["contract"]["quantity_kind"])
    if persisted["quantity_kind"] != wanted_kind:
        return "WRONG_KIND"
    if persisted["dimension"] != wanted_unit["dimension"] or wanted_unit["dimension"] != intent.get("dimension", "length"):
        return "WRONG_DIMENSION"
    target = Decimal(intent["value"]) * Decimal(wanted_unit["factor"])
    observed = Decimal(persisted["value"])
    tolerance = Decimal(intent["tolerance"])
    return "PASS" if abs(observed - target) <= tolerance else "WRONG_MAGNITUDE"


def run_candidate(fixture):
    rows = []
    target_id = fixture["contract"]["target_id"]
    for case in fixture["cases"]:
        saved = _persist(case, fixture)
        intended = Decimal(case["intent"]["value"])
        entered = Decimal(case["entry"]["number"])
        rows.append(
            {
                "case_id": case["id"],
                "target_id": target_id,
                "bare_number_pass": entered == intended,
                "typed_status": _judge(case, fixture, saved),
                "persisted_value": saved["value"],
                "persisted_unit": saved["unit"],
                "persisted_dimension": saved["dimension"],
                "persisted_kind": saved["quantity_kind"],
                "effect_count": saved["effect_count"],
                "effect_id": saved["effect_id"],
                "conversion_known": saved["conversion_known"],
                "rounding_known": saved["rounding_known"],
            }
        )
    return rows


def main():
    print(json.dumps(run_candidate(load_fixture()), sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
