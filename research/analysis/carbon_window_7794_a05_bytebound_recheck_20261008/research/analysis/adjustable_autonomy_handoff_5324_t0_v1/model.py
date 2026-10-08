from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable


POLICIES = ("ROUTE_ONLY", "ACK_ONLY", "TWO_PHASE", "THREE_PHASE", "FAIL_CLOSED_NO_OWNER")


@dataclass(frozen=True)
class Scenario:
    name: str
    events: tuple[str, ...]


SCENARIOS = (
    Scenario("nominal", ("request", "offer_delivered", "target_prepare", "target_accept", "source_quiesce", "commit_delivered", "target_activate", "work")),
    Scenario("offer_lost", ("request", "offer_lost", "timeout")),
    Scenario("target_refuses", ("request", "offer_delivered", "target_refuse", "source_resume")),
    Scenario("target_crash_before_accept", ("request", "offer_delivered", "target_crash", "timeout")),
    Scenario("source_crash_before_accept", ("request", "offer_delivered", "source_crash", "target_accept", "commit_delivered", "target_activate")),
    Scenario("source_crash_after_accept", ("request", "offer_delivered", "target_prepare", "target_accept", "source_crash", "commit_delivered", "target_activate")),
    Scenario("target_crash_after_accept", ("request", "offer_delivered", "target_prepare", "target_accept", "source_quiesce", "target_crash", "commit_delivered", "target_activate")),
    Scenario("commit_lost", ("request", "offer_delivered", "target_prepare", "target_accept", "source_quiesce", "commit_lost", "timeout")),
    Scenario("stale_snapshot", ("request", "offer_delivered", "target_prepare", "snapshot_stale", "target_accept", "source_quiesce", "commit_delivered", "target_activate")),
    Scenario("lease_expiry", ("request", "offer_delivered", "target_prepare", "target_accept", "source_quiesce", "lease_expired", "commit_delivered", "target_activate")),
    Scenario("duplicate_accept", ("request", "offer_delivered", "target_prepare", "target_accept", "target_accept_duplicate", "source_quiesce", "commit_delivered", "target_activate")),
    Scenario("human_intervention", ("request", "offer_delivered", "target_prepare", "human_takeover", "target_accept", "source_quiesce", "commit_delivered", "target_activate")),
    Scenario("reclaim_after_target_crash", ("request", "offer_delivered", "target_prepare", "target_accept", "source_quiesce", "commit_delivered", "target_activate", "target_crash", "reclaim", "source_resume", "work")),
)


@dataclass
class State:
    owners: set[str] = field(default_factory=lambda: {"source"})
    source_alive: bool = True
    target_alive: bool = True
    human_alive: bool = True
    offer_seen: bool = False
    accepted: bool = False
    prepared: bool = False
    quiesced: bool = False
    committed: bool = False
    stale: bool = False
    expired: bool = False
    stopped: bool = False
    false_success_claims: int = 0
    rows: list[dict] = field(default_factory=list)

    def observe(self, tick: int, event: str) -> None:
        self.rows.append({
            "tick": tick, "event": event, "owners": sorted(self.owners),
            "source_alive": self.source_alive, "target_alive": self.target_alive,
            "human_alive": self.human_alive, "offer_seen": self.offer_seen,
            "accepted": self.accepted, "prepared": self.prepared,
            "quiesced": self.quiesced, "committed": self.committed,
            "stale": self.stale, "expired": self.expired,
            "false_success_claims": self.false_success_claims,
        })


def _target_can_activate(s: State) -> bool:
    return (s.target_alive and s.offer_seen and s.accepted and not s.stale
            and not s.expired and "human" not in s.owners)


