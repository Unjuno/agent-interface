#!/usr/bin/env python3
"""Independent reconstruction of fire-cover windows from pinned raw blobs."""
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
F = json.loads((ROOT / "FREEZE.json").read_text(encoding="utf-8"))


def pinned(path):
    raw = subprocess.check_output(["git", "show", F["base_commit"] + ":" + path])
    assert hashlib.sha256(raw).hexdigest() == F["source_blobs"][path]["sha256"]
    return raw


def main():
    report_path, events_path = F["source_blobs"].keys()
    report = json.loads(pinned(report_path))
    records = [json.loads(x) for x in pinned(events_path).splitlines() if x]
    typed = [x for x in records if x.get("event") == "typed_observation"]
    recomputed = []
    for turn in report["decisions"]:
        policy = turn.get("cover_policy") or []
        fire_cover = any(cmd.get("action") in ("fire", "retreat_fire", "advance_fire")
                         for cmd in policy)
        if not fire_cover:
            continue
        lo, hi = turn["controller_model_started_ns"], turn["controller_model_ended_ns"]
        sample = [e for e in typed if lo <= e.get("capture_ns", -1) <= hi]
        values = [e["signals"]["ammo"].get("value") for e in sample
                  if e.get("signals", {}).get("ammo", {}).get("status") == "observed"
                  and isinstance(e["signals"]["ammo"].get("value"), int)
                  and type(e["signals"]["ammo"].get("value")) is int]
        dec = sum(values[i + 1] < values[i] for i in range(len(values) - 1))
        scores = [e for e in records if e.get("event") == "post_control_score"]
        recomputed.append({"decision": turn["iteration"], "typed": len(sample),
                           "first": values[0] if values else None,
                           "last": values[-1] if values else None,
                           "minimum": min(values) if values else None,
                           "decrements": dec,
                           "zero": any(v == 0 for v in values),
                           "score_rows_in_trace": len(scores)})
    result = json.loads((ROOT / "RESULT.json").read_text(encoding="utf-8"))
    actual = [{"decision": w["decision"], "typed": w["typed_observations"],
               "first": w["ammo_first_last_min"][0] if w["ammo_first_last_min"] else None,
               "last": w["ammo_first_last_min"][1] if w["ammo_first_last_min"] else None,
               "minimum": w["ammo_first_last_min"][2] if w["ammo_first_last_min"] else None,
               "decrements": w["ammo_decrements"], "zero": w["ammo_zero_observed"],
               "score_rows_in_trace": result["post_control_score_rows"]}
              for w in result["windows"]]
    checks = {
        "window_rows_reconstructed": actual == recomputed,
        "result_zero_disposition_matches_raw": result["zero_ammo_exposure"] ==
            any(row["zero"] for row in recomputed),
        "posthoc_classification_preserved": "posthoc" in result["classification"],
        "live_allocations_added_zero": result["live_allocation_invocations_added"] == 0,
        "no_per_window_effect_events_claimed": result["per_window_useful_effect_events"] == 0,
    }
    audit = {"format": "59-v39-fire-cover-ammo-posthoc-audit-v1",
             "checks": checks, "passed": sum(checks.values()), "total": len(checks),
             "disposition": "PASS" if all(checks.values()) else "AUDIT_FAILED"}
    (ROOT / "AUDIT.json").write_text(json.dumps(audit, sort_keys=True,
                                      separators=(",", ":")) + "\n", encoding="utf-8")
    print(json.dumps(audit, sort_keys=True))


if __name__ == "__main__":
    main()
