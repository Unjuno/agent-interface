"""Independent raw-only checker. Does not import or execute candidate.py."""
import json
import sys
from pathlib import Path

POLICIES = {"emit_each", "duplicate_batch", "source_linked", "opaque_consolidation"}


def expected_card_ids(case, policy):
    events = case["events"]
    mapping = {}
    cards = {}
    invalid = {e["invalidates"] for e in events if e.get("invalidates")}
    for e in events:
        if e["kind"] not in {"notice", "notice_attempt"}:
            continue
        if e["kind"] == "notice_attempt" and not e.get("authorized"):
            mapping[e["id"]] = None
            continue
        parent_card = mapping.get(e.get("parent"))
        merge_id = None
        if not e.get("hard") and policy == "duplicate_batch":
            for cid, prior in cards.items():
                root = prior["root"]
                pe = next(x for x in events if x["id"] == root)
                if (prior["principal"], prior["task"], prior["target_version"], prior["scope"], pe.get("dedupe")) == (
                    e["principal"], e["task"], e["target_version"], e["scope"], e.get("dedupe")):
                    merge_id = cid
                    break
        if not e.get("hard") and policy == "source_linked" and e.get("consolidable") and parent_card:
            original = cards[parent_card]
            if (original["principal"], original["task"], original["target_version"], original["scope"]) == (
                e["principal"], e["task"], e["target_version"], e["scope"]):
                if original["root"] not in invalid:
                    merge_id = parent_card
        if merge_id:
            mapping[e["id"]] = merge_id
            continue
        cid = "card:" + e["id"]
        cards[cid] = {"root": e["id"], "principal": e["principal"], "task": e["task"],
                      "target_version": e["target_version"], "scope": e["scope"], "parent_card": parent_card,
                      "hard": bool(e.get("hard")), "correct": bool(e.get("correct")),
                      "actionable": bool(e.get("actionable")), "deadline": e.get("deadline"), "opaque": False}
        mapping[e["id"]] = cid
    if policy == "opaque_consolidation" and case["id"] == "opaque_negative_control":
        for eid in ("o0", "o1", "o2"):
            cid = mapping.pop(eid)
            cards.pop(cid, None)
        cards["card:opaque-o0-o1-o2"] = {"root": "o0", "principal": "p1", "task": "bundle", "target_version": 1,
                                         "scope": "opaque", "parent_card": None, "hard": False,
                                         "correct": False, "actionable": False, "deadline": 80, "opaque": True}
        mapping.update({e: "card:opaque-o0-o1-o2" for e in ("o0", "o1", "o2")})
    return mapping, cards


