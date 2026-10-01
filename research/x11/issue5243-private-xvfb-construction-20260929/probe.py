#!/usr/bin/env python3
"""One bounded private-Xvfb namespace construction probe; never sends input."""
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

SOCKET_DIR = "/tmp/.X11-unix"
DISPLAY = ":97"


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


def host_socket_identity():
    st = os.stat(SOCKET_DIR)
    return {"mode": st.st_mode & 0o7777, "inode": st.st_ino, "device": st.st_dev}


def mount_record():
    target = SOCKET_DIR
    for line in Path("/proc/self/mountinfo").read_text().splitlines():
        left, sep, right = line.partition(" - ")
        fields = left.split()
        tail = right.split()
        if sep and len(fields) > 4 and fields[4].replace("\\040", " ") == target:
            return {"target": target, "fstype": tail[0], "source": tail[1]}
    return None


def child(output):
    output = Path(output)
    before = host_socket_identity()
    mount_ns = os.stat("/proc/self/ns/mnt").st_ino
    Path(SOCKET_DIR).mkdir(mode=0o1777, parents=True, exist_ok=True)
    subprocess.run(["mount", "--make-rprivate", "/"], check=True,
                   stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    subprocess.run(["mount", "-t", "tmpfs", "-o", "mode=1777,nosuid,nodev",
                    "tmpfs", SOCKET_DIR], check=True,
                   stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    mounted = mount_record()
    socket_mode = os.stat(SOCKET_DIR).st_mode & 0o7777
    log_path = output / "xvfb.log"
    with log_path.open("wb") as log:
        server = subprocess.Popen(["Xvfb", DISPLAY, "-screen", "0", "640x480x24",
                                   "-nolisten", "tcp", "-noreset", "-ac"],
                                  stdout=log, stderr=subprocess.STDOUT,
                                  start_new_session=False)
        ready = False
        screen = None
        deadline = time.monotonic() + 8.0
        diagnostic = None
        while time.monotonic() < deadline:
            if server.poll() is not None:
                diagnostic = "Xvfb exited before readiness"
                break
            try:
                from Xlib.display import Display as XDisplay
                conn = XDisplay(DISPLAY)
                screen = [conn.screen().width_in_pixels, conn.screen().height_in_pixels]
                conn.close()
                ready = True
                break
            except Exception as exc:  # readiness polling is intentionally bounded
                diagnostic = f"{type(exc).__name__}: {exc}"
                time.sleep(0.05)
        if not ready and server.poll() is None:
            server.terminate()
        try:
            server_exit = server.wait(timeout=3.0)
        except subprocess.TimeoutExpired:
            server.kill()
            server_exit = server.wait(timeout=2.0)
            diagnostic = (diagnostic or "") + "; terminate timed out; killed"
    record = {
        "schema": "issue5243-private-xvfb-construction-v1",
        "host_mount_ns_inode": int(os.environ["HOST_MOUNT_NS_INODE"]),
        "child_mount_ns_inode": mount_ns,
        "namespace_private": mount_ns != int(os.environ["HOST_MOUNT_NS_INODE"]),
        "socket_mount": mounted,
        "socket_dir_mode": socket_mode,
        "xvfb_ready": ready,
        "display": DISPLAY if ready else None,
        "screen": screen,
        "x_socket_exists": os.path.exists(f"{SOCKET_DIR}/X97"),
        "xvfb_exit_code": server_exit,
        "diagnostic": diagnostic,
        "child_host_socket_before": before,
        "xvfb_log": "xvfb.log",
    }
    (output / "child-record.json").write_text(json.dumps(record, indent=2) + "\n")
    return 0 if ready and server_exit == 0 else 2


def run(output_arg):
    output = Path(output_arg).resolve()
    output.mkdir(parents=True, exist_ok=False)
    host_before = host_socket_identity()
    host_ns = os.stat("/proc/self/ns/mnt").st_ino
    env = os.environ.copy()
    env["HOST_MOUNT_NS_INODE"] = str(host_ns)
    command = ["unshare", "--user", "--map-root-user", "--mount", "--fork",
               sys.executable, str(Path(__file__).resolve()), "--child", str(output)]
    completed = bounded_run(command, 20.0, env=env)
    timeout = completed["timeout"]
    stdout, exit_code = completed["output"], completed["exit_code"]
    host_after = host_socket_identity()
    child_record_path = output / "child-record.json"
    child_record = json.loads(child_record_path.read_text()) if child_record_path.exists() else None
    record = {
        "schema": "issue5243-private-xvfb-host-wrapper-v1",
        "command": command,
        "timeout_seconds": 20,
        "timeout": timeout,
        "exit_code": exit_code,
        "stdout": stdout,
        "host_mount_ns_inode": host_ns,
        "host_socket_before": host_before,
        "host_socket_after": host_after,
        "host_socket_unchanged": host_before == host_after,
        "child": child_record,
    }
    (output / "result.json").write_text(json.dumps(record, indent=2) + "\n")
    return 0 if not timeout and exit_code == 0 and child_record else 2


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--child":
        raise SystemExit(child(sys.argv[2]))
    if len(sys.argv) == 2:
        raise SystemExit(run(sys.argv[1]))
    raise SystemExit("usage: probe.py OUTPUT_DIR")
