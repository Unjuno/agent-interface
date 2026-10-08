"""Independent read-only audit for Issue #2918 XCalc formal-01."""
from __future__ import annotations

import hashlib
import itertools
import json
import sys
from pathlib import Path

from PIL import Image

RAW, REPORT = Path(sys.argv[1]), Path(sys.argv[2])
REPORT.mkdir(parents=True, exist_ok=True)
FACTS = ("T", "D", "E", "S")
PHASE_SUPPORT = {"PREPARE": frozenset(("T", "D", "S")),
                 "EFFECT_PENDING": frozenset(FACTS),
                 "TERMINAL": frozenset(("E", "S"))}
KNOWN_PIXELS = {
    10: "45946ce77999990a30ca5978ee7b06ba4a614de5d4a89fb85c9fdd8535858e92",
    12: "94514348c165b68d7c0e3ad47c85686029f7411db442a798c2bff9af1b4fd745",
    14: "ce04031117b2471f3af703b8148c83eeb3a120bb84d97225f601f9dffa8da3e5",
}
EXPECTED_ORDER = ["effect_initial_14", "effect_unmasked_10", "effect_masked_12",
                  "prepare_initial_12", "prepare_unmasked_14", "partial_capture",
                  "missing_display_region", "unrecognized_display_99", "stale_capture",
                  "contradictory_xid", "target_replacement", "ambiguous_target",
                  "intent_epoch_mismatch"]


def state_from_value(value):
    return tuple((value >> bit) & 1 for bit in (3, 2, 1, 0))


def semantic(phase, s):
    T, D, E, S = s
    if phase == "PREPARE":
        return "ABORT" if S else "READY" if T and D else "WAIT"
    if phase == "EFFECT_PENDING":
        return "ABORT" if S else "COMPLETE" if E else "CONTINUE" if T and D else "WAIT"
    if phase == "TERMINAL":
        return "ABORT" if S else "COMPLETE" if E else "TERMINAL_UNRESOLVED"
    raise AssertionError(f"unknown phase {phase}")


def minimum_mask(phase, state):
    for size in range(5):
        for idxs in itertools.combinations(range(4), size):
            mask = frozenset(FACTS[i] for i in idxs)
            target = semantic(phase, state)
            safe = all(semantic(phase, other) == target
                       for other in itertools.product((0, 1), repeat=4)
                       if all(other[i] == state[i] for i in idxs))
            if safe:
                return tuple(sorted(mask))
    raise AssertionError("no certificate found")


def value_from_png(p):
    image = Image.open(p).convert("RGB")
    if image.size != (244, 410):
        return None, image.size, None
    digest = hashlib.sha256(image.crop((198, 5, 235, 32)).tobytes()).hexdigest()
    vals = {v: h for v, h in KNOWN_PIXELS.items()}
    for value, expected in vals.items():
        if digest == expected:
            return value, image.size, digest
    return None, image.size, digest


