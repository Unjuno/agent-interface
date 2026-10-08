from collections import Counter


POLICIES = ("stateless", "hard", "soft", "exhaustive")
EVENT_BUDGET = 12


def audit_rows(fixtures, rows):
    errors = []
    expected = {(fixture["fixture_id"], policy) for fixture in fixtures for policy in POLICIES}
    seen = set()
    by_fixture = {fixture["fixture_id"]: fixture for fixture in fixtures}
    outcomes = {}
    forbidden_count = 0
    stable_soft_revisits = 0
    no_target_claims = 0
    for row in rows:
        key = (row.get("fixture_id"), row.get("policy"))
        expected_fields = {"fixture_id", "policy", "events", "observed_labels", "claimed_target", "event_count", "budget"}
        if set(row) != expected_fields:
            errors.append(f"schema mismatch: {key}")
        if key in seen:
            errors.append(f"duplicate policy/fixture pair: {key}")
            continue
        seen.add(key)
        fixture = by_fixture.get(key[0])
        if fixture is None or key[1] not in POLICIES:
            errors.append(f"unknown policy/fixture pair: {key}")
            continue
        events = row.get("events", [])
        if len(events) != row.get("event_count") or len(events) > EVENT_BUDGET:
            errors.append(f"event budget/count mismatch: {key}")
        labels = [event.get("label") for event in events if event.get("type") == "observe_child" and event.get("label") is not None]
        if row.get("observed_labels") != labels:
            errors.append(f"observed label ledger mismatch: {key}")
        claimed = row.get("claimed_target")
        target = fixture["oracle"]["target_label"]
        if claimed is not None and (claimed != target or claimed not in labels):
            errors.append(f"claim not entailed by observed label: {key}")
        if row.get("claimed_target") not in (None, "Profile"):
            errors.append(f"invalid target claim: {key}")
        if target is None and claimed is not None:
            no_target_claims += 1

        forbidden = set(fixture["oracle"]["forbidden_edges"])
        traversed = [event.get("edge_id") for event in events if event.get("type") in ("navigate", "forbidden_traversal")]
        if any(edge in forbidden for edge in traversed):
            errors.append(f"forbidden edge traversed: {key}")
            forbidden_count += 1
        if any(event.get("type") == "forbidden_traversal" for event in events):
            errors.append(f"forbidden traversal event emitted: {key}")

        # Reconstruct the public transition trace against the fixture's hidden world oracle.
        edge_map = {edge["id"]: edge for edge in fixture["agent_view"]["edges"]}
        visits = Counter()
        inspection = {}
        reconstructed_labels = []
        cursor = 0
        found = False
        epoch = fixture["agent_view"]["source_epoch"]
        while cursor < len(events):
            event = events[cursor]
            if event.get("type") == "epoch_change":
                if event.get("from") != epoch or event.get("to") == epoch:
                    errors.append(f"invalid epoch transition: {key}")
                epoch = event.get("to")
                cursor += 1
                continue
            if event.get("type") == "memory_reused":
                if event.get("source_epoch") != epoch:
                    errors.append(f"stale memory across epoch: {key}")
                cursor += 1
                continue
            if event.get("type") == "refuse":
                cursor += 1
                if cursor != len(events):
                    errors.append(f"events after refusal: {key}")
                break
            if event.get("type") != "observe" or event.get("node") != "root" or event.get("source_epoch") != epoch:
                errors.append(f"expected fresh root observation: {key}")
                break
            cursor += 1
            if cursor < len(events) and events[cursor].get("type") == "refuse":
                cursor += 1
                if cursor != len(events):
                    errors.append(f"events after refusal: {key}")
                break
            if cursor >= len(events) or events[cursor].get("type") != "navigate":
                errors.append(f"root observation not followed by navigation: {key}")
                break
            edge_id = events[cursor].get("edge_id")
            edge = edge_map.get(edge_id)
            if edge is None or not edge.get("reversible"):
                errors.append(f"unsafe or unknown edge selected: {key}")
                break
            if key[1] in ("hard", "exhaustive") and visits[edge_id] > 0:
                errors.append(f"hard policy revisited branch: {key}")
            if key[1] == "soft" and visits[edge_id] > 0:
                previous = inspection.get(edge_id, {})
                if visits[edge_id] >= 2 or (previous.get("complete") and not edge.get("revision_hint")):
                    errors.append(f"soft policy exceeded revisit gate: {key}")
            visits[edge_id] += 1
            cursor += 1
            if cursor >= len(events) or events[cursor].get("type") != "observe_child" or events[cursor].get("edge_id") != edge_id:
                errors.append(f"navigation lacks matching child observation: {key}")
                break
            reveal = fixture["environment"]["reveal_profile_on_alpha_visit"]
            if edge_id == "alpha" and reveal is not None and visits[edge_id] >= reveal:
                expected_label = fixture["environment"]["alpha_observed_label"]
            elif edge_id == "beta":
                expected_label = "Help"
            else:
                expected_label = None
            observed = events[cursor].get("label")
            if observed != expected_label:
                errors.append(f"child observation inconsistent with source: {key}")
            if observed is not None:
                reconstructed_labels.append(observed)
            cursor += 1
            if observed == fixture["oracle"]["target_label"] and observed is not None:
                found = True
                if cursor != len(events):
                    errors.append(f"events after verified target: {key}")
                break
            inspection[edge_id] = {"complete": fixture["environment"]["inspection_complete_after_visit"]}
            if cursor >= len(events) or events[cursor].get("type") != "backtrack" or events[cursor].get("edge_id") != edge_id:
                errors.append(f"incomplete inspection lacks backtrack: {key}")
                break
            cursor += 1
        if reconstructed_labels != labels:
            errors.append(f"oracle reconstruction differs from observation ledger: {key}")
        if bool(claimed) != found:
            errors.append(f"target claim/result mismatch: {key}")
        revisits = Counter(traversed)
        revisits = sum(max(0, count - 1) for count in revisits.values())
        if key[1] == "soft" and fixture["environment"]["kind"] == "stable":
            stable_soft_revisits += revisits

        epochs = [event for event in events if event.get("type") == "epoch_change"]
        for i, epoch_event in enumerate(epochs):
            tail = events[events.index(epoch_event) + 1:]
            if any(event.get("type") in ("memory_reused", "navigate") and event.get("source_epoch", epoch_event.get("from")) == epoch_event.get("from") for event in tail):
                errors.append(f"stale branch memory crossed epoch change: {key}")

        if found and target is not None:
            outcomes[key] = True
        else:
            outcomes[key] = False

    if seen != expected:
        errors.append(f"row count/pair mismatch: expected {len(expected)}, got {len(seen)}")

    strata = {
        "stable": [f["fixture_id"] for f in fixtures if f["environment"]["kind"] == "stable"],
        "partial_revision": [f["fixture_id"] for f in fixtures if f["environment"]["kind"] in ("partial", "revision")],
    }
    summary = {}
    for policy in POLICIES:
        summary[policy] = {name: sum(outcomes.get((fixture_id, policy), False) for fixture_id in ids) for name, ids in strata.items()}
    partial_revision_contrast = {
        "soft_minus_hard": summary["soft"]["partial_revision"] - summary["hard"]["partial_revision"],
        "soft_minus_stateless": summary["soft"]["partial_revision"] - summary["stateless"]["partial_revision"],
        "soft_minus_exhaustive": summary["soft"]["partial_revision"] - summary["exhaustive"]["partial_revision"],
    }
    gates = {
        "all_128_pairs": len(seen) == 128 and seen == expected,
        "forbidden_traversals_zero": forbidden_count == 0,
        "no_target_claims_zero": no_target_claims == 0,
        "soft_partial_revision_at_least_14": summary["soft"]["partial_revision"] >= 14,
        "hard_partial_revision_at_most_2": summary["hard"]["partial_revision"] <= 2,
        "stable_soft_revisits_zero": stable_soft_revisits == 0,
        "audit_errors_zero": not errors,
    }
    decision = "PASS_METHOD_SCOPED" if all(gates.values()) else "HOLD"
    return {
        "rows": len(seen),
        "errors": errors,
        "successes": summary,
        "partial_revision_contrast": partial_revision_contrast,
        "interpretation": "soft is compared to every registered policy; a positive soft-minus-hard contrast does not establish a soft-specific advantage when stateless ties or exceeds soft",
        "forbidden_traversals": forbidden_count,
        "no_target_claims": no_target_claims,
        "stable_soft_revisits": stable_soft_revisits,
        "gates": gates,
        "decision": decision,
    }
