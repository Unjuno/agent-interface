#!/usr/bin/env python3
"""One-shot private Xvfb termination check for issue #5291."""
from __future__ import annotations
import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
import traceback

BASE_MAIN_SHA = "1d5b5f2a7b8d7ac6a467a1aaabdfc30c851f7f72"
HERE = Path(__file__).resolve().parent
HOST_SOCKET = Path("/tmp/.X11-unix/X0")


def socket_identity(path=HOST_SOCKET):
    try:
        st = path.stat()
        return {"exists": True, "device": st.st_dev, "inode": st.st_ino,
                "mode": st.st_mode, "is_socket": path.is_socket()}
    except FileNotFoundError:
        return {"exists": False}


def validate_out(out):
    root = (HERE / "results").resolve()
    target = Path(out).resolve()
    if not target.is_relative_to(root):
        raise ValueError("output must remain under results/")
    if target.exists():
        raise FileExistsError("output collision; STOP without retry")
    return target


SCRIPT = r'''set -eu
unshare --user --map-root-user --mount --fork sh -eu -c '
  mount --make-rprivate /
  mount -t tmpfs -o mode=1777,nosuid,nodev tmpfs /tmp/.X11-unix
  printf "CHILD_MOUNT_NS=%s\\n" "$(readlink /proc/self/ns/mnt)"
  grep " /tmp/.X11-unix " /proc/self/mountinfo
  Xvfb :97 -screen 0 640x480x24 -nolisten tcp -noreset &
  xp=$!
  printf "XVFB_HOST_PID=%s\\n" "$xp"
  i=0
  while [ "$i" -lt 150 ]; do
    if dims=$(python3 -c '\''from Xlib import display; import os; d=display.Display(":97"); s=d.screen(); print("%dx%d"%(s.width_in_pixels,s.height_in_pixels), flush=True); os._exit(0)'\'' 2>/dev/null); then
      printf "READY=%s\\n" "$dims"
      break
    fi
    i=$((i+1)); sleep 0.1
  done
  [ "$i" -lt 150 ] || { kill -TERM "$xp" 2>/dev/null || true; wait "$xp" || true; exit 41; }
  set +e
  wait "$xp"
  rc=$?
  set -e
  printf "XVFB_EXIT_CODE=%s\\n" "$rc"
  exit "$rc"
'
'''


