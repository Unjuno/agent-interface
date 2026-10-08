"""Raw-record-only audit for frozen #8328 formal cases and corruption controls."""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile


SCHEDULE = [("C01", "current"), ("G01", "guard-stable"), ("I01", "guard-interposed"),
            ("C02", "current"), ("G02", "guard-stable"), ("I02", "guard-interposed"),
            ("C03", "current"), ("G03", "guard-stable"), ("I03", "guard-interposed")]
EXPECTED = {"current": ("aB2", 0), "guard-stable": ("aB2", 0),
            "guard-interposed": ("Ab2", 1)}
FROZEN_PLAN_SHA256 = "0e76de1e050e909307e088168b08bfc90e283e19e300773d11fef375f0af2883"
FROZEN_PLAN = json.loads((Path(__file__).resolve().parent / "FREEZE.json").read_text())
SOURCE_MANIFEST_PATH = Path(__file__).resolve().parent / "SOURCE_MANIFEST.json"
SOURCE_MANIFEST = json.loads(SOURCE_MANIFEST_PATH.read_text())
EXPECTED_RUNNER_SHA256 = SOURCE_MANIFEST["files"][FROZEN_PLAN["artifacts"]["runner"]]
EXPECTED_XVFB_STDERR_SHA256 = FROZEN_PLAN["environment"]["expected_xvfb_stderr_sha256"]


def xvfb_stderr_blocks(raw: bytes) -> int | None:
    block = (Path(__file__).resolve().parent / "XVFB_EXPECTED_STDERR.txt").read_bytes()
    if not block or len(raw) % len(block):
        return None
    count = len(raw) // len(block)
    if count not in FROZEN_PLAN["environment"]["expected_xvfb_stderr_blocks"] or raw != block * count:
        return None
    return count


def success_exit(value: object) -> bool:
    return type(value) is int and value == 0


def private_network_boundary(boundary: object) -> bool:
    return (type(boundary) is dict and
            type(boundary.get("namespace_inode")) is int and
            type(boundary.get("pid1_namespace_inode")) is int and
            boundary["namespace_inode"] != boundary["pid1_namespace_inode"] and
            all(type(boundary.get(key)) is list and not boundary[key]
                for key in ("ipv4_non_loopback_routes", "ipv6_non_loopback_routes",
                            "up_non_loopback_interfaces")))


