"""One-shot GTK/X11 first-rung experiment for Issue #3166."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone

sys.path.insert(0, "/repo")
from Xlib import display as xdisplay
from runtime.cli_v1.golden_v3 import dispatch_golden_v3

ROOT = Path("/evidence")
REPO = Path("/repo")
FIXTURE = REPO / "research/integration/golden_v3_second_domain_2246_v1/gtk_fixture_app.py"
DISPLAY = ":155"
EXPECTED_SOURCE = {
    "runtime/cli_v1/golden_v3.py": "4325c6e5b662adaa36138dc2f895d31938541a8e030e59b096c60521bb424d5d",
    "runtime/cli_v1/api.py": "a04d1fa2819d9f7199210cc4ac602de020fdf849fa9e3edf0d44568c9a51ddcd",
    "runtime/selector_v1/__init__.py": "66bc2fcb2797b108cd739b1c000352932dbdd7a16c186c1104cd8d26d0645881",
    "runtime/selector_v1/selector.py": "7f3db522b2250fcd3d8960c87b1d87ad078bf1b2b565900b4210836f6b7ca764",
    "runtime/core_v1/__init__.py": "5284bc097858ceeb4793ffc0b88427c8dc693c893e43e1d244aa4be9fcfa7da0",
    "runtime/core_v1/contract.py": "f053f73ccdeb67175068bf4d663bd484d886beb83305ed679510292809afd536",
    "runtime/core_v1/platform_probe.py": "4b373544e163f88cb74f7a739fd2246ae975b26705d609f01280e9480a16582e",
    "runtime/backends/x11_v1/__init__.py": "50a6767fca7c7a81fc1a5e606de60b6660c4e8045ad0b66902d50c4a4493de6b",
    "runtime/backends/x11_v1/backend.py": "3429a422e61ecb8b1f1f278540d0696842d8197d7967803e01bc8d9453bcb4a8",
    "runtime/backends/x11_v1/session.py": "70ffb0167a70efcf629221c8236dd19ba9fbc2ff3ffc18454f13a0f656b86a93",
    "research/integration/golden_v3_second_domain_2246_v1/gtk_fixture_app.py": "a89740107f5b544cde8a0ab1ae9f1af1764498889f85c982d106301577685f4a",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def policy_admits(policy: str, context: dict) -> bool:
    dep = context["dependency_current"]
    gate = context["gate"]
    gate_true = gate["truth"] == "TRUE"
    gate_bound = gate["intent_match"] and gate["epoch_match"]
    gate_live = gate_true and gate["fresh"] and gate_bound
    if policy == "TWO_TIER_FRESH_GATE":
        return dep and gate_live
    if policy == "DEPENDENCY_ONLY":
        return dep
    if policy == "GATE_ONLY":
        return gate_live
    if policy == "CACHED_PREPARE_GATE":
        return dep and context["cached_prepare_gate_true"]
    raise ValueError(f"unknown policy {policy}")


def contexts():
    return [
        {"case": "live_true", "truth": "TRUE", "fresh": True, "intent_match": True, "epoch_match": True},
        {"case": "fresh_false", "truth": "FALSE", "fresh": True, "intent_match": True, "epoch_match": True},
        {"case": "fresh_unknown", "truth": "UNKNOWN", "fresh": True, "intent_match": True, "epoch_match": True},
        {"case": "stale_true", "truth": "TRUE", "fresh": False, "intent_match": True, "epoch_match": True},
        {"case": "intent_mismatch", "truth": "TRUE", "fresh": True, "intent_match": False, "epoch_match": True},
        {"case": "epoch_mismatch", "truth": "TRUE", "fresh": True, "intent_match": True, "epoch_match": False},
    ]


def read_events(path: Path):
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def start_fixture(case_dir: Path, mode: str, env: dict):
    meta = case_dir / "meta.json"
    effect = case_dir / "effect.json"
    events = case_dir / "events.jsonl"
    out = (case_dir / "fixture.stdout.log").open("wb")
    err = (case_dir / "fixture.stderr.log").open("wb")
    argv = ["/usr/bin/python3", str(FIXTURE), "--mode", mode, "--meta", str(meta),
            "--effect", str(effect), "--events", str(events)]
    proc = None
    try:
        proc = subprocess.Popen(argv, env=env, stdout=out, stderr=err, close_fds=True)
        deadline = time.monotonic() + 8
        while time.monotonic() < deadline and proc.poll() is None and not meta.exists():
            time.sleep(0.02)
        if proc.poll() is not None or not meta.exists():
            raise RuntimeError(f"STOP_FIXTURE_START case={case_dir.name} exit={proc.poll()}")
        return proc, json.loads(meta.read_text(encoding="utf-8")), effect, events
    except Exception:
        if proc is not None and proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=2)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=2)
        raise
    finally:
        out.close()
        err.close()


def close_fixture(proc, window_id: int):
    close_error = None
    try:
        client = xdisplay.Display(DISPLAY)
        client.create_resource_object("window", window_id).destroy()
        client.sync()
        client.close()
        proc.wait(timeout=3)
    except Exception as exc:
        close_error = repr(exc)
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=2)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=2)
    return {"exit_code": proc.returncode, "error": close_error}


def one_row(case_name: str, policy: str, gate: dict, mode: str, env: dict):
    case_dir = ROOT / "cases" / f"{case_name}__{policy.lower()}"
    case_dir.mkdir(parents=True, exist_ok=False)
    context = {"dependency_current": True, "gate": gate,
               "cached_prepare_gate_true": True, "intent": "intent-current", "epoch": 7}
    admitted = policy_admits(policy, context)
    app, meta, effect_path, events_path = start_fixture(case_dir, mode, env)
    row = {"case": case_name, "policy": policy, "context": context,
           "admitted": admitted, "runtime_called": False, "fixture_mode": mode,
           "window_id": meta["window_id"], "started_ns": time.monotonic_ns()}
    try:
        if admitted:
            row["runtime_called"] = True
            program_id = f"{case_name}-{policy.lower()}"
            program = {
                "schema": "agent-interface/program-v1", "program_id": program_id,
                "source": {"observation_seq": 1, "binding_revision": 1},
                "authority": {"lease_id": program_id,
                              "expires_at_ns": time.monotonic_ns() + 8_000_000_000},
                "terminal": {"release_all_required": True},
                "ops": [{"op": "focus", "target": "fixture"},
                        {"op": "key_chord", "keys": ["CTRL", "s"]},
                        {"op": "release_all"}],
            }
            result = dispatch_golden_v3(program, {"fixture": int(meta["window_id"])},
                                        current_observation_seq=1,
                                        current_binding_revision=1,
                                        display_name=DISPLAY)
            time.sleep(0.12)
            row["dispatch"] = result
        row["events"] = read_events(events_path)
        row["effect"] = (json.loads(effect_path.read_text(encoding="utf-8"))
                         if effect_path.exists() else None)
        raw_dispatch = row.get("dispatch", {}).get("raw_dispatch", {})
        nested = raw_dispatch.get("result", {})
        execution = nested.get("execution", {}) if isinstance(nested, dict) else {}
        row["native_status"] = row.get("dispatch", {}).get("native_status")
        row["emissions"] = execution.get("program_emissions", 0)
        releases = execution.get("releases", [])
        row["release_verified"] = bool(releases) and all(
            isinstance(item, dict) and item.get("verified") is True and
            item.get("keys_down") == [] and item.get("buttons_down") == [] for item in releases)
        row["postcondition"] = bool(row["effect"] and row["effect"].get("saved") is True)
        row["end_ns"] = time.monotonic_ns()
        if not admitted:
            row["disposition"] = "POLICY_REFUSED_BEFORE_RUNTIME"
        elif mode == "no_effect" and row["native_status"] == "completed" and not row["postcondition"]:
            row["disposition"] = "HOLD_POSTCONDITION_UNOBSERVED"
        elif row["native_status"] == "completed" and row["release_verified"] and row["postcondition"]:
            row["disposition"] = "EFFECT_VERIFIED_SCOPED"
        else:
            row["disposition"] = "STOP_OR_HOLD_RUNTIME_EVIDENCE"
    finally:
        row["fixture_cleanup"] = close_fixture(app, int(meta["window_id"]))
    row["events"] = read_events(events_path)
    row["event_count"] = len(row["events"])
    (case_dir / "row.json").write_text(json.dumps(row, sort_keys=True) + "\n", encoding="utf-8")
    return row


def main():
    if not ROOT.is_dir() or any(ROOT.iterdir()):
        raise SystemExit("STOP_EVIDENCE_PATH_NOT_EMPTY")
    actual = {name: sha256(REPO / name) for name in EXPECTED_SOURCE}
    if actual != EXPECTED_SOURCE:
        raise SystemExit(f"STOP_SOURCE_HASH_MISMATCH {actual}")
    if not shutil.which("Xvfb"):
        raise SystemExit("STOP_XVFB_MISSING")
    preflight = {"result": "PASS_PREFLIGHT", "utc": datetime.now(timezone.utc).isoformat(),
                 "source_sha256": actual, "fixture_sha256": actual[str(FIXTURE.relative_to(REPO))],
                 "display": DISPLAY, "policy_models": ["TWO_TIER_FRESH_GATE", "DEPENDENCY_ONLY",
                     "GATE_ONLY", "CACHED_PREPARE_GATE"], "formal_cases_before": 0}
    (ROOT / "preflight.json").write_text(json.dumps(preflight, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    xlog = (ROOT / "xvfb.log").open("wb")
    xvfb = subprocess.Popen(["Xvfb", DISPLAY, "-screen", "0", "1024x768x24",
                             "-nolisten", "tcp", "-ac"], stdout=xlog, stderr=xlog,
                            env={"PATH": "/usr/bin:/bin", "HOME": "/tmp"}, close_fds=True)
    rows, stop = [], None
    try:
        deadline = time.monotonic() + 8
        while time.monotonic() < deadline:
            if xvfb.poll() is not None:
                raise RuntimeError(f"STOP_XVFB_EXIT_{xvfb.returncode}")
            try:
                conn = xdisplay.Display(DISPLAY)
                conn.close()
                break
            except Exception:
                time.sleep(0.05)
        else:
            raise RuntimeError("STOP_XVFB_NOT_READY")
        env = {"PATH": "/usr/bin:/bin", "HOME": "/tmp", "LANG": "C.UTF-8",
               "DISPLAY": DISPLAY, "PYTHONPATH": "/repo"}
        for item in contexts():
            gate = {"truth": item["truth"], "fresh": item["fresh"],
                    "intent_match": item["intent_match"], "epoch_match": item["epoch_match"],
                    "commit_intent": "intent-current" if item["intent_match"] else "intent-other",
                    "commit_epoch": 7 if item["epoch_match"] else 6}
            for policy in ("TWO_TIER_FRESH_GATE", "DEPENDENCY_ONLY", "GATE_ONLY", "CACHED_PREPARE_GATE"):
                try:
                    rows.append(one_row(item["case"], policy, gate, "useful", env))
                except Exception as exc:
                    stop = {"reason": "STOP_CASE_EXECUTION", "case": item["case"],
                            "policy": policy, "error": repr(exc), "completed_rows": len(rows)}
                    raise
        live = {"truth": "TRUE", "fresh": True, "intent_match": True, "epoch_match": True,
                "commit_intent": "intent-current", "commit_epoch": 7}
        rows.append(one_row("valid_gate_no_effect", "TWO_TIER_FRESH_GATE", live, "no_effect", env))
    except Exception as exc:
        if stop is None:
            stop = {"reason": "STOP_FORMAL_INFRASTRUCTURE", "error": repr(exc),
                    "completed_rows": len(rows)}
    finally:
        if xvfb.poll() is None:
            xvfb.terminate()
            try:
                xvfb.wait(timeout=3)
            except subprocess.TimeoutExpired:
                xvfb.kill()
                xvfb.wait(timeout=2)
        xlog.close()
    with (ROOT / "raw.jsonl").open("w", encoding="utf-8") as stream:
        for row in rows:
            stream.write(json.dumps(row, sort_keys=True) + "\n")
    if stop is not None:
        (ROOT / "formal_stop.json").write_text(json.dumps(stop, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"decision": stop["reason"], "rows": len(rows)}))
        raise SystemExit(2)
    print(json.dumps({"decision": "FORMAL_MATRIX_COMPLETE_AUDIT_REQUIRED", "rows": len(rows),
                      "raw_sha256": sha256(ROOT / "raw.jsonl")}))


if __name__ == "__main__":
    main()
