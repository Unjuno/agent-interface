"""Bounded local continuation over a planner-authored GUI interface.

Symbols are references only.  The caller must provide fresh observation,
admission, execution and effect-verification adapters.  No model adapter is
available inside this runtime.
"""
import copy
import time


YIELD_REASONS = {
    "unknown_state", "ambiguous_state", "stale_observation", "stale_symbol",
    "missing_symbol", "association_changed", "authority_unavailable",
    "effect_failed", "effect_unavailable", "no_progress", "cancelled",
    "budget_exhausted", "delivery_uncertain", "execution_failed",
}
SCALAR = (str, int, bool)


def _exact(value, fields, label):
    if type(value) is not dict or set(value) != set(fields):
        raise ValueError(f"exact {label} fields required")


def _name(value, label):
    if type(value) is not str or not value or len(value) > 64:
        raise ValueError(f"bounded nonempty {label} required")


def validate(interface):
    """Validate and copy the deliberately small v1 interface language."""
    _exact(interface, {"format", "interface_id", "session_scope", "surface",
                       "predicates", "symbols", "actions", "method"},
           "interface")
    if interface["format"] != "compiled-gui-interface-v1":
        raise ValueError("unsupported interface format")
    for key in ("interface_id", "session_scope", "surface"):
        _name(interface[key], key)
    predicates = interface["predicates"]
    if (type(predicates) is not list or not 1 <= len(predicates) <= 32 or
            len(set(predicates)) != len(predicates)):
        raise ValueError("one to 32 unique predicates required")
    for value in predicates:
        _name(value, "predicate")

    symbols = interface["symbols"]
    if type(symbols) is not dict or not 1 <= len(symbols) <= 32:
        raise ValueError("one to 32 symbols required")
    for alias, symbol in symbols.items():
        _name(alias, "symbol alias")
        _exact(symbol, {"kind", "target_reference", "identity_predicate",
                        "dependencies"}, "symbol")
        if symbol["kind"] != "target_reference":
            raise ValueError("v1 supports target references only")
        _name(symbol["target_reference"], "target reference")
        _name(symbol["identity_predicate"], "identity predicate")
        if symbol["identity_predicate"] not in predicates:
            raise ValueError("symbol identity predicate must be declared")
        deps = symbol["dependencies"]
        if (type(deps) is not list or not deps or
                any(type(item) is not str or item not in predicates for item in deps)):
            raise ValueError("symbol dependencies must be declared predicates")
        forbidden = {"authority", "authorization", "point", "coordinate", "steps"}
        if forbidden & set(symbol):
            raise ValueError("symbols cannot carry input authority or raw actions")

    actions = interface["actions"]
    if type(actions) is not dict or not 1 <= len(actions) <= 16:
        raise ValueError("one to 16 actions required")
    for name, action in actions.items():
        _name(name, "action")
        _exact(action, {"target_symbol", "operation", "expected_effect"}, "action")
        if action["target_symbol"] not in symbols:
            raise ValueError("action target symbol must exist")
        _name(action["operation"], "operation")
        expected_effect = action["expected_effect"]
        if type(expected_effect) is not dict or not expected_effect:
            raise ValueError("nonempty expected effect conditions required")
        for predicate, expected in expected_effect.items():
            if predicate not in predicates or type(expected) not in SCALAR:
                raise ValueError("expected effect must use declared scalar predicates")

    method = interface["method"]
    _exact(method, {"name", "version", "initial_state", "max_transitions",
                    "max_runtime_ms", "states"}, "method")
    for key in ("name", "version", "initial_state"):
        _name(method[key], key)
    if (type(method["max_transitions"]) is not int or
            not 1 <= method["max_transitions"] <= 16):
        raise ValueError("max_transitions must be one to 16")
    if (type(method["max_runtime_ms"]) is not int or
            not 1 <= method["max_runtime_ms"] <= 10_000):
        raise ValueError("max_runtime_ms must be one to 10000")
    states = method["states"]
    if (type(states) is not dict or not 1 <= len(states) <= 16 or
            method["initial_state"] not in states):
        raise ValueError("bounded states including initial_state required")
    for state_name, state in states.items():
        _name(state_name, "state")
        _exact(state, {"branches"}, "state")
        branches = state["branches"]
        if type(branches) is not list or not 1 <= len(branches) <= 16:
            raise ValueError("one to 16 branches per state required")
        for branch in branches:
            _exact(branch, {"when", "outcome", "action", "next_state", "reason"},
                   "branch")
            conditions = branch["when"]
            if type(conditions) is not dict or not conditions:
                raise ValueError("nonempty branch conditions required")
            for predicate, expected in conditions.items():
                if predicate not in predicates or type(expected) not in SCALAR:
                    raise ValueError("declared scalar branch conditions required")
            outcome = branch["outcome"]
            if outcome == "action":
                if branch["action"] not in actions or branch["next_state"] not in states:
                    raise ValueError("action branch requires known action and next state")
                if branch["reason"] is not None:
                    raise ValueError("action branch cannot carry a yield reason")
            elif outcome == "complete":
                if any(branch[key] is not None for key in ("action", "next_state", "reason")):
                    raise ValueError("complete branch has no action, next state or reason")
            elif outcome == "yield":
                if (branch["action"] is not None or branch["next_state"] is not None or
                        branch["reason"] not in YIELD_REASONS):
                    raise ValueError("yield branch requires one typed reason")
            else:
                raise ValueError("branch outcome must be action, complete or yield")
    return copy.deepcopy(interface)


