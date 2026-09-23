from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path


INPUT = Path("/input")
OUTPUT = Path("/evidence")
EXPECTED_ALLOCATION = "issue3588-resident-gtk-sequence-guard-formal-01"
POLICIES = {"UPSTREAM_RESIDENT", "SEQUENCE_GUARDED"}
EFFECTS = {"on", "off"}
TRACE_NAMES = {
    "current_rising_edges", "delayed_replacement_rollback", "valid_new_generation",
    "duplicate_replacement", "delayed_old_observation",
    "delayed_current_generation_observation", "delayed_same_generation_revoke",
    "valid_revoke", "newer_sequence_but_older_generation_replace",
}


def upstream_prefixes(events):
    generation, target = 1, 1
    last_seq, previous, revoked, actions = {}, {}, set(), []
    result = []
    for event in events:
        before = len(actions)
        kind = event["kind"]
        gen = event.get("gen", generation)
        if kind == "replace":
            generation, target = event["gen"], event["target"]
            last_seq, previous, revoked = {}, {}, set()
            actions.append(["invalidate", generation, target])
        elif kind == "revoke":
            revoked.add(gen)
            actions.append(["release", gen])
        elif kind == "obs":
            key = (gen, event.get("target"))
            seq = event["seq"]
            if key != (generation, target) or gen in revoked or seq <= last_seq.get(key, 0):
                actions.append(["refuse", event["id"]])
            else:
                last_seq[key] = seq
                rising = event["value"] is True and not previous.get(key, False)
                previous[key] = event["value"] is True
                if rising:
                    actions.append(["emit", event["id"]])
        result.append({"delta": actions[before:], "actions": copy.deepcopy(actions),
                       "generation": generation, "target": target})
    return result


def guarded_prefixes(events):
    generation, target, stream_seq = 1, 1, 0
    last_seq, previous, revoked, actions = {}, {}, set(), []
    result = []
    for event in events:
        before = len(actions)
        kind, seq = event.get("kind"), event.get("seq")
        if type(seq) is not int or seq <= stream_seq:
            actions.append(["refuse_control", kind, seq])
        else:
            stream_seq = seq
            gen = event.get("gen", generation)
            if kind == "replace":
                new_gen, new_target = event.get("gen"), event.get("target")
                if type(new_gen) is not int or new_gen <= generation or new_target is None:
                    actions.append(["refuse_control", kind, seq])
                else:
                    generation, target = new_gen, new_target
                    actions.append(["invalidate", generation, target])
            elif kind == "revoke":
                if gen != generation:
                    actions.append(["refuse_control", kind, seq])
                else:
                    revoked.add(gen)
                    actions.append(["release", gen])
            elif kind == "obs":
                key = (gen, event.get("target"))
                if key != (generation, target) or gen in revoked or seq <= last_seq.get(key, 0):
                    actions.append(["refuse", event.get("id", "")])
                else:
                    last_seq[key] = seq
                    rising = event.get("value") is True and not previous.get(key, False)
                    previous[key] = event.get("value") is True
                    if rising:
                        actions.append(["emit", event.get("id", "")])
            else:
                actions.append(["refuse_control", kind, seq])
        result.append({"delta": actions[before:], "actions": copy.deepcopy(actions),
                       "generation": generation, "target": target, "stream_seq": stream_seq})
    return result


