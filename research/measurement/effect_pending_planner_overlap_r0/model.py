"""Incremental candidate state machine for Issue #1616."""
from copy import deepcopy

ACTION = "A"
TOKEN = "T"

EVENTS = (
    "RELEASE_OK",
    "RELEASE_BAD_TOKEN",
    "EFFECT_OK",
    "EFFECT_BAD_TOKEN",
    "EFFECT_AUTH",
    "TIMEOUT",
    "TERMINAL_OK",
    "TERMINAL_BAD_TOKEN",
)


def event_row(symbol):
    if symbol == "RELEASE_OK":
        return {"event":"input_released","action_id":ACTION,"intent_token":TOKEN,
                "owner_release":{"verified":True,"keys_down":[],"buttons_down":[]},
                "program_terminal_pending":True,"grants_input_authority":False}
    if symbol == "RELEASE_BAD_TOKEN":
        row = event_row("RELEASE_OK"); row["intent_token"] = "WRONG"; return row
    if symbol == "EFFECT_OK":
        return {"event":"task_effect","action_id":ACTION,"intent_token":TOKEN,
                "role":"TASK_EFFECT","current":True,
                "input_authority":False,"semantic_authority":False,
                "result":"TASK_PREDICATE_TRUE"}
    if symbol == "EFFECT_BAD_TOKEN":
        row = event_row("EFFECT_OK"); row["intent_token"] = "WRONG"; return row
    if symbol == "EFFECT_AUTH":
        row = event_row("EFFECT_OK"); row["input_authority"] = True; return row
    if symbol == "TIMEOUT":
        return {"event":"effect_timeout","action_id":ACTION,"intent_token":TOKEN,
                "role":"UNRESOLVED_EFFECT","input_authority":False,
                "semantic_authority":False}
    if symbol == "TERMINAL_OK":
        return {"event":"terminal","action_id":ACTION,"intent_token":TOKEN,
                "status":"completed"}
    if symbol == "TERMINAL_BAD_TOKEN":
        row = event_row("TERMINAL_OK"); row["intent_token"] = "WRONG"; return row
    raise KeyError(symbol)


class EffectPendingTracker:
    def __init__(self):
        self.accepted = {"action_id": ACTION, "intent_token": TOKEN}
        self.release = None
        self.effect = None
        self.timeout = None
        self.terminal = None
        self.uncertainty = None

    def _fail(self, reason):
        if self.uncertainty is None:
            self.uncertainty = reason

    def ingest_symbol(self, symbol):
        row = event_row(symbol)
        try:
            if row.get("action_id") != ACTION or row.get("intent_token") != TOKEN:
                raise ValueError("lineage")
            ev = row.get("event")
            if ev == "input_released":
                if self.release is not None:
                    raise ValueError("duplicate_release")
                owner = row.get("owner_release")
                if (not isinstance(owner, dict) or owner.get("verified") is not True or
                        owner.get("keys_down") != [] or owner.get("buttons_down") != [] or
                        row.get("program_terminal_pending") is not True or
                        row.get("grants_input_authority") is not False):
                    raise ValueError("release_integrity")
                self.release = deepcopy(row)
            elif ev == "task_effect":
                if self.effect is not None:
                    raise ValueError("duplicate_effect")
                if self.timeout is not None:
                    raise ValueError("effect_after_timeout")
                if (row.get("role") != "TASK_EFFECT" or row.get("current") is not True or
                        row.get("input_authority") is not False or
                        row.get("semantic_authority") is not False):
                    raise ValueError("effect_integrity")
                self.effect = deepcopy(row)
            elif ev == "effect_timeout":
                if self.timeout is not None:
                    raise ValueError("duplicate_timeout")
                if self.effect is not None:
                    raise ValueError("timeout_after_effect")
                if (row.get("role") != "UNRESOLVED_EFFECT" or
                        row.get("input_authority") is not False or
                        row.get("semantic_authority") is not False):
                    raise ValueError("timeout_integrity")
                self.timeout = deepcopy(row)
            elif ev == "terminal":
                if self.terminal is not None:
                    raise ValueError("duplicate_terminal")
                self.terminal = deepcopy(row)
            else:
                raise ValueError("unknown_event")
        except (ValueError, TypeError, AttributeError) as exc:
            self._fail(str(exc))
        return self.view()

    def view(self):
        uncertain = self.uncertainty is not None
        released = self.release is not None
        if uncertain:
            effect_status = "unknown"
        elif self.effect is not None:
            effect_status = "resolved"
        elif self.timeout is not None:
            effect_status = "unresolved"
        else:
            effect_status = "pending"
        return {
            "state": "needs_reconciliation" if uncertain else "tracked",
            "physical_release_verified": released and not uncertain,
            "client_can_resume_reasoning": released and not uncertain,
            "task_effect_status": effect_status,
            "task_effect_resolved": self.effect is not None and not uncertain,
            "effect_timeout_recorded": self.timeout is not None and not uncertain,
            "terminal_received": self.terminal is not None and not uncertain,
            "program_terminal_pending": self.terminal is None and not uncertain,
            "current_input_authority": False,
            "new_input_admissible": False,
            "semantic_authority": False,
            "uncertainty": self.uncertainty,
        }
