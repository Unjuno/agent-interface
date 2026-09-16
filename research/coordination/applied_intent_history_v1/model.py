from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import List, Optional, Dict, Any


@dataclass(frozen=True)
class Receipt:
    intent_id: str
    from_generation: int
    to_generation: int
    confirmation_content_id: str
    confirmation_revision: int

    def content(self) -> Dict[str, Any]:
        return asdict(self)


class SingleSlotLedger:
    def __init__(self, generation: int = 1):
        self.generation = generation
        self.last_applied_transition: Optional[Receipt] = None

    def apply(self, receipt: Receipt) -> None:
        if receipt.from_generation != self.generation:
            raise ValueError("from_generation mismatch")
        if receipt.to_generation != self.generation + 1:
            raise ValueError("transition must increment generation by one")
        self.generation = receipt.to_generation
        self.last_applied_transition = receipt

    def recover(self, requested: Receipt) -> str:
        last = self.last_applied_transition
        if last is None or last.intent_id != requested.intent_id:
            return "UNKNOWN_INTENT_NOT_RETAINED"
        if last == requested:
            return "ALREADY_COMMITTED_SELF"
        return "CONFLICT_INTENT_CONTENT"


class BoundedHistoryLedger:
    def __init__(self, capacity: int, generation: int = 1):
        if capacity <= 0:
            raise ValueError("capacity must be positive")
        self.capacity = capacity
        self.generation = generation
        self.applied_history: List[Receipt] = []

    def apply(self, receipt: Receipt) -> None:
        if receipt.from_generation != self.generation:
            raise ValueError("from_generation mismatch")
        if receipt.to_generation != self.generation + 1:
            raise ValueError("transition must increment generation by one")
        # Within the retained window, an intent ID is content-bound.
        for prior in self.applied_history:
            if prior.intent_id == receipt.intent_id and prior != receipt:
                raise ValueError("intent_id content conflict in retained history")
        self.generation = receipt.to_generation
        self.applied_history.append(receipt)
        if len(self.applied_history) > self.capacity:
            self.applied_history = self.applied_history[-self.capacity :]

    def recover(self, requested: Receipt) -> str:
        matches = [r for r in self.applied_history if r.intent_id == requested.intent_id]
        if matches:
            if any(r == requested for r in matches):
                return "ALREADY_COMMITTED_SELF"
            return "CONFLICT_INTENT_CONTENT"

        # No unbounded tombstone set: if the requested transition ends at or before
        # the oldest retained transition starts, it is outside the bounded horizon.
        if self.applied_history:
            oldest = self.applied_history[0]
            if requested.to_generation <= oldest.from_generation:
                return "UNKNOWN_INTENT_EVICTED"
        return "UNKNOWN_INTENT_NOT_RETAINED"

    def snapshot(self) -> Dict[str, Any]:
        return {
            "generation": self.generation,
            "capacity": self.capacity,
            "history": [r.content() for r in self.applied_history],
        }