def _event(policy: str, s: State, event: str) -> None:
    if event == "request":
        if policy in {"ROUTE_ONLY", "FAIL_CLOSED_NO_OWNER"}:
            s.owners.discard("source")
            s.quiesced = True
            if policy == "FAIL_CLOSED_NO_OWNER":
                s.stopped = True
    elif event == "offer_delivered":
        s.offer_seen = True
    elif event == "target_prepare":
        if s.target_alive and s.offer_seen and not s.stale and not s.expired:
            s.prepared = True
    elif event == "target_accept":
        if s.target_alive and s.offer_seen and not s.stale and not s.expired:
            s.accepted = True
            if policy == "ACK_ONLY":
                s.owners.add("target")
    elif event == "target_accept_duplicate":
        if s.target_alive and s.offer_seen and not s.stale and not s.expired:
            s.accepted = True
            if policy == "ACK_ONLY":
                s.owners.add("target")
    elif event == "source_quiesce":
        s.owners.discard("source")
        s.quiesced = True
    elif event == "commit_delivered":
        s.committed = True
        if policy == "TWO_PHASE" and _target_can_activate(s) and s.quiesced:
            s.owners.add("target")
        if policy == "THREE_PHASE" and _target_can_activate(s) and s.prepared and s.quiesced:
            s.owners.add("target")
    elif event == "target_activate":
        if policy == "ROUTE_ONLY" and s.target_alive and s.offer_seen:
            s.owners.add("target")
        elif policy == "ACK_ONLY" and _target_can_activate(s):
            s.owners.add("target")
        elif policy == "TWO_PHASE" and _target_can_activate(s) and s.quiesced and s.committed:
            s.owners.add("target")
        elif policy == "THREE_PHASE" and _target_can_activate(s) and s.prepared and s.quiesced and s.committed:
            s.owners.add("target")
    elif event == "source_crash":
        s.source_alive = False
        s.owners.discard("source")
    elif event == "target_crash":
        s.target_alive = False
        s.owners.discard("target")
    elif event == "snapshot_stale":
        s.stale = True
        s.owners.discard("target")
    elif event == "lease_expired":
        s.expired = True
        s.owners.discard("source")
        s.owners.discard("target")
    elif event == "human_takeover":
        s.owners.discard("source")
        s.owners.discard("target")
        if s.human_alive:
            s.owners.add("human")
    elif event == "source_resume":
        if s.source_alive and not s.expired and "human" not in s.owners:
            s.owners.add("source")
            s.stopped = False
            s.quiesced = False
            s.committed = False
    elif event == "reclaim":
        s.owners.discard("target")
        s.accepted = False
        s.prepared = False
        s.committed = False
    elif event == "work":
        # T0 records that no task completion oracle exists; success is never claimed.
        pass
    elif event == "target_refuse":
        s.owners.discard("target")
        s.accepted = False
        s.prepared = False
    elif event in {"offer_lost", "commit_lost", "timeout"}:
        pass
    else:
        raise ValueError(f"unknown event: {event}")


def simulate(policy: str, scenario: Scenario) -> dict:
    if policy not in POLICIES:
        raise ValueError(policy)
    state = State()
    state.observe(0, "initial")
    for tick, event in enumerate(scenario.events, start=1):
        _event(policy, state, event)
        state.observe(tick, event)
    owners_by_tick = [set(r["owners"]) for r in state.rows]
    gap_ticks = sum(not owners for owners in owners_by_tick)
    duplicate_ticks = sum(len(owners) > 1 for owners in owners_by_tick)
    work_ticks = [r["tick"] for r in state.rows if r["event"] == "work"]
    lost_work = sum(not state.rows[tick]["owners"] for tick in work_ticks)
    return {
        "policy": policy, "scenario": scenario.name,
        "events": list(scenario.events), "trace": state.rows,
        "authority_gap_ticks": gap_ticks,
        "duplicate_owner_ticks": duplicate_ticks,
        "lost_work": lost_work,
        "false_success_claims": state.false_success_claims,
    }


def run_matrix() -> list[dict]:
    return [simulate(policy, scenario) for scenario in SCENARIOS for policy in POLICIES]


def classify(rows: Iterable[dict]) -> str:
    rows = list(rows)
    by_key = {(r["policy"], r["scenario"]): r for r in rows}
    if any(r["duplicate_owner_ticks"] for r in rows if r["policy"] in {"TWO_PHASE", "THREE_PHASE"}):
        return "FAIL_DUPLICATE_OWNER"
    if any(r["false_success_claims"] for r in rows):
        return "FAIL_FALSE_SUCCESS_CLAIM"
    nominal = ("nominal", "offer_lost", "reclaim_after_target_crash")
    if all(
        by_key[(policy, scenario)]["authority_gap_ticks"]
        <= by_key[("FAIL_CLOSED_NO_OWNER", scenario)]["authority_gap_ticks"]
        for policy in ("TWO_PHASE", "THREE_PHASE")
        for scenario in nominal
    ):
        if any(
            by_key[(policy, scenario)]["authority_gap_ticks"]
            < by_key[("FAIL_CLOSED_NO_OWNER", scenario)]["authority_gap_ticks"]
            for policy in ("TWO_PHASE", "THREE_PHASE")
            for scenario in nominal
        ):
            return "PASS_HANDOFF_BOUNDARIES_SCOPED"
    return "HOLD_NO_DISTINGUISHING_VALUE"
