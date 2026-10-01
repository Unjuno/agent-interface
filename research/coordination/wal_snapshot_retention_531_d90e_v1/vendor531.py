from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Dict, List


@dataclass(frozen=True)
class Receipt:
    intent_id: str
    intent_seq: int
    from_generation: int
    to_generation: int
    confirmation_content_id: str
    confirmation_revision: int

    def content(self) -> Dict[str, Any]:
        return asdict(self)


class IdOnlyLedger:
    """Negative control: bounded receipts, no retirement memory."""

    def __init__(self, capacity: int = 2) -> None:
        self.capacity = capacity
        self.generation = 1
        self.history: List[Receipt] = []

    def classify(self, receipt: Receipt) -> str:
        for prior in self.history:
            if prior.intent_id == receipt.intent_id:
                if prior == receipt:
                    return "ALREADY_COMMITTED_SELF"
                return "CONFLICT_INTENT_CONTENT"
        return "NEW_INTENT_ALLOWED"

    def apply(self, receipt: Receipt) -> str:
        classification = self.classify(receipt)
        if classification != "NEW_INTENT_ALLOWED":
            return classification
        if receipt.from_generation != self.generation or receipt.to_generation != self.generation + 1:
            return "INVALID_TRANSITION"
        self.generation = receipt.to_generation
        self.history.append(receipt)
        if len(self.history) > self.capacity:
            self.history.pop(0)
        return "APPLIED"

    def snapshot(self) -> Dict[str, Any]:
        return {
            "capacity": self.capacity,
            "generation": self.generation,
            "history": [r.content() for r in self.history],
        }


class WatermarkLedger:
    """Bounded receipts plus one scalar retirement watermark."""

    def __init__(self, capacity: int = 2) -> None:
        self.capacity = capacity
        self.generation = 1
        self.history: List[Receipt] = []
        self.retired_through_seq = 0

    def _last_seen_seq(self) -> int:
        if self.history:
            return self.history[-1].intent_seq
        return self.retired_through_seq

    def classify(self, receipt: Receipt) -> str:
        for prior in self.history:
            if prior.intent_seq == receipt.intent_seq:
                if prior == receipt:
                    return "ALREADY_COMMITTED_SELF"
                return "CONFLICT_INTENT_CONTENT"

        if receipt.intent_seq <= self.retired_through_seq:
            return "EXPIRED_INTENT"

        expected_seq = self._last_seen_seq() + 1
        if receipt.intent_seq > expected_seq:
            return "SEQUENCE_GAP"
        if receipt.intent_seq < expected_seq:
            return "EXPIRED_INTENT"

        if receipt.from_generation != self.generation or receipt.to_generation != self.generation + 1:
            return "INVALID_TRANSITION"
        return "NEW_INTENT_ALLOWED"

    def apply(self, receipt: Receipt) -> str:
        classification = self.classify(receipt)
        if classification != "NEW_INTENT_ALLOWED":
            return classification
        self.generation = receipt.to_generation
        self.history.append(receipt)
        if len(self.history) > self.capacity:
            evicted = self.history.pop(0)
            self.retired_through_seq = max(self.retired_through_seq, evicted.intent_seq)
        return "APPLIED"

    def snapshot(self) -> Dict[str, Any]:
        return {
            "capacity": self.capacity,
            "generation": self.generation,
            "retired_through_seq": self.retired_through_seq,
            "history": [r.content() for r in self.history],
            "retirement_state_shape": "scalar",
        }
