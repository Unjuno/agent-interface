"""Fixture-only evidence reducer. Not a runtime authority or production API."""
from __future__ import annotations

CHECKS = {
    "target": (True, "CURRENT"),
    "effect": (True, "VERIFIED_EFFECT"),
    "diagnostic": (False, "CURRENT"),
}
FIELDS = frozenset(("rid", "check", "subject", "session", "decision", "epoch", "role", "value"))
ROLES = frozenset(("CURRENT", "VERIFIED_EFFECT", "HISTORICAL", "PREDICTED"))
BITS = {"PASS": 1, "FAIL": 2, "UNKNOWN": 4, "TIMEOUT": 8}
SCOPE = ("session-vj01", "decision-vj01", 7)


class Reducer:
    """Accumulate payload variants; seal one historical decision explicitly.

    Conflicting payloads with one result identity invalidate that entire identity.
    They must not leave whichever payload arrived first as trusted evidence.
    """

    def __init__(self) -> None:
        self.records: dict[str, set[tuple[str, str, str]]] = {}
        self.invalid = False
        self.rejected = 0
        self.late = 0
        self.final: str | None = None
        self.authority = False

    def feed(self, event: object) -> str:
        if self.final is not None:
            self.late += 1
            return self.final
        if not isinstance(event, dict) or set(event) != FIELDS:
            self.invalid = True
            return self.view()
        if type(event["epoch"]) is not int or any(
            type(event[k]) is not str or not event[k] or len(event[k]) > 128
            for k in FIELDS - {"epoch"}
        ):
            self.invalid = True
            return self.view()
        if event["role"] not in ROLES or event["value"] not in BITS:
            self.invalid = True
            return self.view()
        if event["check"] not in CHECKS:
            self.invalid = True
            return self.view()
        if (event["session"], event["decision"], event["epoch"]) != SCOPE or event["subject"] != event["check"]:
            self.rejected += 1
            return self.view()
        payload = (event["check"], event["role"], event["value"])
        self.records.setdefault(event["rid"], set()).add(payload)
        return self.view()

    def view(self) -> str:
        if self.final is not None:
            return self.final
        state = dict.fromkeys(CHECKS, 0)
        integrity = self.invalid
        for variants in self.records.values():
            if len(variants) != 1:
                integrity = True
                continue
            check, role, value = next(iter(variants))
            if role == CHECKS[check][1]:
                state[check] |= BITS[value]
        # A trustworthy unopposed mandatory failure takes precedence.
        if any(required and bits & 2 and not bits & 1
               for check, bits in state.items() for required, _ in [CHECKS[check]]):
            return "F"
        if integrity or any(bits & 1 and bits & 2 for bits in state.values()):
            return "U"
        if all(state[check] == 1 for check, (required, _) in CHECKS.items() if required):
            return "P"
        return "U"

    def seal(self) -> str:
        if self.final is None:
            self.final = self.view()
        return self.final
