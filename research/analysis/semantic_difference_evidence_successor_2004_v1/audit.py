"""Independent finite audit for #2004 semantic difference successor."""
from __future__ import annotations

import hashlib, json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from difference import difference  # noqa: E402


def obs(**changes):
    row = {"session": "s1", "surface": "u1", "identity": "widget-a", "epoch": 4,
           "focus": "a", "geometry": "0,0,10,10", "text": "old", "enabled": True, "present": True}
    row.update(changes)
    return row


def oracle(before, after, epoch):
    if set(before) != set(after) or set(before) != {"session","surface","identity","epoch","focus","geometry","text","enabled","present"}:
        return ("UNKNOWN", "MALFORMED_OBSERVATION", [])
    if any(before[k] != after[k] for k in ("session", "surface", "identity")):
        return ("UNKNOWN", "IDENTITY_REPLACED", [])
    if before["epoch"] != epoch or after["epoch"] != epoch or after["epoch"] < before["epoch"]:
        return ("UNKNOWN", "STALE_OR_NONMONOTONE_EPOCH", [])
    facts = []
    if before["present"] and not after["present"]: facts.append("disappeared")
    if not before["present"] and after["present"]: facts.append("appeared")
    for field, fact in (("focus", "focus_changed"), ("geometry", "geometry_changed"), ("text", "text_changed"), ("enabled", "enabled_changed")):
        if before[field] != after[field]: facts.append(fact)
    return ("KNOWN", "BOUND_PAIR", sorted(facts))


def main():
    cases = [(obs(), obs(text="new")), (obs(), obs(geometry="0,0,20,10")),
             (obs(present=False), obs()), (obs(), obs(present=False)), (obs(), obs(focus="b")),
             (obs(), obs(enabled=False)), (obs(session="s2"), obs()), (obs(epoch=3), obs()),
             (obs(), {**obs(), "extra": 1}), (obs(), obs())]
    for i, (before, after) in enumerate(cases):
        expected = oracle(before, after, 4)
        actual = difference(before, after, current_epoch=4)
        got = (actual["status"], actual["reason"], actual["facts"])
        if got != expected: raise AssertionError((i, got, expected))
    source = (HERE / "difference.py").read_bytes()
    result = {"status": "PASS_SEMANTIC_DIFFERENCE_EVIDENCE_SCOPED", "cases": len(cases), "oracle_agreement": len(cases), "authority_grants": 0, "source_sha256": hashlib.sha256(source).hexdigest(), "live_gui": "NOT_TESTED", "model": "NOT_TESTED"}
    (HERE / "RESULT.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"PASS_SEMANTIC_DIFFERENCE_EVIDENCE_SCOPED cases={len(cases)} authority_grants=0")


if __name__ == "__main__": main()
