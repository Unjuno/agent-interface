"""Independent reconstruction and anti-survivorship audit."""
import json
import math
import statistics
import sys


def _mean(values):
    return statistics.mean(values) if values else None


def _se(values):
    return statistics.stdev(values) / math.sqrt(len(values)) if len(values) > 1 else None


def audit(ledger, result):
    assert result.get("schema") == "57-paired-all-attempt-analysis-t0-v1"
    assert result.get("adjustment") == {"covariate": None, "status": "NOT_PERFORMED"}
    ids = [p["pair_id"] for p in ledger["pairs"]]
    assert len(ids) == len(set(ids))
    attempt_ids = [a["attempt_id"] for p in ledger["pairs"] for a in p["attempts"]]
    assert len(attempt_ids) == len(set(attempt_ids))
    for pair in ledger["pairs"]:
        attempts = pair["attempts"]
        assert len(attempts) == 2
        assert {a["arm"] for a in attempts} == {"baseline", "integrated"}
        assert len({a["reset_id"] for a in attempts}) == 2
        assert "repair_count" not in pair["pre_treatment"]
        assert pair["pre_treatment"]["captured_at"] < min(a["assigned_at"] for a in attempts)
        for attempt in attempts:
            assert attempt["started_at"] >= attempt["assigned_at"]
            assert attempt["outcome"] in {"COMPLETE", "FAIL", "UNKNOWN"}
            for metric in ("tokens", "elapsed_ms"):
                if attempt["outcome"] == "COMPLETE":
                    assert isinstance(attempt[metric], (int, float)) and attempt[metric] >= 0
                else:
                    assert attempt[metric] is None
    expected_scenarios = sorted({p["scenario"] for p in ledger["pairs"]})
    assert list(result["scenarios"]) == expected_scenarios
    for name in expected_scenarios:
        pairs = [p for p in ledger["pairs"] if p["scenario"] == name]
        scenario = result["scenarios"][name]
        expected_pair_ids = [p["pair_id"] for p in pairs]
        assert scenario["assigned_pairs"] == len(pairs)
        assert scenario["assigned_attempts"] == 2 * len(pairs)
        assert [p["pair_id"] for p in scenario["paired"]["rows"]] == expected_pair_ids
        paired_summary = scenario["paired"]["summary"]
        assert paired_summary["assigned_pairs"] == len(pairs)
        deltas = {"tokens": [], "elapsed_ms": []}
        for pair, row in zip(pairs, scenario["paired"]["rows"]):
            by_arm = {a["arm"]: a for a in pair["attempts"]}
            assert row["baseline_attempt_id"] == by_arm["baseline"]["attempt_id"]
            assert row["integrated_attempt_id"] == by_arm["integrated"]["attempt_id"]
            assert row["baseline_outcome"] == by_arm["baseline"]["outcome"]
            assert row["integrated_outcome"] == by_arm["integrated"]["outcome"]
            for metric in ("tokens", "elapsed_ms"):
                b, i = by_arm["baseline"][metric], by_arm["integrated"][metric]
                want = i - b if b is not None and i is not None else None
                assert row[f"delta_{metric}_integrated_minus_baseline"] == want
                if want is not None:
                    deltas[metric].append(want)
        for metric, values in deltas.items():
            assert paired_summary[f"complete_pairs_{metric}"] == len(values)
            assert paired_summary[f"mean_delta_{metric}_integrated_minus_baseline"] == _mean(values)
            assert paired_summary[f"se_delta_{metric}_complete_pairs_only"] == _se(values)
        for arm in ("baseline", "integrated"):
            attempts = [next(a for a in p["attempts"] if a["arm"] == arm) for p in pairs]
            got = scenario["arms"][arm]
            assert got["attempt_count"] == len(attempts)
            assert got["attempt_ids"] == [a["attempt_id"] for a in attempts]
            assert got["outcomes"] == [a["outcome"] for a in attempts]
            assert got["effect_statuses"] == [a["effect"] for a in attempts]
            assert got["safety_statuses"] == [a["safety"] for a in attempts]
            for metric in ("tokens", "elapsed_ms"):
                summary = got["metrics"][metric]
                values = [a[metric] for a in attempts]
                observed = [x for x in values if x is not None]
                assert summary["assigned_count"] == len(attempts)
                assert summary["observed_count"] == len(observed)
                assert summary["missing_count"] == len(values) - len(observed)
                assert summary["sum_observed"] == (sum(observed) if observed else None)
                assert summary["raw_values_in_attempt_order"] == values
        safe = all(
            a["outcome"] == "COMPLETE" and a["effect"] == "VERIFIED" and a["safety"] == "SAFE"
            for p in pairs for a in p["attempts"]
        )
        assert scenario["safety_gate"] == {"pass": safe, "all_attempts_verified_safe": safe}
        complete = all(a["outcome"] == "COMPLETE" for p in pairs for a in p["attempts"])
        want_interpretation = "DESCRIPTIVE_SYNTHETIC_ONLY" if complete and safe else "HOLD_INCOMPLETE_OR_SAFETY"
        assert scenario["interpretation"] == want_interpretation
        for metric in ("tokens", "elapsed_ms"):
            baseline = [a[metric] for p in pairs for a in p["attempts"] if a["arm"] == "baseline" and a[metric] is not None]
            integrated = [a[metric] for p in pairs for a in p["attempts"] if a["arm"] == "integrated" and a[metric] is not None]
            summary = scenario["unpaired_sensitivity"][metric]
            assert summary["baseline_observed_n"] == len(baseline)
            assert summary["integrated_observed_n"] == len(integrated)
            assert summary["baseline_mean_observed"] == _mean(baseline)
            assert summary["integrated_mean_observed"] == _mean(integrated)
            want_delta = _mean(integrated) - _mean(baseline) if baseline and integrated else None
            assert summary["mean_delta_integrated_minus_baseline"] == want_delta
            be = _se(baseline)
            ie = _se(integrated)
            want_se = math.sqrt(be * be + ie * ie) if be is not None and ie is not None else None
            assert summary["independent_arms_se_observed_only"] == want_se
    null = result["scenarios"]["true_null"]["paired"]["summary"]
    assert null["mean_delta_tokens_integrated_minus_baseline"] == 0
    assert null["mean_delta_elapsed_ms_integrated_minus_baseline"] == 0
    benefit = result["scenarios"]["planted_benefit"]["paired"]["summary"]
    assert benefit["mean_delta_tokens_integrated_minus_baseline"] == -20
    assert benefit["mean_delta_elapsed_ms_integrated_minus_baseline"] == -200
    failure = result["scenarios"]["route_dependent_failure"]
    assert failure["assigned_pairs"] == 3
    assert failure["paired"]["summary"]["complete_pairs_tokens"] == 1
    assert failure["interpretation"] == "HOLD_INCOMPLETE_OR_SAFETY"
    return {
        "status": "METHOD_PASS_SCOPED",
        "scenarios_reconstructed": len(expected_scenarios),
        "pairs_reconstructed": len(ids),
        "attempts_retained": 2 * len(ids),
        "mutation_controls": 7,
        "scope": "synthetic ledger method only",
    }


if __name__ == "__main__":
    with open(sys.argv[1], encoding="utf-8") as f:
        fixture = json.load(f)
    with open(sys.argv[2], encoding="utf-8") as f:
        raw = json.load(f)
    print(json.dumps(audit(fixture, raw), sort_keys=True))