def validate(raw: dict, *, check_files: bool = True) -> list[str]:
    errors = []
    rows = raw.get("rows")
    if not isinstance(rows, list) or len(rows) != 36:
        return ["expected exactly 36 rows"]
    if set(raw.get("trace_names", [])) != TRACE_NAMES:
        errors.append("frozen trace schedule mismatch")
    expected = {(p, case, effect) for p in POLICIES
                for case in TRACE_NAMES for effect in EFFECTS}
    observed = {(r.get("policy"), r.get("case"), r.get("effect_mode")) for r in rows}
    if observed != expected:
        errors.append("matrix keys/denominator mismatch")
    if len(observed) != len(rows):
        errors.append("duplicate matrix keys")

    frame_root = INPUT
    for row in rows:
        label = f"{row.get('policy')}/{row.get('case')}/{row.get('effect_mode')}"
        if row.get("error") is not None:
            errors.append(f"{label}: runner error {row['error']}")
            continue
        expected_prefixes = (upstream_prefixes(row["events"]) if row["policy"] == "UPSTREAM_RESIDENT"
                             else guarded_prefixes(row["events"]))
        if len(row.get("prefixes", [])) != len(expected_prefixes):
            errors.append(f"{label}: prefix count mismatch")
            continue
        emitted_indices, total_emits = [], 0
        for index, (actual, expected_prefix) in enumerate(zip(row["prefixes"], expected_prefixes)):
            if actual.get("index") != index or actual.get("event") != row["events"][index]:
                errors.append(f"{label} prefix {index}: event/order mismatch")
            if actual.get("action_delta") != expected_prefix["delta"]:
                errors.append(f"{label} prefix {index}: action delta differs from independent replay")
            if actual.get("actions_so_far") != expected_prefix["actions"]:
                errors.append(f"{label} prefix {index}: cumulative actions differ from independent replay")
            emits = [a for a in expected_prefix["delta"] if a[0] == "emit"]
            if emits:
                emitted_indices.extend([index] * len(emits))
            total_emits += len(emits)
            visible_expected = total_emits if row["effect_mode"] == "on" else 0
            if actual.get("visible_effect_count") != visible_expected:
                errors.append(f"{label} prefix {index}: visible effect differs from emitted actions")
            if actual.get("visible_title") != f"resident-fixture:{visible_expected}":
                errors.append(f"{label} prefix {index}: GTK visible title mismatch")
            if actual.get("space_key_up") is not True:
                errors.append(f"{label} prefix {index}: Space key not independently observed up")
        if row.get("prefix_effect_counts") != [
                sum(len([a for a in p["delta"] if a[0] == "emit"]) for p in expected_prefixes[:i + 1])
                if row["effect_mode"] == "on" else 0
                for i in range(len(expected_prefixes))]:
            errors.append(f"{label}: prefix effect-count ledger mismatch")
        expected_task_effect = total_emits if row["effect_mode"] == "on" else 0
        if row.get("emitted_event_indices") != emitted_indices:
            errors.append(f"{label}: emitted event-index ledger mismatch")
        if row.get("action_count") != total_emits or row.get("transport_count") != total_emits:
            errors.append(f"{label}: action count mismatch")
        if row.get("task_effect_count") != expected_task_effect:
            errors.append(f"{label}: final task effect mismatch")
        if row.get("gui_title") != f"resident-fixture:{expected_task_effect}":
            errors.append(f"{label}: GTK title mismatch")
        if row.get("key_release_verified") is not True or len(row.get("key_release_reads", [])) != total_emits or not all(row.get("key_release_reads", [])):
            errors.append(f"{label}: key release evidence missing")
        if not row.get("focus_verified"):
            errors.append(f"{label}: focus was not verified")
        if row.get("fixture_reaped") is not True or row.get("xvfb_reaped") is not True:
            errors.append(f"{label}: process cleanup/reap missing")
        if row.get("fixture_exit_code") not in {-15, 0} or row.get("xvfb_exit_code") not in {-15, 0}:
            errors.append(f"{label}: process exit status unexpected")
        if row.get("socket_disappeared") is not True:
            errors.append(f"{label}: Xvfb socket persisted")
        if not row.get("fixture_start_ticks") or not row.get("xvfb_start_ticks") or row.get("fixture_pid") == row.get("xvfb_pid"):
            errors.append(f"{label}: process-incarnation evidence invalid")
        if row.get("width", 0) <= 0 or row.get("height", 0) <= 0 or row.get("width") != row.get("after_width") or row.get("height") != row.get("after_height"):
            errors.append(f"{label}: frame dimensions invalid")
        if row.get("bytes_per_frame") != row.get("width", 0) * row.get("height", 0) * 4:
            errors.append(f"{label}: frame byte length differs from dimensions")
        for path_key, hash_key in (("before_path", "before_sha256"), ("after_path", "after_sha256")):
            path = frame_root / row.get(path_key, "")
            if check_files and not path.is_file():
                errors.append(f"{label}: missing frame {path_key}")
                continue
            if not check_files:
                continue
            data = path.read_bytes()
            if len(data) != row.get("bytes_per_frame") or hashlib.sha256(data).hexdigest() != row.get(hash_key):
                errors.append(f"{label}: frame bytes/hash mismatch {path_key}")
        if row.get("window_pixels_changed") != (row.get("before_sha256") != row.get("after_sha256")):
            errors.append(f"{label}: pixel-delta flag/hash mismatch")
        if row.get("effect_mode") == "on" and row.get("task_effect_count", 0) > 0 and not row.get("window_pixels_changed"):
            errors.append(f"{label}: expected visible pixel change is absent")

    rollback = {(r.get("policy"), r.get("effect_mode")): r for r in rows
                if r.get("case") == "delayed_replacement_rollback"}
    for mode in EFFECTS:
        old = rollback.get(("UPSTREAM_RESIDENT", mode))
        new = rollback.get(("SEQUENCE_GUARDED", mode))
        if old is None or new is None:
            errors.append("rollback contrast row missing")
            continue
        if old.get("action_count") < 1 or old.get("task_effect_count") != (1 if mode == "on" else 0):
            errors.append(f"upstream rollback failure not visible in mode={mode}")
        if new.get("action_count") != 0 or new.get("task_effect_count") != 0:
            errors.append(f"guarded stale replacement path acted in mode={mode}")
    positives = {
        ("UPSTREAM_RESIDENT", "current_rising_edges"): 2,
        ("SEQUENCE_GUARDED", "current_rising_edges"): 2,
        ("UPSTREAM_RESIDENT", "valid_new_generation"): 1,
        ("SEQUENCE_GUARDED", "valid_new_generation"): 1,
    }
    for (policy, case), expected in positives.items():
        for mode in EFFECTS:
            row = next((r for r in rows if r.get("policy") == policy and r.get("case") == case and r.get("effect_mode") == mode), None)
            visible = expected if mode == "on" else 0
            if row is None or row.get("action_count") != expected or row.get("task_effect_count") != visible:
                errors.append(f"positive control failed: {policy}/{case}/{mode}")
    if raw.get("formal_invocations") != 1 or raw.get("reruns") != 0:
        errors.append("formal invocation/retry accounting mismatch")
    return errors


