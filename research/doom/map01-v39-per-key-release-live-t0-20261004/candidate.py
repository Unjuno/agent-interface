"""One-shot no-model X11 validation of the current-v39 release telemetry path."""
import argparse
import hashlib
import json
import os
import platform
import socket
import subprocess
import sys
import tarfile
import threading
import time
from pathlib import Path


ROOT = Path(os.environ.get("V39_TELEMETRY_ROOT", "/repo")).resolve()
PACKAGE = ROOT / "research/doom/map01-v39-per-key-release-live-t0-20261004"


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def verify_frozen(freeze):
    if freeze.get("allocation_id") != "MAP01-V39-RELEASE-TELEMETRY-LIVE-59-T0-20261004-01":
        raise RuntimeError("STOP_ALLOCATION_ID")
    for name, expected in freeze["sha256"].items():
        path = (ROOT / name).resolve()
        if not path.is_file() or sha256(path) != expected:
            raise RuntimeError("STOP_SOURCE_DRIFT:" + name)
    environment_path = PACKAGE / "ENVIRONMENT.json"
    if sha256(environment_path) != freeze["runtime_environment_sha256"]:
        raise RuntimeError("STOP_RUNTIME_ENVIRONMENT_HASH")
    environment = json.loads(environment_path.read_text(encoding="utf-8"))
    if environment.get("python_version") != sys.version or \
            environment.get("platform") != platform.platform():
        raise RuntimeError("STOP_RUNTIME_ENVIRONMENT_DRIFT")
    if environment.get("python_packages") != subprocess.check_output(
            [sys.executable, "-m", "pip", "freeze", "--all"], text=True).strip():
        raise RuntimeError("STOP_PYTHON_PACKAGE_DRIFT")
    dpkg_format = "-f=" + "$" + "{binary:Package}=" + "$" + "{Version}\\n"
    if environment.get("dpkg_packages") != subprocess.check_output(
            ["dpkg-query", "-W", dpkg_format], text=True).strip():
        raise RuntimeError("STOP_OS_PACKAGE_DRIFT")
    interfaces = sorted(name for _index, name in socket.if_nameindex())
    allowed_interfaces = ["ip6tnl0", "lo", "sit0", "tunl0"]
    links = subprocess.check_output(["ip", "-brief", "link"], text=True).splitlines()
    link_states = {
        line.split()[0].split("@", 1)[0]: line.split()[1]
        for line in links if len(line.split()) >= 2
    }
    ipv4_routes = subprocess.check_output(["ip", "route"], text=True).strip()
    ipv6_routes = subprocess.check_output(["ip", "-6", "route"], text=True).strip()
    if (interfaces != allowed_interfaces or
            set(link_states) != set(allowed_interfaces) or
            any(state != "DOWN" for state in link_states.values()) or
            ipv4_routes or ipv6_routes):
        raise RuntimeError("STOP_NETWORK_NAMESPACE:" + repr(interfaces))
    return {
        "network_interfaces": interfaces,
        "network_link_states": link_states,
        "network_ipv4_routes": ipv4_routes,
        "network_ipv6_routes": ipv6_routes,
    }


def initial_candidate_record(freeze, network_receipt):
    expected_network_fields = {
        "network_interfaces", "network_link_states",
        "network_ipv4_routes", "network_ipv6_routes",
    }
    if (not isinstance(network_receipt, dict)
            or set(network_receipt) != expected_network_fields):
        raise RuntimeError("STOP_NETWORK_RECEIPT_INCOMPLETE")
    return {
        "allocation_id": freeze["allocation_id"],
        "candidate_completed": False,
        "model_calls": 0,
        "runtime_environment_sha256": freeze["runtime_environment_sha256"],
        **network_receipt,
        "trials": [], "cleanup": {}, "issues": [],
    }


