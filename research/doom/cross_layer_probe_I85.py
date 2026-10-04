"""Run the frozen v3 release producer through the frozen direct analyzer."""
import json
import sys
import threading
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import analyze_map01_direct_retained_input_v1 as analyzer
import test_doom_retained_input_backend_v3 as producer_fixture


def admission(token, key, admitted_ns, input_ack_ns):
    return {"event": "input_admission", "intent_token": token, "key": key,
            "admitted_ns": admitted_ns, "input_ack_ns": input_ack_ns}


def through_fake_backend(token, receipt_token):
    owner = producer_fixture.Owner(owner_id="owner-1", receipt_token=receipt_token)
    backend = producer_fixture.make_backend({"a"}, owner, token=token)
    backend.raw("a", False)
    receipt = backend.emitted[0]
    return receipt


def through_actual_wrapper(cleanup_during_up=False, prior_cleanup=False):
    return producer_fixture.actual_wrapper_batch_evidence(
        cleanup_during_up=cleanup_during_up, prior_cleanup=prior_cleanup
    )


def evaluate(case, receipt, identity, mutate_order=False, owner_records=None):
    start = receipt["release_call_started_ns"]
    events = [admission(identity, "a", start - 20, start - 10), dict(receipt)]
    if mutate_order:
        events[-1]["release_call_returned_ns"] = start - 1
    result = analyzer.analyze(events)
    return {
        "case": case,
        "producer_verified": receipt.get("owner_transition_verified") is True,
        "producer_receipt": receipt,
        "owner_records": owner_records or [],
        "events": events,
        "consumer_result": result,
    }


def main():
    results = []
    normal = through_fake_backend("intent-1", "intent-1")
    results.append(evaluate("normal_nonempty_identity", normal, "intent-1"))

    prior = through_actual_wrapper(prior_cleanup=True)
    results.append(evaluate("prior_cleanup_outside_bracket", prior["receipt"],
                            "intent-1", owner_records=prior["owner_records"]))

    overlapping = through_actual_wrapper(cleanup_during_up=True)
    results.append(evaluate("cleanup_inside_release_bracket", overlapping["receipt"],
                            "intent-1", owner_records=overlapping["owner_records"]))

    for name, token, receipt_token in (
        ("empty_identity", "", ""),
        ("integer_identity", 17, 17),
        ("mismatched_identity", "intent-1", "other"),
        ("missing_identity", None, None),
    ):
        receipt = through_fake_backend(token, receipt_token)
        results.append(evaluate(name, receipt, token))

    results.append(evaluate("consumer_timestamp_order_mutation", normal,
                            "intent-1", mutate_order=True))
    output = {
        "schema": "map01-release-producer-analyzer-cross-layer-candidate-I85-v1",
        "case_count": len(results),
        "results": results,
    }
    print(json.dumps(output, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