def challenge_mutations(raw: dict) -> list[dict]:
    mutations = []
    for name, mutate in (
        ("row-removed", lambda x: x["rows"].pop()),
        ("prefix-action-forged", lambda x: x["rows"][0]["prefixes"][0].update(action_delta=[["emit", "forged"]])),
        ("key-release-cleared", lambda x: x["rows"][0].update(key_release_verified=False)),
        ("task-effect-forged", lambda x: x["rows"][0].update(task_effect_count=999)),
    ):
        damaged = copy.deepcopy(raw)
        mutate(damaged)
        mutations.append({"name": name, "detected": bool(validate(damaged, check_files=False))})
    return mutations


def self_test() -> None:
    rows = []
    trace_names = sorted(TRACE_NAMES)
    for policy in POLICIES:
        for case in trace_names:
            events = [{"kind": "obs", "id": "x", "seq": 1, "gen": 1, "target": 1, "value": True}]
            prefixes = guarded_prefixes(events) if policy == "SEQUENCE_GUARDED" else upstream_prefixes(events)
            effect = "on"
            rows.append({"policy": policy, "case": case, "effect_mode": effect,
                         "events": events, "prefixes": [{"index": 0, "event": events[0],
                             "action_delta": prefixes[0]["delta"], "actions_so_far": prefixes[0]["actions"],
                             "visible_effect_count": 1, "visible_title": "resident-fixture:1", "space_key_up": True}],
                         "prefix_effect_counts": [1], "emitted_event_indices": [0],
                         "action_count": 1, "transport_count": 1, "task_effect_count": 1,
                         "gui_title": "resident-fixture:1", "key_release_verified": True,
                         "key_release_reads": [True], "focus_verified": True,
                         "fixture_reaped": True, "xvfb_reaped": True,
                         "fixture_exit_code": 0, "xvfb_exit_code": 0, "socket_disappeared": True,
                         "fixture_start_ticks": "1", "xvfb_start_ticks": "2", "fixture_pid": 10, "xvfb_pid": 11,
                         "width": 1, "height": 1, "after_width": 1, "after_height": 1,
                         "bytes_per_frame": 4, "before_path": "na", "after_path": "na",
                         "before_sha256": "0", "after_sha256": "1", "window_pixels_changed": True})
    test_raw = {"trace_names": trace_names, "rows": rows, "formal_invocations": 1, "reruns": 0}
    # Keep mutation challenges independent of scenario realism; their contract is rejection.
    sample = rows[0]
    for p in sample["prefixes"]:
        p["visible_title"] = "resident-fixture:1"
    mutations = challenge_mutations(test_raw)
    if len(mutations) != 4 or not all(x["detected"] for x in mutations):
        raise AssertionError(f"corruption challenges failed: {mutations}")


