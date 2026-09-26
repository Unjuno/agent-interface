"""One-shot GTK/X11 allocation for Issue #3166, additive rung 2."""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path("/evidence")
REPO = Path("/repo")
DISPLAY = ":151"
SOURCE_COMMIT = "2c5be06f9563deb3e5e739df6e7f154d145a8687"
STUDY = REPO / "research/integration/issue_3166_gate_integrity_rung2_v1"
FIXTURE = REPO / "research/integration/golden_v3_second_domain_2246_v1/gtk_fixture_app.py"
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(STUDY))
from policy import POLICIES, SCENARIOS, admits, context, gate_is_current  # noqa: E402
from runtime.cli_v1.golden_v3 import dispatch_golden_v3  # noqa: E402

SOURCE_FILES = (
    "runtime/cli_v1/golden_v3.py",
    "runtime/cli_v1/api.py",
    "runtime/selector_v1/__init__.py",
    "runtime/selector_v1/selector.py",
    "runtime/core_v1/__init__.py",
    "runtime/core_v1/contract.py",
    "runtime/core_v1/platform_probe.py",
    "runtime/backends/x11_v1/__init__.py",
    "runtime/backends/x11_v1/backend.py",
    "runtime/backends/x11_v1/session.py",
    "research/integration/golden_v3_second_domain_2246_v1/gtk_fixture_app.py",
)


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


def read_events(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def fixture_start(case_dir: Path, mode: str, env: dict) -> tuple[subprocess.Popen, Path, Path, Path, dict]:
    case_dir.mkdir(parents=True, exist_ok=False)
    meta, effect, events = case_dir / "meta.json", case_dir / "effect.json", case_dir / "events.jsonl"
    proc = subprocess.Popen(
        ["/usr/bin/python3", "-B", str(FIXTURE), "--mode", mode,
         "--meta", str(meta), "--effect", str(effect), "--events", str(events)],
        env=env, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True,
    )
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        if proc.poll() is not None:
            raise RuntimeError(f"GTK fixture exited before metadata: {proc.stderr.read()[-2000:]}")
        if meta.exists():
            info = read_json(meta)
            xid = str(info["window_id"])
            alive = subprocess.run(
                ["xwininfo", "-display", DISPLAY, "-id", xid],
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=3,
            )
            if alive.returncode != 0:
                raise RuntimeError(f"GTK target not live after prepare: {alive.stdout}")
            return proc, meta, effect, events, info
        time.sleep(0.02)
    proc.terminate()
    proc.wait(timeout=3)
    raise TimeoutError("GTK fixture metadata timeout")


def fixture_close(proc: subprocess.Popen, xid: str) -> dict:
    error = None
    try:
        subprocess.run(["xdotool", "windowclose", xid], env=os.environ.copy(),
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                       timeout=2, check=False)
        proc.wait(timeout=3)
    except Exception as exc:  # retained as cleanup evidence
        error = repr(exc)
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=2)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=2)
    stderr = proc.stderr.read()[-4000:] if proc.stderr else ""
    return {"exit_code": proc.returncode, "error": error, "stderr_tail": stderr}


def build_program(program_id: str) -> dict:
    return {
        "schema": "agent-interface/program-v1",
        "program_id": program_id,
        "source": {"observation_seq": 1, "binding_revision": 1},
        "authority": {"lease_id": program_id,
                      "expires_at_ns": time.monotonic_ns() + 30_000_000_000},
        "terminal": {"release_all_required": True},
        "ops": [
            {"op": "focus", "target": "fixture"},
            {"op": "key_chord", "keys": ["CTRL", "s"]},
            {"op": "release_all"},
        ],
    }


def dispatch_one(program: dict, xid: str) -> dict:
    return dispatch_golden_v3(
        program, {"fixture": int(xid)}, current_observation_seq=1,
        current_binding_revision=1, display_name=DISPLAY,
    )


def runtime_fields(result: dict | None) -> dict:
    if not result:
        return {"native_status": None, "emissions": 0, "release_verified": False}
    raw = result.get("raw_dispatch", {})
    nested = raw.get("result", {}) if isinstance(raw, dict) else {}
    execution = nested.get("execution", {}) if isinstance(nested, dict) else {}
    releases = execution.get("releases", [])
    return {
        "native_status": result.get("native_status"),
        "emissions": execution.get("program_emissions", 0),
        "release_verified": bool(releases) and all(
            type(item) is dict and item.get("verified") is True
            and item.get("keys_down") == [] and item.get("buttons_down") == []
            for item in releases
        ),
    }


