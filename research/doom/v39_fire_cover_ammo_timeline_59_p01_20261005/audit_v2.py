#!/usr/bin/env python3
"""Reconstruct every P01 result field from immutable Git-pinned inputs."""
import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FREEZE = json.loads((ROOT / "AUDIT_V2_FREEZE.json").read_text(encoding="utf-8"))


class AuditError(RuntimeError):
    pass


def git_blob(commit, path, receipt):
    oid = subprocess.check_output(
        ["git", "rev-parse", f"{commit}:{path}"], cwd=ROOT, text=True).strip()
    if oid != receipt["git_blob"]:
        raise AuditError(f"git blob identity mismatch: {path}")
    data = subprocess.check_output(["git", "show", f"{commit}:{path}"], cwd=ROOT)
    digest = hashlib.sha256(data).hexdigest()
    if digest != receipt["sha256"]:
        raise AuditError(f"sha256 mismatch: {path}")
    return data


def load_predecessor():
    commit = FREEZE["created_from_commit"]
    blobs = FREEZE["predecessor_blobs"]
    loaded = {path: git_blob(commit, path, receipt)
              for path, receipt in blobs.items()}
    base = FREEZE["predecessor_path"]
    freeze_path = f"{base}/FREEZE.json"
    predecessor_freeze = json.loads(loaded[freeze_path])
    if predecessor_freeze != FREEZE["predecessor_freeze"]:
        raise AuditError("embedded predecessor freeze differs from pinned freeze blob")
    raw = {}
    for path, receipt in predecessor_freeze["source_blobs"].items():
        raw[path] = git_blob(predecessor_freeze["base_commit"], path, receipt)
    return predecessor_freeze, loaded, raw