def main():
    raw_bytes = (INPUT / "raw.json").read_bytes()
    raw = json.loads(raw_bytes)
    freeze_bytes = Path("/freeze.json").read_bytes()
    manifest_bytes = Path("/source_manifest.json").read_bytes()
    freeze, manifest = json.loads(freeze_bytes), json.loads(manifest_bytes)
    errors = []
    if hashlib.sha256(freeze_bytes).hexdigest() != raw.get("freeze_sha256"):
        errors.append("raw/freeze hash mismatch")
    if hashlib.sha256(manifest_bytes).hexdigest() != raw.get("source_manifest_sha256"):
        errors.append("raw/manifest hash mismatch")
    if freeze.get("source_manifest_sha256") != hashlib.sha256(manifest_bytes).hexdigest():
        errors.append("freeze/manifest binding mismatch")
    if raw.get("source_commit") != freeze.get("source_commit"):
        errors.append("source commit mismatch")
    if raw.get("image_id") != freeze.get("image_id"):
        errors.append("image identity mismatch")
    for rel, expected_sha in manifest.get("files", {}).items():
        p = Path("/src") / rel
        if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest() != expected_sha:
            errors.append(f"source hash mismatch: {rel}")
    payload = dict(raw)
    claimed_result_sha = payload.pop("result_sha256", None)
    if hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest() != claimed_result_sha:
        errors.append("raw result self-hash mismatch")
    errors.extend(validate(raw))
    mutations = challenge_mutations(raw)
    if len(mutations) != 4 or not all(item["detected"] for item in mutations):
        errors.append("auditor corruption challenge failed")
    decision = "PASS_INDEPENDENT_GTK_SEQUENCE_GUARD_AUDIT" if not errors else "HOLD_OR_FAIL_GTK_SEQUENCE_GUARD_AUDIT"
    summary = {"audit": decision, "row_count": len(raw.get("rows", [])),
               "raw_sha256": hashlib.sha256(raw_bytes).hexdigest(),
               "freeze_sha256": hashlib.sha256(freeze_bytes).hexdigest(),
               "source_manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
               "corruption_controls": mutations, "errors": errors}
    (OUTPUT / "audit.json").write_text(json.dumps(summary, sort_keys=True, indent=2) + "\n")
    print(json.dumps(summary, sort_keys=True))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
