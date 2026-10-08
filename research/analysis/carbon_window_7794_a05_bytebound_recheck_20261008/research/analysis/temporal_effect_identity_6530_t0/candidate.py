#!/usr/bin/env python3
"""Candidate temporal-effect classifier; formal execution is separately gated."""
import json
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


def possible_instants(local_text: str, zone_name: str) -> list[str]:
    local = datetime.fromisoformat(local_text)
    zone = ZoneInfo(zone_name)
    results = []
    for fold in (0, 1):
        aware = local.replace(tzinfo=zone, fold=fold)
        utc = aware.astimezone(ZoneInfo("UTC"))
        roundtrip = utc.astimezone(zone).replace(tzinfo=None)
        if roundtrip == local:
            value = utc.isoformat(timespec="seconds").replace("+00:00", "Z")
            if value not in results:
                results.append(value)
    return results


def classify(case: dict) -> dict:
    intent, observed = case["intent"], case["observed"]
    kind = intent["kind"]
    count = observed.get("count", 0)
    if count == 0 or observed.get("event_id") is None:
        return {"classification": "NO_EFFECT"}
    if count != 1:
        return {"classification": "DUPLICATE_EFFECT"}
    if kind == "RECURRENCE_IN_ZONE":
        zone = intent["zone"]
        expected = []
        for day in intent["dates"]:
            expected.extend(possible_instants(f"{day}T{intent['local_time']}:00", zone))
        actual = observed.get("utc_occurrences", [])
        return {"classification": "MATCH" if expected == actual else "WRONG_RECURRENCE",
                "expected_utc_occurrences": expected}
    possible = possible_instants(intent["local"], intent["zone"])
    if not possible:
        return {"classification": "NONEXISTENT_LOCAL_TIME"}
    if len(possible) > 1 and intent.get("fold") is None:
        return {"classification": "AMBIGUOUS_UNRESOLVED", "possible_utc": possible}
    chosen = possible[int(intent.get("fold", 0))]
    observed_utc = observed.get("utc")
    if observed.get("zone") != intent["zone"]:
        result = "WRONG_ZONE"
    elif observed_utc != chosen:
        result = "WRONG_INSTANT"
    else:
        result = "MATCH"
    return {"classification": result, "expected_utc": chosen}


def baselines(case: dict) -> dict:
    """Comparators deliberately ignore typed intent; results expose their limits."""
    intent, observed = case["intent"], case["observed"]
    display_expected = intent.get("local", "").replace("T", " ")[:16]
    if intent.get("kind") == "RECURRENCE_IN_ZONE":
        display_expected = f"{intent['dates'][0]} {intent['local_time']}"
    visible_displays = observed.get("local_displays", [])
    string_accept = (display_expected in visible_displays if visible_displays
                     else observed.get("local_display") == display_expected)
    # This baseline accepts when the offset is plausible for the named zone at
    # the first visible local time; it does not bind a fold choice or recurrence.
    offset_accept = bool(observed.get("zone")) and (
        observed.get("utc") is not None or bool(observed.get("utc_occurrences")))
    return {"string_only_accept": string_accept, "offset_only_accept": offset_accept}


def main() -> int:
    source = Path(sys.argv[1])
    output = Path(sys.argv[2])
    fixture = json.loads(source.read_text(encoding="utf-8"))
    rows = []
    for case in fixture["cases"]:
        rows.append({"id": case["id"], **baselines(case),
                     "typed": classify(case)})
    output.write_text(json.dumps({"schema": "temporal-effect-candidate-raw-v1",
                                  "rows": rows}, indent=2, sort_keys=True) + "\n",
                      encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
