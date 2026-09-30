#!/usr/bin/env python3
"""Single private Xvfb reset/terminate construction probe; never sends input."""
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

SOCKET_DIR = "/tmp/.X11-unix"
DISPLAY = ":98"


def bounded_run(command, timeout, env=None):
    proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            text=True, start_new_session=True, env=env)
    try:
        output, _ = proc.communicate(timeout=timeout)
        return {"exit_code": proc.returncode, "timeout": False, "output": output}
    except subprocess.TimeoutExpired:
        os.killpg(proc.pid, signal.SIGTERM)
        try:
            output, _ = proc.communicate(timeout=2.0)
        except subprocess.TimeoutExpired:
            os.killpg(proc.pid, signal.SIGKILL)
            output, _ = proc.communicate(timeout=2.0)
        return {"exit_code": 124, "timeout": True, "output": output}


def socket_identity():
    st = os.stat(SOCKET_DIR)
    return {"mode": st.st_mode & 0o7777, "inode": st.st_ino, "device": st.st_dev}


def mount_record():
    for line in Path("/proc/self/mountinfo").read_text().splitlines():
        left, sep, right = line.partition(" - ")
        fields, tail = left.split(), right.split()
        if sep and len(fields) > 4 and fields[4].replace("\\040", " ") == SOCKET_DIR:
            return {"target": SOCKET_DIR, "fstype": tail[0], "source": tail[1]}
    return None


def child(output):
    output = Path(output)
    host_meta = socket_identity()
    child_ns = os.stat("/proc/self/ns/mnt").st_ino
    host_ns = int(os.environ["HOST_MOUNT_NS_INODE"])
    subprocess.run(["mount", "--make-rprivate", "/"], check=True,
                   stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    subprocess.run(["mount", "-t", "tmpfs", "-o", "mode=1777,nosuid,nodev",
                    "tmpfs", SOCKET_DIR], check=True,
                   stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    mounted = mount_record()
    dir_mode = os.stat(SOCKET_DIR).st_mode & 0o7777
    log_path = output / "xvfb.log"
    with log_path.open("wb") as log:
        server = subprocess.Popen(["Xvfb", DISPLAY, "-screen", "0", "640x480x24",
                                   "-nolisten", "tcp", "-terminate", "-ac"],
                                  stdout=log, stderr=subprocess.STDOUT,
                                  start_new_session=False)
        ready = False
        screen = None
        x_socket_exists = False
        diagnostic = None
        deadline = time.monotonic() + 8.0
        while time.monotonic() < deadline:
            if server.poll() is not None:
                diagnostic = "Xvfb exited before the Xlib query"
                break
            try:
                from Xlib.display import Display as XDisplay
                conn = XDisplay(DISPLAY)
                screen = [conn.screen().width_in_pixels, conn.screen().height_in_pixels]
                x_socket_exists = os.path.exists(f"{SOCKET_DIR}/X98")
                conn.close()  # Last client disconnect asks -terminate to exit naturally.
                ready = True
                break
            except Exception as exc:
                diagnostic = f"{type(exc).__name__}: {exc}"
                time.sleep(0.05)
        natural_exit = False
        try:
            server_exit = server.wait(timeout=3.0)
            natural_exit = ready and server_exit == 0
        except subprocess.TimeoutExpired:
            diagnostic = (diagnostic or "") + "; natural reset exit timed out"
            server.terminate()
            try:
                server_exit = server.wait(timeout=2.0)
            except subprocess.TimeoutExpired:
                server.kill()
                server_exit = server.wait(timeout=2.0)
    record = {
        "schema": "issue5243-xvfb-reset-child-v1",
        "host_mount_ns_inode": host_ns,
        "child_mount_ns_inode": child_ns,
        "namespace_private": child_ns != host_ns,
        "socket_mount": mounted,
        "socket_dir_mode": dir_mode,
        "xvfb_args": [":98", "-screen", "0", "640x480x24", "-nolisten", "tcp", "-terminate", "-ac"],
        "noreset_used": False,
        "xvfb_ready": ready,
        "display": DISPLAY if ready else None,
        "screen": screen,
        "x_socket_exists": x_socket_exists,
        "natural_exit": natural_exit,
        "xvfb_exit_code": server_exit,
        "diagnostic": diagnostic,
        "host_socket_before": host_meta,
        "xvfb_log": "xvfb.log",
    }
    (output / "child-record.json").write_text(json.dumps(record, indent=2) + "\n")
    return 0 if natural_exit else 2


def run(output_arg):
    output = Path(output_arg).resolve()
    output.mkdir(parents=True, exist_ok=False)
    before = socket_identity()
    host_ns = os.stat("/proc/self/ns/mnt").st_ino
    env = os.environ.copy()
    env["HOST_MOUNT_NS_INODE"] = str(host_ns)
    command = ["unshare", "--user", "--map-root-user", "--mount", "--fork",
               sys.executable, str(Path(__file__).resolve()), "--child", str(output)]
    completed = bounded_run(command, 20.0, env=env)
    after = socket_identity()
    child_path = output / "child-record.json"
    child_data = json.loads(child_path.read_text()) if child_path.exists() else None
    result = {
        "schema": "issue5243-xvfb-reset-host-v1",
        "command": command,
        "timeout_seconds": 20,
        "timeout": completed["timeout"],
        "exit_code": completed["exit_code"],
        "stdout": completed["output"],
        "host_mount_ns_inode": host_ns,
        "host_socket_before": before,
        "host_socket_after": after,
        "host_socket_unchanged": before == after,
        "child": child_data,
    }
    (output / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    return 0 if not completed["timeout"] and completed["exit_code"] == 0 and child_data else 2


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--child":
        raise SystemExit(child(sys.argv[2]))
    if len(sys.argv) == 2:
        raise SystemExit(run(sys.argv[1]))
    raise SystemExit("usage: probe.py OUTPUT_DIR")