def audit(cases, artifact):
    errors = []
    table = {(x["case_id"], x["policy"]): x for x in artifact.get("results", [])}
    if len(table) != len(artifact.get("results", [])):
        errors.append("duplicate result row")
    for case in cases["cases"]:
        events = case["events"]
        event_by_id = {e["id"]: e for e in events}
        for e in events:
            if e.get("parent") and not any(p["id"] == e["parent"] for p in events):
                errors.append(f"{case['id']}: missing raw parent {e['parent']}")
            if e.get("time", -1) < 0 or e.get("time", case.get("horizon", 0) + 1) > cases.get("horizon", 0):
                errors.append(f"{case['id']}: event outside frozen horizon")
            parent = event_by_id.get(e.get("parent"))
            if parent and parent.get("time", -1) > e.get("time", -1):
                errors.append(f"{case['id']}: parent occurs after child")
        for policy in POLICIES:
            row = table.get((case["id"], policy))
            if row is None:
                errors.append(f"{case['id']}/{policy}: missing row")
                continue
            mapping, expected = expected_card_ids(case, policy)
            actual_cards = {c.get("id"): c for c in row.get("cards", [])}
            if set(actual_cards) != set(expected):
                errors.append(f"{case['id']}/{policy}: card identity set mismatch")
            if row.get("event_card") != mapping:
                errors.append(f"{case['id']}/{policy}: event-to-card map mismatch")
            for cid, ec in expected.items():
                ac = actual_cards.get(cid)
                if ac is None:
                    continue
                for field in ("principal", "task", "target_version", "scope", "parent_card", "hard", "actionable", "correct", "deadline", "opaque"):
                    if ac.get(field) != ec.get(field):
                        errors.append(f"{case['id']}/{policy}/{cid}: {field} mismatch")
            expected_edges = sum(e.get("parent") is not None for e in events)
            if row.get("event_parent_edges") != expected_edges:
                errors.append(f"{case['id']}/{policy}: raw parent-edge count mismatch")
            expected_truth = sum(e.get("correct", False) for e in events
                                 if e["kind"] in ("notice", "notice_attempt") and e.get("authorized", True))
            expected_correct = 0 if policy == "opaque_consolidation" and case["id"] == "opaque_negative_control" else expected_truth
            if row.get("effect_truth") != expected_truth or row.get("correct_effects") != expected_correct:
                errors.append(f"{case['id']}/{policy}: independent task-effect count mismatch")
            if row.get("notice_count") != len(expected):
                errors.append(f"{case['id']}/{policy}: notice count mismatch")
            if row.get("hard_alert_count") != sum(bool(c["hard"]) for c in expected.values()):
                errors.append(f"{case['id']}/{policy}: mandatory hard alert count mismatch")
            expected_depth = {}
            def depth(card_id):
                if card_id not in expected_depth:
                    parent = expected[card_id]["parent_card"]
                    expected_depth[card_id] = 1 if not parent else 1 + depth(parent)
                return expected_depth[card_id]
            longest = max((depth(cid) for cid in expected), default=0)
            if row.get("max_card_chain_length") != longest:
                errors.append(f"{case['id']}/{policy}: parent-chain tail length mismatch")
            roots = [e["time"] for e in events if e["kind"] in ("notice", "notice_attempt") and e.get("parent") is None]
            expected_span = max((e["time"] for e in events), default=(min(roots) if roots else 0)) - (min(roots) if roots else 0)
            if row.get("trace_span_to_quiescence") != expected_span:
                errors.append(f"{case['id']}/{policy}: trace-span-to-quiescence mismatch")
            if case["id"] == "target_revision" and row.get("event_card", {}).get("r0") == row.get("event_card", {}).get("r1"):
                errors.append(f"{policy}: distinct target versions merged")
            if case["id"] == "target_revision" and row.get("approval_accepted", {}).get("r2") is not False:
                errors.append(f"{policy}: stale target approval was accepted")
            if case["id"] == "cross_principal_attempt" and row.get("event_card", {}).get("p1") is not None:
                errors.append(f"{policy}: unauthorized cross-principal notice emitted")
            if case["id"] == "opaque_negative_control" and policy == "opaque_consolidation":
                if row.get("disposition") != "CHAIN_REDUCTION_WITH_BURDEN_UNKNOWN_OR_WORSE":
                    errors.append("opaque control was promoted as benefit")
    chain = {r["policy"]: r for r in artifact.get("results", []) if r["case_id"] == "two_generation_chain"}
    if chain and chain.get("source_linked", {}).get("notice_count") >= chain.get("emit_each", {}).get("notice_count", 999):
        errors.append("source-linked policy did not reduce chain notices")
    if chain:
        emit = chain.get("emit_each", {})
        source = chain.get("source_linked", {})
        if emit.get("notice_count") != 3 or source.get("notice_count") != 2:
            errors.append("frozen chain contrast counts differ")
        if source.get("correct_effects") != emit.get("correct_effects"):
            errors.append("source-linked policy changed task-effect truth")
        if emit.get("max_card_chain_length") != 3 or source.get("max_card_chain_length") != 2:
            errors.append("frozen parent-chain tail lengths differ")
    return {"status": "PASS_METHOD_SCOPED" if not errors else "FAIL", "errors": errors,
            "scope": "finite deterministic fixture only; no human, causal, prevalence or burden claim"}


def main(case_path, artifact_path, out_path):
    cases = json.loads(Path(case_path).read_text(encoding="utf-8"))
    artifact = json.loads(Path(artifact_path).read_text(encoding="utf-8"))
    result = audit(cases, artifact)
    Path(out_path).write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return 0 if result["status"] == "PASS_METHOD_SCOPED" else 1


if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise SystemExit("usage: auditor.py CASES.json CANDIDATE.json AUDIT.json")
    raise SystemExit(main(*sys.argv[1:]))
