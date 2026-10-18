"""Candidate finite external-write/recovery classifier; standard library only."""


def replay(case, model):
    if not case["coverage_complete"]:
        return None, "UNKNOWN_COVERAGE"
    state = {"object_id": model["target"]["object_id"], "generation": model["target"]["generation"],
             "global_revision": model["agent_write"]["global_revision"],
             "fields": {"x": model["agent_write"]["after"], "y": 0},
             "field_revisions": {"x": model["agent_write"]["field_revision"], "y": 0}}
    previous_seq = 0
    previous_global = state["global_revision"]
    for event in case["events"]:
        if event["seq"] != previous_seq + 1:
            return None, "UNKNOWN_EVENT_ORDER_OR_GAP"
        previous_seq = event["seq"]
        if event["global_revision"] != previous_global + 1:
            return None, "UNKNOWN_REVISION_GAP"
        if event["kind"] == "replace":
            state = {"object_id": event["object_id"], "generation": event["generation"],
                     "global_revision": event["global_revision"], "fields": dict(event["fields"]),
                     "field_revisions": {"x": 0, "y": 0}}
        elif event["kind"] == "write":
            if (event["object_id"], event["generation"]) != (state["object_id"], state["generation"]):
                return None, "UNKNOWN_TARGET_LINEAGE"
            state["fields"][event["field"]] = event["value"]
            state["field_revisions"][event["field"]] = event["field_revision"]
            state["global_revision"] = event["global_revision"]
        else:
            return None, "UNKNOWN_EVENT_KIND"
        previous_global = event["global_revision"]
    if state["global_revision"] != model["agent_write"]["global_revision"] + len(case["events"]):
        return None, "UNKNOWN_UNJOURNALED_REVISION"
    if state != case["snapshot"]:
        return None, "UNKNOWN_SNAPSHOT_DISAGREEMENT"
    return state, "HISTORY_RECONCILED"


def evaluate(case, model):
    state, history_status = replay(case, model)
    if state is None:
        return {"history": history_status, "disposition": "UNKNOWN", "field_scoped": "UNKNOWN",
                "whole_object": "UNKNOWN", "blind_inverse": "NOT_RUN", "compensation": None}
    original = {"x": 0, "y": 0}
    # A blind whole-object snapshot inverse restores both fields to the
    # original artifact and therefore erases a later disjoint writer's value.
    blind = dict(original)
    whole = "ELIGIBLE" if state["global_revision"] == model["agent_write"]["global_revision"] else "CONFLICT"
    if state["object_id"] != model["target"]["object_id"] or state["generation"] != model["target"]["generation"]:
        field_policy = "CONFLICT_TARGET_REPLACED"
    elif state["fields"].get("x") != model["agent_write"]["after"] or state["field_revisions"].get("x") != model["agent_write"]["field_revision"]:
        field_policy = "CONFLICT_OWNED_FIELD_CHANGED"
    else:
        field_policy = "ELIGIBLE"
    compensation = None
    if field_policy == "ELIGIBLE":
        result = dict(state["fields"])
        result["x"] = model["agent_write"]["before"]
        compensation = {"event_id": "compensate-x-new-effect", "kind": "semantic_compensation",
                        "fields_after": result, "preserved_disjoint_fields": True,
                        "claims_exact_rollback": False}
    return {"history": history_status, "disposition": "RECONCILED", "field_scoped": field_policy,
            "whole_object": whole, "blind_inverse": {"fields_after": blind,
            "lost_disjoint_y": state["fields"].get("y") != 0 and blind.get("y") == 0},
            "compensation": compensation}


def run(model):
    return [{"case_id": case["id"], **evaluate(case, model)} for case in model["cases"]]
