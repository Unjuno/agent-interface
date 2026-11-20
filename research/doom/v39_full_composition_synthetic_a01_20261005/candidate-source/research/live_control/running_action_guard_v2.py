"""Exact program binding plus one authoritative running-action receipt.

V2 wraps the v1 continuous validity state machine.  It binds every submitted
motor program to the validated planner action and exposes current authority at
the receipt root while retaining the first Executor admission as history.
"""
from copy import deepcopy
import hashlib
import json

from action_validity_admission_v1 import action_fingerprint
from final_action_admission_v2 import record_executor_admission
from running_action_guard_v1 import RunningActionGuard


SCHEMA = "running-action-guard-v2"


def _fingerprint(value):
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"),
                         ensure_ascii=False, allow_nan=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _semantic_commands(value):
    if (type(value) is not list or not value or
            any(type(command) is not dict or set(command) != {"action", "extent"} or
                not isinstance(command["action"], str) or not command["action"] or
                not isinstance(command["extent"], str) or not command["extent"]
                for command in value)):
        raise ValueError("exact semantic action/extent commands required")
    return value


def _semantic_action(value):
    required = {"commands", "contingencies", "action_validity"}
    if type(value) is not dict or not required <= set(value):
        raise ValueError("validated planner action required")
    commands, contingencies, validity = value["commands"], value["contingencies"], value["action_validity"]
    if (type(contingencies) is not list or
            type(validity) is not list or len(validity) != 1):
        raise ValueError("active action commands, contingencies and validity required")
    _semantic_commands(commands)
    indices = []
    for row in contingencies:
        if (type(row) is not dict or
                set(row) != {"after_command", "condition", "commands"} or
                row["condition"] != "no_visible_effect" or
                type(row["after_command"]) is not int or
                not 0 <= row["after_command"] < len(commands) or
                type(row["commands"]) is not list or not row["commands"]):
            raise ValueError("exact bounded contingency required")
        _semantic_commands(row["commands"])
        indices.append(row["after_command"])
    if indices != sorted(set(indices)):
        raise ValueError("unique ordered contingency boundaries required")
    return {"commands": deepcopy(commands), "contingencies": deepcopy(contingencies),
            "action_validity": deepcopy(validity)}


def _program(value):
    expected = {"role", "semantic_commands", "command_indices",
                "contingency_after", "compiled_steps"}
    if (type(value) is not dict or set(value) != expected or
            value["role"] not in ("primary", "fallback") or
            type(value["semantic_commands"]) is not list or
            not value["semantic_commands"] or
            type(value["command_indices"]) is not list or
            len(value["command_indices"]) != len(value["semantic_commands"]) or
            any(type(index) is not int or index < 0 for index in value["command_indices"]) or
            type(value["compiled_steps"]) is not list or
            len(value["compiled_steps"]) != len(value["semantic_commands"]) or
            any(type(step) is not dict for step in value["compiled_steps"])):
        raise ValueError("exact semantic and compiled program binding required")
    if value["role"] == "primary" and value["contingency_after"] is not None:
        raise ValueError("primary program cannot claim a contingency")
    if value["role"] == "fallback" and type(value["contingency_after"]) is not int:
        raise ValueError("fallback contingency boundary required")
    return value