def _strict_json(raw, name):
    def unique_object(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise AuditError(f"duplicate JSON key {key!r} in {name}")
            result[key] = value
        return result

    try:
        return json.loads(raw, object_pairs_hook=unique_object)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise AuditError(f"invalid JSON in {name}: {exc}") from exc


def reconstruct_result():
    predecessor_freeze, loaded, raw = load_predecessor()
    base = FREEZE["predecessor_path"]
    report_path = next(path for path in raw if path.endswith("/report.json"))
    events_path = next(path for path in raw if path.endswith("/events.jsonl"))
    report = _strict_json(raw[report_path], report_path)
    records = [_strict_json(line, events_path) for line in raw[events_path].splitlines() if line]
    if any(type(row) is not dict or type(row.get("event")) is not str for row in records):
        raise AuditError("raw event rows must have exact object/event-string types")
    typed = [row for row in records if row["event"] == "typed_observation"]
    windows = []
    for decision in report["decisions"]:
        if type(decision) is not dict:
            raise AuditError("report decisions must be objects")
        cover = decision.get("cover_policy") or []
        if type(cover) is not list:
            raise AuditError("cover_policy must be a list when present")
        if not any(type(item) is dict and item.get("action") in
                   {"fire", "retreat_fire", "advance_fire"} for item in cover):
            continue
        start = decision.get("controller_model_started_ns")
        end = decision.get("controller_model_ended_ns")
        if type(start) is not int or type(end) is not int or not 0 <= start <= end:
            raise AuditError("invalid model-wait boundaries")
        rows = [row for row in typed
                if type(row.get("capture_ns")) is int and start <= row["capture_ns"] <= end]
        ammo = []
        health = []
        for row in rows:
            signals = row.get("signals")
            if type(signals) is not dict:
                continue
            for name, out in (("ammo", ammo), ("health", health)):
                signal = signals.get(name)
                if (type(signal) is dict and signal.get("status") == "observed" and
                        type(signal.get("value")) is int):
                    out.append(signal["value"])
        invalidation = (decision.get("final_action_admission", {}).get(
            "policy_invalidation") or {})
        windows.append({
            "decision": decision["iteration"],
            "cover_actions": [item["action"] for item in cover],
            "model_wait_ms": round((end - start) / 1e6, 3),
            "typed_observations": len(rows),
            "ammo_first_last_min": ([ammo[0], ammo[-1], min(ammo)] if ammo else None),
            "ammo_decrements": sum(after < before for before, after in zip(ammo, ammo[1:])),
            "ammo_zero_observed": any(value == 0 for value in ammo),
            "health_first_last": ([health[0], health[-1]] if health else None),
            "policy_invalidation_signal": invalidation.get("signal", {}).get("signal_id"),
        })
    event_names = sorted({row["event"] for row in records})
    effect_names = set(FREEZE["result_contract"]["time_local_effect_event_types"])
    time_local_effects = sum(row["event"] in effect_names for row in records)
    run_path = f"{base}/RUN.md"
    run_text = loaded[run_path].decode("utf-8")
    match = re.search(r"Added live allocation invocations:\s*(\d+)", run_text)
    if not match:
        raise AuditError("pinned run record lacks live-allocation count")
    score_rows = [row for row in records if row["event"] == "post_control_score"]
    zero_exposure = any(window["ammo_zero_observed"] for window in windows)
    return {
        "active_fire_cover_windows": len(windows),
        "classification": FREEZE["result_contract"]["classification"],
        "disposition": "ZERO_AMMO_EXPOSED" if zero_exposure else "NO_ZERO_EXPOSURE",
        "event_names": event_names,
        "format": FREEZE["result_contract"]["format"],
        "live_allocation_invocations_added": int(match.group(1)),
        "per_window_useful_effect_events": time_local_effects,
        "post_control_score_rows": len(score_rows),
        "runtime_event_rows_total": len(records),
        "source_base_commit": predecessor_freeze["base_commit"],
        "source_hashes_verified": True,
        "typed_observations_total": len(typed),
        "windows": windows,
        "zero_ammo_exposure": zero_exposure,
    }


def mismatch_paths(expected, actual, prefix="$"):
    if type(expected) is not type(actual):
        return [prefix]
    if type(expected) is dict:
        mismatches = []
        for key in sorted(set(expected) | set(actual)):
            child = f"{prefix}.{key}"
            if key not in expected or key not in actual:
                mismatches.append(child)
            else:
                mismatches.extend(mismatch_paths(expected[key], actual[key], child))
        return mismatches
    if type(expected) is list:
        mismatches = []
        if len(expected) != len(actual):
            mismatches.append(prefix + ".length")
        for index, (left, right) in enumerate(zip(expected, actual)):
            mismatches.extend(mismatch_paths(left, right, f"{prefix}[{index}]"))
        return mismatches
    return [] if expected == actual else [prefix]


def audit(candidate_bytes):
    expected = reconstruct_result()
    candidate = _strict_json(candidate_bytes, "candidate RESULT.json")
    if type(candidate) is not dict:
        raise AuditError("candidate result must be a JSON object")
    mismatches = mismatch_paths(expected, candidate)
    return {
        "format": "59-v39-fire-cover-ammo-full-result-audit-v2",
        "disposition": "PASS_FULL_RESULT_RECONSTRUCTION" if not mismatches else "FAIL_RESULT_MISMATCH",
        "source_identities_verified": True,
        "expected_result_fields": len(expected),
        "mismatch_paths": mismatches,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate-result", type=Path)
    parser.add_argument("--output", type=Path, default=ROOT / "AUDIT_V2.json")
    args = parser.parse_args()
    if args.candidate_result:
        candidate_bytes = args.candidate_result.read_bytes()
    else:
        path = f"{FREEZE['predecessor_path']}/RESULT.json"
        candidate_bytes = git_blob(FREEZE["created_from_commit"], path,
                                   FREEZE["predecessor_blobs"][path])
    result = audit(candidate_bytes)
    args.output.write_text(json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n",
                           encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(0 if result["disposition"] == "PASS_FULL_RESULT_RECONSTRUCTION" else 1)


if __name__ == "__main__":
    main()