def matrix_row(scenario: str, policy: str, rows_path: Path, env: dict) -> dict:
    case_dir = ROOT / "cases" / f"{scenario}__{policy.lower()}"
    proc, meta_path, effect_path, events_path, meta = fixture_start(case_dir, "useful", env)
    started = time.monotonic_ns()
    prepared, current, gate = context(scenario, started)
    xid = str(meta["window_id"])
    prepared["target_id"] = xid
    gate["target_id"] = xid
    gate_valid = gate_is_current(prepared, gate, time.monotonic_ns())
    admitted = admits(policy, prepared, current, gate, time.monotonic_ns())
    row = {
        "record_type": "matrix",
        "case": scenario,
        "policy": policy,
        "prepared": prepared,
        "current": current,
        "gate_receipt": gate,
        "gate_valid_recomputed_by_runner": gate_valid,
        "target_live_before_admission": True,
        "window_id": xid,
        "admitted": admitted,
        "runtime_called": False,
        "started_ns": started,
    }
    result = None
    try:
        if admitted:
            row["runtime_called"] = True
            result = dispatch_one(build_program(f"rung2-{scenario}-{policy.lower()}"), xid)
            time.sleep(0.12)
        row["dispatch"] = result
        row.update(runtime_fields(result))
        row["events"] = read_events(events_path)
        row["effect"] = read_json(effect_path)
        row["postcondition_exact"] = row["effect"] == {"saved": True, "text": ""}
        row["disposition"] = (
            "POLICY_REFUSED_BEFORE_RUNTIME" if not admitted else
            "EFFECT_VERIFIED_SCOPED" if row["native_status"] == "completed"
            and row["release_verified"] and row["postcondition_exact"] else
            "HOLD_OR_FAIL_RUNTIME_POSTCONDITION"
        )
        row["ended_ns"] = time.monotonic_ns()
    finally:
        row["fixture_cleanup"] = fixture_close(proc, xid)
    row["events"] = read_events(events_path)
    row["effect"] = read_json(effect_path)
    with rows_path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")
    return row


def duplicate_probe(rows_path: Path, env: dict) -> dict:
    case_dir = ROOT / "duplicate_probe"
    proc, _meta, effect_path, events_path, meta = fixture_start(case_dir, "useful", env)
    xid = str(meta["window_id"])
    started = time.monotonic_ns()
    prepared, current, gate = context("valid", started)
    prepared["target_id"] = gate["target_id"] = xid
    pid = "rung2-duplicate-same-program-id-intent-epoch"
    program = build_program(pid)
    attempts = []
    try:
        for attempt in (1, 2):
            admitted = admits("TWO_TIER_FRESH_GATE", prepared, current, gate, time.monotonic_ns())
            result = dispatch_one(program, xid) if admitted else None
            time.sleep(0.12)
            attempts.append({"attempt": attempt, "admitted": admitted,
                             "intent_id": prepared["intent_id"],
                             "commit_epoch": prepared["commit_epoch"],
                             "receipt": gate, "program": program,
                             "dispatch": result, "events": read_events(events_path),
                             "effect": read_json(effect_path), **runtime_fields(result)})
        row = {"record_type": "duplicate_probe", "prepared": prepared,
               "current": current, "attempts": attempts,
               "events": read_events(events_path), "effect": read_json(effect_path),
               "fixture_mode": "useful", "window_id": xid,
               "fixture_cleanup": None}
    finally:
        row["fixture_cleanup"] = fixture_close(proc, xid)
    row["events"] = read_events(events_path)
    row["effect"] = read_json(effect_path)
    saves = sum(event.get("type") == "save" for event in row["events"])
    row["disposition"] = "DUPLICATE_COMMIT_REFUSED_SCOPED" if saves <= 1 else "FAIL_DUPLICATE_COMMIT_REPLAY_ACCEPTED"
    with rows_path.open("a", encoding="utf-8") as stream:
        for attempt in attempts:
            attempt_row = {
                "record_type": "duplicate_attempt",
                "probe_id": "duplicate-same-program-intent-epoch",
                "prepared": prepared,
                "current": current,
                "attempt": attempt["attempt"],
                "attempt_count": 2,
                "intent_id": attempt["intent_id"],
                "commit_epoch": attempt["commit_epoch"],
                "receipt": attempt["receipt"],
                "program": attempt["program"],
                "admitted": attempt["admitted"],
                "dispatch": attempt["dispatch"],
                "native_status": attempt["native_status"],
                "emissions": attempt["emissions"],
                "release_verified": attempt["release_verified"],
                "effect": attempt["effect"],
                "events": attempt["events"],
                "window_id": xid,
                "probe_disposition": row["disposition"],
                "fixture_cleanup": row["fixture_cleanup"],
            }
            stream.write(json.dumps(attempt_row, sort_keys=True, separators=(",", ":")) + "\n")
    return row


