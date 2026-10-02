"""Independent raw-only audit; intentionally does not import the analyzer."""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path


FIELDS = ("id", "step", "status", "source_sequence", "source_ammo", "source_status",
          "in_loop_ammo_values", "ammo_decreased_in_loop")


def _value(row):
    signal = (row.get("signals") or {}).get("ammo") or {}
    v = signal.get("value")
    return v if signal.get("status") == "observed" and type(v) is int and v >= 0 else None


def audit_events(events: list[dict], submitted: dict) -> list[str]:
    """Independently reconstruct the row-level semantic facts from raw events."""
    definitions, typed, obs = {}, [], defaultdict(list)
    starts, admissions, markers, ends, terminal_status = {}, defaultdict(list), {}, set(), {}
    active = None
    errors = []
    for event in events:
        kind = event.get("event")
        if kind == "command" and (event.get("command") or {}).get("op") == "submit":
            c = event["command"]
            for idx, step in enumerate(c.get("steps", [])):
                if step.get("op") == "hold":
                    definitions[(c.get("id"), idx)] = (list(step.get("keys", [])), c.get("expected_sequence"))
        elif kind == "typed_observation":
            typed.append(event)
        elif kind == "observation":
            obs[(event.get("id"), event.get("step"))].append(event)
        elif kind == "step_started" and event.get("operation") == "hold":
            k = (event.get("id"), event.get("step"))
            if k not in definitions or active is not None:
                errors.append(f"invalid hold start {k}")
            active = k
            starts[k] = event.get("issued_ns")
        elif kind == "input_admission":
            if active is None:
                errors.append("input admission outside hold")
            else:
                admissions[active].append(event.get("key"))
        elif kind == "keys_held":
            k = (event.get("id"), event.get("step"))
            if active != k or k in markers:
                errors.append(f"invalid keys_held marker {k}")
            markers[k] = list(event.get("keys", []))
        elif kind == "step_completed":
            k = (event.get("id"), event.get("step"))
            if k in definitions:
                ends.add(k)
            if active == k:
                active = None
        elif kind == "terminal":
            terminal_status[event.get("id")] = event.get("status")
            if active is not None and active[0] == event.get("id"):
                active = None

    typed_at = defaultdict(list)
    for row in typed:
        typed_at[(row.get("sequence"), row.get("capture_ns"))].append(row)

    expected_rows = []
    for k in sorted(starts, key=lambda key: starts[key]):
        requested, expected_seq = definitions[k]
        if "space" not in requested:
            continue
        full = k in markers and sorted(markers[k]) == sorted(requested) and admissions[k] == requested
        status = ("completed_keyset_confirmed" if full and k in ends else
                  "interrupted_after_keyset" if full else
                  "partial_or_unconfirmed_no_keyset_marker")
        if k in markers and sorted(markers[k]) != sorted(requested):
            errors.append(f"marker keyset mismatch {k}")
        if k in markers and admissions[k] != requested:
            errors.append(f"admission order mismatch {k}")

        before = [row for row in typed if type(row.get("capture_ns")) is int
                  and row["capture_ns"] <= starts[k]]
        source = max(before, key=lambda row: row["capture_ns"]) if before else None
        source_ammo = _value(source) if source else None
        source_status = ("no_pre_step_typed_ammo" if source is None else
                         "observed" if source_ammo is not None else "pre_step_ammo_unknown")
        values = []
        if status == "completed_keyset_confirmed":
            if source_ammo is None:
                errors.append(f"completed step lacks source ammo {k}")
            ordered = sorted(obs[k], key=lambda row: row.get("capture_ns", -1))
            if not ordered:
                errors.append(f"post-release observation missing {k}")
            for picture in ordered[:-1]:
                loc = (picture.get("sequence"), picture.get("capture_ns"))
                exact = typed_at.get(loc, [])
                if len(exact) != 1:
                    errors.append(f"typed locator not unique {k} {loc}")
                    continue
                value = _value(exact[0])
                if value is not None:
                    values.append(value)
            if not values:
                errors.append(f"completed step lacks in-loop ammo sample {k}")
        dec = (None if status != "completed_keyset_confirmed" or source_ammo is None
               else any(value < source_ammo for value in values))
        expected_rows.append({
            "id": k[0], "step": k[1], "status": status,
            "source_sequence": source.get("sequence") if source else None,
            "source_ammo": source_ammo, "source_status": source_status,
            "in_loop_ammo_values": values, "ammo_decreased_in_loop": dec,
        })

    actual_rows = submitted.get("space_steps", [])
    if len(actual_rows) != len(expected_rows):
        errors.append("space-step row count mismatch")
    actual_by_key = {(r.get("id"), r.get("step")): r for r in actual_rows}
    for expected in expected_rows:
        key = (expected["id"], expected["step"])
        actual = actual_by_key.get(key)
        if actual is None or any(actual.get(field) != expected[field] for field in FIELDS):
            errors.append(f"space-step semantic mismatch {key}")

    completed = [r for r in expected_rows if r["status"] == "completed_keyset_confirmed"]
    decreased = sum(r["ammo_decreased_in_loop"] is True for r in completed)
    expected_fraction = decreased / len(completed) if completed else None
    if submitted.get("completed_decrease_fraction") != expected_fraction:
        errors.append("completed decrease fraction mismatch")
    expected_counts = {
        "space_steps_started": len(expected_rows),
        "completed_keyset_confirmed": len(completed),
        "interrupted_after_keyset": sum(r["status"] == "interrupted_after_keyset" for r in expected_rows),
        "partial_or_unconfirmed_no_keyset_marker": sum(
            r["status"] == "partial_or_unconfirmed_no_keyset_marker" for r in expected_rows),
        "source_ammo_unknown": sum(r["source_ammo"] is None for r in expected_rows),
        "source_ammo_zero": sum(r["source_ammo"] == 0 for r in expected_rows),
        "completed_with_in_loop_ammo_decrease": decreased,
        "completed_missing_source_ammo": sum(r["status"] == "completed_keyset_confirmed" and
                                              r["source_ammo"] is None for r in expected_rows),
        "completed_missing_in_loop_ammo_sample": sum(r["status"] == "completed_keyset_confirmed" and
                                                       not r["in_loop_ammo_values"] for r in expected_rows),
    }
    if submitted.get("counts") != expected_counts:
        errors.append("run counts mismatch")
    return errors


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--repo-root", type=Path, default=Path.cwd())
    p.add_argument("--result", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    a = p.parse_args()
    root = a.repo_root.resolve()
    package = Path(__file__).resolve().parent
    freeze = json.loads((package / "FREEZE.json").read_text())
    frozen_sources = {
        "analysis_source_sha256": package / "analyze_ammo_fire_diagnostic.py",
        "auditor_source_sha256": package / "audit_ammo_fire_diagnostic.py",
        "test_source_sha256": package / "test_ammo_fire_diagnostic.py",
        "plan_sha256": package / "PLAN.md",
    }
    for field, path in frozen_sources.items():
        if sha(path) != freeze[field]:
            all_errors.append(f"frozen source hash mismatch {field}")
    result = json.loads(a.result.read_text())
    all_errors = []
    input_receipts = {}
    for name, item in freeze["inputs"].items():
        ep, rp = root / item["events"], root / item["report"]
        eh, rh = sha(ep), sha(rp)
        if eh != item["events_sha256"] or rh != item["report_sha256"]:
            all_errors.append(f"input hash mismatch {name}")
            continue
        raw = [json.loads(line) for line in ep.read_text(encoding="utf-8").splitlines()]
        run = next((r for r in result.get("runs", []) if r.get("run") == name), None)
        if run is None:
            all_errors.append(f"missing result run {name}")
            continue
        all_errors.extend(f"{name}:{err}" for err in audit_events(raw, run))
        if run.get("events_sha256") != eh or run.get("report_sha256") != rh:
            all_errors.append(f"result source hash mismatch {name}")
        input_receipts[name] = {"events_sha256": eh, "report_sha256": rh, "event_rows": len(raw)}

    runs = {run.get("run"): run for run in result.get("runs", [])}
    v38, v39 = runs.get("map01-v38-integrated-threat-live-01"), runs.get("map01-v39-coast-liveness-live-01")
    if v38 is None or v39 is None:
        all_errors.append("required run pair missing")
    else:
        integrity_ok = not any("lacks source ammo" in error or "lacks in-loop ammo sample" in error
                               for error in all_errors)
        all_positive = all(row.get("source_ammo") is not None and row["source_ammo"] > 0
                           for run in (v38, v39) for row in run.get("space_steps", [])
                           if row.get("status") == "completed_keyset_confirmed")
        supported = (integrity_ok and all_positive and
                     v38.get("completed_decrease_fraction") is not None and
                     v39.get("completed_decrease_fraction") is not None and
                     v39["completed_decrease_fraction"] > v38["completed_decrease_fraction"])
        if result.get("hypothesis_supported") != supported:
            all_errors.append("hypothesis summary mismatch")
        expected = ("FAIL_INTEGRITY" if not integrity_ok else
                    "PASS_DIAGNOSTIC_CONTRAST_SCOPED" if supported else "HYPOTHESIS_NOT_SUPPORTED")
        if result.get("decision") != expected:
            all_errors.append("decision mismatch")
        if result.get("measurement_integrity_ok") != integrity_ok:
            all_errors.append("measurement integrity summary mismatch")

    status = "PASS_AMMO_FIRE_RAW_AUDIT" if not all_errors else "FAIL_AMMO_FIRE_RAW_AUDIT"
    payload = {"status": status, "errors": all_errors,
               "candidate_sha256": sha(a.result), "input_receipts": input_receipts}
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))
    return 0 if not all_errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
