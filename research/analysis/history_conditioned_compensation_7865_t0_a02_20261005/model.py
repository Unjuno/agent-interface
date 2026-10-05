"""Finite candidate model for Issue #7865 T0 A01."""

from copy import deepcopy

POLICIES = (
    "BLIND_INVERSE",
    "WHOLE_OBJECT_VERSION_GUARD",
    "FIELD_SCOPED_COMPARE_AND_COMPENSATE",
    "NO_AUTO_COMPENSATION",
)


def trace(name):
    base = {"identity": "doc-A", "generation": 0,
            "fields": {"title": "A", "body": "x"},
            "field_revisions": {"title": 0, "body": 0}}
    post = deepcopy(base)
    post["generation"] = 1
    post["fields"]["title"] = "B"
    post["field_revisions"]["title"] = 1
    events = {
        "none": [],
        "disjoint": [{"seq": 1, "field": "body", "value": "y"}],
        "same_field": [{"seq": 1, "field": "title", "value": "C"}],
        "aba": [{"seq": 1, "field": "title", "value": "C"},
                {"seq": 2, "field": "title", "value": "B"}],
        "replacement": [{"seq": 1, "replace": True}],
        "unknown": None,
        "out_of_order": [{"seq": 2, "field": "body", "value": "y"},
                          {"seq": 1, "field": "body", "value": "z"}],
    }[name]
    if events is not None:
        for event in events:
            if event.get("replace"):
                post = {"identity": "doc-B", "generation": 0,
                        "fields": {"title": "B", "body": "x"},
                        "field_revisions": {"title": 0, "body": 0}}
                continue
            post["generation"] += 1
            field = event["field"]
            post["fields"][field] = event["value"]
            post["field_revisions"][field] += 1
    return {"name": name, "base": base, "post_agent": {
        "identity": "doc-A", "generation": 1,
        "fields": {"title": "B", "body": "x"},
        "field_revisions": {"title": 1, "body": 0}},
        "state": post, "events": events,
        "history_known": events is not None,
        "footprint": ["title"], "expected_title": "B",
        "expected_title_revision": 1}


def _outcome(disposition, state, wrote, literal_rollback=False):
    return {"disposition": disposition, "state": state, "wrote": wrote,
            "literal_rollback": literal_rollback}


def decide(case, policy):
    state = deepcopy(case["state"])
    if policy == "BLIND_INVERSE":
        return _outcome("COMPENSATED_NEW_EFFECT", deepcopy(case["base"]),
                        True)
    if policy == "NO_AUTO_COMPENSATION":
        return _outcome("CONFLICT_OR_HOLD", state, False)
    if policy == "WHOLE_OBJECT_VERSION_GUARD":
        eligible = (case["history_known"] and
                    state["identity"] == case["post_agent"]["identity"] and
                    state["generation"] == case["post_agent"]["generation"])
        if not eligible:
            return _outcome("CONFLICT_OR_HOLD", state, False)
        return _outcome("COMPENSATED_NEW_EFFECT", deepcopy(case["base"]),
                        True)
    if policy == "FIELD_SCOPED_COMPARE_AND_COMPENSATE":
        eligible = (case["history_known"] and
                    ["title"] == case["footprint"] and
                    state["identity"] == case["post_agent"]["identity"] and
                    state["fields"].get("title") == case["expected_title"] and
                    state["field_revisions"].get("title") ==
                    case["expected_title_revision"] and
                    all(a["seq"] < b["seq"] for a, b in
                        zip(case["events"], case["events"][1:])))
        if not eligible:
            return _outcome("CONFLICT_OR_HOLD", state, False)
        state["fields"]["title"] = "A"
        state["generation"] += 1
        state["field_revisions"]["title"] += 1
        return _outcome("COMPENSATED_NEW_EFFECT", state, True)
    raise ValueError("unrecognized policy")


def all_results():
    return {name: {policy: decide(trace(name), policy) for policy in POLICIES}
            for name in ("none", "disjoint", "same_field", "aba",
                         "replacement", "unknown", "out_of_order")}