def audit_record(case_id: str, arm: str, record: dict) -> list[str]:
    errors: list[str] = []
    expected_value, expected_lock = EXPECTED[arm]
    def require(condition: bool, message: str) -> None:
        if not condition:
            errors.append(message)

    def neutral_keymap(value: object) -> bool:
        return (type(value) is list and len(value) == 32 and
                all(type(byte) is int and 0 <= byte <= 255 for byte in value) and
                value == [0] * 32)

    require(record.get("kind") == "formal-public-dispatch-case", "kind")
    require(record.get("study_id") == "caps-text-query-xtest-a02-20261008", "study id")
    require(record.get("case_id") == case_id, "case id")
    require(record.get("arm") == arm, "arm")
    require(record.get("main_backend_sha256") == "c4bd1c2ccda7db43a4a62efc866547f21e2d11c0d795834f1f8e1d6b32f63126", "main backend identity")
    before = record.get("before", {})
    after = record.get("after", {})
    require(type(before.get("lockmask")) is int and before.get("lockmask") == 0,
            "initial LockMask exact integer")
    require(neutral_keymap(before.get("keymap")), "initial keymap exact integer bytes")
    require(type(after.get("lockmask")) is int and after.get("lockmask") == expected_lock,
            "final LockMask exact integer")
    require(neutral_keymap(after.get("keymap")), "final keymap exact integer bytes")
    require(record.get("app_after", {}).get("value") == expected_value, "Entry value")
    require(record.get("response", {}).get("result", {}).get("status") == "completed", "dispatch status")
    execution = record.get("response", {}).get("result", {}).get("execution", {})
    completed_ops = execution.get("completed_ops")
    require(type(completed_ops) is list and all(type(op) is int for op in completed_ops) and
            completed_ops == [0, 1, 2], "completed operation indices exact integers")
    releases = execution.get("releases", [])
    require(type(releases) is list and bool(releases) and type(releases[-1]) is dict and
            releases[-1].get("verified") is True and
            releases[-1].get("keys_down") == [] and releases[-1].get("buttons_down") == [],
            "verified neutral release receipt")
    require(type(record.get("app", {}).get("exit")) is int and
            record.get("app", {}).get("exit") == 0, "app exit exact integer")
    require(type(record.get("errors")) is list and not record["errors"], "record errors")
    window = record.get("app", {}).get("ready", {}).get("window")
    require(type(window) is int and window > 0, "fixture window identity")
    server = record.get("display_server", {})
    require(server.get("display") == record.get("display"), "Xvfb display identity")
    require(type(server.get("pid")) is int and server["pid"] > 0, "Xvfb PID")
    server_argv = server.get("argv")
    require(type(server_argv) is list and all(type(arg) is str for arg in server_argv) and
            bool(server_argv) and Path(server_argv[0]).name == "Xvfb" and
            any(server_argv[i:i + 2] == ["-nolisten", "tcp"]
                for i in range(len(server_argv) - 1)), "Xvfb argv/isolation")
    events = record.get("entry_events", [])
    require(type(events) is list and all(type(event) is dict for event in events),
            "Entry event row shape")
    if type(events) is not list or not all(type(event) is dict for event in events):
        events = []
    allowed_event_types = {"KeyPress", "KeyRelease", "value", "exit"}
    require(all(event.get("event") in allowed_event_types for event in events),
            "Entry event type")
    event_times = [event.get("ns") for event in events]
    require(all(type(ns) is int for ns in event_times) and
            event_times == sorted(event_times), "Entry event chronology")
    presses = [e for e in events if e.get("event") == "KeyPress"]
    key_releases = [e for e in events if e.get("event") == "KeyRelease"]
    character_presses = [e for e in presses if e.get("char")]
    require([e.get("char") for e in character_presses] == list(expected_value),
            "exact Entry character sequence")
    pressed_codes = [e.get("keycode") for e in presses]
    released_codes = [e.get("keycode") for e in key_releases]
    require(all(type(code) is int for code in pressed_codes + released_codes) and
            Counter(pressed_codes) == Counter(released_codes),
            "Entry KeyPress/KeyRelease keycode balance")
    held_codes: set[int] = set()
    key_chronology_ok = True
    for event in events:
        kind = event.get("event")
        if kind not in ("KeyPress", "KeyRelease"):
            continue
        code = event.get("keycode")
        if type(code) is not int:
            key_chronology_ok = False
            continue
        if kind == "KeyPress":
            if code in held_codes:
                key_chronology_ok = False
            held_codes.add(code)
        else:
            if code not in held_codes:
                key_chronology_ok = False
            else:
                held_codes.remove(code)
    require(key_chronology_ok and not held_codes, "Entry per-key chronology")
    value_rows = [(i, e) for i, e in enumerate(events) if e.get("event") == "value"]
    expected_prefixes = [expected_value[:i] for i in range(1, len(expected_value) + 1)]
    require([e.get("value") for _, e in value_rows] == expected_prefixes,
            "Entry value progression")
    causal_value_order = len(value_rows) == len(character_presses)
    for (press_i, press), (value_i, _) in zip(
            [(i, e) for i, e in enumerate(events) if e.get("event") == "KeyPress" and e.get("char")],
            value_rows):
        release_i = next((i for i, e in enumerate(events)
                          if i > press_i and e.get("event") == "KeyRelease" and
                          e.get("keycode") == press.get("keycode")), -1)
        causal_value_order = causal_value_order and press_i < value_i < release_i
    require(causal_value_order, "Entry value event after character KeyPress")
    exit_rows = [(i, e) for i, e in enumerate(events) if e.get("event") == "exit"]
    require(len(exit_rows) == 1 and exit_rows[0][0] == len(events) - 1 and
            exit_rows[0][1].get("value") == expected_value,
            "fixture exit after input")
    program = record.get("program", {})
    require(program.get("ops") == [{"op": "focus", "target": "entry"},
                                     {"op": "text", "text": "aB2"},
                                     {"op": "release_all"}], "exact public program")
    require(record.get("program_id") == f"formal-{case_id}-{arm}", "program id")
    boundary = record.get("network_boundary", {})
    require(private_network_boundary(boundary), "private network namespace")
    require(private_network_boundary(boundary), "network disabled for case")
    if arm == "guard-interposed":
        actor = record.get("actor", {})
        try:
            actor_doc = json.loads(actor.get("stdout", ""))
        except (ValueError, TypeError):
            actor_doc = {}
        presses = [e for e in events if e.get("event") == "KeyPress"]
        require(success_exit(actor.get("exit")), "actor exit")
        require(type(actor.get("stderr")) is str and not actor["stderr"], "actor stderr")
        require(type(actor.get("pid")) is int and actor["pid"] not in
                (record.get("driver_pid"), record.get("app", {}).get("pid")), "separate actor process")
        actor_state = {"candidate_sample": 0, "pre_lock": 0, "accepted": 1, "post_lock": 1}
        require(all(type(actor_doc.get(name)) is int for name in actor_state) and
                all(actor_doc.get(name) == expected for name, expected in actor_state.items()),
                "actor state exact integers")
        require(type(actor_doc.get("ack_ns")) is int, "actor ACK timestamp exact integer")
        require(bool(presses) and actor_doc.get("ack_ns", 2**63) < presses[0].get("ns", -1),
                "ACK before first KeyPress")
    else:
        require("actor" not in record, "unexpected actor")
    require(type(record.get("app", {}).get("stderr", "")) is str and
            not record.get("app", {}).get("stderr", "") and
            type(record.get("app_stderr")) is str and not record["app_stderr"],
            "app stderr")
    if arm.startswith("guard-"):
        require(record.get("current_main_candidate_patch_sha256") ==
                FROZEN_PLAN["source_base"]["current_main_candidate_patch_sha256"],
                "current-main candidate patch identity")
    imports = record.get("runtime_imports", {})
    require("runtime.cli_v1.api" in imports, "public dispatch source identity")
    require("runtime.backends.x11_v1.backend" in imports, "backend source identity")
    require(bool(imports.get("runtime.cli_v1.api", {}).get("sha256")), "dispatch source digest")
    require(bool(imports.get("runtime.backends.x11_v1.backend", {}).get("sha256")), "backend source digest")
    require(type(record.get("runner_sha256")) is str and
            record.get("runner_sha256") == EXPECTED_RUNNER_SHA256, "runner source identity")
    require(record.get("freeze_sha256") == FROZEN_PLAN_SHA256, "freeze source digest")
    return errors


