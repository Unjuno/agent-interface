"""Additive one-shot #5236 formal successor with private X11 sockets."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import select
import signal
import subprocess
import sys
import time

import Xlib
from Xlib.display import Display as XDisplay

from runtime.backends.x11_v1.backend import X11Backend
from runtime.backends.x11_v1.session import X11RuntimeSession
from runtime.core_v1.contract import SCHEMA_PROGRAM

REPO_ROOT = Path(__file__).resolve().parents[2]
ROWS = (("control_us", "us", None), ("jp_to_us", "jp", "us"), ("us_to_jp", "us", "jp"))
WAIT_MS = 1500
POST_SAVE_WAIT_MS = 250
EXPECTED_EFFECT = (json.dumps({"saved": True, "text": "a_"}, sort_keys=True) + "\n").encode()
SOCKET_DIR = "/tmp/.X11-unix"
FROZEN_OUTPUT_REL = (
    "research/x11_midprogram_keymap_5236_formal07_20261001/"
    "results/formal07-20261001-01"
)


def source_blob_id(path: Path) -> str:
    content = path.read_bytes().replace(b"\r\n", b"\n")
    header = f"blob {len(content)}\0".encode("ascii")
    return hashlib.sha1(header + content).hexdigest()


def source_manifest_errors(manifest: dict, repo_root: Path = REPO_ROOT) -> list[str]:
    files = manifest.get("files")
    if not isinstance(files, dict) or not files:
        return ["files"]
    errors = []
    for relative, expected in files.items():
        path = Path(relative)
        if path.is_absolute() or ".." in path.parts:
            errors.append(str(relative))
            continue
        try:
            actual = source_blob_id(repo_root / path)
        except OSError:
            errors.append(str(relative))
            continue
        if actual != expected:
            errors.append(str(relative))
    return errors


def write_json(path: Path, value: dict) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def socket_identity() -> dict:
    stat = os.stat(SOCKET_DIR)
    return {"mode": stat.st_mode & 0o7777, "inode": stat.st_ino, "device": stat.st_dev}


def mount_record() -> dict | None:
    for line in Path("/proc/self/mountinfo").read_text(encoding="utf-8").splitlines():
        left, separator, right = line.partition(" - ")
        before, after = left.split(), right.split()
        if separator and len(before) > 4 and before[4].replace("\\040", " ") == SOCKET_DIR:
            return {"target": SOCKET_DIR, "fstype": after[0], "source": after[1]}
    return None


def run_bounded(command: list[str], timeout: float, env: dict[str, str] | None = None) -> dict:
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               text=True, env=env, start_new_session=True)
    try:
        stdout, stderr = process.communicate(timeout=timeout)
        return {"returncode": process.returncode, "timeout": False, "stdout": stdout, "stderr": stderr}
    except subprocess.TimeoutExpired:
        os.killpg(process.pid, signal.SIGTERM)
        try:
            stdout, stderr = process.communicate(timeout=3)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            stdout, stderr = process.communicate(timeout=3)
        return {"returncode": process.returncode, "timeout": True, "stdout": stdout, "stderr": stderr}


def child_command(output: Path, host_namespace: int) -> list[str]:
    bootstrap = (
        "import runpy,sys; "
        f"sys.path.insert(0,{str(REPO_ROOT)!r}); "
        f"sys.argv=[{str(Path(__file__).resolve())!r},'--child','--child-output',"
        f"{str(output)!r},'--host-namespace',{str(host_namespace)!r}]; "
        f"runpy.run_path({str(Path(__file__).resolve())!r},run_name='__main__')"
    )
    return ["unshare", "--user", "--map-root-user", "--mount", "--fork",
            sys.executable, "-c", bootstrap]


def verify_fixture_runtime() -> dict:
    code = (
        "import json,tkinter; from runtime.backends.x11_v1 import fixture_app; "
        "import _tkinter; print(json.dumps({'tkinter':tkinter.TkVersion,"
        "'tkinter_file':_tkinter.__file__,'fixture_import':fixture_app.__file__},sort_keys=True))"
    )
    result = subprocess.run([sys.executable, "-c", code], cwd=REPO_ROOT,
                            capture_output=True, text=True, timeout=10)
    return {"returncode": result.returncode, "stdout": result.stdout,
            "stderr": result.stderr, "argv": [sys.executable, "-c", code]}


def _layout_query(display_name: str) -> dict:
    argv = ["setxkbmap", "-display", display_name, "-query"]
    result = subprocess.run(argv, text=True, capture_output=True, check=False)
    return {"argv": argv, "exit": result.returncode, "stdout": result.stdout, "stderr": result.stderr}


def _start_server(row_dir: Path) -> tuple[subprocess.Popen, str, XDisplay, object]:
    log = (row_dir / "xvfb.log").open("wb")
    argv = ["Xvfb", "-displayfd", "1", "-screen", "0", "1024x768x24",
            "-nolisten", "tcp", "-terminate", "-ac"]
    server = subprocess.Popen(argv, stdout=subprocess.PIPE, stderr=log, text=True, bufsize=1)
    anchor = None
    try:
        readable, _, _ = select.select([server.stdout], [], [], 8.0)
        display_line = server.stdout.readline().strip() if readable else ""
        if not display_line.isdecimal():
            detail = "no displayfd line" if not display_line else f"invalid displayfd line: {display_line!r}"
            raise RuntimeError(f"STOP_XVFB_STARTUP: {detail}")
        display_name = ":" + display_line
        anchor = XDisplay(display_name)
        size = [anchor.screen().width_in_pixels, anchor.screen().height_in_pixels]
        if size != [1024, 768]:
            raise RuntimeError(f"STOP_XVFB_GEOMETRY: {size}")
        return server, display_name, anchor, log
    except Exception:
        if anchor is not None:
            try:
                anchor.close()
            except Exception:
                pass
        if server.poll() is None:
            server.terminate()
            try:
                server.wait(timeout=2)
            except subprocess.TimeoutExpired:
                server.kill()
                server.wait()
        if server.stdout is not None:
            server.stdout.close()
        log.close()
        raise


def _actor_command(display_name: str, target: str, receipt_path: Path) -> list[str]:
    source = (
        "import json,subprocess,sys,time; d,t,out=sys.argv[1:]; time.sleep(0.25); "
        "start=time.monotonic_ns(); argv=['setxkbmap','-display',d,'-layout',t]; "
        "p=subprocess.run(argv,capture_output=True,text=True); end=time.monotonic_ns(); "
        "open(out,'w',encoding='utf-8').write(json.dumps({'argv':argv,'target_layout':t,"
        "'started_ns':start,'ended_ns':end,'exit':p.returncode,'stdout':p.stdout,"
        "'stderr':p.stderr},sort_keys=True)+'\\n'); sys.exit(p.returncode)"
    )
    return [sys.executable, "-c", source, display_name, target, str(receipt_path)]


def run_row(root: Path, row_id: str, initial: str, target: str | None) -> dict:
    row_dir = root / row_id
    row_dir.mkdir()
    record: dict = {"row": row_id, "initial_layout": initial, "target_layout": target,
                    "status": "STOP_ROW_INCOMPLETE"}
    server = None
    anchor = None
    xvfb_log = None
    backend = None
    fixture = None
    actor = None
    try:
        server, display_name, anchor, xvfb_log = _start_server(row_dir)
        record["display"] = display_name
        record["xvfb"] = {"argv": ["Xvfb", "-displayfd", "1", "-screen", "0", "1024x768x24",
                                    "-nolisten", "tcp", "-terminate", "-ac"],
                          "pid": server.pid, "exit_code": None, "cleanup_action": None}
        setup_argv = ["setxkbmap", "-display", display_name, "-layout", initial]
        setup = subprocess.run(setup_argv, text=True, capture_output=True, check=False)
        record["layout_setup"] = {"argv": setup_argv, "exit": setup.returncode,
                                  "stdout": setup.stdout, "stderr": setup.stderr}
        if setup.returncode != 0:
            record["status"] = "STOP_LAYOUT_SETUP"
            return record
        initial_layout = _layout_query(display_name)
        record["layout_initial"] = initial_layout
        if initial_layout["exit"] != 0:
            record["status"] = "STOP_LAYOUT_READBACK"
            return record

        meta = row_dir / "meta.json"
        effect = row_dir / "effect.json"
        events = row_dir / "events.jsonl"
        fixture_argv = [sys.executable, "-m", "runtime.backends.x11_v1.fixture_app",
                        "--meta", str(meta), "--effect", str(effect), "--events", str(events)]
        fixture = subprocess.Popen(fixture_argv, env=os.environ | {"DISPLAY": display_name},
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        record["fixture_argv"] = fixture_argv
        deadline = time.monotonic() + 8.0
        while not meta.exists() and time.monotonic() < deadline:
            if fixture.poll() is not None:
                record["status"] = "STOP_FIXTURE_EXIT"
                break
            time.sleep(0.02)
        if not meta.exists():
            if record["status"] == "STOP_ROW_INCOMPLETE":
                record["status"] = "STOP_FIXTURE_TIMEOUT"
            return record

        window_id = json.loads(meta.read_text(encoding="utf-8"))["window_id"]
        backend = X11Backend(display_name, {"fixture": window_id})
        session = X11RuntimeSession(backend)
        actor_path = row_dir / "actor.json"
        actor_argv = None
        if target is not None:
            actor_argv = _actor_command(display_name, target, actor_path)
            actor = subprocess.Popen(actor_argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        program = {
            "schema": SCHEMA_PROGRAM,
            "program_id": "issue5236-formal07-" + row_id,
            "source": {"observation_seq": 7, "binding_revision": 3},
            "authority": {"lease_id": "issue5236-formal07", "expires_at_ns": time.monotonic_ns() + 30_000_000_000},
            "terminal": {"release_all_required": True},
            "ops": [
                {"op": "focus", "target": "fixture"},
                {"op": "pointer_move", "target": "fixture", "frame": "window_client", "x": 50, "y": 55},
                {"op": "pointer_button", "button": "left", "down": True},
                {"op": "pointer_button", "button": "left", "down": False},
                {"op": "text", "text": "a"},
                {"op": "wait_update", "timeout_ms": WAIT_MS},
                {"op": "text", "text": "_"},
                {"op": "key_chord", "keys": ["CTRL", "S"]},
                {"op": "wait_update", "timeout_ms": POST_SAVE_WAIT_MS},
                {"op": "release_all"},
            ],
        }
        dispatch_started = time.monotonic_ns()
        dispatch = session.dispatch(program, current_observation_seq=7, current_binding_revision=3)
        dispatch_ended = time.monotonic_ns()
        actor_stdout, actor_stderr = actor.communicate(timeout=8) if actor else ("", "")
        fixture_stdout, fixture_stderr = fixture.communicate(timeout=0.1) if fixture.poll() is not None else ("", "")
        effect_hex = effect.read_bytes().hex() if effect.exists() else None
        layout_after = _layout_query(display_name)
        actor_receipt = json.loads(actor_path.read_text(encoding="utf-8")) if actor_path.exists() else None
        execution = dispatch.get("execution", {})
        waits = execution.get("waits", [])
        record.update({
            "status": "row_complete" if dispatch.get("status") in {"completed", "execution_failed"} else "STOP_DISPATCH",
            "program": program,
            "dispatch_started_ns": dispatch_started,
            "dispatch_ended_ns": dispatch_ended,
            "dispatch": dispatch,
            "wait": waits[0] if waits else None,
            "post_save_wait": waits[1] if len(waits) >= 2 else None,
            "saved_effect_hex": effect_hex,
            "expected_effect_hex": EXPECTED_EFFECT.hex(),
            "layout_after": layout_after,
            "actor_argv": actor_argv,
            "actor_receipt": actor_receipt,
            "actor_exit": actor.returncode if actor else None,
            "actor_stdout": actor_stdout,
            "actor_stderr": actor_stderr,
            "fixture_exit_before_cleanup": fixture.returncode,
            "fixture_stdout_before_cleanup": fixture_stdout,
            "fixture_stderr_before_cleanup": fixture_stderr,
            "events_hex": events.read_bytes().hex() if events.exists() else None,
        })
        if target is not None and (actor.returncode != 0 or actor_receipt is None):
            record["status"] = "STOP_ACTOR"
        if layout_after["exit"] != 0:
            record["status"] = "STOP_LAYOUT_AFTER"
        return record
    except Exception as exc:
        record["status"] = "STOP_EXCEPTION"
        record["exception"] = f"{type(exc).__name__}: {exc}"
        return record
    finally:
        if backend is not None:
            try:
                backend.close()
            except Exception as exc:
                record["backend_close_error"] = repr(exc)
        if actor is not None and actor.poll() is None:
            actor.terminate()
            try:
                actor.wait(timeout=2)
            except subprocess.TimeoutExpired:
                actor.kill()
                actor.wait()
        if fixture is not None and fixture.poll() is None:
            fixture.terminate()
            try:
                fixture.wait(timeout=3)
            except subprocess.TimeoutExpired:
                fixture.kill()
                fixture.wait()
        if fixture is not None:
            try:
                out, err = fixture.communicate(timeout=0.1)
                record.setdefault("fixture_exit", fixture.returncode)
                record.setdefault("fixture_stdout", out)
                record.setdefault("fixture_stderr", err)
            except subprocess.TimeoutExpired:
                record["fixture_cleanup"] = "STOP_FIXTURE_REAP_TIMEOUT"
        if anchor is not None:
            try:
                anchor.close()
            except Exception as exc:
                record["anchor_close_error"] = repr(exc)
        if server is not None:
            try:
                server.wait(timeout=3)
                cleanup = "natural_terminate" if server.returncode == 0 else "unexpected_exit"
            except subprocess.TimeoutExpired:
                cleanup = "signal_fallback"
                server.terminate()
                try:
                    server.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    cleanup = "kill_fallback"
                    server.kill()
                    server.wait()
            if "xvfb" in record:
                record["xvfb"].update(exit_code=server.returncode, cleanup_action=cleanup)
            if cleanup != "natural_terminate" and record.get("status") == "row_complete":
                record["status"] = "STOP_XVFB_CLEANUP"
        if xvfb_log is not None:
            xvfb_log.close()


def child_main(output: Path, host_namespace: int) -> int:
    manifest_path = Path(__file__).with_name("SOURCE_MANIFEST.json")
    source_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    raw = {"schema": "issue5236-formal07-raw-v1", "rows": [],
           "host_mount_ns_inode": host_namespace,
           "source_manifest": source_manifest, "source_blobs": source_manifest.get("files", {})}
    try:
        child_namespace = os.stat("/proc/self/ns/mnt").st_ino
        subprocess.run(["mount", "--make-rprivate", "/"], check=True, capture_output=True, text=True)
        subprocess.run(["mount", "-t", "tmpfs", "-o", "mode=1777,nosuid,nodev", "tmpfs", SOCKET_DIR],
                       check=True, capture_output=True, text=True)
        raw["namespace"] = {"host_mount_ns_inode": host_namespace,
                             "child_mount_ns_inode": child_namespace,
                             "private": child_namespace != host_namespace,
                             "socket_mount": mount_record(),
                             "socket_dir_mode": os.stat(SOCKET_DIR).st_mode & 0o7777}
        raw["environment"] = {"python": sys.version, "platform": platform.platform(),
                               "python_xlib": getattr(Xlib, "__version__", "unknown"),
                               "display_server": "private Xvfb per row", "docker": False}
        for row_id, initial, target in ROWS:
            row = run_row(output, row_id, initial, target)
            raw["rows"].append(row)
            write_json(output / "raw.json", raw)
            if row.get("status") != "row_complete":
                return 2
        return 0
    except Exception as exc:
        raw["stop"] = f"{type(exc).__name__}: {exc}"
        write_json(output / "raw.json", raw)
        return 2


def host_main(output_arg: Path) -> int:
    output = output_arg.resolve()
    try:
        output.relative_to(REPO_ROOT)
    except ValueError:
        raise SystemExit("STOP_OUTPUT_PATH_OUTSIDE_REPO")
    if output == REPO_ROOT or output.exists():
        raise SystemExit("STOP_OUTPUT_COLLISION: output path already exists")
    if output.relative_to(REPO_ROOT).as_posix() != FROZEN_OUTPUT_REL:
        raise SystemExit("STOP_OUTPUT_PATH_UNFROZEN")
    manifest_path = Path(__file__).with_name("SOURCE_MANIFEST.json")
    try:
        source_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"STOP_SOURCE_MANIFEST: {exc}")
    source_errors = source_manifest_errors(source_manifest)
    if source_errors:
        raise SystemExit("STOP_SOURCE_HASH_MISMATCH: " + ",".join(source_errors))
    fixture_preflight = verify_fixture_runtime()
    if fixture_preflight["returncode"] != 0:
        raise SystemExit("STOP_FIXTURE_RUNTIME_PREFLIGHT: " + fixture_preflight["stderr"])
    output.mkdir(parents=True, exist_ok=False)
    host_namespace = os.stat("/proc/self/ns/mnt").st_ino
    before = socket_identity()
    command = child_command(output, host_namespace)
    completed = run_bounded(command, 180.0, env=os.environ.copy())
    after = socket_identity()
    child_raw_path = output / "raw.json"
    child_raw = json.loads(child_raw_path.read_text(encoding="utf-8")) if child_raw_path.exists() else None
    wrapper = {"schema": "issue5236-formal07-wrapper-v1", "command": command,
               "timeout_seconds": 180, "timeout": completed["timeout"],
               "returncode": completed["returncode"], "stdout": completed["stdout"],
               "stderr": completed["stderr"], "host_mount_ns_inode": host_namespace,
               "host_socket_before": before, "host_socket_after": after,
               "host_socket_unchanged": before == after, "child_raw_available": child_raw is not None,
               "source_manifest": source_manifest, "fixture_preflight": fixture_preflight,
               "repository_root": str(REPO_ROOT), "runner_path": str(Path(__file__).resolve()),
               "python_executable": sys.executable}
    write_json(output / "wrapper.json", wrapper)
    if child_raw is None or completed["timeout"] or completed["returncode"] != 0 or before != after:
        return 2
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    parser.add_argument("--child", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--host-namespace", type=int, help=argparse.SUPPRESS)
    parser.add_argument("--child-output", type=Path, help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    if args.child:
        if args.child_output is None or args.host_namespace is None:
            raise SystemExit("STOP_CHILD_ARGUMENTS")
        return child_main(args.child_output, args.host_namespace)
    if args.output is None:
        raise SystemExit("--output is required")
    return host_main(args.output)


if __name__ == "__main__":
    raise SystemExit(main())