def contradictory_probe(rows_path: Path, env: dict) -> dict:
    case_dir = ROOT / "contradictory_control"
    proc, _meta, effect_path, events_path, meta = fixture_start(case_dir, "partial", env)
    xid = str(meta["window_id"])
    started = time.monotonic_ns()
    prepared, current, gate = context("valid", started)
    prepared["target_id"] = gate["target_id"] = xid
    admitted = admits("TWO_TIER_FRESH_GATE", prepared, current, gate, time.monotonic_ns())
    result = None
    row = {"record_type": "contradictory_control", "prepared": prepared,
           "current": current, "gate_receipt": gate, "admitted": admitted,
           "fixture_mode": "partial", "window_id": xid, "started_ns": started}
    try:
        if admitted:
            result = dispatch_one(build_program("rung2-partial-collateral-control"), xid)
            time.sleep(0.12)
        row["dispatch"] = result
        row.update(runtime_fields(result))
        row["events"] = read_events(events_path)
        row["effect"] = read_json(effect_path)
        row["postcondition_exact"] = row["effect"] == {"saved": True, "text": ""}
        row["disposition"] = (
            "HOLD_POSTCONDITION_CONTRADICTORY"
            if row["effect"] == {"saved": True, "text": "", "collateral": "fixture-label"}
            else "HOLD_OR_UNEXPECTED_PARTIAL_EFFECT"
        )
    finally:
        row["fixture_cleanup"] = fixture_close(proc, xid)
    row["events"] = read_events(events_path)
    row["effect"] = read_json(effect_path)
    row["ended_ns"] = time.monotonic_ns()
    with rows_path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")
    return row


def main() -> int:
    ROOT.mkdir(parents=True, exist_ok=True)
    rows_path = ROOT / "raw.jsonl"
    if rows_path.exists() or any(ROOT.iterdir()):
        raise RuntimeError("formal evidence directory must be fresh and empty")
    if os.environ.get("FROZEN_SOURCE_COMMIT") != SOURCE_COMMIT:
        raise RuntimeError("source commit environment pin mismatch")
    if not FIXTURE.is_file():
        raise RuntimeError("frozen fixture missing")
    source_hashes = {name: digest(REPO / name) for name in SOURCE_FILES}
    (ROOT / "source_hashes.json").write_text(
        json.dumps(source_hashes, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    env = os.environ.copy()
    env["DISPLAY"] = DISPLAY
    xvfb = subprocess.Popen(
        ["Xvfb", DISPLAY, "-screen", "0", "1024x768x24", "-nolisten", "tcp", "-ac"],
        env=env, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True,
    )
    try:
        time.sleep(0.35)
        if xvfb.poll() is not None:
            raise RuntimeError(f"Xvfb exited: {xvfb.stderr.read()[-2000:]}")
        matrix = []
        for scenario in SCENARIOS:
            for policy in POLICIES:
                matrix.append(matrix_row(scenario, policy, rows_path, env))
        duplicate = duplicate_probe(rows_path, env)
        contradictory = contradictory_probe(rows_path, env)
        summary = {
            "allocation": "issue3166-gate-integrity-rung2-20260927-01",
            "source_commit": SOURCE_COMMIT,
            "image_id": os.environ.get("FROZEN_IMAGE_ID"),
            "matrix_rows": len(matrix),
            "duplicate_records": len(duplicate["attempts"]),
            "contradictory_controls": 1,
            "raw_records": len(matrix) + len(duplicate["attempts"]) + 1,
            "matrix_admitted": sum(row["admitted"] for row in matrix),
            "two_tier_invalid_admissions": sum(
                row["admitted"] for row in matrix
                if row["policy"] == "TWO_TIER_FRESH_GATE" and row["case"] != "valid"),
            "duplicate_disposition": duplicate["disposition"],
            "contradictory_disposition": contradictory["disposition"],
            "formal_run_count": 1,
        }
        (ROOT / "summary.json").write_text(
            json.dumps(summary, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(summary, sort_keys=True))
        return 0
    finally:
        xvfb.terminate()
        try:
            xvfb.wait(timeout=3)
        except subprocess.TimeoutExpired:
            xvfb.kill()
            xvfb.wait(timeout=3)


if __name__ == "__main__":
    raise SystemExit(main())