def audit(root: Path) -> tuple[list[str], dict]:
    errors: list[str] = []
    rows = []
    seen_hashes: dict[str, list[str]] = {}
    common_modules = None
    server_pids = set()
    snapshot_ids = set()
    freeze_ids = set()
    manifest_path = Path(__file__).resolve().parent / "SOURCE_MANIFEST.json"
    try:
        manifest = json.loads(manifest_path.read_text())
        expected_imports = manifest["expected_imports"]
    except Exception as exc:
        errors.append(f"source manifest unavailable: {type(exc).__name__}: {exc}")
        expected_imports = {}
    index_path = root / "RAW_INDEX.json"
    try:
        index = json.loads(index_path.read_text())
    except Exception as exc:
        errors.append(f"raw index unavailable: {type(exc).__name__}: {exc}")
        index = {}
    preflight_path = root / "PREFLIGHT.json"
    try:
        preflight = json.loads(preflight_path.read_text())
        if preflight.get("status") != "PASS" or preflight.get("scope") != "excluded pre-allocation readiness only":
            errors.append("pre-allocation environment preflight")
        if (not success_exit(preflight.get("xvfb", {}).get("exit")) or
                preflight.get("xtest_present") is not True):
            errors.append("preflight Xvfb/XTEST")
        preflight_stderr_path = root / "preflight-xvfb" / "xvfb.stderr"
        if preflight_stderr_path.is_file():
            preflight_stderr = preflight_stderr_path.read_bytes()
        else:
            preflight_stderr_value = preflight.get("xvfb", {}).get("stderr", "")
            preflight_stderr = (preflight_stderr_value.encode()
                                if type(preflight_stderr_value) is str else b"")
        if (xvfb_stderr_blocks(preflight_stderr) is None or
                type(preflight.get("xvfb", {}).get("stderr_blocks")) is not int or
                preflight.get("xvfb", {}).get("stderr_blocks") != xvfb_stderr_blocks(preflight_stderr)):
            errors.append("preflight Xvfb stderr identity")
        boundary = preflight.get("network_boundary", {})
        if not private_network_boundary(boundary):
            errors.append("preflight network isolation")
    except Exception as exc:
        errors.append(f"preflight unavailable: {type(exc).__name__}: {exc}")
    if index:
        if index.get("schema") != "caps-text-query-xtest-formal-index-v1":
            errors.append("raw index schema")
        if index.get("study_id") != "caps-text-query-xtest-a02-20261008":
            errors.append("raw index study id")
        if index.get("status") != "COMPLETE":
            errors.append("raw index incomplete")
        if index.get("freeze_sha256") != FROZEN_PLAN_SHA256:
            errors.append("raw index freeze digest")
        if index.get("source_manifest_sha256") != hashlib.sha256(manifest_path.read_bytes()).hexdigest():
            errors.append("raw index source-manifest digest")
        if set(index.get("cases", {})) != {case_id for case_id, _ in SCHEDULE}:
            errors.append("raw index case coverage")
        expected_index_schedule = [{"case_id": case_id, "arm": arm, "block": i // 3 + 1}
                                   for i, (case_id, arm) in enumerate(SCHEDULE)]
        if index.get("schedule") != expected_index_schedule:
            errors.append("raw index schedule")
        if index.get("case_errors"):
            errors.append("raw index contains case errors")
    for (case_id, arm) in SCHEDULE:
        path = root / case_id / "probe" / "record.json"
        if not path.is_file():  # unit-test fixture path; formal runner uses probe/record.json
            path = root / case_id / "record.json"
        if not path.is_file():
            errors.append(f"{case_id}: missing record")
            continue
        raw = path.read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        try:
            record = json.loads(raw)
        except (ValueError, UnicodeDecodeError) as exc:
            errors.append(f"{case_id}: invalid JSON: {exc}")
            continue
        for error in audit_record(case_id, arm, record):
            errors.append(f"{case_id}: {error}")
        supervisor_path = root / case_id / "supervisor.json"
        if supervisor_path.is_file():
            supervisor = json.loads(supervisor_path.read_text())
            if supervisor.get("study_id") != "caps-text-query-xtest-a02-20261008":
                errors.append(f"{case_id}: supervisor study identity")
            if not success_exit(supervisor.get("probe_exit")):
                errors.append(f"{case_id}: public runner exit")
            if not success_exit(supervisor.get("xvfb_exit")):
                errors.append(f"{case_id}: Xvfb exit")
            if supervisor.get("record_display_server_pid") != record.get("display_server", {}).get("pid"):
                errors.append(f"{case_id}: Xvfb process identity mismatch")
            if supervisor.get("case_id") != case_id or supervisor.get("arm") != arm:
                errors.append(f"{case_id}: supervisor case identity")
            if supervisor.get("errors"):
                errors.append(f"{case_id}: supervisor errors")
            if (not private_network_boundary(supervisor.get("network_boundary")) or
                    json.dumps(supervisor.get("network_boundary"), sort_keys=True) !=
                    json.dumps(record.get("network_boundary"), sort_keys=True)):
                errors.append(f"{case_id}: supervisor network boundary mismatch")
            xvfb = supervisor.get("xvfb", {})
            if xvfb.get("socket_removed") is not True or xvfb.get("lock_removed") is not True:
                errors.append(f"{case_id}: Xvfb cleanup")
            xvfb_stderr = xvfb.get("stderr", "")
            xvfb_raw = xvfb_stderr.encode() if type(xvfb_stderr) is str else b""
            if (type(xvfb_stderr) is not str or
                    xvfb_stderr_blocks(xvfb_raw) is None or
                    type(xvfb.get("stderr_blocks")) is not int or
                    xvfb.get("stderr_blocks") != xvfb_stderr_blocks(xvfb_raw)):
                errors.append(f"{case_id}: unexpected Xvfb stderr")
            probe_stderr = root / case_id / "probe.stderr"
            if not probe_stderr.is_file() or probe_stderr.read_text(errors="replace"):
                errors.append(f"{case_id}: probe stderr")
            if index:
                indexed = index.get("cases", {}).get(case_id, {})
                if (not success_exit(indexed.get("probe_exit")) or
                        not success_exit(indexed.get("xvfb_exit"))):
                    errors.append(f"{case_id}: raw index process exit types")
                if indexed.get("record_sha256") != digest:
                    errors.append(f"{case_id}: raw index record hash")
                if indexed.get("supervisor_sha256") != hashlib.sha256(supervisor_path.read_bytes()).hexdigest():
                    errors.append(f"{case_id}: raw index supervisor hash")
                if indexed.get("probe_exit") != supervisor.get("probe_exit") or indexed.get("xvfb_exit") != supervisor.get("xvfb_exit"):
                    errors.append(f"{case_id}: raw index process exits")
        else:
            errors.append(f"{case_id}: missing supervisor receipt")
        server_pid = record.get("display_server", {}).get("pid")
        if server_pid in server_pids:
            errors.append(f"{case_id}: Xvfb PID reused across fresh cases")
        server_pids.add(server_pid)
        snapshot_ids.add(record.get("repo_head"))
        freeze_ids.add(record.get("freeze_sha256"))
        backend = record.get("runtime_imports", {}).get("runtime.backends.x11_v1.backend", {})
        seen_hashes.setdefault(arm, []).append(backend.get("sha256"))
        modules = {name: data for name, data in record.get("runtime_imports", {}).items()
                   if name != "runtime.backends.x11_v1.backend"}
        if common_modules is None:
            common_modules = modules
        elif modules != common_modules:
            errors.append(f"{case_id}: non-backend runtime source closure differs")
        expected_arm = expected_imports.get("current" if arm == "current" else "guard", {})
        if record.get("runtime_imports") != expected_arm:
            errors.append(f"{case_id}: imported runtime closure differs from frozen source manifest")
        if arm.startswith("guard-"):
            if record.get("predecessor_patch_sha256") != "86913be26400e2ac74b051df4bc9505a97fff60fc5dc652cab04caa4b4af9d65":
                errors.append(f"{case_id}: predecessor patch identity")
            if record.get("current_main_candidate_patch_sha256") != FROZEN_PLAN["source_base"]["current_main_candidate_patch_sha256"]:
                errors.append(f"{case_id}: current-main candidate patch identity")
            if record.get("barrier_patch_sha256") != FROZEN_PLAN["source_base"]["fixture_instrumentation_sha256"]:
                errors.append(f"{case_id}: barrier patch identity")
        rows.append({"case_id": case_id, "arm": arm, "record_sha256": digest,
                     "entry": record.get("app_after", {}).get("value"),
                     "dispatch": record.get("response", {}).get("result", {}).get("status"),
                     "main_backend_sha256": record.get("main_backend_sha256"),
                     "executed_backend_sha256": backend.get("sha256")})
    if len(rows) == len(SCHEDULE):
        if len(snapshot_ids) != 1 or None in snapshot_ids:
            errors.append("study source snapshot differs across cases")
        if len(freeze_ids) != 1 or None in freeze_ids:
            errors.append("freeze document differs across cases")
        if index.get("source_freeze_commit") not in snapshot_ids:
            errors.append("raw index source commit differs from executed source snapshot")
        require_map = {name for _, name in SCHEDULE}
        if set(seen_hashes) != require_map:
            errors.append("arm coverage")
        if seen_hashes.get("current") != ["c4bd1c2ccda7db43a4a62efc866547f21e2d11c0d795834f1f8e1d6b32f63126"] * 3:
            errors.append("current executed backend identity")
        if (not seen_hashes.get("guard-stable") or
                len(set(seen_hashes["guard-stable"] + seen_hashes.get("guard-interposed", []))) != 1):
            errors.append("candidate backend identity differs across guard arms")
    return errors, {"schedule": SCHEDULE, "rows": rows, "status": "PASS" if not errors else "FAIL", "errors": errors}


def mutation_controls(root: Path) -> dict:
    from copy import deepcopy
    record_path = root / "C01" / "probe" / "record.json"
    if not record_path.is_file():
        record_path = root / "C01" / "record.json"
    original = json.loads(record_path.read_text())
    mutations = {
        "wrong_arm": lambda r: r.update(arm="guard-stable"),
        "wrong_value": lambda r: r["app_after"].update(value="wrong"),
        "dispatch_not_complete": lambda r: r["response"]["result"].update(status="failed"),
        "wrong_lock_initial": lambda r: r["before"].update(lockmask=1),
        "nonneutral_keymap": lambda r: r["after"].update(keymap=[1] + [0] * 31),
        "app_nonzero_exit": lambda r: r["app"].update(exit=1),
        "app_stderr": lambda r: r.update(app_stderr="injected"),
        "app_error": lambda r: r.update(errors=["injected"]),
        "wrong_study": lambda r: r.update(study_id="other"),
        "wrong_freeze": lambda r: r.update(freeze_sha256="wrong"),
        "missing_backend_source": lambda r: r["runtime_imports"].pop("runtime.backends.x11_v1.backend"),
        "boolean_lockmask_and_keymap_integer_fields": lambda r: (
            r["before"].update(lockmask=False), r["before"]["keymap"].__setitem__(0, False)),
        "boolean_completed_operation_index": lambda r: r["response"]["result"]["execution"][
            "completed_ops"].__setitem__(0, False),
        "unexpected_entry_event_type": lambda r: r["entry_events"].insert(
            2, {"event": "MapNotify", "ns": r["entry_events"][1]["ns"]}),
        "wrong_runner_source_identity": lambda r: r.update(runner_sha256="unrecognized-runner"),
        "boolean_network_namespace_inode": lambda r: r["network_boundary"].update(
            namespace_inode=True),
        "malformed_record_errors_and_stderr": lambda r: (
            r.update(errors=None, app_stderr=[])),
        "string_xvfb_argv": lambda r: r["display_server"].update(
            argv="Xvfb -nolisten tcp"),
    }
    def move_value_and_exit_before_input(record: dict) -> None:
        terminal = [e for e in record["entry_events"] if e.get("event") in ("value", "exit")]
        record["entry_events"] = terminal + [
            e for e in record["entry_events"] if e.get("event") not in ("value", "exit")
        ]
    def move_release_before_press(record: dict) -> None:
        events = record["entry_events"]
        press_index = next(i for i, event in enumerate(events)
                           if event.get("event") == "KeyPress" and event.get("char"))
        press = events[press_index]
        release_index = next(i for i, event in enumerate(events)
                             if event.get("event") == "KeyRelease" and
                             event.get("keycode") == press.get("keycode"))
        release = events[release_index]
        release["ns"] = press["ns"]
        press["ns"] += 1
        events.pop(release_index)
        events.insert(press_index, release)
    def move_final_value_before_character_press(record: dict) -> None:
        events = record["entry_events"]
        value_index = next(i for i, event in enumerate(events)
                           if event.get("event") == "value" and
                           event.get("value") == EXPECTED[record["arm"]][0])
        press_index = next(i for i, event in enumerate(events)
                           if event.get("event") == "KeyPress" and event.get("char") ==
                           EXPECTED[record["arm"]][0][-1])
        value = events.pop(value_index)
        press_index -= value_index < press_index
        value["ns"] = events[press_index]["ns"] - 1
        events.insert(press_index, value)
    mutations["value_and_exit_before_input"] = move_value_and_exit_before_input
    mutations["release_before_press"] = move_release_before_press
    mutations["final_value_before_character_press"] = move_final_value_before_character_press
    outcomes = {}
    for name, mutate in mutations.items():
        sample = deepcopy(original)
        mutate(sample)
        outcomes[name] = audit_record("C01", "current", sample)
    record_path = root / "I01" / "probe" / "record.json"
    if not record_path.is_file():
        record_path = root / "I01" / "record.json"
    interposed = json.loads(record_path.read_text())
    timing = deepcopy(interposed)
    actor_doc = json.loads(timing["actor"]["stdout"])
    actor_doc["ack_ns"] = max(e["ns"] for e in timing["entry_events"] if e["event"] == "KeyPress") + 1
    timing["actor"]["stdout"] = json.dumps(actor_doc)
    outcomes["ack_after_keypress"] = audit_record("I01", "guard-interposed", timing)
    actor_state = deepcopy(interposed)
    actor_doc = json.loads(actor_state["actor"]["stdout"])
    actor_doc["post_lock"] = 0
    actor_state["actor"]["stdout"] = json.dumps(actor_doc)
    outcomes["mutation_not_observed"] = audit_record("I01", "guard-interposed", actor_state)
    boolean_actor_state = deepcopy(interposed)
    actor_doc = json.loads(boolean_actor_state["actor"]["stdout"])
    actor_doc["accepted"] = True
    boolean_actor_state["actor"]["stdout"] = json.dumps(actor_doc)
    outcomes["boolean_actor_state"] = audit_record(
        "I01", "guard-interposed", boolean_actor_state)
    boolean_actor_timestamp = deepcopy(interposed)
    actor_doc = json.loads(boolean_actor_timestamp["actor"]["stdout"])
    actor_doc["ack_ns"] = True
    boolean_actor_timestamp["actor"]["stdout"] = json.dumps(actor_doc)
    outcomes["boolean_actor_ack_timestamp"] = audit_record(
        "I01", "guard-interposed", boolean_actor_timestamp)
    actor_exit = deepcopy(interposed)
    actor_exit["actor"]["exit"] = 1
    outcomes["actor_nonzero_exit"] = audit_record("I01", "guard-interposed", actor_exit)
    boolean_actor_exit = deepcopy(interposed)
    boolean_actor_exit["actor"]["exit"] = False
    outcomes["boolean_actor_exit"] = audit_record(
        "I01", "guard-interposed", boolean_actor_exit)
    actor_stderr = deepcopy(interposed)
    actor_stderr["actor"]["stderr"] = "injected"
    outcomes["actor_stderr"] = audit_record("I01", "guard-interposed", actor_stderr)
    candidate_patch = deepcopy(interposed)
    candidate_patch["current_main_candidate_patch_sha256"] = "wrong"
    outcomes["wrong_current_main_candidate_patch"] = audit_record(
        "I01", "guard-interposed", candidate_patch)

    def audit_root_mutation(name: str, mutate) -> None:
        with tempfile.TemporaryDirectory(prefix="caps-formal-mutation-") as tmp:
            copied = Path(tmp) / "run"
            shutil.copytree(root, copied)
            mutate(copied)
            errors, _ = audit(copied)
            outcomes[name] = errors

    def false_preflight_exit(copied: Path) -> None:
        path = copied / "PREFLIGHT.json"
        doc = json.loads(path.read_text())
        doc["xvfb"]["exit"] = False
        path.write_text(json.dumps(doc))

    def false_supervisor_exit(field: str):
        def mutate(copied: Path) -> None:
            supervisor_path = copied / "C01" / "supervisor.json"
            supervisor = json.loads(supervisor_path.read_text())
            supervisor[field] = False
            supervisor_path.write_text(json.dumps(supervisor))
            index_path = copied / "RAW_INDEX.json"
            index = json.loads(index_path.read_text())
            index["cases"]["C01"][field] = False
            index["cases"]["C01"]["supervisor_sha256"] = hashlib.sha256(
                supervisor_path.read_bytes()).hexdigest()
            index_path.write_text(json.dumps(index))
        return mutate

    def false_index_exit(copied: Path) -> None:
        index_path = copied / "RAW_INDEX.json"
        index = json.loads(index_path.read_text())
        index["cases"]["C01"]["probe_exit"] = False
        index_path.write_text(json.dumps(index))

    audit_root_mutation("boolean_preflight_xvfb_exit", false_preflight_exit)
    audit_root_mutation("boolean_supervisor_probe_exit", false_supervisor_exit("probe_exit"))
    audit_root_mutation("boolean_supervisor_xvfb_exit", false_supervisor_exit("xvfb_exit"))
    audit_root_mutation("boolean_index_probe_exit", false_index_exit)
    escaped = [name for name, errors in outcomes.items() if not errors]
    if escaped:
        raise AssertionError(f"effective mutation controls escaped: {escaped}")
    return {"controls": {name: {"rejected": True, "errors": errors}
                         for name, errors in outcomes.items()}, "status": "PASS"}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--mutation-controls", action="store_true")
    args = parser.parse_args()
    errors, result = audit(args.root)
    if not errors and args.mutation_controls:
        try:
            result["mutation_controls"] = mutation_controls(args.root)
        except Exception as exc:
            errors.append(f"mutation controls: {type(exc).__name__}: {exc}")
            result["errors"] = errors
            result["status"] = "FAIL"
    if args.out:
        args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