def main():
    candidates = json.loads((RAW / "candidate_results.json").read_text())
    sealed = json.loads((RAW / "sealed_oracle.json").read_text())
    allocation = json.loads((RAW / "allocation.json").read_text())
    assert [r["case"] for r in candidates] == EXPECTED_ORDER
    assert [r["case"] for r in sealed] == EXPECTED_ORDER
    assert len(candidates) == len(sealed) == 13
    assert allocation["cases"] == 13
    assert allocation["api_calls"] == 12

    audited = []
    expected_disposition = {
        "effect_initial_14": "FORWARD", "effect_unmasked_10": "SUPPRESS",
        "effect_masked_12": "FORWARD", "prepare_initial_12": "FORWARD",
        "prepare_unmasked_14": "SUPPRESS", "partial_capture": "YIELD",
        "missing_display_region": "YIELD", "unrecognized_display_99": "YIELD",
        "stale_capture": "YIELD", "contradictory_xid": "YIELD",
        "target_replacement": "YIELD", "ambiguous_target": "YIELD",
        "intent_epoch_mismatch": "YIELD",
    }
    expected_reason = {
        "partial_capture": "incomplete_or_unexpected_xcalc_surface",
        "missing_display_region": "incomplete_or_unexpected_xcalc_surface",
        "unrecognized_display_99": "unrecognized_or_missing_display_value",
        "stale_capture": "stale_observation",
        "contradictory_xid": "observation_binding_mismatch",
        "target_replacement": "binding_or_intent_epoch_changed",
        "ambiguous_target": "ambiguous_target",
        "intent_epoch_mismatch": "binding_or_intent_epoch_changed",
    }
    expected_values = {"effect_initial_14": 14, "effect_unmasked_10": 10,
                       "effect_masked_12": 12, "prepare_initial_12": 12,
                       "prepare_unmasked_14": 14, "partial_capture": 14,
                       "missing_display_region": 14, "unrecognized_display_99": 99,
                       "stale_capture": 14, "contradictory_xid": 14,
                       "target_replacement": 14, "ambiguous_target": None,
                       "intent_epoch_mismatch": 14}
    expected_prior = {
        "effect_unmasked_10": ("EFFECT_PENDING", (1, 1, 1, 0), ("E", "S"), "intent-effect-01"),
        "effect_masked_12": ("EFFECT_PENDING", (1, 0, 1, 0), ("E", "S"), "intent-effect-01"),
        "prepare_unmasked_14": ("PREPARE", (1, 1, 0, 0), ("D", "S", "T"), "intent-prepare-01"),
        "target_replacement": ("EFFECT_PENDING", (1, 1, 1, 0), ("E", "S"), "replace-epoch"),
        "intent_epoch_mismatch": ("EFFECT_PENDING", (1, 1, 1, 0), ("E", "S"), "old-intent"),
    }
    for row, oracle in zip(candidates, sealed):
        tag = row["case"]
        assert oracle["case"] == tag
        assert row["requested_value"] == expected_values[tag]
        assert oracle["requested_value"] == expected_values[tag]
        assert row["disposition"] == expected_disposition[tag]
        assert row["disposition"] in {"FORWARD", "SUPPRESS", "YIELD"}
        assert row["public_api_calls"] == oracle["public_api_calls"]
        assert row["artifact_sha256"] == oracle["artifact_sha256"]
        assert row["capture_ended_ns"] == oracle["capture_ended_ns"]
        assert row["decision_monotonic_ns"] == oracle["decision_monotonic_ns"]
        assert row["side_effect_authority"] is False
        assert row["input_dispatched_by_observer"] is False

        if tag == "ambiguous_target":
            assert row["public_api_calls"] == 0
            assert row["matching_xids"] == sorted(row["matching_xids"])
            assert len(set(row["matching_xids"])) == 2
            assert len(set(row["matching_client_pids"])) == 2
            assert len(set(row["matching_generations"])) == 2
            assert row["reason"] == expected_reason[tag]
            assert row["artifact_sha256"] is None
            assert row["input_trace"] == []
            audited.append({"case": tag, "disposition": "YIELD", "reason": row["reason"],
                            "api_calls": 0, "pass": True})
            continue

        assert row["public_api_calls"] == 1
        assert row["api_status"] == "returned"
        assert row["artifact_sha256"] and row["receipt_sha256"]
        assert row["capture_started_ns"] <= row["capture_ended_ns"] <= row["decision_monotonic_ns"]
        img = RAW / "captures" / Path(row["artifact_path"]).name
        assert img.is_file()
        blob = img.read_bytes()
        assert hashlib.sha256(blob).hexdigest() == row["artifact_sha256"]
        assert row["artifact_sha256"] == oracle["artifact_sha256"]
        assert row["receipt_sha256"] == oracle["receipt_sha256"]
        assert row["observation_epoch"] == row["observation_id"] == oracle["observation_epoch"]
        image_value, dimensions, pixel_digest = value_from_png(img)
        assert row["observed_xid"] == row["binding"]["xid"]
        assert row["observed_client_pid_before"] == row["binding"]["client_pid"]
        assert row["observed_client_pid_after"] == row["binding"]["client_pid"]
        assert row["observed_client_resource_base_before"] == row["binding"]["client_resource_base"]
        assert row["observed_client_resource_base_after"] == row["binding"]["client_resource_base"]
        assert row["candidate_observed_client_pid"] == row["observed_client_pid_before"]
        assert row["candidate_observed_client_resource_base"] == row["observed_client_resource_base_before"]
        if tag == "contradictory_xid":
            assert row["candidate_observed_xid"] != row["binding"]["xid"]
        else:
            assert row["candidate_observed_xid"] == row["binding"]["xid"]
        trace = row["input_trace"]
        assert trace and trace[0]["kind"] == "button" and trace[0]["button"] == "AC"
        assert trace[0]["xid"] == row["binding"]["xid"]
        assert [event["keysym"] for event in trace[1:]] == list(str(expected_values[tag]))
        assert all(a["monotonic_ns"] < b["monotonic_ns"] for a, b in zip(trace, trace[1:]))
        if tag in {"effect_initial_14", "effect_unmasked_10", "effect_masked_12",
                   "prepare_initial_12", "prepare_unmasked_14", "stale_capture",
                   "contradictory_xid", "target_replacement", "intent_epoch_mismatch"}:
            assert image_value == expected_values[tag], (tag, image_value)
            if tag in {"effect_initial_14", "effect_unmasked_10", "effect_masked_12",
                       "prepare_initial_12", "prepare_unmasked_14"}:
                assert row["state"] == list(state_from_value(image_value))
            else:
                assert "state" not in row
        elif tag == "unrecognized_display_99":
            assert dimensions == (244, 410) and image_value is None
        else:
            assert dimensions != (244, 410)

        if tag in {"effect_initial_14", "effect_unmasked_10", "effect_masked_12",
                   "prepare_initial_12", "prepare_unmasked_14"}:
            state = state_from_value(expected_values[tag])
            mask = minimum_mask(row["phase"], state)
            assert tuple(row["mask"]) == mask
            provenance = row["dependency_provenance"]
            assert provenance["public_artifact_sha256"] == row["artifact_sha256"]
            assert provenance["display_roi_pixel_sha256"] == pixel_digest
            assert provenance["display_roi"] == {"x":198,"y":5,"width":37,"height":27}
            assert provenance["value_to_facts"] == dict(zip(FACTS,state))
            assert provenance["required_facts"] == list(FACTS)
            assert provenance["phase_support"] == sorted(PHASE_SUPPORT[row["phase"]])
            assert row["observation_epoch"] == row["observation_id"]
            assert row["certificate_generation_ns"] >= row["capture_ended_ns"]
            assert row["certificate_generation_ns"] <= row["decision_monotonic_ns"]
        if tag in expected_prior:
            phase, state, mask, epoch = expected_prior[tag]
            p = row["prior"]
            assert p["phase"] == phase and tuple(p["state"]) == state
            assert tuple(sorted(p["mask"])) == mask and p["intent_epoch"] == epoch
        if tag in expected_reason:
            assert row["reason"] == expected_reason[tag], (tag, row.get("reason"))
        if tag == "stale_capture":
            assert row["decision_monotonic_ns"] - row["capture_ended_ns"] > 250_000_000
        if tag == "contradictory_xid":
            assert row["binding_conflict_injected"] is True
            assert row["candidate_observed_xid"] != row["binding"]["xid"]
        if tag == "target_replacement":
            assert row["old_xid"] == row["binding"]["xid"]
            assert row["prior"]["binding"]["xid"] == row["old_xid"]
            assert row["prior"]["binding"]["client_pid"] != row["binding"]["client_pid"]
            assert row["prior"]["binding"]["client_resource_base"] == row["binding"]["client_resource_base"]
            assert row["prior"]["binding"]["window_generation"] != row["binding"]["window_generation"]
        if tag == "intent_epoch_mismatch":
            assert row["prior"]["intent_epoch"] != row["intent_epoch"]

        audited.append({"case": tag, "disposition": row["disposition"],
                        "reason": row.get("reason"), "requested_value": expected_values[tag],
                        "image_value": image_value, "image_sha256": row["artifact_sha256"],
                        "api_calls": row["public_api_calls"], "pass": True})

    # Recompute end dispositions and suppression gates independently from the
    # observed values and #1904's declared semantics, without importing it.
    assert semantic("EFFECT_PENDING", state_from_value(14)) == "COMPLETE"
    assert semantic("EFFECT_PENDING", state_from_value(10)) == "COMPLETE"
    assert semantic("EFFECT_PENDING", state_from_value(12)) == "CONTINUE"
    assert semantic("PREPARE", state_from_value(12)) == semantic("PREPARE", state_from_value(14)) == "READY"
    controls = [r for r in candidates if r["case"] in expected_reason]
    assert all(r["disposition"] == "YIELD" for r in controls)
    assert sum(r["disposition"] == "SUPPRESS" for r in candidates) == 2
    assert sum(r["public_api_calls"] for r in candidates) == 12

    by_case = {r["case"]: r for r in candidates}
    phase_support = {"PREPARE": frozenset(("T", "D", "S")),
                     "EFFECT_PENDING": frozenset(FACTS),
                     "TERMINAL": frozenset(("E", "S"))}
    transitions = [("effect_initial_14", "effect_unmasked_10"),
                   ("effect_unmasked_10", "effect_masked_12"),
                   ("prepare_initial_12", "prepare_unmasked_14")]
    control_rows = []
    for source_tag, target_tag in transitions:
        source, target = by_case[source_tag], by_case[target_tag]
        before, after = state_from_value(expected_values[source_tag]), state_from_value(expected_values[target_tag])
        changed = {name for name, a, b in zip(FACTS, before, after) if a != b}
        phase = target["phase"]
        global_decision = "FORWARD" if changed else "SUPPRESS"
        phase_decision = "FORWARD" if changed & phase_support[phase] else "SUPPRESS"
        before_outcome, after_outcome = semantic(phase, before), semantic(phase, after)
        assert target["disposition"] == ("SUPPRESS" if source_tag == "effect_initial_14" and target_tag == "effect_unmasked_10" or source_tag == "prepare_initial_12" else "FORWARD")
        if target["disposition"] == "SUPPRESS":
            assert before_outcome == after_outcome
        control_rows.append({"from":source_tag,"to":target_tag,"changed_facts":sorted(changed),
            "candidate":target["disposition"],"phase_support_control":phase_decision,
            "global_support_control":global_decision,"outcome_before":before_outcome,
            "outcome_after":after_outcome,
            "api_capture_ns":target["capture_ended_ns"]-target["capture_started_ns"],
            "capture_to_certificate_ns":target.get("certificate_generation_ns",target["decision_monotonic_ns"])-target["capture_ended_ns"]})
    assert sum(t["candidate"]=="SUPPRESS" for t in control_rows)==2
    assert sum(t["phase_support_control"]=="SUPPRESS" for t in control_rows)==1
    assert sum(t["global_support_control"]=="SUPPRESS" for t in control_rows)==0

    result = {"decision":"PASS_XCALC_LIVE_CERTIFICATE_TRANSFER_SCOPED",
              "cases":len(candidates),"public_api_calls":sum(r["public_api_calls"] for r in candidates),
              "forward":sum(r["disposition"]=="FORWARD" for r in candidates),
              "suppress":sum(r["disposition"]=="SUPPRESS" for r in candidates),
              "yield":sum(r["disposition"]=="YIELD" for r in candidates),
              "unsafe_suppressions":0,"independent_effect_oracle":"display value -> binary state -> #1904 semantics",
              "control_comparison":{"phase_support_suppressions":1,"candidate_suppressions":2,
                  "incremental_suppressions_vs_phase_support":1,"global_support_suppressions":0,
                  "incremental_suppressions_vs_global":2,"transitions":control_rows},
              "scope":"one XCalc desktop app in pinned private Xvfb, pixel-exact display templates, no model, no external desktop, no product claim",
              "rows":audited}
    (REPORT / "independent_audit.json").write_text(json.dumps(result, sort_keys=True, indent=2)+"\n")
    print(json.dumps({k:result[k] for k in ("decision","cases","public_api_calls","forward","suppress","yield","unsafe_suppressions")}))


if __name__ == "__main__":
    main()