def _observation(value, interface, previous_sequence):
    _exact(value, {"sequence", "captured_ns", "surface", "predicates",
                   "evidence_ref", "evidence_digest"}, "observation")
    if type(value["sequence"]) is not int or value["sequence"] <= previous_sequence:
        return None, "stale_observation"
    if type(value["captured_ns"]) is not int or value["captured_ns"] < 0:
        raise ValueError("nonnegative captured_ns required")
    if value["surface"] != interface["surface"]:
        return None, "association_changed"
    if type(value["predicates"]) is not dict:
        raise ValueError("predicate object required")
    if set(value["predicates"]) - set(interface["predicates"]):
        raise ValueError("undeclared observation predicate")
    for result in value["predicates"].values():
        if type(result) not in SCALAR:
            raise ValueError("scalar predicate result required")
    _name(value["evidence_ref"], "evidence reference")
    _name(value["evidence_digest"], "evidence digest")
    return copy.deepcopy(value), None


def run(interface, adapters, *, clock=time.perf_counter_ns):
    """Execute a bounded method locally; return an auditable compact receipt."""
    interface = validate(interface)
    required = {"observe", "admit", "execute", "verify_effect", "cancelled"}
    if type(adapters) is not dict or any(not callable(adapters.get(k)) for k in required):
        raise ValueError("observe/admit/execute/verify_effect/cancelled adapters required")
    journal = adapters.get("journal", lambda event: None)
    if not callable(journal):
        raise ValueError("journal adapter must be callable")
    started = clock()
    deadline = started + interface["method"]["max_runtime_ms"] * 1_000_000
    state = interface["method"]["initial_state"]
    previous_sequence = -1
    previous_digest = None
    pending_effect = None
    transitions = []
    observations = []
    critical_events = []

    def emit(event):
        row = copy.deepcopy(event)
        journal(row)
        if row["event"] in {"branch_selected", "admission_refused",
                            "action_terminal", "effect_checked", "runtime_finished"}:
            critical_events.append(row)

    def finish(outcome, reason):
        ended = clock()
        receipt = {
            "format": "compiled-gui-runtime-receipt-v1",
            "interface_id": interface["interface_id"],
            "method": interface["method"]["name"],
            "method_version": interface["method"]["version"],
            "session_scope": interface["session_scope"],
            "outcome": outcome,
            "reason": reason,
            "completed_transitions": len(transitions),
            "frontier_model_resumptions": 0,
            "observations": observations,
            "transitions": transitions,
            "critical_events": critical_events,
            "latest_evidence_ref": observations[-1]["evidence_ref"] if observations else None,
            "pending_effect": copy.deepcopy(pending_effect),
            "started_ns": started,
            "ended_ns": ended,
            "elapsed_ns": ended - started,
            "input_authority": "admission_per_action_only",
            "raw_evidence_retention": "adapter_responsibility_unverified",
        }
        final_event = {"event": "runtime_finished", "outcome": outcome,
                       "reason": reason, "completed_transitions": len(transitions)}
        emit(final_event)
        receipt["critical_events"] = critical_events
        return receipt

    while True:
        if adapters["cancelled"]():
            return finish("SAFE_YIELD", "cancelled")
        if clock() > deadline:
            return finish("SAFE_YIELD", "budget_exhausted")
        raw = adapters["observe"]({"state": state,
                                    "required_predicates": interface["predicates"]})
        observation, refusal = _observation(raw, interface, previous_sequence)
        if refusal:
            return finish("SAFE_YIELD", refusal)
        previous_sequence = observation["sequence"]
        observations.append({key: copy.deepcopy(observation[key]) for key in
                             ("sequence", "captured_ns", "evidence_ref",
                              "evidence_digest", "predicates")})
        emit({"event": "observation_recorded", "state": state,
              "sequence": observation["sequence"],
              "evidence_ref": observation["evidence_ref"]})

        if pending_effect is not None:
            if observation["evidence_digest"] == previous_digest:
                return finish("SAFE_YIELD", "no_progress")
            expected = pending_effect["expected_effect"]
            observed = observation["predicates"]
            unknown = any(key not in observed or observed.get(key) == "unknown"
                          for key in expected)
            mismatch = any(observed.get(key) != value
                           for key, value in expected.items())
            if unknown or mismatch:
                status = "unavailable" if unknown else "failed"
                emit({"event": "effect_checked", "action": pending_effect["action"],
                      "status": status, "evidence_ref": observation["evidence_ref"],
                      "verifier": "compiled_predicate_condition"})
                return finish("SAFE_YIELD", "effect_" + status)
            effect = adapters["verify_effect"]({
                "expected_effect": copy.deepcopy(expected),
                "action": pending_effect["action"],
                "effect_ref": pending_effect["effect_ref"],
                "observation": copy.deepcopy(observation),
            })
            _exact(effect, {"status", "evidence_ref"}, "effect verdict")
            if effect["status"] not in {"succeeded", "failed", "unavailable"}:
                raise ValueError("typed effect status required")
            emit({"event": "effect_checked", "action": pending_effect["action"],
                  "status": effect["status"], "evidence_ref": effect["evidence_ref"]})
            if effect["status"] != "succeeded":
                reason = "effect_failed" if effect["status"] == "failed" else "effect_unavailable"
                return finish("SAFE_YIELD", reason)
            pending_effect = None

        matches = []
        for branch in interface["method"]["states"][state]["branches"]:
            if all(observation["predicates"].get(key) == expected
                   for key, expected in branch["when"].items()):
                matches.append(branch)
        if not matches:
            return finish("SAFE_YIELD", "unknown_state")
        if len(matches) != 1:
            return finish("SAFE_YIELD", "ambiguous_state")
        branch = matches[0]
        emit({"event": "branch_selected", "state": state,
              "outcome": branch["outcome"], "action": branch["action"],
              "matched_conditions": copy.deepcopy(branch["when"]),
              "evidence_ref": observation["evidence_ref"]})
        if branch["outcome"] == "complete":
            return finish("TASK_SUCCEEDED", "method_complete")
        if branch["outcome"] == "yield":
            return finish("SAFE_YIELD", branch["reason"])

        if len(transitions) >= interface["method"]["max_transitions"]:
            return finish("SAFE_YIELD", "budget_exhausted")
        if adapters["cancelled"]():
            return finish("SAFE_YIELD", "cancelled")
        action_name = branch["action"]
        action = interface["actions"][action_name]
        symbol = interface["symbols"][action["target_symbol"]]
        admission = adapters["admit"]({
            "interface_id": interface["interface_id"],
            "session_scope": interface["session_scope"],
            "action": action_name,
            "operation": action["operation"],
            "symbol": copy.deepcopy(symbol),
            "observation": copy.deepcopy(observation),
        })
        _exact(admission, {"eligible", "status", "authorization",
                           "expected_sequence", "valid_until_ns"}, "admission")
        if type(admission["eligible"]) is not bool:
            raise ValueError("boolean admission eligibility required")
        if not admission["eligible"]:
            mapping = {"stale": "stale_symbol", "missing": "missing_symbol",
                       "association_changed": "association_changed"}
            reason = mapping.get(admission["status"], "authority_unavailable")
            emit({"event": "admission_refused", "action": action_name,
                  "status": admission["status"], "reason": reason})
            return finish("SAFE_YIELD", reason)
        if (admission["status"] != "revalidated" or
                type(admission["authorization"]) is not str or
                not admission["authorization"] or
                admission["expected_sequence"] != observation["sequence"] or
                type(admission["valid_until_ns"]) is not int or
                admission["valid_until_ns"] <= clock()):
            raise ValueError("fresh revalidated admission required")
        if adapters["cancelled"]():
            return finish("SAFE_YIELD", "cancelled")
        terminal = adapters["execute"]({
            "action": action_name,
            "operation": action["operation"],
            "authorization": admission["authorization"],
            "expected_sequence": admission["expected_sequence"],
            "valid_until_ns": admission["valid_until_ns"],
        })
        _exact(terminal, {"status", "action_id", "effect_ref", "release"},
               "execution terminal")
        release = terminal["release"]
        _exact(release, {"verified", "keys_down", "buttons_down"}, "release")
        released = (release["verified"] is True and release["keys_down"] == [] and
                    release["buttons_down"] == [])
        emit({"event": "action_terminal", "action": action_name,
              "status": terminal["status"], "action_id": terminal["action_id"],
              "release_verified": released})
        if not released:
            return finish("RUNTIME_FAILED", "execution_failed")
        if terminal["status"] != "completed":
            reason = ("delivery_uncertain" if terminal["status"] == "delivery_uncertain"
                      else "execution_failed")
            return finish("SAFE_YIELD", reason)
        _name(terminal["action_id"], "action id")
        _name(terminal["effect_ref"], "effect reference")
        transitions.append({
            "from_state": state,
            "to_state": branch["next_state"],
            "action": action_name,
            "matched_conditions": copy.deepcopy(branch["when"]),
            "observation_sequence": observation["sequence"],
            "evidence_ref": observation["evidence_ref"],
            "action_id": terminal["action_id"],
            "effect_ref": terminal["effect_ref"],
            "release_verified": True,
        })
        pending_effect = {"action": action_name,
                          "expected_effect": copy.deepcopy(action["expected_effect"]),
                          "effect_ref": terminal["effect_ref"]}
        previous_digest = observation["evidence_digest"]
        state = branch["next_state"]
