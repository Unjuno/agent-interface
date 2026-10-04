"""Re-audit the retained weapon/ammo sample without trusting SAVED_AUDIT.json."""

from __future__ import annotations

import json
import math
import re
import sys
from pathlib import Path
from typing import Any


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def finite_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def neutral_action(row: dict[str, Any]) -> bool:
    buttons = row.get("buttons")
    action = row.get("action")
    return (
        isinstance(buttons, list)
        and bool(buttons)
        and all(isinstance(button, str) for button in buttons)
        and isinstance(action, list)
        and len(action) == len(buttons)
        and all(finite_number(value) and value == 0 for value in action)
    )


def audit(root: Path) -> dict[str, Any]:
    # The committed package stores 00-coast directly. Accept the pre-publication
    # runner layout too, so this audit can be run against either retained form.
    cell = root / "00-coast"
    if not cell.is_dir():
        cell = root / "sample-pair-04" / "00-coast"

    result = read_json(cell / "RESULT.json")
    final = read_json(cell / "FINAL.json")
    events = read_jsonl(cell / "events.jsonl")
    rows = read_jsonl(cell / "scorer-last-action.jsonl")
    window_start = result["window_start_ns"]
    window_end = result["window_end_ns"]
    selected = [
        row
        for row in rows
        if row["coherent_tic"]
        and window_start <= row["sample_started_ns"]
        and row["sample_returned_ns"] <= window_end
    ]

    checks: dict[str, bool] = {}
    initial_matches = [
        event
        for event in events
        if event.get("event") == "typed_observation" and event.get("id") == "initial"
    ]
    checks["one_initial_observation"] = len(initial_matches) == 1
    if not checks["one_initial_observation"]:
        return {"disposition": "HOLD_INVALID_INITIAL_OBSERVATION", "checks": checks}
    initial = initial_matches[0]

    published_initial = [
        event
        for event in events
        if event.get("event") == "observation" and event.get("id") == "initial"
    ]
    checks["typed_capture_matches_observation_event"] = (
        len(published_initial) == 1
        and all(
            initial.get(key) == published_initial[0].get(key)
            for key in ("id", "step", "sequence", "capture_ns", "pointer_binding", "frame_rgb_sha256")
        )
    )

    checks["sample_window_nonempty"] = bool(selected)
    if not selected:
        return {"disposition": "HOLD_NO_COHERENT_WINDOW_SAMPLES", "checks": checks}

    finite_samples = all(
        row["sample_started_ns"] <= row["sample_returned_ns"]
        and row["tic_before"] == row["tic_after"]
        and isinstance(row["variables"], dict)
        and all(finite_number(value) for value in row["variables"].values())
        for row in selected
    )
    checks["coherent_samples_finite_and_ordered"] = finite_samples
    checks["window_samples_neutral"] = all(
        neutral_action(row)
        for row in selected
    )

    binding = initial.get("pointer_binding")
    signals = initial.get("signals", {})
    expected_signal_ids = {"health": "health", "ammo": "ammo"}
    checks["capture_binding_well_formed"] = (
        isinstance(binding, dict)
        and isinstance(binding.get("focus"), int)
        and isinstance(binding.get("surface"), int)
        and isinstance(binding.get("geometry"), list)
        and len(binding["geometry"]) == 4
        and all(isinstance(value, int) and value > 0 for value in binding["geometry"])
    )
    checks["initial_frame_digest_well_formed"] = bool(
        re.fullmatch(r"[0-9a-f]{64}", str(initial.get("frame_rgb_sha256", "")))
    )
    signal_values: dict[str, float] = {}
    signal_meta_ok = checks["capture_binding_well_formed"]
    capture_digest: str | None = None
    for name, signal_id in expected_signal_ids.items():
        signal = signals.get(name, {})
        valid = (
            signal.get("status") == "observed"
            and signal.get("format") == "observable-signal-v1"
            and signal.get("signal_id") == signal_id
            and finite_number(signal.get("value"))
            and signal.get("capture_ns") == initial.get("capture_ns")
            and signal.get("sequence") == initial.get("sequence")
            and signal.get("binding") == binding
            and bool(re.fullmatch(r"[0-9a-f]{64}", str(signal.get("wad_sha256", ""))))
        )
        signal_meta_ok = signal_meta_ok and valid
        if valid:
            signal_values[name] = float(signal["value"])
            digest = signal["wad_sha256"]
            if capture_digest is None:
                capture_digest = digest
            else:
                signal_meta_ok = signal_meta_ok and digest == capture_digest
    checks["HUD_signals_validly_bound_to_initial_capture"] = signal_meta_ok

    coherent_rows = [row for row in rows if row.get("coherent_tic")]
    near = min(coherent_rows, key=lambda row: abs(row["sample_returned_ns"] - initial["capture_ns"]))
    checks["nearest_api_sample_neutral"] = neutral_action(near)
    variables = near["variables"]
    selected_weapon = variables.get("SELECTED_WEAPON")
    selected_ammo = variables.get("SELECTED_WEAPON_AMMO")
    health_api = variables.get("HEALTH")
    checks["selected_weapon_and_ammo_well_formed"] = (
        finite_number(selected_weapon)
        and int(selected_weapon) == selected_weapon
        and 0 <= int(selected_weapon) <= 9
        and finite_number(selected_ammo)
        and finite_number(health_api)
    )
    slot_ammo = None
    if checks["selected_weapon_and_ammo_well_formed"]:
        slot_ammo = variables.get(f"AMMO{int(selected_weapon)}")
    checks["selected_ammo_matches_selected_slot"] = (
        finite_number(slot_ammo)
        and finite_number(selected_ammo)
        and math.isclose(float(slot_ammo), float(selected_ammo), rel_tol=0, abs_tol=1e-6)
    )

    differences: dict[str, float] = {}
    if len(signal_values) == 2:
        differences = {
            "health": float(health_api) - signal_values["health"],
            "ammo": float(selected_ammo) - signal_values["ammo"],
        }
    checks["HUD_API_values_agree"] = (
        len(differences) == 2 and all(abs(value) <= 1e-6 for value in differences.values())
    )
    checks["clean_child_and_reader_exit"] = result.get("child_exit") == 0 and result.get("reader_alive") is False
    checks["no_external_rescue"] = final.get("external_rescue") is False

    passed = all(checks.values())
    return {
        "disposition": "PASS_HUD_WEAPON_AMMO_BINDING_SCOPED" if passed else "HOLD_AUDIT_CHECK_FAILED",
        "checks": checks,
        "sample_count": len(selected),
        "all_neutral": checks["window_samples_neutral"],
        "selected_weapon": selected_weapon,
        "selected_weapon_ammo": selected_ammo,
        "matching_slot_ammo": slot_ammo,
        "initial_hud_values": signal_values,
        "hud_api_differences": differences,
        "nearest_api_offset_ns": near["sample_returned_ns"] - initial["capture_ns"],
        "limits": "Near-time selected-fixture binding only; not simultaneous oracle, damage exposure, recovery efficacy, or controller-visible trust/adoption evidence.",
    }


def main() -> int:
    root = Path(__file__).resolve().parent
    try:
        report = audit(root)
    except (KeyError, TypeError, ValueError, OSError, json.JSONDecodeError) as exc:
        report = {"disposition": "HOLD_MALFORMED_OR_MISSING_EVIDENCE", "error": str(exc)}
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["disposition"] == "PASS_HUD_WEAPON_AMMO_BINDING_SCOPED" else 1


if __name__ == "__main__":
    sys.exit(main())
