"""Construction checks, not the one-shot frozen runner invocation."""

import audit
import candidate
import oracle
import runner


def test_baseline_all_policies_support_the_synthetic_claim():
    case = runner.scenarios()["BASELINE"]
    for policy in candidate.POLICIES:
        assert candidate.evaluate(policy, case["evidence"], case["current_revision"])[0] == "SUPPORTED"


def test_each_single_dimension_gate_rejects_its_targeted_fault():
    cases = runner.scenarios()
    assert candidate.evaluate("DYNAMIC_CASE", cases["DEPENDENCY_CHANGED"]["evidence"], 2)[0] == "STALE"
    assert candidate.evaluate("STATIC_CASE", cases["MISSING_CAUSALITY"]["evidence"], 1)[0] == "PARTIAL"
    assert candidate.evaluate("DEFEATER_AWARE", cases["DIRECT_DEFEATER"]["evidence"], 1)[0] == "CONFLICTED"
    assert candidate.evaluate("INDEPENDENCE_AWARE", cases["CORRELATED_DUPLICATE"]["evidence"], 1)[0] == "PARTIAL"


def test_composite_rejects_all_seeded_faults_and_supports_baseline():
    cases = runner.scenarios()
    assert candidate.evaluate("COMPOSITE_DYNAMIC_CASE", cases["BASELINE"]["evidence"], 1)[0] == "SUPPORTED"
    for name in set(cases) - {"BASELINE"}:
        assert candidate.evaluate("COMPOSITE_DYNAMIC_CASE", cases[name]["evidence"], cases[name]["current_revision"])[0] != "SUPPORTED"


def test_flat_arm_exposes_unsound_support_for_all_seeded_faults():
    cases = runner.scenarios()
    for name in set(cases) - {"BASELINE"}:
        assert candidate.evaluate("FLAT_RECEIPTS", cases[name]["evidence"], cases[name]["current_revision"])[0] == "SUPPORTED"
        assert oracle.expected("COMPOSITE_DYNAMIC_CASE", cases[name])[0] != "SUPPORTED"


def test_unsound_supported_count_drops_across_assurance_gates():
    raw = runner.build_raw()
    cases = raw["scenario_inputs"]
    counts = {}
    for policy in candidate.POLICIES:
        count = 0
        for row in raw["rows"]:
            if row["policy"] != policy:
                continue
            truth, _ = oracle.top_claim_truth(cases[row["case_id"]])
            count += row["status"] == "SUPPORTED" and truth != "SUPPORTED"
        counts[policy] = count
    assert counts == {
        "FLAT_RECEIPTS": 5,
        "STATIC_CASE": 4,
        "DYNAMIC_CASE": 2,
        "DEFEATER_AWARE": 1,
        "INDEPENDENCE_AWARE": 1,
        "COMPOSITE_DYNAMIC_CASE": 0,
    }


def test_historical_graph_revision_digest_is_unchanged():
    history = runner.scenarios()["NEGATIVE_SUCCESSOR"]["history"][0]
    assert history["before_digest"] == history["after_digest"] == runner.canonical_digest(history["graph"])


def test_raw_audit_and_six_corruption_controls():
    raw = runner.build_raw()
    assert audit.audit(raw) == []
    controls = audit.corruption_controls(raw)
    assert len(controls) == 6
    assert all(row["rejected"] for row in controls)


def test_no_policy_output_is_authority_or_effect():
    raw = runner.build_raw()
    assert len(raw["rows"]) == 36
    assert all(row["authority_created"] is False for row in raw["rows"])
    assert all(row["external_effect_calls"] == 0 for row in raw["rows"])