def run(out_arg):
    out = validate_out(out_arg)
    out.mkdir(parents=True, exist_ok=False)
    raw_path, log_path = out / "raw.json", out / "runner.log"
    rec = {"schema":"x11-private-xvfb-5291-v1", "base_main_sha":BASE_MAIN_SHA,
           "started_utc":dt.datetime.now(dt.timezone.utc).isoformat(),
           "decision":"STOP", "checks":{}, "errors":[], "forced_kill":False}
    log = []
    proc = None
    try:
        rec["host_socket_before"] = socket_identity()
        for binary in ("unshare", "mount", "Xvfb", "python3"):
            p = subprocess.run(["sh", "-lc", f"command -v {binary}"], capture_output=True, text=True)
            rec.setdefault("preflight", {})[binary] = p.stdout.strip()
            if p.returncode:
                raise RuntimeError(f"missing binary: {binary}")
        proc = subprocess.Popen(["sh", "-c", SCRIPT], stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, text=True, start_new_session=True, bufsize=1)
        rec["wrapper_pid"] = proc.pid
        rec["wrapper_mount_ns"] = os.readlink("/proc/self/ns/mnt")
        deadline = time.monotonic() + 20
        ready = False
        while time.monotonic() < deadline:
            line = proc.stdout.readline() if proc.poll() is None else ""
            if not line:
                if proc.poll() is not None:
                    break
                continue
            line = line.rstrip("\n")
            log.append(line)
            if line.startswith("CHILD_MOUNT_NS="):
                rec["child_mount_ns"] = line.partition("=")[2]
            elif line.startswith("XVFB_HOST_PID="):
                rec["xvfb_pid"] = int(line.partition("=")[2])
            elif line.startswith("READY="):
                value = line.partition("=")[2].split("x")
                rec["readiness"] = {"width":int(value[0]), "height":int(value[1]), "display":":97"}
                ready = rec["readiness"] == {"width":640,"height":480,"display":":97"}
                if ready:
                    break
            elif " /tmp/.X11-unix " in line:
                rec["mountinfo_line"] = line
        rec["checks"]["readiness"] = ready
        if not ready:
            raise TimeoutError("completed Xlib readiness probe not observed")
        if not isinstance(rec.get("xvfb_pid"), int):
            raise RuntimeError("Xvfb PID record missing")
        rec["xvfb_proc_mount_ns"] = os.readlink(f'/proc/{rec["xvfb_pid"]}/ns/mnt')
        rec["xvfb_proc_stat_before_signal"] = Path(f'/proc/{rec["xvfb_pid"]}/stat').read_text()
        os.kill(rec["xvfb_pid"], signal.SIGTERM)
        rec["sigterm_sent"] = True
        try:
            rec["wrapper_exit_code"] = proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            rec["forced_kill"] = True
            os.killpg(proc.pid, signal.SIGKILL)
            rec["wrapper_exit_code"] = proc.wait()
        for line in proc.stdout.readlines():
            line = line.rstrip("\n")
            log.append(line)
            if line.startswith("XVFB_EXIT_CODE="):
                rec["xvfb_exit_code"] = int(line.partition("=")[2])
        rec["checks"]["wrapper_exit_zero"] = rec["wrapper_exit_code"] == 0
        rec["checks"]["xvfb_exit_zero"] = rec.get("xvfb_exit_code") == 0
        rec["checks"]["namespace_bound"] = rec.get("xvfb_proc_mount_ns") == rec.get("child_mount_ns") and rec.get("child_mount_ns") != rec.get("wrapper_mount_ns")
        mi = rec.get("mountinfo_line", "").split(" - ")
        rec["checks"]["private_tmpfs"] = len(mi) == 2 and mi[1].split()[:1] == ["tmpfs"] and mi[0].split()[4:5] == ["/tmp/.X11-unix"]
        rec["host_socket_after"] = socket_identity()
        rec["checks"]["host_socket_unchanged"] = rec["host_socket_before"] == rec["host_socket_after"]
        rec["checks"]["no_forced_kill"] = not rec["forced_kill"]
        rec["decision"] = "PASS" if all(rec["checks"].values()) else "STOP"
    except BaseException as exc:
        rec["errors"].append({"type":type(exc).__name__, "message":str(exc), "traceback":traceback.format_exc()})
        if proc and proc.poll() is None:
            try:
                os.killpg(proc.pid, signal.SIGTERM); proc.wait(timeout=3)
            except BaseException:
                try:
                    rec["forced_kill"] = True; os.killpg(proc.pid, signal.SIGKILL); proc.wait()
                except BaseException as e:
                    rec["errors"].append({"cleanup_error":repr(e)})
    finally:
        if proc and proc.stdout:
            log.extend(x.rstrip("\n") for x in proc.stdout.readlines())
        rec["finished_utc"] = dt.datetime.now(dt.timezone.utc).isoformat()
        log_path.write_text("\n".join(log)+"\n", encoding="utf-8")
        rec["log_sha256"] = hashlib.sha256(log_path.read_bytes()).hexdigest()
        raw_path.write_text(json.dumps(rec, indent=2, sort_keys=True)+"\n", encoding="utf-8")
    print(json.dumps({"decision":rec["decision"], "raw":str(raw_path), "log":str(log_path)}))
    return 0 if rec["decision"] == "PASS" else 2


if __name__ == "__main__":
    ap=argparse.ArgumentParser(); ap.add_argument("--out", required=True)
    sys.exit(run(ap.parse_args().out))
