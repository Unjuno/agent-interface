#!/usr/bin/env python3
"""One-shot private Xvfb construction runner for issue #5286."""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
import traceback

BASE_MAIN_SHA = "c45e1947e498dce08abfb27e459e610054a0602e"
HERE = Path(__file__).resolve().parent
HOST_SOCKET = Path("/tmp/.X11-unix/X0")


def socket_identity(path: Path = HOST_SOCKET):
    try:
        st = path.stat()
        return {"exists": True, "device": st.st_dev, "inode": st.st_ino,
                "mode": st.st_mode, "file_type": "socket" if path.is_socket() else "other"}
    except FileNotFoundError:
        return {"exists": False}


def validate_out(out: Path):
    root = (HERE / "results").resolve()
    target = out.resolve()
    if not target.is_relative_to(root):
        raise ValueError("output path must be contained below results/")
    if target.exists():
        raise FileExistsError("output path already exists; collisions are STOP")
    return target


def run(out_arg: str):
    out = validate_out(Path(out_arg))
    out.mkdir(parents=True, exist_ok=False)
    raw_path, log_path = out / "raw.json", out / "runner.log"
    rec = {"schema": "x11-private-xvfb-5286-v1", "base_main_sha": BASE_MAIN_SHA,
           "started_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
           "decision": "STOP", "checks": {}, "errors": [], "forced_kill": False}
    log = []
    proc = None
    try:
        rec["host_socket_before"] = socket_identity()
        for binary in ("unshare", "mount", "Xvfb"):
            p = subprocess.run(["sh", "-lc", f"command -v {binary}"], capture_output=True, text=True)
            rec.setdefault("preflight", {})[binary] = p.stdout.strip()
            if p.returncode:
                raise RuntimeError(f"missing required binary: {binary}")
        script = r'''set -eu
unshare --user --map-root-user --mount --fork sh -eu -c '
  mount --make-rprivate /
  mount -t tmpfs -o mode=1777,nosuid,nodev tmpfs /tmp/.X11-unix
  ns=$(readlink /proc/self/ns/mnt)
  printf "CHILD_MOUNT_NS=%s\\n" "$ns"
  cat /proc/self/mountinfo | grep " /tmp/.X11-unix "
  Xvfb :97 -screen 0 640x480x24 -nolisten tcp -noreset &
  xp=$!
  printf "XVFB_HOST_PID=%s\\n" "$xp"
  ready=0
  i=0
  while [ "$i" -lt 150 ]; do
    if python3 -c '\''from Xlib import display; d=display.Display(":97"); s=d.screen(); print("READY=%dx%d"%(s.width_in_pixels,s.height_in_pixels), flush=True); d.close()'\''; then ready=1; break; fi
    i=$((i+1)); sleep 0.1
  done
  [ "$ready" -eq 1 ] || { kill -TERM "$xp" 2>/dev/null || true; wait "$xp" || true; exit 41; }
  wait "$xp"; rc=$?
  printf "XVFB_EXIT_CODE=%s\\n" "$rc"
  exit "$rc"
'
'''
        proc = subprocess.Popen(["sh", "-c", script], stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, text=True, start_new_session=True,
                                bufsize=1)
        rec["wrapper_mount_ns"] = os.readlink("/proc/self/ns/mnt")
        rec["launcher_pid"] = proc.pid
        rec["process_group"] = proc.pid
        deadline = time.monotonic() + 20
        ready = False
        while time.monotonic() < deadline:
            line = proc.stdout.readline() if proc.poll() is None else ""
            if line:
                log.append(line.rstrip("\n"))
                if "CHILD_MOUNT_NS=" in line:
                    rec["child_mount_ns"] = line.strip().split("=", 1)[1]
                if "XVFB_HOST_PID=" in line:
                    rec["xvfb_pid"] = int(line.strip().split("=", 1)[1])
                if line.startswith("READY="):
                    dims = line.partition("=")[2].split("x")
                    rec["readiness"] = {"display": ":97", "width": int(dims[0]), "height": int(dims[1]), "probe": "inside-private-mount-namespace"}
                    ready = (int(dims[0]), int(dims[1])) == (640, 480)
                if " /tmp/.X11-unix " in line:
                    rec["mountinfo_line"] = line.strip()
            if ready:
                break
            if proc.poll() is not None:
                raise RuntimeError(f"Xvfb wrapper exited before readiness: {proc.returncode}")
            if not line:
                time.sleep(.05)
        rec["checks"]["readiness"] = ready
        if not ready:
            raise TimeoutError("Xvfb readiness timeout")
        # Bind the child's self-reported namespace to the host's procfs view
        # while the server is alive; /proc/<pid> vanishes after termination.
        rec["xvfb_proc_mount_ns"] = os.readlink(f'/proc/{rec["xvfb_pid"]}/ns/mnt')
        rec["sigterm_sent"] = True
        os.kill(rec["xvfb_pid"], signal.SIGTERM)
        try:
            rec["xvfb_exit_code"] = proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            rec["forced_kill"] = True
            os.killpg(proc.pid, signal.SIGKILL)
            rec["xvfb_exit_code"] = proc.wait()
        rec["checks"]["clean_sigterm"] = rec["xvfb_exit_code"] == 0 and not rec["forced_kill"]
        rec["checks"]["namespace_bound"] = bool(rec.get("xvfb_pid")) and rec.get("xvfb_proc_mount_ns") == rec.get("child_mount_ns") and rec.get("child_mount_ns") != rec.get("wrapper_mount_ns")
        rec["checks"]["mount_private_tmpfs"] = " /tmp/.X11-unix " in rec.get("mountinfo_line", "") and " - tmpfs " in rec.get("mountinfo_line", "")
        rec["host_socket_after"] = socket_identity()
        rec["checks"]["host_socket_unchanged"] = rec["host_socket_before"] == rec["host_socket_after"]
        rec["decision"] = "PASS" if all(rec["checks"].values()) else "STOP"
    except BaseException as exc:
        rec["errors"].append({"type": type(exc).__name__, "message": str(exc), "traceback": traceback.format_exc()})
        if proc and proc.poll() is None:
            try:
                rec["cleanup_sigterm_sent"] = True
                os.killpg(proc.pid, signal.SIGTERM)
                proc.wait(timeout=3)
            except BaseException:
                try:
                    rec["forced_kill"] = True
                    os.killpg(proc.pid, signal.SIGKILL)
                    proc.wait()
                except BaseException as cleanup_exc:
                    rec["errors"].append({"cleanup_error": repr(cleanup_exc)})
    finally:
        if proc and proc.stdout:
            try:
                log.extend(line.rstrip("\n") for line in proc.stdout.readlines())
            except Exception as exc:
                rec["errors"].append({"log_read_error": repr(exc)})
        rec["finished_utc"] = dt.datetime.now(dt.timezone.utc).isoformat()
        log_path.write_text("\n".join(log) + "\n", encoding="utf-8")
        rec["log_sha256"] = __import__("hashlib").sha256(log_path.read_bytes()).hexdigest()
        raw_path.write_text(json.dumps(rec, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"decision": rec["decision"], "raw": str(raw_path), "log": str(log_path)}))
    return 0 if rec["decision"] == "PASS" else 2


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    sys.exit(run(ap.parse_args().out))
