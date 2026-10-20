#!/usr/bin/env python3
"""Candidate reducer for the frozen #7164 finite field-invalidation fixture."""
import argparse
import hashlib
import json
from pathlib import Path


UNKNOWN = {"status": "UNKNOWN", "value": None}


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def current(value):
    return {"status": "CURRENT", "value": value}


def value_of(fields, name):
    item = fields.get(name, UNKNOWN)
    return item.get("value") if item.get("status") == "CURRENT" else None


def dynamic_dependencies(name, fields, schema):
    mode = value_of(fields, "ui_mode")
    branch = schema.get("dynamic_dependencies", {}).get(name, {}).get(mode)
    if branch is not None:
        return branch
    return schema["dependencies"][name]


def derive(name, fields, coverage_complete):
    if not coverage_complete:
        return UNKNOWN
    if name == "enabled":
        mode = value_of(fields, "ui_mode")
        source = "enabled_edit" if mode == "edit" else "enabled_preview" if mode == "preview" else None
        value = value_of(fields, source) if source else None
        return current(value) if value is not None else UNKNOWN
    if name == "screen_position":
        origin = value_of(fields, "surface_origin")
        local = value_of(fields, "local_position")
        if origin is None or local is None:
            return UNKNOWN
        return current([origin[0] + local[0], origin[1] + local[1]])
    if name == "contextual_role":
        role = value_of(fields, "surface_role")
        scope = value_of(fields, "task_scope")
        return current(role + ":" + scope) if role is not None and scope is not None else UNKNOWN
    if name == "recovery_anchor":
        position = value_of(fields, "screen_position")
        surface = value_of(fields, "surface_id")
        scope = value_of(fields, "task_scope")
        if position is None or surface is None or scope is None:
            return UNKNOWN
        return current(surface + "@" + str(position[0]) + "," + str(position[1]) + "#" + scope)
    if name == "object_caption":
        label = value_of(fields, "accessible_name")
        text = value_of(fields, "text_value")
        return current(label + "|" + text) if label is not None and text is not None else UNKNOWN
    raise ValueError("unknown derived field: " + name)


def refresh_all(fields, schema, coverage_complete):
    count = 0
    for name in schema["derived_order"]:
        fields[name] = derive(name, fields, coverage_complete)
        count += int(fields[name]["status"] == "CURRENT")
    return count


def affected_derived(changed, fields, schema):
    affected = set()
    frontier = set(changed)
    for name in schema["derived_order"]:
        deps = set(dynamic_dependencies(name, fields, schema))
        if deps & frontier:
            affected.add(name)
            frontier.add(name)
    return [name for name in schema["derived_order"] if name in affected]


def initial_state(base, schema):
    fields = {name: current(value) for name, value in base["fields"].items()}
    for name in schema["derived_order"]:
        fields[name] = UNKNOWN
    count = refresh_all(fields, schema, base["coverage_complete"])
    return {
        "key": dict(base["key"]),
        "epoch": base["epoch"],
        "coverage_complete": base["coverage_complete"],
        "fields": fields,
        "initial_recomputed": count,
    }


