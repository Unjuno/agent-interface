"""No-input state machine for continuous action-validity enforcement.

The guard consumes observations that an Executor program already produces.  It
does not capture, issue input, cancel a program, or grant authority.  A caller
must perform cancellation and return the exact cancellation/release receipts.
"""
from copy import deepcopy

from action_validity_admission_v1 import evaluate_action_validity


SCHEMA = "running-action-guard-v1"
ACTIVE = "INPUT_ACTIVE"
READY = "READY_FOR_PROGRAM_ADMISSION"
BETWEEN = "BETWEEN_PROGRAMS_REQUIRES_FRESH_CHECK"
CANCEL = "CANCEL_REQUIRED"
REVOKED = "REVOKED_ACTION_NOT_CURRENT"
REJECTED = "REJECTED_BEFORE_PROGRAM_ADMISSION"
COMPLETED = "COMPLETED"


def _accepted(value):
    expected = {"event", "id", "accepted_ns"}
    if (type(value) is not dict or set(value) != expected or
            value["event"] != "accepted" or not isinstance(value["id"], str) or
            not value["id"] or type(value["accepted_ns"]) is not int or
            value["accepted_ns"] < 0):
        raise ValueError("exact Executor acceptance required")
    return value


def _released_terminal(value, status, after_ns):
    if (type(value) is not dict or value.get("event") != "terminal" or
            value.get("status") != status or type(value.get("id")) is not str or
            type(value.get("terminal_ns")) is not int or
            value["terminal_ns"] < after_ns):
        raise ValueError(f"exact {status} terminal required")
    release = value.get("release")
    if (type(release) is not dict or release.get("verified") is not True or
            release.get("keys_down") != [] or release.get("buttons_down") != [] or
            type(release.get("verified_ns")) is not int or
            not after_ns <= release["verified_ns"] <= value["terminal_ns"]):
        raise ValueError("terminal must prove empty physical input release")
    return value


class RunningActionGuard:
    """Track one exact action across one or more bounded Executor programs."""

    def __init__(self, action, contract, initial_validity):
        if (type(initial_validity) is not dict or
                initial_validity.get("status") != "VALID_CURRENT"):
            raise ValueError("initial VALID_CURRENT result required")
        recomputed = evaluate_action_validity(
            action, contract, initial_validity["snapshot"],
            initial_validity["controller_decided_ns"])
        if recomputed != initial_validity or initial_validity.get("grants_input_authority") is not False:
            raise ValueError("initial validity must reproduce exactly")
        self.action = deepcopy(action)
        self.contract = deepcopy(contract)
        self.state = READY
        self.active_program = None
        self.admissions = []
        self.terminals = []
        self.checks = [deepcopy(initial_validity)]
        self.invalidation = None
        self.cancellation = None
        self.last_sequence = initial_validity["snapshot"]["sequence"]
        self.last_capture_ns = initial_validity["snapshot"]["capture_ns"]

    def receipt(self):
        return {
            "schema": SCHEMA,
            "state": self.state,
            "action": deepcopy(self.action),
            "contract": deepcopy(self.contract),
            "active_program": deepcopy(self.active_program),
            "program_admissions": deepcopy(self.admissions),
            "program_terminals": deepcopy(self.terminals),
            "validity_checks": deepcopy(self.checks),
            "invalidation": deepcopy(self.invalidation),
            "cancellation": deepcopy(self.cancellation),
            "current_input_authority": self.state == ACTIVE,
            "physical_input_may_be_down": self.active_program is not None,
            "physical_release_verified": self.active_program is None,
            "requires_new_decision": self.state in (CANCEL, REVOKED, REJECTED),
            "grants_input_authority": False,
        }

    def admit_program(self, accepted):
        accepted = _accepted(accepted)
        if self.state != READY or self.active_program is not None:
            raise ValueError("fresh READY guard required for program admission")
        if any(row["id"] == accepted["id"] for row in self.admissions):
            raise ValueError("program id must be unique within the action")
        latest = self.checks[-1]
        if (latest["status"] != "VALID_CURRENT" or
                accepted["accepted_ns"] < latest["controller_decided_ns"]):
            raise ValueError("program acceptance must follow current validity")
        self.active_program = deepcopy(accepted)
        self.admissions.append(deepcopy(accepted))
        self.state = ACTIVE
        return self.receipt()

    def check_current(self, snapshot, controller_decided_ns):
        if self.state not in (ACTIVE, BETWEEN):
            raise ValueError("current evidence is accepted only during or between programs")
        if (snapshot.get("sequence", -1) <= self.last_sequence or
                snapshot.get("capture_ns", -1) <= self.last_capture_ns):
            invalidation = {
                "kind": "observation_order",
                "reason": "running_observation_not_strictly_newer",
                "snapshot": deepcopy(snapshot),
                "controller_decided_ns": controller_decided_ns,
                "requires_new_decision": True,
                "grants_input_authority": False,
            }
            self.invalidation = invalidation
            self.state = CANCEL if self.active_program is not None else REJECTED
            return self.receipt()
        result = evaluate_action_validity(
            self.action, self.contract, snapshot, controller_decided_ns)
        self.last_sequence = snapshot["sequence"]
        self.last_capture_ns = snapshot["capture_ns"]
        self.checks.append(deepcopy(result))
        if result["status"] == "VALID_CURRENT":
            if self.state == BETWEEN:
                self.state = READY
            return self.receipt()
        self.invalidation = {
            "kind": "action_validity",
            "result": deepcopy(result),
            "requires_new_decision": True,
            "grants_input_authority": False,
        }
        self.state = CANCEL if self.active_program is not None else REJECTED
        return self.receipt()

    def record_cancel_requested(self, event):
        if (self.state != CANCEL or self.active_program is None or
                type(event) is not dict or
                set(event) != {"event", "id", "matched", "requested_ns"} or
                event["event"] != "cancel_requested" or
                event["id"] != self.active_program["id"] or
                event["matched"] is not True or
                type(event["requested_ns"]) is not int):
            raise ValueError("matching active-program cancellation required")
        invalidated_ns = (self.invalidation.get("result", {}) or {}).get(
            "controller_decided_ns", self.invalidation.get("controller_decided_ns"))
        if event["requested_ns"] < invalidated_ns:
            raise ValueError("cancellation cannot precede invalidation")
        self.cancellation = deepcopy(event)
        return self.receipt()

    def record_cancelled_terminal(self, terminal):
        if self.state != CANCEL or self.cancellation is None or self.active_program is None:
            raise ValueError("cancel receipt required before cancelled terminal")
        terminal = _released_terminal(terminal, "cancelled", self.cancellation["requested_ns"])
        if terminal["id"] != self.active_program["id"]:
            raise ValueError("terminal must match active program")
        self.terminals.append(deepcopy(terminal))
        self.active_program = None
        self.state = REVOKED
        return self.receipt()

    def record_completed_terminal(self, terminal, *, final):
        if self.state != ACTIVE or self.active_program is None or type(final) is not bool:
            raise ValueError("active program and explicit final flag required")
        terminal = _released_terminal(
            terminal, "completed", self.active_program["accepted_ns"])
        if terminal["id"] != self.active_program["id"]:
            raise ValueError("terminal must match active program")
        self.terminals.append(deepcopy(terminal))
        self.active_program = None
        self.state = COMPLETED if final else BETWEEN
        return self.receipt()

    def record_action_complete(self):
        """Close an action after its last completed program and branch decision."""
        if self.state != BETWEEN or self.active_program is not None:
            raise ValueError("completed program boundary required")
        self.state = COMPLETED
        return self.receipt()