class RunningActionGuardV2:
    def __init__(self, planner_action, final_admission, compiler,
                 compiler_identity):
        action = _semantic_action(planner_action)
        if (type(final_admission) is not dict or
                final_admission.get("schema") != "final-action-admission-v2" or
                final_admission.get("status") != "READY_FOR_FRESH_EXECUTOR_ADMISSION" or
                type(final_admission.get("action_validity")) is not dict or
                final_admission["action_validity"].get("status") != "VALID_CURRENT" or
                final_admission.get("executor_admission") is not None or
                final_admission.get("input_authority_admitted") is not False):
            raise ValueError("fresh final-admission-v2 receipt required")
        validity = final_admission["action_validity"]
        contract = validity["contract"]
        if contract["action_fingerprint"] != action_fingerprint(action["commands"]):
            raise ValueError("immediate contract must bind exact primary commands")
        if not callable(compiler) or not isinstance(compiler_identity, str) or not compiler_identity:
            raise ValueError("deterministic compiler and identity required")
        self.action = action
        self.action_fingerprint = _fingerprint(action)
        self.compiler = compiler
        self.compiler_identity = compiler_identity
        self.final_admission = deepcopy(final_admission)
        self.guard = RunningActionGuard(action["commands"], contract, validity)
        self.program_bindings = []
        self.next_primary_index = 0
        self.fallback_used = False

    def receipt(self):
        running = self.guard.receipt()
        return {
            "schema": SCHEMA,
            "state": running["state"],
            "planner_action": deepcopy(self.action),
            "planner_action_fingerprint": self.action_fingerprint,
            "compiler_identity": self.compiler_identity,
            "historical_first_admission": deepcopy(
                self.final_admission.get("executor_admission")),
            "program_bindings": deepcopy(self.program_bindings),
            "running_validity": running,
            "invalidation": deepcopy(running["invalidation"]),
            "cancellation": deepcopy(running["cancellation"]),
            "current_input_authority": running["current_input_authority"],
            "physical_input_may_be_down": running["physical_input_may_be_down"],
            "physical_release_verified": running["physical_release_verified"],
            "requires_new_decision": running["requires_new_decision"],
            "grants_input_authority": False,
            "authority_semantics": "root current_input_authority is authoritative; historical_first_admission records only the first past Executor acceptance",
        }

    def _validate_plan_position(self, program, branch_evidence):
        role = program["role"]
        if role == "primary":
            indices = program["command_indices"]
            expected = list(range(self.next_primary_index,
                                  self.next_primary_index + len(indices)))
            if (self.fallback_used or indices != expected or
                    indices[-1] >= len(self.action["commands"]) or
                    program["semantic_commands"] !=
                    self.action["commands"][indices[0]:indices[-1] + 1] or
                    branch_evidence is not None):
                raise ValueError("primary program must be the next exact planner slice")
            return
        boundary = program["contingency_after"]
        candidates = [row for row in self.action["contingencies"]
                      if row["after_command"] == boundary]
        evidence_keys = {"after_command", "condition", "primary_program_id",
                         "command_index", "semantic_command", "effect_receipt"}
        latest_binding = self.program_bindings[-1] if self.program_bindings else None
        latest_terminal = self.guard.terminals[-1] if self.guard.terminals else None
        effect = (branch_evidence.get("effect_receipt")
                  if type(branch_evidence) is dict else None)
        if (self.fallback_used or len(candidates) != 1 or
                self.next_primary_index != boundary + 1 or
                program["semantic_commands"] != candidates[0]["commands"] or
                program["command_indices"] != list(range(len(candidates[0]["commands"]))) or
                type(branch_evidence) is not dict or
                set(branch_evidence) != evidence_keys or
                branch_evidence["after_command"] != boundary or
                branch_evidence["condition"] != "no_visible_effect" or
                branch_evidence["command_index"] != boundary or
                branch_evidence["semantic_command"] != self.action["commands"][boundary] or
                type(effect) is not dict or effect.get("result") != "no_visible_effect" or
                effect.get("action") != self.action["commands"][boundary].get("action") or
                effect.get("extent") != self.action["commands"][boundary].get("extent") or
                type(effect.get("effect_observed_ns")) is not int or
                type(latest_binding) is not dict or
                latest_binding["program"]["role"] != "primary" or
                latest_binding["program"]["command_indices"][-1] != boundary or
                latest_binding["accepted"]["id"] != branch_evidence["primary_program_id"] or
                type(latest_terminal) is not dict or
                latest_terminal.get("status") != "completed" or
                latest_terminal.get("id") != branch_evidence["primary_program_id"] or
                not (latest_binding["accepted"]["accepted_ns"] <=
                     effect["effect_observed_ns"] <= latest_terminal["terminal_ns"])):
            raise ValueError("fallback requires the exact authored branch and evidence")

    def admit_program(self, program, submit, accepted, branch_evidence=None):
        program = _program(program)
        self._validate_plan_position(program, branch_evidence)
        recomputed_steps = self.compiler(deepcopy(program["semantic_commands"]))
        if (type(submit) is not dict or set(submit) != {"command", "sent_ns"} or
                type(submit["sent_ns"]) is not int or type(submit["command"]) is not dict or
                set(submit["command"]) != {"op", "id", "expected_sequence",
                                           "valid_until_ns", "steps"} or
                submit["command"]["op"] != "submit" or
                program["compiled_steps"] != recomputed_steps or
                submit["command"]["steps"] != recomputed_steps or
                type(submit["command"]["expected_sequence"]) is not int or
                type(submit["command"]["valid_until_ns"]) is not int or
                type(accepted) is not dict or
                set(accepted) != {"event", "id", "steps", "program_sha256",
                                  "accepted_ns"} or
                accepted["event"] != "accepted" or
                accepted["id"] != submit["command"]["id"] or
                accepted["steps"] != len(program["compiled_steps"]) or
                accepted["program_sha256"] != _fingerprint(recomputed_steps) or
                accepted["accepted_ns"] < submit["sent_ns"] or
                (branch_evidence is not None and
                 accepted["accepted_ns"] <
                 branch_evidence["effect_receipt"]["effect_observed_ns"])):
            raise ValueError("submitted bytes and exact Executor acceptance must agree")
        small = {"event": "accepted", "id": accepted["id"],
                 "accepted_ns": accepted["accepted_ns"]}
        self.guard.admit_program(small)
        if self.final_admission["executor_admission"] is None:
            self.final_admission = record_executor_admission(
                self.final_admission, small)
        record = {"planner_action_fingerprint": self.action_fingerprint,
                  "compiler_identity": self.compiler_identity,
                  "program_fingerprint": _fingerprint(program),
                  "program": deepcopy(program), "submit": deepcopy(submit),
                  "accepted": deepcopy(accepted),
                  "branch_evidence": deepcopy(branch_evidence)}
        self.program_bindings.append(record)
        if program["role"] == "primary":
            self.next_primary_index += len(program["command_indices"])
        else:
            self.fallback_used = True
        return self.receipt()

    def check_current(self, snapshot, controller_decided_ns):
        self.guard.check_current(snapshot, controller_decided_ns)
        return self.receipt()

    def record_cancel_requested(self, event):
        self.guard.record_cancel_requested(event); return self.receipt()

    def record_cancelled_terminal(self, terminal):
        self.guard.record_cancelled_terminal(terminal); return self.receipt()

    def record_completed_terminal(self, terminal, *, final=False):
        self.guard.record_completed_terminal(terminal, final=final)
        return self.receipt()

    def record_action_complete(self):
        self.guard.record_action_complete(); return self.receipt()