def install_support(path, expected_sha):
    if sha256(path) != expected_sha:
        raise RuntimeError("STOP_SUPPORT_ARCHIVE_HASH")
    manifest = json.loads((PACKAGE / "SOURCE_MANIFEST.json").read_text(encoding="utf-8"))
    if manifest.get("archive_sha256") != expected_sha:
        raise RuntimeError("STOP_SUPPORT_MANIFEST_HASH")
    root = Path("/tmp/v39-telemetry-support")
    root.mkdir(mode=0o700)
    with tarfile.open(path, mode="r:gz") as archive:
        for member in archive.getmembers():
            target = (root / member.name).resolve()
            if not target.is_relative_to(root.resolve()) or not member.isfile():
                raise RuntimeError("STOP_SUPPORT_ARCHIVE_MEMBER")
            source = archive.extractfile(member)
            if source is None:
                raise RuntimeError("STOP_SUPPORT_ARCHIVE_CONTENT")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(source.read())
    rows = {row["path"]: row for row in manifest.get("files", [])}
    if len(rows) != len(manifest.get("files", [])):
        raise RuntimeError("STOP_SUPPORT_MANIFEST_DUPLICATE")
    for name, row in rows.items():
        target = root / name
        if not target.is_file() or target.stat().st_size != row.get("bytes") or \
                sha256(target) != row.get("sha256"):
            raise RuntimeError("STOP_SUPPORT_MEMBER_HASH:" + name)
    sys.path[:0] = [
        str(root / "research/observation_tiles"),
        str(root / "research/observation_gating"),
        str(root / "research/real_apps_v1"),
        str(root),
    ]
    return root


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    out = args.out.resolve()
    if not out.is_dir() or any(out.iterdir()):
        raise RuntimeError("STOP_OUTPUT_NOT_EMPTY")
    freeze = json.loads((PACKAGE / "FREEZE.json").read_text(encoding="utf-8"))
    if out != (ROOT / freeze["output_root"]).resolve():
        raise RuntimeError("STOP_OUTPUT_ROOT_MISMATCH")
    network_receipt = verify_frozen(freeze)
    support = install_support(PACKAGE / "source-support.tar.gz",
                              freeze["source_support_sha256"])
    (out / "candidate_started.json").write_text(json.dumps({
        "allocation_id": freeze["allocation_id"],
        "started_ns": time.perf_counter_ns(),
        "platform": platform.platform(), "python": sys.version,
        "support_root": str(support), "model_calls": 0,
        "execution_route": freeze["execution_route"],
        "network_isolation": freeze["network_isolation"],
        "scope": "current-v39 backend and executor on private Xvfb; no game/task",
    }, indent=2) + "\n", encoding="utf-8")

    import Xlib.display as xdisplay
    from Xlib import XK
    sys.path[:0] = [str(ROOT / "research/doom"),
                    str(ROOT / "research/live_control")]
    import session_map01_v12 as runtime

    if runtime.Backend.__module__ != "doom_typed_release_backend_v3":
        raise RuntimeError("FAIL_V39_BACKEND_SELECTION")
    if runtime.Executor.__module__ != "executor_v12":
        raise RuntimeError("FAIL_V39_EXECUTOR_SELECTION")

    events = []
    observer_rows = []
    lock = threading.RLock()
    condition = threading.Condition(lock)
    state = {"trial": None, "observer": None}

    def sample(label, keys, trial_id):
        codes = {key: state["observer"].keysym_to_keycode(
            XK.string_to_keysym(key)) for key in keys}
        if any(code <= 0 for code in codes.values()):
            raise RuntimeError("STOP_X11_KEYCODE")
        bitmap = bytes(state["observer"].query_keymap())
        row = {
            "trial_id": trial_id, "label": label,
            "timestamp_ns": time.perf_counter_ns(),
            "keycodes": codes, "keymap_hex": bitmap.hex(),
            "keys_down": {key: bool(bitmap[code // 8] & (1 << (code % 8)))
                          for key, code in codes.items()},
        }
        observer_rows.append(row)
        with (out / "observer.jsonl").open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(row, sort_keys=True) + "\n")
            stream.flush()
        return row

    def emit(record):
        with condition:
            record = dict(record)
            record["emit_started_ns"] = time.perf_counter_ns()
            events.append(record)
            with (out / "events.jsonl").open("a", encoding="utf-8") as stream:
                stream.write(json.dumps(record, sort_keys=True) + "\n")
                stream.flush()
            if record.get("event") == "input_admission" and state["trial"]:
                trial = state["trial"]
                if record.get("key") in trial["keys"]:
                    try:
                        sample("after_admission:" + record["key"],
                               trial["keys"], trial["id"])
                    except Exception as exc:
                        trial["observer_error"] = repr(exc)
            condition.notify_all()

    session = backend = executor = None
    candidate = initial_candidate_record(freeze, network_receipt)
    exit_code = 2
    try:
        session = runtime.suite.Session()
        for key in ("DISPLAY", "XAUTHORITY", "HOME", "XDG_CONFIG_HOME",
                    "XDG_CACHE_HOME", "XDG_RUNTIME_DIR"):
            os.environ[key] = session.env[key]
        os.environ["SDL_VIDEODRIVER"] = "x11"
        os.environ.pop("WAYLAND_DISPLAY", None)
        (out / "x11-display.txt").write_text(session.name, encoding="utf-8")
        state["observer"] = xdisplay.Display(session.name)

        iwad = Path(__import__("vizdoom").__file__).parent / "freedoom2.wad"
        if not iwad.is_file():
            raise RuntimeError("STOP_VIZDOOM_IWAD_MISSING")
        readers = {name: runtime.DoomStatusNumberReader(iwad, signal_id=name)
                   for name in ("health", "ammo")}
        backend = runtime.Backend(session, out, emit, readers)
        executor = runtime.Executor(backend, emit)
        backend.snapshot("telemetry-validation-initial", 0)
        candidate["backend_class"] = runtime.Backend.__module__ + ".Backend"
        candidate["executor_class"] = runtime.Executor.__module__ + ".Executor"
        candidate["owner_id"] = backend.owner.owner_id
        candidate["source_manifest_sha256"] = sha256(PACKAGE / "SOURCE_MANIFEST.json")
        candidate["runtime_source_hashes"] = {
            item: sha256(ROOT / item) for item in freeze["runtime_source_paths"]}

        trials = (("v39-single-space", ["space"]),
                  ("v39-two-key-up-space", ["Up", "space"]))
        for trial_id, keys in trials:
            first = sample("before", keys, trial_id)
            if any(first["keys_down"].values()):
                candidate["issues"].append("preexisting_requested_key_down")
                break
            trial_start = len(events)
            trial_state = {"id": trial_id, "keys": list(keys), "observer_error": None}
            state["trial"] = trial_state
            expected_sequence = backend.sequence
            deadline_ns = time.perf_counter_ns() + 15_000_000_000
            executor.submit(trial_id, [{"op": "hold", "keys": list(keys),
                                         "duration_ms": 600}],
                            expected_sequence, deadline_ns)
            accepted = next((row for row in events[trial_start:]
                             if row.get("event") == "accepted" and row.get("id") == trial_id), None)
            if not accepted:
                candidate["issues"].append("accepted_receipt_missing")
                break
            end = time.monotonic() + 20
            with condition:
                while not any(row.get("event") == "terminal" and row.get("id") == trial_id
                              for row in events[trial_start:]):
                    remaining = end - time.monotonic()
                    if remaining <= 0:
                        candidate["issues"].append("terminal_timeout")
                        break
                    condition.wait(remaining)
            terminal = next((row for row in events[trial_start:]
                             if row.get("event") == "terminal" and row.get("id") == trial_id), None)
            after = sample("after_terminal", keys, trial_id)
            state["trial"] = None
            trial_events = events[trial_start:]
            candidate["trials"].append({
                "trial_id": trial_id, "keys": list(keys),
                "intent_token": accepted.get("intent_token"),
                "expected_sequence": expected_sequence,
                "event_start_index": trial_start,
                "event_end_index": trial_start + len(trial_events),
                "terminal": terminal,
                "pre_keymap": first, "post_keymap": after,
                "admission_keymaps": [row for row in observer_rows
                    if row["trial_id"] == trial_id and row["label"].startswith("after_admission:")],
                "observer_error": trial_state["observer_error"],
            })
            if terminal is None or terminal.get("status") != "completed":
                candidate["issues"].append("program_not_completed")
                break
            if any(after["keys_down"].values()):
                candidate["issues"].append("requested_key_down_after_terminal")
                break

        if executor is not None:
            executor.close()
        candidate["candidate_completed"] = len(candidate["trials"]) == 2
        exit_code = 0 if candidate["candidate_completed"] else 2
    except Exception as exc:
        candidate["issues"].append(type(exc).__name__ + ":" + str(exc))
    finally:
        state["trial"] = None
        if state["observer"] is not None:
            try:
                state["observer"].close()
            except Exception as exc:
                candidate["issues"].append("observer_close:" + repr(exc))
        if backend is not None:
            try:
                backend.close()
                candidate["cleanup"]["owner_thread_alive"] = bool(backend.owner._inner.thread.is_alive())
                (out / "owner-events.json").write_text(
                    json.dumps(backend.owner.records, indent=2) + "\n", encoding="utf-8")
            except Exception as exc:
                candidate["issues"].append("owner_close:" + repr(exc))
        if session is not None:
            try:
                session.close()
                candidate["cleanup"]["x11_processes"] = [
                    {"pid": process.pid, "returncode": process.returncode}
                    for process in session.procs]
            except Exception as exc:
                candidate["issues"].append("session_close:" + repr(exc))
        candidate["candidate_completed"] = (
            candidate["candidate_completed"] and not candidate["issues"])
        if not candidate["candidate_completed"]:
            exit_code = 2
        candidate["candidate_finished_ns"] = time.perf_counter_ns()
        event_path = out / "events.jsonl"
        candidate["events_sha256"] = sha256(event_path) if event_path.exists() else None
        (out / "candidate.json").write_text(
            json.dumps(candidate, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
