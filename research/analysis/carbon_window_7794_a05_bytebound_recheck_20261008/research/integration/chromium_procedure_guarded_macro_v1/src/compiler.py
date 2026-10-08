from __future__ import annotations
import copy

EXPECTED_METHOD = {
    "first_action": "enter_exact_token",
    "continue_when": "field_pixels_changed_and_submit_revalidated",
    "second_action": "activate_submit",
    "complete_when": "submission_pixels_changed_then_independent_score",
}

class CompileError(ValueError):
    pass


def _validate_example(example):
    grounding = example.get("grounding") or {}
    if grounding.get("method") != EXPECTED_METHOD:
        raise CompileError("unknown_method_vocabulary")
    if set(grounding) != {"field_point", "submit_point", "method"}:
        raise CompileError("grounding_shape")
    for key in ("field_point", "submit_point"):
        point = grounding[key]
        if not (isinstance(point, list) and len(point) == 2 and all(isinstance(x, int) for x in point)):
            raise CompileError("point_shape")


def compile_literal(example):
    _validate_example(example)
    return {
        "schema": "literal_replay_v1",
        "kind": "LITERAL_REPLAY",
        "parameters": ["token"],
        "context_guard": copy.deepcopy(example["context"]),
        "field_point": copy.deepcopy(example["grounding"]["field_point"]),
        "submit_point": copy.deepcopy(example["grounding"]["submit_point"]),
        "procedure": copy.deepcopy(EXPECTED_METHOD),
        "authority": "external",
    }


def compile_guarded(example):
    _validate_example(example)
    # The compiler consumes role names and the frontier-authored method, but deliberately
    # discards the concrete task1 points and token. Target identity is a runtime parameter.
    roles = sorted(k[:-6] for k in example["grounding"] if k.endswith("_point"))
    if roles != ["field", "submit"]:
        raise CompileError("unrecognized_target_roles")
    artifact = {
        "schema": "guarded_typed_macro_v1",
        "kind": "GUARDED_TYPED_MACRO",
        "parameters": ["token", "field_handle", "submit_handle"],
        "procedure": copy.deepcopy(EXPECTED_METHOD),
        "steps": [
            {"op": "require_current_target", "target": "$field_handle"},
            {"op": "activate_target", "target": "$field_handle"},
            {"op": "select_all"},
            {"op": "enter_parameter", "parameter": "$token"},
            {"op": "wait_for", "predicate": "field_pixels_changed_and_submit_revalidated"},
            {"op": "require_current_target", "target": "$submit_handle"},
            {"op": "activate_target", "target": "$submit_handle"},
            {"op": "external_verify", "predicate": "submission_pixels_changed_then_independent_score"},
        ],
        "authority": "external",
        "on_unknown": "YIELD",
    }
    validate_guarded_artifact(artifact, forbidden_token=example.get("token"))
    return artifact


def validate_guarded_artifact(artifact, forbidden_token=None):
    if artifact.get("kind") != "GUARDED_TYPED_MACRO":
        raise CompileError("kind")
    if artifact.get("authority") != "external" or artifact.get("on_unknown") != "YIELD":
        raise CompileError("authority_or_unknown_policy")
    if artifact.get("parameters") != ["token", "field_handle", "submit_handle"]:
        raise CompileError("parameters")
    if artifact.get("procedure") != EXPECTED_METHOD:
        raise CompileError("procedure")
    serial = repr(artifact)
    if forbidden_token and forbidden_token in serial:
        raise CompileError("fixed_token_leak")
    # Absolute target coordinate vocabulary is forbidden. This does not forbid unrelated numbers
    # elsewhere because the macro schema itself intentionally contains no x/y/point fields.
    def walk(v):
        if isinstance(v, dict):
            for k, x in v.items():
                if k in {"x", "y", "point", "field_point", "submit_point", "coordinates"}:
                    raise CompileError("coordinate_leak")
                walk(x)
        elif isinstance(v, list):
            for x in v: walk(x)
    walk(artifact)
    allowed_ops = {"require_current_target","activate_target","select_all","enter_parameter","wait_for","external_verify"}
    if any(step.get("op") not in allowed_ops for step in artifact.get("steps", [])):
        raise CompileError("unknown_macro_op")
    return True


def evaluate_literal(artifact, state):
    if state["context"] != artifact["context_guard"]:
        return {"decision":"YIELD","reason":"context_mismatch","pointer_events":0,"emitted":None,"matches_current_target":False,"historical_coordinates_emitted":False}
    emitted = {"field_point": artifact["field_point"], "submit_point": artifact["submit_point"]}
    ev = state["evaluator"]
    match = emitted["field_point"] == ev["current_field_point"] and emitted["submit_point"] == ev["current_submit_point"]
    return {"decision":"ACTION","reason":None,"pointer_events":2,"emitted":emitted,"matches_current_target":match,"historical_coordinates_emitted":not match}


def evaluate_guarded(artifact, state):
    validate_guarded_artifact(artifact)
    ctl = state["controller"]
    if ctl.get("field_status") != "eligible":
        return {"decision":"YIELD","reason":"field_handle_not_current","pointer_events":0,"emitted":None,"matches_current_target":False,"historical_coordinates_emitted":False}
    if not ctl.get("field_handle"):
        return {"decision":"YIELD","reason":"field_handle_missing","pointer_events":0,"emitted":None,"matches_current_target":False,"historical_coordinates_emitted":False}
    if ctl.get("submit_status") != "eligible":
        return {"decision":"YIELD","reason":"submit_handle_not_current","pointer_events":1,"emitted":{"field_handle":ctl["field_handle"]},"matches_current_target":False,"historical_coordinates_emitted":False}
    if not ctl.get("submit_handle"):
        return {"decision":"YIELD","reason":"submit_handle_missing","pointer_events":1,"emitted":{"field_handle":ctl["field_handle"]},"matches_current_target":False,"historical_coordinates_emitted":False}
    emitted = {"field_handle":ctl["field_handle"],"submit_handle":ctl["submit_handle"],"token_parameter":state["token"]}
    ev = state["evaluator"]
    match = emitted["field_handle"] == ev["current_field_handle"] and emitted["submit_handle"] == ev["current_submit_handle"]
    return {"decision":"ACTION","reason":None,"pointer_events":2,"emitted":emitted,"matches_current_target":match,"historical_coordinates_emitted":False}
