#!/usr/bin/env python3
"""Independent raw-ledger replay and frozen decision audit; imports no candidate code."""
import copy, hashlib, json, random, statistics, sys
from pathlib import Path

fixture_path, raw_path, audit_path = map(Path, sys.argv[1:4])
fx = json.loads(fixture_path.read_text(encoding="utf-8"))
raw = json.loads(raw_path.read_text(encoding="utf-8"))

def validate(data, strict_alarm_map=False):
    assert data["schema"] == "mode-flap-raw-a01"
    assert data["fixture_sha256"] == hashlib.sha256(fixture_path.read_bytes()).hexdigest()
    expected = len(fx["families"]) * (len(fx["calibration_seeds"]) + len(fx["heldout_seeds"]))
    assert len(data["episodes"]) == expected
    keys = [(e["family"], e["split"], e["seed"]) for e in data["episodes"]]
    assert len(keys) == len(set(keys))
    assert set(keys) == {(fam, split, seed) for fam in fx["families"]
                         for split, seeds in (("calibration", fx["calibration_seeds"]), ("heldout", fx["heldout_seeds"])) for seed in seeds}
    row_count = 0
    computed = {}
    replayed_alarms = {}
    alarm_map_mismatches = 0
    for ep in data["episodes"]:
        fam, ev = ep["family"], ep["events"]
        rng = random.Random(ep["seed"] + 900_000 * fx["families"].index(fam))
        expected_mode = "A"
        switch_at = 10 + rng.randrange(3)
        next_flip = 3
        assert len(ev) == fx["horizon_ticks"]
        q, previous_mode, cusum, recoveries, pending = 0, "A", 0.0, [], None
        computed_rows = []
        for tick, x in enumerate(ev):
            assert x["tick"] == tick
            transition = False
            if fam == "endogenous_flicker" and tick == switch_at and tick < fx["degraded_onset_tick"]:
                expected_mode = "B" if expected_mode == "A" else "A"
                transition = True
                switch_at = tick + max(1, 8 - tick // 8)
            elif fam == "endogenous_flicker" and tick == fx["degraded_onset_tick"]:
                expected_mode, transition = "DEGRADED", expected_mode != "DEGRADED"
            elif fam == "policy_oscillation" and tick == next_flip:
                expected_mode = "B" if expected_mode == "A" else "A"
                transition = True
                next_flip += 3
            expected_demand = (2 if tick < 20 else 3 if tick < 40 else 4) if fam == "demand_drift" else 3
            assert x["demand"] == expected_demand
            if fam == "endogenous_flicker":
                service_expected = 1 if expected_mode == "DEGRADED" else (5 if expected_mode == "A" else 2)
                if transition and expected_mode != "DEGRADED": service_expected = max(0, service_expected - 1)
                assert x["service"] == service_expected and x["service_mode"] == expected_mode
            elif fam == "policy_oscillation":
                assert x["service"] == 4 and x["service_mode"] == expected_mode
            elif fam == "abrupt_failure":
                assert x["service"] == (0 if tick >= fx["abrupt_onset_tick"] else 4) and x["service_mode"] == "A"
            elif fam == "single_mode_noise":
                assert x["service"] == 4 and x["service_mode"] == "SINGLE"
                assert x["service_observation"] == rng.choice([2, 5])
            else:
                assert x["service"] == 4 and x["service_mode"] == "A"
            assert x["safety_service"] == 1 and x["safety_backlog"] == 0
            assert x["probe"] == int(tick in fx["probe_ticks"])
            assert x["offered"] == x["demand"] + x["probe"]
            if fam == "single_mode_noise":
                assert x["service"] == 4 and x["service_observation"] in (2, 5) and x["service_mode"] == "SINGLE"
            else:
                assert x["service_observation"] == x["service"]
            assert x["queue_before"] == q
            q2 = max(0, q + x["offered"] - x["service"])
            assert x["queue"] == q2
            assert x["mode_transition"] == int(transition)
            cusum = max(0.0, cusum + (q2 - q) - fx["cusum_reference"])
            assert x["cusum_state"] == round(cusum, 6)
            if x["probe"]:
                pending = (tick, q)
            elif pending is not None and q2 <= pending[1]:
                recoveries.append(tick - pending[0]); pending = None
            assert x["recovery_durations"] == recoveries
            w = ev[max(0, tick - fx["rolling_window_ticks"] + 1):tick + 1]
            want = {
                "rolling_mode_transition_count": sum(z["mode_transition"] for z in w),
                "rolling_mean_queue": sum(z["queue"] for z in w) / len(w),
                "rolling_maximum_service_margin_deficit": max(max(0, z["demand"] + z["probe"] - z["service_observation"]) for z in w),
                "recovery_duration_ratio": recoveries[-1] / recoveries[0] if len(recoveries) >= 2 and recoveries[0] else 0.0,
                "positive_queue_cusum": round(cusum, 6)
            }
            assert x["scores"] == want
            computed_rows.append((q2, want))
            q, previous_mode = q2, x["service_mode"]
            row_count += 1
        n = fx["persistent_loss_ticks"]
        endpoint = next((i for i in range(len(ev) - n + 1) if all(ev[j]["queue"] >= fx["queue_loss_threshold"] for j in range(i, i + n))), None)
        assert ep["loss_tick"] == endpoint
        eligible = [(i < fx["abrupt_onset_tick"] if fam == "abrupt_failure" else endpoint is None or i < endpoint) for i in range(len(ev))]
        assert [x["warning_eligible"] for x in ev] == eligible
        computed[(fam, ep["split"], ep["seed"])] = (ev, endpoint)

    thresholds = {}
    for metric in fx["metrics"]:
        vals = [row["scores"][metric] for ep in data["episodes"] if ep["split"] == "calibration" and ep["family"] in fx["negative_calibration_families"] for row in ep["events"] if row["warning_eligible"]]
        thresholds[metric] = max(vals)
    assert data["thresholds"] == thresholds
    for ep in data["episodes"]:
        expected_alarms = {}
        for metric in fx["metrics"]:
            alarm = next((row["tick"] for row in ep["events"] if row["warning_eligible"] and row["scores"][metric] > thresholds[metric]), None)
            expected_alarms[metric] = alarm
        if ep["alarms"] != expected_alarms:
            alarm_map_mismatches += 1
        if strict_alarm_map:
            assert ep["alarms"] == expected_alarms
        replayed_alarms[(ep["family"], ep["split"], ep["seed"])] = expected_alarms
    return {"thresholds": thresholds, "rows": row_count, "computed": computed,
            "alarms": replayed_alarms, "alarm_map_mismatches": alarm_map_mismatches}

replay = validate(raw)
mutations = {}
normalized = copy.deepcopy(raw)
for ep in normalized["episodes"]:
    ep["alarms"] = replay["alarms"][(ep["family"], ep["split"], ep["seed"])]
def reject(name, change):
    clone = copy.deepcopy(normalized); change(clone)
    try: validate(clone, strict_alarm_map=True)
    except (AssertionError, KeyError, TypeError, ValueError): mutations[name] = "REJECTED"
    else: mutations[name] = "ESCAPED"
reject("queue_state", lambda d: d["episodes"][0]["events"][0].__setitem__("queue", 999))
reject("source_transition", lambda d: d["episodes"][0]["events"][1].__setitem__("mode_transition", 1))
reject("safety_lane", lambda d: d["episodes"][0]["events"][0].__setitem__("safety_backlog", 1))
reject("endpoint", lambda d: d["episodes"][0].__setitem__("loss_tick", 0))
reject("threshold", lambda d: d["thresholds"].__setitem__("rolling_mean_queue", -1))
reject("alarm", lambda d: d["episodes"][0]["alarms"].__setitem__("positive_queue_cusum", 0))
reject("duplicate_cell", lambda d: d["episodes"].__setitem__(1, copy.deepcopy(d["episodes"][0])))

held = [e for e in raw["episodes"] if e["split"] == "heldout"]
by = {m: [] for m in fx["metrics"]}
family_counts = {}
for ep in held:
    family_counts.setdefault(ep["family"], {"n": 0, "alarms": {m: 0 for m in fx["metrics"]}, "losses": 0})
    g = family_counts[ep["family"]]; g["n"] += 1; g["losses"] += int(ep["loss_tick"] is not None)
    for metric in fx["metrics"]:
        at = replay["alarms"][(ep["family"], ep["split"], ep["seed"])][metric]
        if at is not None: g["alarms"][metric] += 1
        if ep["family"] == "endogenous_flicker" and ep["loss_tick"] is not None:
            by[metric].append(ep["loss_tick"] - at if at is not None else 0)

control_families = set(fx["negative_calibration_families"])
false_alarms = {m: sum(family_counts[f]["alarms"][m] for f in control_families) for m in fx["metrics"]}
lead_medians = {m: statistics.median(v) for m, v in by.items()}
positive_n = len(by["rolling_mode_transition_count"])
improves_all = all(lead_medians["rolling_mode_transition_count"] > lead_medians[m] for m in fx["metrics"] if m != "rolling_mode_transition_count")
no_negative_alarms = all(false_alarms[m] == 0 for m in fx["metrics"])
positive_all_warn = (len(by["rolling_mode_transition_count"]) == len(fx["heldout_seeds"])
                     and all(v > 0 for v in by["rolling_mode_transition_count"]))
mutation_pass = all(v == "REJECTED" for v in mutations.values())
method_gate = "PASS_METHOD_SCOPED" if (positive_all_warn and improves_all and no_negative_alarms and mutation_pass) else "FAIL_METHOD_SCOPED"
decision = "HOLD_AUDIT" if replay["alarm_map_mismatches"] else method_gate
result = {"audit": "PASS_INDEPENDENT_REPLAY_SCOPED_POSTHOC_V2", "decision": decision,
          "reconstructed_method_gate": method_gate,
          "episodes": len(raw["episodes"]), "event_rows": replay["rows"], "mismatches": 0,
          "candidate_alarm_map_complete": replay["alarm_map_mismatches"] == 0,
          "candidate_episodes_with_alarm_map_mismatch": replay["alarm_map_mismatches"],
          "thresholds": replay["thresholds"], "calibration_false_alarms": {m: 0 for m in fx["metrics"]},
          "heldout_negative_control_false_alarms": false_alarms, "heldout_flicker_median_lead_ticks": lead_medians,
          "heldout_flicker_n": positive_n, "heldout_flicker_all_warned": positive_all_warn,
          "improves_over_all_comparators": improves_all, "negative_controls_alarm_free": no_negative_alarms,
          "safety_lane_invariants": "PASS_ALL_ROWS", "mutation_controls": mutations,
          "mutation_controls_pass": mutation_pass,
          "mode_threshold_sensitivity": "NOT_APPLICABLE_SOURCE_BOUND_LABELS"}
audit_path.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
print(json.dumps(result, sort_keys=True, separators=(",", ":")))

