"""Raw-record-only audit for frozen #8328 formal cases and corruption controls."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys


SCHEDULE = [("C01", "current"), ("G01", "guard-stable"), ("I01", "guard-interposed"),
            ("C02", "current"), ("G02", "guard-stable"), ("I02", "guard-interposed"),
            ("C03", "current"), ("G03", "guard-stable"), ("I03", "guard-interposed")]
EXPECTED = {"current": ("aB2", 0), "guard-stable": ("aB2", 0),
            "guard-interposed": ("Ab2", 1)}
FROZEN_PLAN_SHA256 = "892fec8ad9d2c92b07c6613305d5053aee3bfc5d4b42f8896e0bae9ce340f130"
FROZEN_PLAN = json.loads((Path(__file__).resolve().parent / "FREEZE.json").read_text())
EXPECTED_XVFB_STDERR_SHA256 = FROZEN_PLAN["environment"]["expected_xvfb_stderr_sha256"]


def audit_record(case_id: str, arm: str, record: dict) -> list[str]:
    errors: list[str] = []
    expected_value, expected_lock = EXPECTED[arm]
    def require(condition: bool, message: str) -> None:
        if not condition:
            errors.append(message)

    require(record.get("kind") == "formal-public-dispatch-case", "kind")
    require(record.get("study_id") == "caps-text-query-xtest-a01-20261007", "study id")
    require(record.get("case_id") == case_id, "case id")
    require(record.get("arm") == arm, "arm")
    require(record.get("main_backend_sha256") == "6ba5ea5d4e8fc797fc26a19879cffcfd00926606f53b0ef76fbff5f6b5f779db", "main backend identity")
    require(record.get("before", {}).get("lockmask") == 0, "initial LockMask")
    require(record.get("before", {}).get("keymap") == [0] * 32, "initial keymap neutrality")
    require(record.get("after", {}).get("lockmask") == expected_lock, "final LockMask")
    require(record.get("after", {}).get("keymap") == [0] * 32, "final keymap release")
    require(record.get("app_after", {}).get("value") == expected_value, "Entry value")
    require(record.get("response", {}).get("result", {}).get("status") == "completed", "dispatch status")
    execution = record.get("response", {}).get("result", {}).get("execution", {})
    require(execution.get("completed_ops") == [0, 1, 2], "completed operation sequence")
    releases = execution.get("releases", [])
    require(bool(releases) and releases[-1].get("verified") is True and
            releases[-1].get("keys_down") == [] and releases[-1].get("buttons_down") == [],
            "verified neutral release receipt")
    require(record.get("app", {}).get("exit") == 0, "app exit")
    require(not record.get("errors"), "record errors")
    require(record.get("app", {}).get("ready", {}).get("window") is not None, "fixture window identity")
    server = record.get("display_server", {})
    require(server.get("display") == record.get("display"), "Xvfb display identity")
    require(isinstance(server.get("pid"), int) and server["pid"] > 0, "Xvfb PID")
    require(any("Xvfb" in arg for arg in server.get("argv", [])) and
            "-nolisten" in server.get("argv", []) and "tcp" in server.get("argv", []), "Xvfb argv/isolation")
    events = record.get("entry_events", [])
    presses = [e for e in events if e.get("event") == "KeyPress"]
    key_releases = [e for e in events if e.get("event") == "KeyRelease"]
    require([e.get("char") for e in presses] == list(expected_value), "exact Entry KeyPress sequence")
    require(len(key_releases) >= len(presses) == 3, "Entry KeyRelease count")
    require(any(e.get("event") == "value" and e.get("value") == expected_value for e in events),
            "Entry value-change journal")
    require(any(e.get("event") == "exit" and e.get("value") == expected_value for e in events),
            "fixture exit value")
    program = record.get("program", {})
    require(program.get("ops") == [{"op": "focus", "target": "entry"},
                                     {"op": "text", "text": "aB2"},
                                     {"op": "release_all"}], "exact public program")
    require(record.get("program_id") == f"formal-{case_id}-{arm}", "program id")
    boundary = record.get("network_boundary", {})
    require(boundary.get("namespace_inode") != boundary.get("pid1_namespace_inode"),
            "private network namespace")
    require(not boundary.get("ipv4_non_loopback_routes") and
            not boundary.get("ipv6_non_loopback_routes") and
            not boundary.get("up_non_loopback_interfaces"), "network disabled for case")
    if arm == "guard-interposed":
        actor = record.get("actor", {})
        try:
            actor_doc = json.loads(actor.get("stdout", ""))
        except (ValueError, TypeError):
            actor_doc = {}
        presses = [e for e in events if e.get("event") == "KeyPress"]
        require(actor.get("exit") == 0, "actor exit")
        require(not actor.get("stderr"), "actor stderr")
        require(isinstance(actor.get("pid"), int) and actor["pid"] not in
                (record.get("driver_pid"), record.get("app", {}).get("pid")), "separate actor process")
        require(actor_doc.get("candidate_sample") == 0 and actor_doc.get("pre_lock") == 0, "actor sampled/pre-lock state")
        require(actor_doc.get("accepted") == 1 and actor_doc.get("post_lock") == 1, "actor mutation state")
        require(bool(presses) and actor_doc.get("ack_ns", 2**63) < presses[0].get("ns", -1), "ACK before first KeyPress")
    else:
        require("actor" not in record, "unexpected actor")
    require(not (record.get("app", {}).get("stderr") or record.get("app_stderr")), "app stderr")
    imports = record.get("runtime_imports", {})
    require("runtime.cli_v1.api" in imports, "public dispatch source identity")
    require("runtime.backends.x11_v1.backend" in imports, "backend source identity")
    require(bool(imports.get("runtime.cli_v1.api", {}).get("sha256")), "dispatch source digest")
    require(bool(imports.get("runtime.backends.x11_v1.backend", {}).get("sha256")), "backend source digest")
    require(bool(record.get("runner_sha256")), "runner source digest")
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
        if preflight.get("xvfb", {}).get("exit") != 0 or not preflight.get("xtest_present"):
            errors.append("preflight Xvfb/XTEST")
        if preflight.get("xvfb", {}).get("stderr_sha256") != EXPECTED_XVFB_STDERR_SHA256:
            errors.append("preflight Xvfb stderr identity")
        boundary = preflight.get("network_boundary", {})
        if (boundary.get("namespace_inode") == boundary.get("pid1_namespace_inode") or
                boundary.get("ipv4_non_loopback_routes") or boundary.get("ipv6_non_loopback_routes") or
                boundary.get("up_non_loopback_interfaces")):
            errors.append("preflight network isolation")
    except Exception as exc:
        errors.append(f"preflight unavailable: {type(exc).__name__}: {exc}")
    if index:
        if index.get("schema") != "caps-text-query-xtest-formal-index-v1":
            errors.append("raw index schema")
        if index.get("study_id") != "caps-text-query-xtest-a01-20261007":
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
            if supervisor.get("probe_exit") != 0:
                errors.append(f"{case_id}: public runner exit")
            if supervisor.get("xvfb_exit") != 0:
                errors.append(f"{case_id}: Xvfb exit")
            if supervisor.get("record_display_server_pid") != record.get("display_server", {}).get("pid"):
                errors.append(f"{case_id}: Xvfb process identity mismatch")
            if supervisor.get("case_id") != case_id or supervisor.get("arm") != arm:
                errors.append(f"{case_id}: supervisor case identity")
            if supervisor.get("errors"):
                errors.append(f"{case_id}: supervisor errors")
            if supervisor.get("network_boundary") != record.get("network_boundary"):
                errors.append(f"{case_id}: supervisor network boundary mismatch")
            xvfb = supervisor.get("xvfb", {})
            if not xvfb.get("socket_removed") or not xvfb.get("lock_removed"):
                errors.append(f"{case_id}: Xvfb cleanup")
            if hashlib.sha256(xvfb.get("stderr", "").encode()).hexdigest() != EXPECTED_XVFB_STDERR_SHA256:
                errors.append(f"{case_id}: unexpected Xvfb stderr")
            probe_stderr = root / case_id / "probe.stderr"
            if not probe_stderr.is_file() or probe_stderr.read_text(errors="replace"):
                errors.append(f"{case_id}: probe stderr")
            if index:
                indexed = index.get("cases", {}).get(case_id, {})
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
            if record.get("barrier_patch_sha256") != "3dee9d60273a5100612f17514e0d06f3cb5b279e8c4c8eae01aa7fa3d89f370e":
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
        if seen_hashes.get("current") != ["6ba5ea5d4e8fc797fc26a19879cffcfd00926606f53b0ef76fbff5f6b5f779db"] * 3:
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
    }
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
    actor_exit = deepcopy(interposed)
    actor_exit["actor"]["exit"] = 1
    outcomes["actor_nonzero_exit"] = audit_record("I01", "guard-interposed", actor_exit)
    actor_stderr = deepcopy(interposed)
    actor_stderr["actor"]["stderr"] = "injected"
    outcomes["actor_stderr"] = audit_record("I01", "guard-interposed", actor_stderr)
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
