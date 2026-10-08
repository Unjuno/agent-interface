"""Independent raw-result auditor; intentionally does not import candidate/runner."""

import json
import sys
from collections import Counter
from pathlib import Path


def reject(message):
    raise AssertionError(message)


def safe_reachable(fixture):
    if fixture.get("target") is None:
        return False
    pending = [fixture["start"]]
    visited = set()
    while pending:
        node = pending.pop()
        if node == fixture["target"]:
            return True
        if node in visited:
            continue
        visited.add(node)
        for edge in fixture["screens"][node]["edges"]:
            if edge["reversible"]:
                nxt = fixture["transitions"].get(node, {}).get(edge["id"])
                if nxt is not None:
                    pending.append(nxt)
    return False


def audit_one(fixture, row, budget, task):
    if row.get("trace") != row.get("environment_events"):
        reject("candidate trace differs from independent environment event record")
    current = fixture["start"]
    epoch = 0
    stack = []
    latest_edges = None
    spent = 0
    counts = Counter()
    seen_nodes = {current}

    for index, event in enumerate(row["trace"]):
        kind = event.get("kind")
        if kind == "OBSERVE":
            obs = event.get("observation", {})
            expected = fixture["screens"].get(current)
            if expected is None:
                reject(f"unknown current node at event {index}")
            if set(obs) != {"screen_id", "epoch", "label", "edges"}:
                reject(f"observation schema leak/omission at event {index}")
            if obs != {"screen_id": current, "epoch": epoch, "label": expected["label"],
                       "edges": expected["edges"]}:
                reject(f"observation does not match current visible node/epoch at event {index}")
            latest_edges = {edge["id"]: edge for edge in expected["edges"]}
            counts["observations"] += 1
            spent += 1
        elif kind == "REFUSE_UNSAFE":
            if event.get("screen_id") != current or latest_edges is None:
                reject(f"invalid unsafe refusal at event {index}")
            edge = latest_edges.get(event.get("edge_id"))
            if edge is None or edge["reversible"]:
                reject(f"refused edge was not a visible unsafe edge at event {index}")
            counts["refusals"] += 1
            spent += 1
        elif kind == "NAVIGATE":
            if event.get("screen_id") != current or latest_edges is None:
                reject(f"navigation without current observation at event {index}")
            edge = latest_edges.get(event.get("edge_id"))
            if edge is None or not edge["reversible"]:
                reject(f"unsafe or unseen navigation at event {index}")
            destination = fixture["transitions"].get(current, {}).get(edge["id"])
            if destination is None or event.get("to_screen") != destination:
                reject(f"transition mismatch at event {index}")
            stack.append((current, edge["id"], destination))
            current = destination
            seen_nodes.add(current)
            latest_edges = None
            counts["navigation"] += 1
            spent += 1
        elif kind == "BACKTRACK":
            if not stack:
                reject(f"backtrack without reversible path at event {index}")
            source, edge_id, destination = stack.pop()
            if current != destination or event.get("from_screen") != current or event.get("to_screen") != source or event.get("via_edge_id") != edge_id:
                reject(f"backtrack path mismatch at event {index}")
            current = source
            epoch = fixture.get("epoch_after_backtrack", {}).get(source, epoch)
            if event.get("epoch") != epoch:
                reject(f"backtrack epoch mismatch at event {index}")
            latest_edges = None
            counts["backtracks"] += 1
            spent += 1
        else:
            reject(f"unknown event kind at event {index}: {kind}")

        if spent > budget:
            reject("budget exceeded")

    if row.get("final_screen") != current:
        reject("final screen does not match replay")
    claim = row.get("claim", {})
    if claim.get("screen_id") != current:
        reject("claim screen does not match replay")
    last_observation = next((event.get("observation", {}).get("screen_id")
                             for event in reversed(row["trace"]) if event.get("kind") == "OBSERVE"), None)
    true_target = (fixture.get("target") == current and fixture.get("target") is not None
                   and last_observation == current)
    if bool(claim.get("found")) != true_target:
        reject("target claim disagrees with independent oracle")
    if row.get("budget_remaining") != budget - spent:
        reject("remaining budget mismatch")

    expected_cost = {"api_calls": spent, "observations": counts["observations"],
                     "navigation": counts["navigation"], "backtracks": counts["backtracks"],
                     "forbidden_effects": 0}
    if row.get("cost") != expected_cost:
        reject("cost counters do not match audited trace")
    if fixture.get("target") is None:
        expected_eligibility = "NO_TARGET_CASE"
    elif not safe_reachable(fixture):
        expected_eligibility = "NO_SAFE_PATH"
    elif row.get("policy") == "direct_search" and not fixture.get("direct_search"):
        expected_eligibility = "NOT_APPLICABLE_DIRECT_SEARCH_UNAVAILABLE"
    else:
        expected_eligibility = "ELIGIBLE"
    if row.get("eligibility") != expected_eligibility:
        reject("eligibility classification disagrees with independent graph enumeration")
    return {"correct": True, "found": true_target, "spent": spent,
            "visited": sorted(seen_nodes), "cost": expected_cost}


def audit(spec, raw):
    if raw.get("protocol") != spec["protocol"]:
        reject("protocol mismatch")
    if raw.get("result_count") != len(spec["fixtures"]) * len(spec["policies"]):
        reject("intention-to-test row count mismatch")
    fixtures = {fixture["id"]: fixture for fixture in spec["fixtures"]}
    expected_pairs = {(fixture["id"], policy) for fixture in spec["fixtures"] for policy in spec["policies"]}
    rows = {(row.get("fixture_id"), row.get("policy")): row for row in raw.get("results", [])}
    if set(rows) != expected_pairs or len(rows) != len(raw.get("results", [])):
        reject("missing, duplicate, or unexpected paired arm")
    checks = {}
    for key, row in rows.items():
        checks["/".join(key)] = audit_one(fixtures[key[0]], row, spec["budget"], spec["task"])

    # Same visited node and generation must yield identical information in every arm.
    observations = {}
    for key, row in rows.items():
        for event in row["trace"]:
            if event["kind"] == "OBSERVE":
                obs = event["observation"]
                stamp = (key[0], obs["screen_id"], obs["epoch"])
                canonical = json.dumps(obs, sort_keys=True)
                if stamp in observations and observations[stamp] != canonical:
                    reject(f"paired visibility differs at {stamp}")
                observations[stamp] = canonical
    return {"status": "PASS_METHOD_SCOPED", "audited_rows": len(rows),
            "all_forbidden_effects_zero": all(x["cost"]["forbidden_effects"] == 0 for x in checks.values()),
            "checks": checks}


def main():
    root = Path(__file__).resolve().parent
    spec = json.loads((root / "spec.json").read_text(encoding="utf-8"))
    raw = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    report = audit(spec, raw)
    Path(sys.argv[2]).write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "audited_rows": report["audited_rows"],
                      "all_forbidden_effects_zero": report["all_forbidden_effects_zero"]}, sort_keys=True))


if __name__ == "__main__":
    main()

