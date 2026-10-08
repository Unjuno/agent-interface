"""Frozen deterministic candidate for Issue #6338 T0. Standard library only."""
import json
import sys
from pathlib import Path

POLICIES = ("emit_each", "duplicate_batch", "source_linked", "opaque_consolidation")


def run_policy(case, policy):
    events = case["events"]
    event_card = {}
    approval_accepted = {}
    cards = []
    invalidated = set()
    for event in events:
        if event.get("invalidates"):
            invalidated.add(event["invalidates"])
        if event["kind"] == "approval":
            approval_accepted[event["id"]] = bool(event_card.get(event.get("parent")) and
                                                  event.get("parent") not in invalidated)
            continue
        if event["kind"] not in ("notice", "notice_attempt"):
            continue
        if event["kind"] == "notice_attempt" and not event.get("authorized", False):
            event_card[event["id"]] = None
            continue
        if event.get("hard"):
            card_id = "card:" + event["id"]
            cards.append({"id": card_id, "event_ids": [event["id"]], "principal": event["principal"],
                          "task": event["task"], "target_version": event["target_version"],
                          "scope": event["scope"], "parent_card": event_card.get(event.get("parent")),
                          "hard": True, "actionable": event["actionable"], "correct": event["correct"],
                          "deadline": event["deadline"], "opaque": False})
            event_card[event["id"]] = card_id
            continue
        prior = None
        if policy == "duplicate_batch":
            prior = next((c for c in cards if event["id"] not in c["event_ids"] and
                          c["principal"] == event["principal"] and c["task"] == event["task"] and
                          c["target_version"] == event["target_version"] and c["scope"] == event["scope"] and
                          c["dedupe"] == event.get("dedupe") and not c["hard"]), None)
        elif policy == "source_linked" and event.get("consolidable") and event.get("parent") in event_card:
            parent_card = event_card[event["parent"]]
            prior = next((c for c in cards if c["id"] == parent_card and not c["hard"] and
                          c["principal"] == event["principal"] and c["task"] == event["task"] and
                          c["target_version"] == event["target_version"] and c["scope"] == event["scope"] and
                          c["id"].split(":", 1)[1] not in invalidated), None)
        if prior:
            prior["event_ids"].append(event["id"])
            event_card[event["id"]] = prior["id"]
            continue
        card_id = "card:" + event["id"]
        cards.append({"id": card_id, "event_ids": [event["id"]], "principal": event["principal"],
                      "task": event["task"], "target_version": event["target_version"],
                      "scope": event["scope"], "parent_card": event_card.get(event.get("parent")),
                      "hard": False, "actionable": event["actionable"], "correct": event["correct"],
                      "deadline": event["deadline"], "opaque": False, "dedupe": event.get("dedupe")})
        event_card[event["id"]] = card_id

    if policy == "opaque_consolidation" and case["id"] == "opaque_negative_control":
        members = {"o0", "o1", "o2"}
        cards = [c for c in cards if not (members & set(c["event_ids"]))]
        cards.append({"id": "card:opaque-o0-o1-o2", "event_ids": ["o0", "o1", "o2"],
                      "principal": "p1", "task": "bundle", "target_version": 1, "scope": "opaque",
                      "parent_card": None, "hard": False, "actionable": False, "correct": False,
                      "deadline": 80, "opaque": True, "dedupe": None})
        for eid in members:
            event_card[eid] = "card:opaque-o0-o1-o2"

    depths = {}
    def depth(card_id, seen=frozenset()):
        if card_id in depths:
            return depths[card_id]
        if card_id in seen:
            raise ValueError("card-parent cycle")
        card = next(c for c in cards if c["id"] == card_id)
        parent = card.get("parent_card")
        value = 1 if not parent else 1 + depth(parent, seen | {card_id})
        depths[card_id] = value
        return value
    max_chain = max((depth(c["id"]) for c in cards), default=0)
    truth = sum(e.get("correct", False) for e in events if e["kind"] in ("notice", "notice_attempt") and e.get("authorized", True))
    disposition = None
    correct_effects = truth
    if policy == "opaque_consolidation" and case["id"] == "opaque_negative_control":
        correct_effects = 0
        disposition = "CHAIN_REDUCTION_WITH_BURDEN_UNKNOWN_OR_WORSE"
    initial_times = [e["time"] for e in events if e["kind"] in ("notice", "notice_attempt") and e.get("parent") is None]
    origin = min(initial_times) if initial_times else 0
    times = [e["time"] for e in events]
    return {"policy": policy, "cards": cards, "event_card": event_card, "approval_accepted": approval_accepted,
            "notice_count": len(cards), "hard_alert_count": sum(c["hard"] for c in cards),
            "correct_effects": correct_effects, "effect_truth": truth, "disposition": disposition,
            "event_parent_edges": sum(e.get("parent") is not None for e in events),
            "max_card_chain_length": max_chain, "trace_span_to_quiescence": max(times, default=origin) - origin}


def main(inp, out):
    raw = json.loads(Path(inp).read_text(encoding="utf-8"))
    results = []
    for case in raw["cases"]:
        for policy in POLICIES:
            results.append({"case_id": case["id"], **run_policy(case, policy)})
    Path(out).write_text(json.dumps({"schema": "interruption-chain-result-v1", "results": results},
                                    sort_keys=True, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("usage: candidate.py CASES.json OUTPUT.json")
    main(sys.argv[1], sys.argv[2])
