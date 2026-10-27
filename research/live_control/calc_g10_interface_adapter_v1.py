"""Translate the retained two-action G10 graph to fresh-reference guarded form.

This structural adapter preserves task predicates and state transitions. It does
not choose a target, perform OCR, mint references, execute input, or certify an
effect. The caller supplies the runtime scope/surface and distinct second alias.
"""
from copy import deepcopy

from runtime.core_v1.compiled_gui import validate


def adapt_retained_g10_graph_v1(interface, *, session_scope, surface,
                                second_reference="a1_second",
                                second_symbol="second_anchor"):
    """Split G10's shared anchor into a primary and a fresh second reference.

    Accept only the retained two-save G10 graph shape: two sequential actions,
    one shared target symbol, and a terminal state. Unknown variants fail closed.
    """
    if type(interface) is not dict:
        raise ValueError("G10 interface mapping required")
    if any(type(v) is not str or not v for v in
           (session_scope, surface, second_reference, second_symbol)):
        raise ValueError("nonempty scope, surface, second reference and symbol required")

    graph = deepcopy(interface)
    actions = graph.get("actions")
    symbols = graph.get("symbols")
    method = graph.get("method")
    if (graph.get("format") != "compiled-gui-interface-v1" or
            type(actions) is not dict or set(actions) != {"first", "second"} or
            type(symbols) is not dict or set(symbols) != {"anchor"} or
            type(method) is not dict):
        raise ValueError("unsupported retained G10 graph structure")

    anchor = symbols["anchor"]
    first, second = actions["first"], actions["second"]
    expected_action = {
        "operation": "enter_product",
        "expected_effect": {"row_visible": True},
    }
    if (type(anchor) is not dict or anchor.get("kind") != "target_reference" or
            type(anchor.get("target_reference")) is not str or not anchor["target_reference"] or
            type(anchor.get("identity_predicate")) is not str or
            type(anchor.get("dependencies")) is not list or
            any(type(name) is not str or not name for name in anchor["dependencies"]) or
            any(type(action) is not dict or
                {k: action.get(k) for k in expected_action} != expected_action or
                action.get("target_symbol") != "anchor" for action in (first, second))):
        raise ValueError("retained G10 anchor/action contract differs")
    if second_reference == anchor["target_reference"] or second_symbol in symbols:
        raise ValueError("second target must use a distinct alias and symbol")

    states = method.get("states")
    if (method.get("initial_state") != "first" or method.get("max_transitions") != 2 or
            type(states) is not dict or set(states) != {"first", "second", "done"}):
        raise ValueError("retained G10 two-action state contract differs")

    def sole_branch(state):
        value = states[state]
        branches = value.get("branches") if type(value) is dict else None
        if type(branches) is not list or len(branches) != 1:
            raise ValueError("retained G10 branch contract differs")
        return branches[0]

    first_branch = sole_branch("first")
    second_branch = sole_branch("second")
    done_branch = sole_branch("done")
    if (first_branch != {"when": {"ready": True}, "outcome": "action",
                         "action": "first", "next_state": "second", "reason": None} or
            second_branch != {"when": {"ready": True}, "outcome": "action",
                              "action": "second", "next_state": "done", "reason": None} or
            done_branch != {"when": {"ready": True}, "outcome": "complete",
                            "action": None, "next_state": None, "reason": None}):
        raise ValueError("retained G10 transitions differ")

    graph["session_scope"] = session_scope
    graph["surface"] = surface
    second_anchor = deepcopy(anchor)
    second_anchor["target_reference"] = second_reference
    graph["symbols"][second_symbol] = second_anchor
    graph["actions"]["second"]["target_symbol"] = second_symbol
    return validate(graph)
