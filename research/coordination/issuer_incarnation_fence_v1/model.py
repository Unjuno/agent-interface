from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Dict, List


@dataclass(frozen=True)
class Receipt:
    issuer_incarnation: int
    intent_id: str
    intent_seq: int
    from_generation: int
    to_generation: int
    confirmation_content_id: str
    confirmation_revision: int

    def content(self) -> Dict[str, Any]:
        return asdict(self)


class ResettableSequenceLedger:
    """Negative control: restart resets the only sequence namespace."""

    def __init__(self, capacity: int = 2) -> None:
        self.capacity = capacity
        self.generation = 1
        self.history: List[Receipt] = []
        self.retired_through_seq = 0
        self.writes = 0

    def _next_seq(self) -> int:
        live = max((r.intent_seq for r in self.history), default=0)
        return max(self.retired_through_seq, live) + 1

    def classify(self, receipt: Receipt) -> str:
        # Incarnation is deliberately ignored in this baseline.
        for existing in self.history:
            if existing.intent_seq == receipt.intent_seq:
                if existing.content() == receipt.content():
                    return "ALREADY_COMMITTED_SELF"
                return "CONFLICT_INTENT_CONTENT"
        if receipt.intent_seq <= self.retired_through_seq:
            return "EXPIRED_INTENT"
        if receipt.intent_seq != self._next_seq():
            return "SEQUENCE_GAP"
        return "NEW_INTENT_ALLOWED"

    def apply(self, receipt: Receipt) -> str:
        if self.classify(receipt) != "NEW_INTENT_ALLOWED":
            return "REJECTED"
        if receipt.from_generation != self.generation or receipt.to_generation != self.generation + 1:
            return "GENERATION_MISMATCH"
        self.generation = receipt.to_generation
        self.history.append(receipt)
        self.writes += 1
        while len(self.history) > self.capacity:
            evicted = self.history.pop(0)
            self.retired_through_seq = max(self.retired_through_seq, evicted.intent_seq)
        return "APPLIED"

    def restart_reset_namespace(self) -> None:
        # This is the unsafe liveness strategy under test: sequence state is reset
        # and no issuer-incarnation identity survives to distinguish old seq values.
        self.history.clear()
        self.retired_through_seq = 0

    def snapshot(self) -> Dict[str, Any]:
        return {
            "generation": self.generation,
            "capacity": self.capacity,
            "retired_through_seq": self.retired_through_seq,
            "history": [r.content() for r in self.history],
            "writes": self.writes,
            "incarnation_tracking": False,
        }


class IncarnationFencedLedger:
    """Candidate: one installed issuer incarnation + bounded sequence history."""

    def __init__(self, current_incarnation: int = 1, capacity: int = 2) -> None:
        self.capacity = capacity
        self.generation = 1
        self.current_incarnation = current_incarnation
        self.history: List[Receipt] = []
        self.retired_through_seq = 0
        self.writes = 0
        self.incarnation_installs = 0

    def _next_seq(self) -> int:
        live = max((r.intent_seq for r in self.history), default=0)
        return max(self.retired_through_seq, live) + 1

    def classify(self, receipt: Receipt) -> str:
        if receipt.issuer_incarnation < self.current_incarnation:
            return "STALE_ISSUER_INCARNATION"
        if receipt.issuer_incarnation > self.current_incarnation:
            return "UNINSTALLED_ISSUER_INCARNATION"
        for existing in self.history:
            if existing.intent_seq == receipt.intent_seq:
                if existing.content() == receipt.content():
                    return "ALREADY_COMMITTED_SELF"
                return "CONFLICT_INTENT_CONTENT"
        if receipt.intent_seq <= self.retired_through_seq:
            return "EXPIRED_INTENT"
        if receipt.intent_seq != self._next_seq():
            return "SEQUENCE_GAP"
        return "NEW_INTENT_ALLOWED"

    def apply(self, receipt: Receipt) -> str:
        if self.classify(receipt) != "NEW_INTENT_ALLOWED":
            return "REJECTED"
        if receipt.from_generation != self.generation or receipt.to_generation != self.generation + 1:
            return "GENERATION_MISMATCH"
        self.generation = receipt.to_generation
        self.history.append(receipt)
        self.writes += 1
        while len(self.history) > self.capacity:
            evicted = self.history.pop(0)
            self.retired_through_seq = max(self.retired_through_seq, evicted.intent_seq)
        return "APPLIED"

    def install_incarnation(self, new_incarnation: int) -> str:
        if new_incarnation != self.current_incarnation + 1:
            return "INCARNATION_INSTALL_REJECTED"
        self.current_incarnation = new_incarnation
        self.history.clear()
        self.retired_through_seq = 0
        self.incarnation_installs += 1
        return "INCARNATION_INSTALLED"

    def snapshot(self) -> Dict[str, Any]:
        return {
            "generation": self.generation,
            "capacity": self.capacity,
            "current_incarnation": self.current_incarnation,
            "retired_through_seq": self.retired_through_seq,
            "history": [r.content() for r in self.history],
            "writes": self.writes,
            "incarnation_installs": self.incarnation_installs,
            "retirement_state_shape": "scalar_per_current_incarnation",
        }
