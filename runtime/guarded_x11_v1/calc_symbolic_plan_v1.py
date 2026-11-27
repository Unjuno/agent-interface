"""Validation and binding for planner-authored, bounded Calc task plans.

This module accepts only a small declarative graph for the registered two-cell
workflow. It does not grant target authority, execute input, or score an
artifact. Current aliases, scope, and surface are supplied by the trusted
caller after a fresh observation and review.
"""
import copy
import hashlib
import json
import re

from runtime.core_v1.compiled_gui import validate as validate_compiled_interface


PLAN_SCHEMA = "agent-interface/calc-symbolic-plan-v1"
_PREDICATES = {"context_ok", "blank", "cells_match"}
_MAX_PLAN_BYTES = 16 * 1024


def _bounded_name(value, label):
    if (type(value) is not str or not value
            or len(value) > 64
            or not re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]*", value)):
        raise ValueError(f"invalid {label}")


def _bounded_identity(value, label):
    """Validate opaque runtime scope/surface IDs without parsing their syntax."""
    if (type(value) is not str or not value or len(value) > 128
            or not value.isascii()
            or any(ord(char) < 0x21 or ord(char) > 0x7e for char in value)):
        raise ValueError(f"invalid {label}")


def validate_and_bind_calc_plan(plan, *, session_scope, surface,
                                target_aliases):
    """Validate one planner graph and bind only fresh server-minted aliases.

    ``plan`` contains semantic symbol/action/state names, never coordinates,
    aliases, values, paths, callbacks, commands, or raw input steps. Task values
    are supplied independently to the registered task adapter.
    """
    _bounded_identity(session_scope, "session scope")
    _bounded_identity(surface, "surface")
    if (type(target_aliases) is not dict or set(target_aliases) != {"entry", "save"}
            or any(type(alias) is not str
                   or not re.fullmatch(r"[a-z][a-z0-9_]{0,31}", alias)
                   for alias in target_aliases.values())
            or target_aliases["entry"] == target_aliases["save"]):
        raise ValueError("fresh distinct entry/save aliases required")

    if type(plan) is not dict or set(plan) != {
            "schema", "interface_id", "predicates", "symbols", "actions", "method"}:
        raise ValueError("exact Calc symbolic-plan fields required")
    try:
        encoded = json.dumps(plan, sort_keys=True, separators=(",", ":"),
                             allow_nan=False).encode("utf-8")
    except (TypeError, ValueError) as error:
        raise ValueError("Calc plan must be finite JSON data") from error
    if len(encoded) > _MAX_PLAN_BYTES:
        raise ValueError("Calc plan exceeds byte limit")
    if plan["schema"] != PLAN_SCHEMA:
        raise ValueError("unsupported Calc plan schema")
    _bounded_name(plan["interface_id"], "interface ID")

    predicates = plan["predicates"]
    if (type(predicates) is not list or len(predicates) != len(_PREDICATES)
            or any(type(item) is not str for item in predicates)
            or set(predicates) != _PREDICATES):
        raise ValueError("Calc plan must declare exactly the registered predicates")

    symbols = plan["symbols"]
    if type(symbols) is not dict or len(symbols) != 2:
        raise ValueError("Calc plan requires two semantic target symbols")
    operation_symbols = {}
    for symbol_name, symbol in symbols.items():
        _bounded_name(symbol_name, "symbol name")
        if (type(symbol) is not dict
                or set(symbol) != {"role", "identity_predicate", "dependencies"}
                or type(symbol["role"]) is not str
                or symbol["role"] not in {"entry", "save"}
                or symbol["identity_predicate"] != "context_ok"
                or type(symbol["dependencies"]) is not list):
            raise ValueError("invalid Calc symbol declaration")
        role = symbol["role"]
        expected_dependencies = ( ["context_ok"] if role == "entry" else
                                  ["context_ok", "cells_match"] )
        if symbol["dependencies"] != expected_dependencies or role in operation_symbols:
            raise ValueError("Calc symbol dependencies/roles must match the registered contract")
        operation_symbols[role] = symbol_name
    if set(operation_symbols) != {"entry", "save"}:
        raise ValueError("one entry and one save symbol required")

    actions = plan["actions"]
    if type(actions) is not dict or len(actions) != 2:
        raise ValueError("Calc plan requires exactly two registered actions")
    operation_actions = {}
    bound_actions = {}
    for action_name, action in actions.items():
        _bounded_name(action_name, "action name")
        if (type(action) is not dict
                or set(action) != {"operation", "target_symbol", "expected_effect"}
                or type(action["operation"]) is not str
                or action["operation"] not in {"enter_pair", "request_save"}
                or type(action["target_symbol"]) is not str
                or type(action["expected_effect"]) is not dict
                or action["expected_effect"] != {"cells_match": True}):
            raise ValueError("Calc actions must use the registered bounded operations")
        operation = action["operation"]
        role = "entry" if operation == "enter_pair" else "save"
        if (role in operation_actions
                or action["target_symbol"] != operation_symbols[role]):
            raise ValueError("Calc action target or operation order contract is invalid")
        operation_actions[role] = action_name
        bound_actions[action_name] = {
            "target_symbol": action["target_symbol"],
            "operation": operation,
            "expected_effect": {"cells_match": True},
        }
    if set(operation_actions) != {"entry", "save"}:
        raise ValueError("one enter_pair and one request_save action required")

    method = plan["method"]
    if type(method) is not dict or set(method) != {
            "name", "version", "initial_state", "max_transitions",
            "max_runtime_ms", "states"}:
        raise ValueError("exact bounded Calc method fields required")
    _bounded_name(method["name"], "method name")
    if (type(method["version"]) is not str
            or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,31}", method["version"])):
        raise ValueError("invalid method version")
    states = method["states"]
    if (type(states) is not dict or len(states) != 3
            or method["max_transitions"] != 2
            or type(method["max_transitions"]) is not int
            or type(method["max_runtime_ms"]) is not int
            or not 1 <= method["max_runtime_ms"] <= 10_000
            or type(method["initial_state"]) is not str
            or method["initial_state"] not in states):
        raise ValueError("Calc method must be a bounded three-state, two-action graph")
    for state_name, state in states.items():
        _bounded_name(state_name, "state name")
        if type(state) is not dict or set(state) != {"branches"}:
            raise ValueError("invalid Calc state")
        if type(state["branches"]) is not list or len(state["branches"]) != 1:
            raise ValueError("each Calc state requires exactly one branch")

    initial_state = method["initial_state"]
    enter_branch = states[initial_state]["branches"][0]
    if (type(enter_branch) is not dict
            or enter_branch.get("when") != {"context_ok": True, "blank": True}
            or enter_branch.get("outcome") != "action"
            or enter_branch.get("action") != operation_actions["entry"]
            or enter_branch.get("reason") is not None):
        raise ValueError("initial Calc state must enter only on a fresh blank-sheet cue")
    filled_state = enter_branch.get("next_state")
    if type(filled_state) is not str or filled_state not in states or filled_state == initial_state:
        raise ValueError("entry action must transition to a distinct state")
    save_branch = states[filled_state]["branches"][0]
    if (type(save_branch) is not dict
            or save_branch.get("when") != {"context_ok": True, "cells_match": True}
            or save_branch.get("outcome") != "action"
            or save_branch.get("action") != operation_actions["save"]
            or save_branch.get("reason") is not None):
        raise ValueError("Save may follow only a fresh matching-cells observation")
    saved_state = save_branch.get("next_state")
    if (type(saved_state) is not str or saved_state not in states
            or saved_state in {initial_state, filled_state}):
        raise ValueError("Save must transition to a distinct handoff state")
    handoff = states[saved_state]["branches"][0]
    if (type(handoff) is not dict
            or handoff.get("when") != {"context_ok": True}
            or handoff.get("outcome") != "yield"
            or handoff.get("action") is not None
            or handoff.get("next_state") is not None
            or handoff.get("reason") != "effect_unavailable"):
        raise ValueError("Calc Save must hand off as effect_unavailable")

    bound_symbols = {}
    for role, symbol_name in operation_symbols.items():
        bound_symbols[symbol_name] = {
            "kind": "target_reference",
            "target_reference": target_aliases[role],
            "identity_predicate": "context_ok",
            "dependencies": copy.deepcopy(symbols[symbol_name]["dependencies"]),
        }
    interface = {
        "format": "compiled-gui-interface-v1",
        "interface_id": plan["interface_id"],
        "session_scope": session_scope,
        "surface": surface,
        "predicates": copy.deepcopy(predicates),
        "symbols": bound_symbols,
        "actions": bound_actions,
        "method": copy.deepcopy(method),
    }
    validated = validate_compiled_interface(interface)
    return {
        "interface": validated,
        "plan_sha256": hashlib.sha256(encoded).hexdigest(),
        "plan_bytes": len(encoded),
    }
