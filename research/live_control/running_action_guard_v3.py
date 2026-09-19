"""Two-phase revocation: physical release can precede program terminal closure."""
from copy import deepcopy

from running_action_guard_v2 import RunningActionGuardV2


SCHEMA = "running-action-guard-v3"
RELEASED_PENDING = "REVOKED_INPUT_RELEASED_AWAITING_TERMINAL"


class RunningActionGuardV3(RunningActionGuardV2):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.active_intent = None
        self.early_releases = []

    def receipt(self):
        receipt = super().receipt()
        receipt["schema"] = SCHEMA
        receipt["active_intent"] = deepcopy(self.active_intent)
        receipt["early_physical_releases"] = deepcopy(self.early_releases)
        pending = self.active_intent is not None and bool(self.early_releases)
        receipt["program_terminal_pending"] = pending
        if pending:
            receipt.update({"state": RELEASED_PENDING,
                "current_input_authority": False,
                "physical_input_may_be_down": False,
                "physical_release_verified": True,
                "requires_new_decision": True})
        return receipt

    def admit_program(self, program, submit, accepted, branch_evidence=None):
        if (type(accepted) is not dict or
                set(accepted) != {"event", "id", "steps", "program_sha256",
                                  "intent_token", "accepted_ns"} or
                not isinstance(accepted["intent_token"], str) or
                not accepted["intent_token"]):
            raise ValueError("Executor intent token required")
        token = accepted["intent_token"]
        old = {key: accepted[key] for key in
               ("event", "id", "steps", "program_sha256", "accepted_ns")}
        super().admit_program(program, submit, old, branch_evidence=branch_evidence)
        self.active_intent = {"id": accepted["id"], "intent_token": token,
                              "accepted_ns": accepted["accepted_ns"]}
        return self.receipt()

    def record_input_released(self, event):
        expected = {"event", "id", "intent_token", "owner_release",
                    "published_ns", "program_terminal_pending",
                    "grants_input_authority"}
        release = event.get("owner_release") if type(event) is dict else None
        cancellation = self.guard.cancellation
        if (self.guard.state != "CANCEL_REQUIRED" or cancellation is None or
                self.active_intent is None or type(event) is not dict or
                set(event) != expected or event["event"] != "input_released" or
                event["id"] != self.active_intent["id"] or
                event["intent_token"] != self.active_intent["intent_token"] or
                event["program_terminal_pending"] is not True or
                event["grants_input_authority"] is not False or
                type(release) is not dict or release.get("event") != "owner_release" or
                release.get("reason") not in ("cancelled", "stop_requested") or
                release.get("verified") is not True or release.get("keys_down") != [] or
                release.get("buttons_down") != [] or
                type(release.get("verified_ns")) is not int or
                type(event.get("published_ns")) is not int or
                not cancellation["requested_ns"] <= release["verified_ns"] <= event["published_ns"]):
            raise ValueError("exact lease-bound empty physical release required")
        if self.early_releases:
            raise ValueError("physical release already recorded")
        self.early_releases.append(deepcopy(event))
        return self.receipt()

    def record_cancelled_terminal(self, terminal):
        if self.early_releases:
            early_ns = self.early_releases[-1]["owner_release"]["verified_ns"]
            release = terminal.get("release") if type(terminal) is dict else None
            if type(release) is not dict or release.get("verified_ns", -1) < early_ns:
                raise ValueError("terminal cleanup cannot precede physical release")
        result = super().record_cancelled_terminal(terminal)
        self.active_intent = None
        result = self.receipt()
        result["program_terminal_pending"] = False
        return result

    def record_completed_terminal(self, terminal, *, final=False):
        result = super().record_completed_terminal(terminal, final=final)
        self.active_intent = None
        return self.receipt()
