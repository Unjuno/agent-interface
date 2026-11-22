"""Join a separately recorded orphan recovery to a retained action/effect run.

The source action remains UNKNOWN; recovery is a distinct attempt.
"""
from __future__ import annotations
import hashlib, json
from typing import Any
from comparison_measurement_v1 import validate_measured_run
from effect_attribution_v1 import adjudicate_effect

class OrphanRecoveryHandoffError(ValueError):
    pass

def _fail(message: str) -> None:
    raise OrphanRecoveryHandoffError(message)

def _canonical(value: Any) -> bytes:
    return json.dumps(value,sort_keys=True,separators=(",",":"),ensure_ascii=False,allow_nan=False).encode("utf-8")

def adapt_orphan_recovery_effect(*, measured: dict[str, Any], action_public: dict[str, Any],
        recovery_envelope: dict[str, Any], recovery_raw_report: dict[str, Any], effect_receipt: dict[str, Any], custody_record: dict[str, Any]) -> dict[str, Any]:
    """Validate exact source/effect/recovery identities without upgrading UNKNOWN.

    `recovery_envelope` is the retained public-call runner record containing
    `initial_recovery_receipt`; it is distinct from the source action results.
    """
    try:
        validate_measured_run(measured)
    except Exception as error:
        _fail(f"measured run invalid: {type(error).__name__}: {error}")
    if type(action_public) is not dict or type(recovery_envelope) is not dict or type(recovery_raw_report) is not dict or type(effect_receipt) is not dict or type(custody_record) is not dict:
        _fail("all retained evidence inputs must be objects")
    ledger=measured["task_ledger"]; measurement=measured["measurement"]
    actions=[e for e in ledger["events"] if e.get("kind")=="tool_call" and e.get("method")=="interface_dispatch"]
    scores=[e for e in ledger["events"] if e.get("kind")=="task_score"]
    lookups=[e for e in ledger["events"] if e.get("kind")=="tool_call" and e.get("call_id")==effect_receipt.get("lookup_tool_call_id") and e.get("method")=="interface_results"]
    if len(actions)!=1 or len(scores)!=1 or len(lookups)!=1 or scores[0].get("independent") is not True:
        _fail("one dispatch, one exact results lookup, and one independent score are required")
    score=scores[0]; task=ledger["task"]
    for key in ("task_id","scorer_id","scorer_sha256","task_success","state_sha256"):
        expected={"task_id":task.get("task_id"),"scorer_id":score.get("scorer_id"),"scorer_sha256":task.get("scorer_sha256"),"task_success":score.get("task_success"),"state_sha256":score.get("state_sha256")}[key]
        if effect_receipt.get(key)!=expected: _fail(f"effect receipt {key} does not match measured ledger")
    if type(effect_receipt.get("before_task_success")) is not bool or type(effect_receipt.get("task_success")) is not bool or not isinstance(effect_receipt.get("before_state_sha256"),str):
        _fail("effect receipt lacks a boolean baseline and terminal score")
    if effect_receipt["task_success"] and (effect_receipt["before_task_success"] or effect_receipt["before_state_sha256"]==effect_receipt["state_sha256"]):
        _fail("successful task effect must differ from an unsuccessful baseline")
    dispatch=actions[0].get("result",{}).get("result",{}).get("content",[])
    texts=[x.get("text") for x in dispatch if x.get("type")=="text" and isinstance(x.get("text"),str)]
    if len(texts)!=1: _fail("dispatch journal has no unique public response")
    try: dispatch_public=json.loads(texts[0])
    except (TypeError,ValueError): _fail("dispatch response is not JSON")
    source_action=action_public.get("action")
    try: lookup_public=json.loads(lookups[0]["result"]["result"]["content"][0]["text"])
    except (KeyError,IndexError,TypeError,ValueError): _fail("exact results lookup response is not valid JSON")
    lookup_action=lookup_public.get("action")
    if type(source_action) is not dict or type(lookup_action) is not dict:
        _fail("exact source action receipt is missing")
    dispatch_raw=dispatch_public.get("receipt",{}).get("source",{}).get("raw_report",{}); action_id=dispatch_public.get("call_id"); operation=dispatch_raw.get("operation_id"); generation=dispatch_raw.get("target_generation")
    if (action_id!=effect_receipt.get("action_call_id") or action_public.get("call_id")!=action_id or
        lookup_public.get("call_id")!=action_id or lookup_action.get("operation_id")!=operation or
        lookup_action.get("target_generation")!=generation or lookup_action.get("status")!="unknown" or
        source_action.get("operation_id")!=operation or source_action.get("target_generation")!=generation or
        effect_receipt.get("action_operation_id")!=operation or effect_receipt.get("target_generation")!=generation):
        _fail("source action, dispatch, and effect receipt identities do not join")
    if (source_action.get("status")!="unknown" or source_action.get("input_dispatched") is not True or
        source_action.get("release_confirmed") is not False or source_action.get("task_success") is not None or
        source_action.get("replay_allowed") is not False):
        _fail("source action must remain UNKNOWN, release-unconfirmed, and replay-denied")
    if (custody_record.get("classification")!="UNKNOWN_RELEASE_UNCONFIRMED_STOPPED" or
        custody_record.get("operation_id")!=operation or custody_record.get("target_generation")!=generation or
        custody_record.get("do_not_replay") is not True or custody_record.get("observed_producer_live") is not False):
        _fail("source custody record does not bind the exact UNKNOWN action")
    expected_custody_hash=hashlib.sha256(_canonical(custody_record)).hexdigest()
    recovery_outer=recovery_envelope.get("initial_recovery_receipt")
    if type(recovery_outer) is not dict: _fail("public orphan recovery receipt is missing")
    recovery=recovery_outer.get("recovery_receipt")
    if type(recovery) is not dict: _fail("orphan recovery lifecycle receipt is missing")
    if (recovery_raw_report.get("status")!="recovered" or recovery_raw_report.get("recovery_status")!="recovered" or
        recovery_raw_report.get("source_operation_id")!=operation or recovery_raw_report.get("source_target_generation")!=generation or
        recovery_raw_report.get("source_custody_canonical_sha256")!=expected_custody_hash or
        _canonical(recovery_raw_report.get("recovery_receipt"))!=_canonical(recovery) or
        recovery_outer.get("status")!="recovered" or recovery_outer.get("recovery_status")!="recovered" or
        recovery_outer.get("source_action_status")!="unknown" or recovery_outer.get("source_operation_id")!=operation or
        recovery_outer.get("source_target_generation")!=generation or recovery_outer.get("task_success") is not None or
        recovery_outer.get("replay_allowed") is not False or recovery_outer.get("source_custody_canonical_sha256")!=expected_custody_hash):
        _fail("orphan recovery envelope does not preserve/bind the source custody")
    recovery_id=recovery.get("recovery_id"); release=recovery.get("release_receipt",{}); release_detail=release.get("release_receipt",{}); readback=recovery.get("readback",{})
    if (recovery.get("status")!="recovered" or recovery.get("operation_id")!=operation or
        recovery.get("source_target_generation")!=generation or recovery.get("release_confirmed") is not True or
        recovery.get("late_input_horizon_verified") is not True or release.get("release_accepted") is not True or
        release.get("operation_id")!=operation or release.get("recovery_id")!=recovery_id or
        release_detail.get("verified") is not True or readback.get("neutral") is not True or
        readback.get("operation_id")!=operation or readback.get("recovery_id")!=recovery_id):
        _fail("separate recovery lacks exact release, neutral readback, or horizon proof")
    horizon=recovery.get("late_input_horizon_ns"); release_ns=recovery.get("late_input_release_received_monotonic_ns");
    start=recovery.get("late_input_observation_start_monotonic_ns"); end=recovery.get("late_input_observation_end_monotonic_ns");
    count=recovery.get("late_input_observation_count"); gap=recovery.get("late_input_max_observed_gap_ns"); allowed=recovery.get("late_input_max_sample_gap_ns")
    if (type(horizon) is not int or horizon<=0 or type(release_ns) is not int or type(start) is not int or
        type(end) is not int or end<start or end-release_ns<horizon or type(count) is not int or count<2 or
        type(gap) is not int or gap<0 or type(allowed) is not int or allowed<=0 or gap>allowed):
        _fail("late-input horizon bounds are invalid or insufficient")
    attribution=measurement.get("effect_attribution")
    effect_ns=effect_receipt.get("effect_interval_ns",{}).get("upper_ns")
    if (type(attribution) is not dict or attribution.get("effect_observed_ns")!=effect_ns or
        attribution.get("authority_expiry_ns")!=action_public.get("standard_program",{}).get("authority",{}).get("expires_at_ns") or
        attribution.get("release_received_ns")!=release_ns or attribution.get("horizon_end_ns")!=end):
        _fail("measured attribution is not bound to the exact action and orphan recovery times")
    adjudication=adjudicate_effect(task_success=score["task_success"],effect_observed_ns=effect_ns,
        authority_expiry_ns=attribution["authority_expiry_ns"],release_received_ns=release_ns,horizon_end_ns=end)
    if effect_receipt.get("effect_interval_ns",{}).get("lower_ns") is not None and effect_ns is not None and effect_receipt["effect_interval_ns"]["lower_ns"]>effect_ns:
        _fail("effect interval endpoints are reversed")
    return {"schema":"agent-interface/orphan-recovery-effect-handoff-v1",
        "task_id":task["task_id"],"source_action":{"call_id":action_id,"operation_id":operation,"target_generation":generation,
            "status":"unknown","input_dispatched":True,"release_confirmed":False,"task_success":None,"replay_allowed":False},
        "recovery_attempt":{"call_id":recovery_outer.get("call_id"),"recovery_id":recovery_id,"status":"recovered",
            "release_confirmed":True,"neutral_readback":True,"horizon_ns":horizon,"horizon_observation_count":count,
            "horizon_max_sample_gap_ns":gap,"horizon_gap_limit_ns":allowed,"source_custody_sha256":expected_custody_hash},
        "effect":{"factual_task_success":adjudication["factual_task_success"],
            "effect_timing":adjudication["effect_timing"],"eligible_task_success":adjudication["eligible_task_success"],
            "effect_observed_ns":effect_ns,"authority_expiry_ns":attribution["authority_expiry_ns"],
            "recovery_release_received_ns":release_ns,"recovery_horizon_end_ns":end},
        "measurement":{"elapsed_ns":measurement["elapsed_ns"],"model_delivered_image_count":len(measurement["model_delivered_images"]),
            "local_observation_count":len(measurement["local_observations"]),"provider_usage":"unavailable"},
        "raw_join":{"effect_receipt_sha256":hashlib.sha256(_canonical(effect_receipt)).hexdigest(),
            "recovery_envelope_sha256":hashlib.sha256(_canonical(recovery_envelope)).hexdigest(),
            "recovery_raw_report_sha256":hashlib.sha256(_canonical(recovery_raw_report)).hexdigest(),
            "action_public_sha256":hashlib.sha256(_canonical(action_public)).hexdigest()},
        "inference":"recovery is a separate attempt; it does not upgrade source action status or authorize replay"}
