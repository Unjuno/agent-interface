from __future__ import annotations
import copy
SOURCE_SHA256 = "9506457a371565b489b5e1b9f7313c05d3f13a28bd5448b4b2944211ee4f313e"
POSITIVE = ("KILL_COUNT_INCREASE", "MAP_EXIT")
NEGATIVE = ("DEATH_COUNT_INCREASE", "PLAYER_DEAD", "EPISODE_FINISHED_NO_EXIT")
CASES = (
    ("01-KILL_COUNT_INCREASE", "KILL_COUNT_INCREASE", "positive", True),
    ("02-MAP_EXIT", "MAP_EXIT", "positive", True),
    ("03-FUTURE_SCORER_EVENT_V3", "FUTURE_SCORER_EVENT_V3", "positive", True),
    ("04-KILL_COUNT_INCREASEE", "KILL_COUNT_INCREASEE", "positive", True),
    ("05-PLAYER_DEAD", "PLAYER_DEAD", "negative", False),
)
A05_ERROR = "positive useful event kind is outside v2 producer vocabulary"
def _expected_case(sequence, label, kind, polarity, useful):
    event = {"schema":"independent-progress-event-v2","event_sequence":sequence,"observed_ns":200,"kind":kind,"polarity":polarity,"useful":useful,"controller_visible":False}
    rows = []
    if polarity == "positive" and useful:
        rows = [{"event_sequence":sequence,"kind":kind,"detection_interval_ns":[100,200],"status":"SINGLE_POSSIBLE_INTENT_ENVELOPE","reason":"one_verified_envelope_spans_detection_interval","possible_intent_tokens":["intent-a"],"intent_token":None,"causal_attribution":"NOT_ESTABLISHED"}]
    a04 = {"accepted":True,"rows":rows}
    if polarity == "positive" and useful and kind not in POSITIVE:
        a05 = {"accepted":False,"error":A05_ERROR}
    else:
        a05 = {"accepted":True,"rows":copy.deepcopy(rows)}
    return {"case":label,"event":event,"a04":a04,"a05":a05}
def _expected_document():
    return {"schema":"scorer-feedback-attribution-a05-raw-v1","producer_vocab":list(POSITIVE),"producer_negative_vocab":list(NEGATIVE),"cases":[_expected_case(i,*case) for i,case in enumerate(CASES,1)],"formal_live_allocation":False,"scope":"synthetic schema-construction; no task/game/model/input"}
def _same_typed_value(actual, expected):
    if type(actual) is not type(expected): return False
    if isinstance(expected, dict):
        return actual.keys() == expected.keys() and all(_same_typed_value(actual[k],expected[k]) for k in expected)
    if isinstance(expected, list):
        return len(actual)==len(expected) and all(_same_typed_value(a,e) for a,e in zip(actual,expected))
    return actual == expected
def audit_document(document):
    if not _same_typed_value(document,_expected_document()):
        raise ValueError("raw candidate differs from the exact preregistered five-case contract")
