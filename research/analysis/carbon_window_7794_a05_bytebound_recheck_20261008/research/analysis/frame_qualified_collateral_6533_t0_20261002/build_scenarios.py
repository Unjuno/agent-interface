#!/usr/bin/env python3
"""Build the frozen, deterministic structured-document fixture for Issue #6533."""

import json
import hashlib
import sys
from pathlib import Path


def build_case(case_id, changes, metadata, target_expected=2, unrelated_count=256):
    before = {f"unrelated:{i:03d}": f"stable-{i:03d}" for i in range(unrelated_count)}
    before.update(
        {
            "target:value": 1,
            "formula:derived": 2,
            "alias:peer": 1,
            "callback:result": 0,
            "external:value": 0,
            "persisted:value": 1,
        }
    )
    after = dict(before)
    after.update(changes)
    observed_generation = metadata.pop("observed_generation", 7)
    events = [{"seq": 1, "kind": "action_admitted", "action_id": f"fixture-action:{case_id}",
               "generation": 7}]
    writer_by_key = {
        "target:value": "agent_action",
        "formula:derived": "fixture_formula",
        "alias:peer": "alias_projection",
        "callback:result": "unknown_callback",
        "external:value": "remote_actor",
        "persisted:value": "autosave_worker",
    }
    for seq, (key, value) in enumerate(sorted(changes.items()), start=2):
        events.append({"seq": seq, "kind": "write", "key": key, "new_value": value,
                       "writer": writer_by_key.get(key, "unclassified_writer")})
    if not metadata["persistence_complete"]:
        events.append({"seq": len(events) + 1, "kind": "save_pending", "action_id": f"fixture-action:{case_id}"})
    events.append({"seq": len(events) + 1, "kind": "snapshot_observed",
                   "generation": observed_generation, "durable": metadata["persistence_complete"]})
    event_manifest_sha256 = hashlib.sha256(
        json.dumps(events, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return {
        "case_id": case_id,
        "action_id": f"fixture-action:{case_id}",
        "certificate_version": 1,
        "before": before,
        "after": after,
        "authorized_changes": {"target:value": target_expected},
        "direct_footprint": ["target:value"],
        "source_generation": 7,
        "observed_generation": observed_generation,
        "events": events,
        "event_manifest_sha256": event_manifest_sha256,
        "metadata": metadata,
    }


def scenarios():
    complete = {
        "writer_inventory_complete": True,
        "dependency_inventory_complete": True,
        "dependency_provenance_complete": True,
        "alias_inventory_complete": True,
        "callback_inventory_complete": True,
        "external_writer_inventory_complete": True,
        "persistence_complete": True,
        "elided_collateral_predicates": ["unchanged:all-cells-outside-closure"],
        "dependency_edges": [],
        "alias_edges": [],
        "callbacks": [],
        "external_writers": [],
    }
    cases = [
        build_case(
            "isolated_target_write",
            {"target:value": 2},
            dict(complete),
        ),
        build_case(
            "transitive_formula_collateral",
            {"target:value": 2, "formula:derived": 9},
            {**complete, "dependency_edges": [["target:value", "formula:derived", "fixture-rule:formula-v1"]]},
        ),
        build_case(
            "alias_write",
            {"target:value": 2, "alias:peer": 2},
            {
                **complete,
                "alias_edges": [["target:value", "alias:peer"]],
            },
        ),
        build_case(
            "hidden_callback_write",
            {"target:value": 2, "callback:result": 1},
            {
                **complete,
                "callback_inventory_complete": False,
                "callbacks": ["on_change:unknown_writer"],
            },
        ),
        build_case(
            "external_writer_change",
            {"target:value": 2, "external:value": 1},
            {
                **complete,
                "external_writer_inventory_complete": False,
                "external_writers": ["remote_actor:external:value"],
            },
        ),
        build_case(
            "stale_generation",
            {"target:value": 2},
            {**complete, "observed_generation": 6},
        ),
        build_case(
            "delayed_durable_save",
            {"target:value": 2, "persisted:value": 1},
            {**complete, "persistence_complete": False},
        ),
        build_case(
            "missing_dependency_edge",
            {"target:value": 2, "formula:derived": 9},
            {**complete, "dependency_inventory_complete": False},
        ),
        build_case("genuinely_disjoint_small", {"target:value": 2}, dict(complete),
                   unrelated_count=8),
        build_case("genuinely_disjoint_medium", {"target:value": 2}, dict(complete),
                   unrelated_count=64),
        build_case("genuinely_disjoint_large", {"target:value": 2}, dict(complete),
                   unrelated_count=256),
    ]
    return {"schema": "issue6533-fixture-v1", "cases": cases}


if __name__ == "__main__":
    destination = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("scenarios.json")
    destination.write_text(json.dumps(scenarios(), sort_keys=True, indent=2) + "\n")