def apply_case(case, schema, method):
    state = initial_state(case["base"], schema)
    recomputed = 0
    accepted = []
    rejected = []
    for event in case["events"]:
        event_key = event["key"]
        if event_key != state["key"]:
            old_generation = state["key"].get("generation")
            new_generation = event_key.get("generation")
            if (event_key.get("object_id") == state["key"].get("object_id")
                    and isinstance(new_generation, int) and isinstance(old_generation, int)
                    and new_generation > old_generation and "snapshot" in event):
                snapshot = event["snapshot"]
                direct = {name: UNKNOWN.copy() for name in schema["direct_fields"]}
                direct.update({name: current(value) for name, value in snapshot["fields"].items()})
                state = {
                    "key": dict(event_key),
                    "epoch": event["epoch"],
                    "coverage_complete": snapshot["coverage_complete"],
                    "fields": direct,
                }
                for name in schema["derived_order"]:
                    state["fields"][name] = UNKNOWN
                count = refresh_all(state["fields"], schema, state["coverage_complete"])
                recomputed += count if method in ("whole_record", "dependency_aware") else 0
                accepted.append({"event_id": event["event_id"], "status": "NEW_GENERATION_RESET"})
            else:
                rejected.append({"event_id": event["event_id"], "status": "REJECTED_WRONG_GENERATION"})
            continue
        if event["epoch"] <= state["epoch"]:
            rejected.append({"event_id": event["event_id"], "status": "REJECTED_STALE_EPOCH"})
            continue

        before = state["fields"]
        changed = set(event.get("updates", {})) | set(event.get("invalidate_fields", []))
        effective_schema = dict(schema)
        if event.get("removed_dependency_edges"):
            effective_schema["dependencies"] = {
                name: [dep for dep in deps if [dep, name] not in event["removed_dependency_edges"]]
                for name, deps in schema["dependencies"].items()
            }
        for name, value in event.get("updates", {}).items():
            before[name] = current(value)
        for name in event.get("invalidate_fields", []):
            before.pop(name, None)
        state["epoch"] = event["epoch"]
        state["coverage_complete"] = event["coverage_complete"]

        if method == "whole_record":
            recomputed += refresh_all(before, schema, state["coverage_complete"])
        elif method == "independent_field":
            # Deliberately weak comparison: direct fields update, but derived
            # fields are not invalidated through their support dependencies.
            pass
        elif method == "dependency_aware":
            if not state["coverage_complete"]:
                for name in schema["derived_order"]:
                    before[name] = UNKNOWN
            else:
                affected = affected_derived(changed, before, effective_schema)
                for name in affected:
                    # Candidate follows its declared dependency graph. A
                    # deliberately removed support edge can therefore leave
                    # this derivation stale; the independent auditor catches it.
                    before[name] = derive(name, before, state["coverage_complete"])
                    recomputed += int(before[name]["status"] == "CURRENT")
        else:
            raise ValueError("unknown method")
        accepted.append({"event_id": event["event_id"], "status": "ACCEPTED"})

    return {
        "case_id": case["case_id"],
        "method": method,
        "key": state["key"],
        "epoch": state["epoch"],
        "coverage_complete": state["coverage_complete"],
        "accepted_events": accepted,
        "rejected_events": rejected,
        "event_recomputed_derived": recomputed,
        "fields": state["fields"],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--schema", required=True)
    parser.add_argument("--freeze", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    input_path, schema_path, freeze_path = map(Path, (args.input, args.schema, args.freeze))
    freeze = json.loads(freeze_path.read_text())
    package = Path(__file__).parent
    actual = {name: sha256(package / name) for name in freeze["sha256"]}
    if any(freeze["sha256"].get(name) != digest for name, digest in actual.items()):
        raise SystemExit("FREEZE_HASH_MISMATCH")
    if sha256(input_path) != actual["INPUT.json"] or sha256(schema_path) != actual["SCHEMA.json"]:
        raise SystemExit("ARGUMENT_HASH_MISMATCH")
    inputs = json.loads(input_path.read_text())
    schema = json.loads(schema_path.read_text())
    results = []
    for case in inputs["cases"]:
        for method in schema["methods"]:
            results.append(apply_case(case, schema, method))
    output = {
        "format": "field-invalidation-candidate-v1",
        "freeze_id": freeze["freeze_id"],
        "source_main": freeze["source_main"],
        "input_sha256": actual["INPUT.json"],
        "schema_sha256": actual["SCHEMA.json"],
        "candidate_sha256": actual["candidate.py"],
        "results": results,
    }
    Path(args.output).write_text(json.dumps(output, sort_keys=True, separators=(",", ":")) + "\n")


if __name__ == "__main__":
    main()
