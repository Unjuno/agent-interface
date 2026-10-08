"""One public-dispatch case under xvfb-run.

One invocation creates exactly one arm and preserves its process, IPC, Entry,
X-server and imported-source evidence. Construction is the default mode;
formal cases require an explicit preregistered mode flag and distinct output.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import socket
import subprocess
import sys
import time
import traceback

from Xlib import X, display


MAIN_BACKEND_SHA256 = "c4bd1c2ccda7db43a4a62efc866547f21e2d11c0d795834f1f8e1d6b32f63126"
PREDECESSOR_PATCH = Path("research/integration/caps_text_boundary_k8n4_v1/study/candidate.patch")
CURRENT_CANDIDATE_PATCH = Path("research/integration/caps_text_check_to_xtest_successor_v2/current_main_candidate.patch")
BARRIER_PATCH = Path("research/integration/caps_text_check_to_xtest_successor_v2/current_main_barrier_instrumentation.patch")
FREEZE_FILE = Path("research/integration/caps_text_check_to_xtest_successor_v2/FREEZE.json")
HOOK_ENV = "AGENT_INTERFACE_CAPS_BARRIER_SOCKET"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_line(stream, timeout: float = 8.0) -> str:
    import select
    if not select.select([stream], [], [], timeout)[0]:
        raise TimeoutError("fixture response timeout")
    value = stream.readline()
    if not value:
        raise RuntimeError("fixture EOF")
    return value


def snapshot(d) -> dict:
    started = time.monotonic_ns()
    root = d.screen().root
    pointer = root.query_pointer()
    focus = d.get_input_focus().focus
    return {
        "started_ns": started,
        "ended_ns": time.monotonic_ns(),
        "lockmask": int(bool(pointer.mask & X.LockMask)),
        "mask": int(pointer.mask),
        "keymap": list(d.query_keymap()),
        "focus": getattr(focus, "id", focus),
    }


def xvfb_identity() -> dict:
    expected_pid = os.environ.get("AGENT_INTERFACE_XVFB_PID")
    if expected_pid:
        pid = int(expected_pid)
        argv = [part.decode("utf-8", "replace") for part in
                Path(f"/proc/{pid}/cmdline").read_bytes().split(b"\0") if part]
        if not argv or "Xvfb" not in Path(argv[0]).name:
            raise RuntimeError("formal Xvfb PID does not identify the expected server")
        if "-nolisten" not in argv or "tcp" not in argv:
            raise RuntimeError("formal Xvfb does not disable TCP listening")
        return {"display": os.environ["DISPLAY"], "pid": pid, "argv": argv}
    rows = subprocess.check_output(["ps", "-eo", "pid=,args="], text=True).splitlines()
    display_name = os.environ["DISPLAY"]
    matches = []
    for row in rows:
        try:
            pid_text, argv = row.strip().split(None, 1)
        except ValueError:
            continue
        if "Xvfb" in argv and display_name in argv:
            matches.append({"pid": int(pid_text), "argv": argv.split()})
    if len(matches) != 1:
        raise RuntimeError(f"expected one private Xvfb for {display_name}; found {matches}")
    return {"display": display_name, **matches[0]}


def network_boundary() -> dict:
    """Capture the network namespace and reject any non-local route/interface."""
    own_ns = Path("/proc/self/ns/net").stat().st_ino
    init_ns = Path("/proc/1/ns/net").stat().st_ino
    interfaces = socket.if_nameindex()
    ipv4_routes = [line for line in Path("/proc/net/route").read_text().splitlines()[1:]
                   if line.split() and line.split()[0] != "lo"]
    ipv6_routes = [line for line in Path("/proc/net/ipv6_route").read_text().splitlines()
                   if line.split() and line.split()[-1] != "lo"]
    up_non_loopback = []
    for _, name in interfaces:
        if name == "lo":
            continue
        flags = int(Path("/sys/class/net", name, "flags").read_text().strip(), 16)
        if flags & 1:  # IFF_UP
            up_non_loopback.append(name)
    result = {
        "namespace_inode": own_ns,
        "pid1_namespace_inode": init_ns,
        "interfaces": interfaces,
        "ipv4_non_loopback_routes": ipv4_routes,
        "ipv6_non_loopback_routes": ipv6_routes,
        "up_non_loopback_interfaces": up_non_loopback,
    }
    if own_ns == init_ns or ipv4_routes or ipv6_routes or up_non_loopback:
        raise RuntimeError("formal case is not isolated in a route-free network namespace")
    return result


def prepare_guard(repo: Path, out: Path) -> Path:
    candidate = out / "guard_source"
    candidate.mkdir()
    shutil.copytree(repo / "runtime", candidate / "runtime")
    for rel in (CURRENT_CANDIDATE_PATCH, BARRIER_PATCH):
        subprocess.run(["git", "apply", str(repo / rel)], cwd=candidate, check=True)
    return candidate


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--arm", choices=("current", "guard-stable", "guard-interposed"), required=True)
    parser.add_argument("--mode", choices=("construction", "formal"), default="construction")
    parser.add_argument("--case-id")
    args = parser.parse_args()
    if args.mode == "formal" and not args.case_id:
        parser.error("--case-id is required in formal mode")
    repo = args.repo.resolve()
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    baseline_backend = repo / "runtime/backends/x11_v1/backend.py"
    if sha256(baseline_backend) != MAIN_BACKEND_SHA256:
        raise RuntimeError("current-main backend identity differs from preregistered source")
    freeze = json.loads((repo / FREEZE_FILE).read_text(encoding="utf-8"))
    if args.mode == "formal" and freeze.get("status") != "FROZEN_NOT_STARTED":
        raise RuntimeError("formal plan is not frozen-not-started")

    record = {
        "kind": f"{args.mode}-public-dispatch-case",
        "study_id": "caps-text-query-xtest-a02-20261008",
        "case_id": args.case_id,
        "arm": args.arm,
        "network_boundary": network_boundary() if args.mode == "formal" else None,
        "repo_head": subprocess.check_output(
            ["git", "-C", str(repo), "rev-parse", "HEAD"], text=True
        ).strip(),
        "main_backend_sha256": sha256(baseline_backend),
        "driver_pid": os.getpid(),
        "runner_sha256": sha256(Path(__file__).resolve()),
        "freeze_sha256": sha256(repo / FREEZE_FILE),
        "python_version": sys.version,
        "platform": platform.platform(),
        "display": os.environ["DISPLAY"],
        "display_server": xvfb_identity(),
        "started_ns": time.monotonic_ns(),
        "errors": [],
        "ipc": [],
    }
    app = actor = None
    streams = []
    observer = display.Display(os.environ["DISPLAY"])
    original_barrier = os.environ.pop(HOOK_ENV, None)
    try:
        source = repo
        if args.arm.startswith("guard-"):
            source = prepare_guard(repo, out)
            record["candidate_backend_sha256"] = sha256(source / "runtime/backends/x11_v1/backend.py")
            record["predecessor_patch_sha256"] = sha256(repo / PREDECESSOR_PATCH)
            record["current_main_candidate_patch_sha256"] = sha256(repo / CURRENT_CANDIDATE_PATCH)
            record["barrier_patch_sha256"] = sha256(repo / BARRIER_PATCH)
            frozen_source = freeze["source_base"]
            if record["candidate_backend_sha256"] != frozen_source["candidate_backend_sha256"]:
                raise RuntimeError("#8255 candidate backend differs from frozen identity")
            if record["predecessor_patch_sha256"] != frozen_source["predecessor_candidate_patch_sha256"]:
                raise RuntimeError("#8255 candidate patch differs from frozen identity")
            if record["current_main_candidate_patch_sha256"] != frozen_source["current_main_candidate_patch_sha256"]:
                raise RuntimeError("current-main candidate patch differs from frozen identity")
            if record["barrier_patch_sha256"] != frozen_source["fixture_instrumentation_sha256"]:
                raise RuntimeError("fixture instrumentation differs from frozen identity")
        sys.path.insert(0, str(source))
        from runtime.cli_v1.api import dispatch

        app_log = out / "app.jsonl"
        app_err = (out / "app.stderr").open("x", encoding="utf-8")
        streams.append(app_err)
        app_argv = [sys.executable, "-B", str(Path(__file__).with_name("app_fixture.py")), str(app_log)]
        child_env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
        app = subprocess.Popen(app_argv, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                               stderr=app_err, env=child_env, text=True, bufsize=1)
        ready_raw = read_line(app.stdout)
        record["ipc"].append({"direction": "fixture-ready", "raw": ready_raw})
        ready = json.loads(ready_raw)
        record["app"] = {"pid": app.pid, "argv": app_argv, "ready": ready}

        def app_request(command: str) -> dict:
            raw = json.dumps({"command": command}) + "\n"
            record["ipc"].append({"direction": "to-app", "raw": raw})
            app.stdin.write(raw)
            app.stdin.flush()
            response = read_line(app.stdout)
            record["ipc"].append({"direction": "from-app", "raw": response})
            return json.loads(response)

        record["before"] = snapshot(observer)
        if record["before"]["lockmask"] != 0:
            raise RuntimeError("private Xvfb did not start with Caps Lock off")
        record["app_before"] = app_request("snapshot")

        if args.arm == "guard-interposed":
            socket_path = out / "caps-barrier.sock"
            actor_argv = [sys.executable, "-B", str(Path(__file__).with_name("lock_actor.py")),
                          str(socket_path), os.environ["DISPLAY"]]
            actor_out = (out / "actor.stdout").open("x", encoding="utf-8")
            actor_err = (out / "actor.stderr").open("x", encoding="utf-8")
            streams.extend((actor_out, actor_err))
            actor = subprocess.Popen(actor_argv, stdout=actor_out, stderr=actor_err,
                                     env=child_env, text=True)
            record["actor"] = {"pid": actor.pid, "argv": actor_argv}
            deadline = time.monotonic() + 4
            while not socket_path.exists() and actor.poll() is None and time.monotonic() < deadline:
                time.sleep(0.01)
            if not socket_path.exists():
                raise RuntimeError("separate lock actor did not bind barrier socket")
            os.environ[HOOK_ENV] = str(socket_path)

        program = {
            "schema": "agent-interface/program-v1",
            "program_id": ("formal-" + args.case_id + "-" + args.arm
                           if args.mode == "formal" else "construction-" + args.arm),
            "source": {"observation_seq": 1, "binding_revision": 1},
            "authority": {"lease_id": "private-fixture-only",
                          "expires_at_ns": time.monotonic_ns() + 20_000_000_000},
            "terminal": {"release_all_required": True},
            "ops": [
                {"op": "focus", "target": "entry"},
                {"op": "text", "text": "aB2"},
                {"op": "release_all"},
            ],
        }
        record["program_id"] = program["program_id"]
        record["program"] = program
        (out / "program.json").write_text(json.dumps(program, indent=2, sort_keys=True) + "\n")
        record["dispatch_started_ns"] = time.monotonic_ns()
        response = dispatch(
            program, {"entry": ready["window"]}, current_observation_seq=1,
            current_binding_revision=1, display_name=os.environ["DISPLAY"]
        )
        record["dispatch_ended_ns"] = time.monotonic_ns()
        record["response"] = response
        (out / "response.json").write_text(json.dumps(response, indent=2, sort_keys=True) + "\n")
        record["app_after"] = app_request("snapshot")
        record["after"] = snapshot(observer)

        if actor is not None:
            actor.wait(timeout=5)
            record["actor"].update(
                exit=actor.returncode,
                stdout=(out / "actor.stdout").read_text(encoding="utf-8"),
                stderr=(out / "actor.stderr").read_text(encoding="utf-8"),
            )
        app_request("close")
        app.wait(timeout=5)
        record["app"]["exit"] = app.returncode
        app_err.flush()
        app_err.close()
        record["app_stderr"] = (out / "app.stderr").read_text(encoding="utf-8")
        record["entry_events"] = [
            json.loads(line) for line in app_log.read_text(encoding="utf-8").splitlines()
        ]
        record["runtime_imports"] = {}
        for name, module in list(sys.modules.items()):
            path = getattr(module, "__file__", None)
            if name.startswith("runtime") and path and Path(path).is_file():
                try:
                    rel = Path(path).resolve().relative_to(source)
                except ValueError:
                    continue
                record["runtime_imports"][name] = {"path": rel.as_posix(), "sha256": sha256(Path(path))}
        actual = record["app_after"].get("value")
        expected = "Ab2" if args.arm == "guard-interposed" else "aB2"
        record.update(expected=expected, actual=actual, ended_ns=time.monotonic_ns())
        (out / "record.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
        print(json.dumps({"arm": args.arm, "actual": actual, "expected": expected,
                          "status": response.get("result", {}).get("status"),
                          "record": str(out / "record.json")}, sort_keys=True))
        return 0 if actual == expected else 1
    except Exception:
        record["errors"].append(traceback.format_exc())
        record["ended_ns"] = time.monotonic_ns()
        (out / "record.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
        raise
    finally:
        os.environ.pop(HOOK_ENV, None)
        if original_barrier is not None:
            os.environ[HOOK_ENV] = original_barrier
        if actor is not None and actor.poll() is None:
            actor.terminate()
            actor.wait(timeout=3)
        if app is not None and app.poll() is None:
            app.terminate()
            app.wait(timeout=3)
        observer.close()
        for stream in streams:
            stream.close()
        if app is not None:
            app.stdout.close()
            app.stdin.close()
        sys.path.remove(str(source)) if "source" in locals() and str(source) in sys.path else None


if __name__ == "__main__":
    raise SystemExit(main())
