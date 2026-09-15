"""Prepare a candidate after verified release while terminal reconciliation continues."""
import copy
import hashlib
import json

try:
    from .release_pending_action_v1 import PendingAction
except ImportError:  # direct script/research runner use
    from release_pending_action_v1 import PendingAction


SCHEMA = "release-aware-preparation-v1"


def _sha(value):
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"),
                         ensure_ascii=False, allow_nan=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


class ReleaseAwarePreparation:
    """A no-authority overlap boundary; fresh admission remains external."""
    def __init__(self, action_id):
        self.action = PendingAction(action_id)
        self.started_ns = None
        self.completed_ns = None
        self.candidate = None
        self.candidate_sha256 = None
        self.uncertainty = None

    def ingest(self, reply):
        state = self.action.ingest(reply)
        if state["uncertainty"] is not None and self.uncertainty is None:
            self.uncertainty = state["uncertainty"]
        return self.view()

    def begin(self, started_ns):
        release = self.action.released
        if (self.uncertainty is not None or release is None or
                self.started_ns is not None or type(started_ns) is not int or
                started_ns < release["published_ns"]):
            raise ValueError("unique preparation after verified release required")
        self.started_ns = started_ns
        return self.view()

    def complete(self, candidate, completed_ns):
        if (self.uncertainty is not None or self.started_ns is None or
                self.completed_ns is not None or type(candidate) is not dict or
                not candidate or type(completed_ns) is not int or
                completed_ns < self.started_ns):
            raise ValueError("unique bounded candidate preparation required")
        self.candidate = copy.deepcopy(candidate)
        self.candidate_sha256 = _sha(candidate)
        self.completed_ns = completed_ns
        return self.view()

    def view(self):
        action = self.action.view()
        if self.uncertainty:
            state = "NEEDS_RECONCILIATION"
        elif action["terminal"] is not None and self.completed_ns is not None:
            state = "PREPARED_REQUIRES_FRESH_ACTION_VALIDITY"
        elif action["terminal"] is not None:
            state = "TERMINAL_RECEIVED_PREPARATION_INCOMPLETE"
        elif self.completed_ns is not None:
            state = "PREPARED_AWAITING_TERMINAL"
        elif self.started_ns is not None:
            state = "PREPARING_AWAITING_TERMINAL"
        elif action["released"] is not None:
            state = "RELEASED_READY_TO_PREPARE"
        else:
            state = "AWAITING_RELEASE"
        release_ns = (action["released"] or {}).get("published_ns")
        terminal_ns = (action["terminal"] or {}).get("terminal_ns")
        return {"schema": SCHEMA, "state": state,
            "action_id": action["action_id"],
            "physical_release_verified": action["physical_release_verified"],
            "program_terminal_pending": action["program_terminal_pending"],
            "preparation_started_ns": self.started_ns,
            "preparation_completed_ns": self.completed_ns,
            "candidate": copy.deepcopy(self.candidate),
            "candidate_sha256": self.candidate_sha256,
            "overlap_before_terminal_ns": (None if terminal_ns is None or
                self.completed_ns is None else
                max(0, terminal_ns - max(self.started_ns, release_ns))),
            "requires_fresh_action_validity":
                state == "PREPARED_REQUIRES_FRESH_ACTION_VALIDITY",
            "may_submit_to_executor": False,
            "grants_input_authority": False,
            "uncertainty": self.uncertainty}
