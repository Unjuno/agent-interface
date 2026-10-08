"""One-shot InputOwner/XQueryKeymap exercise against private real Xvfb."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import select
import stat
import subprocess
import sys
import threading
import time
import types

ROOT = Path(__file__).resolve().parent
FREEZE = ROOT / "FREEZE.json"
CASES = ROOT / "cases.json"
SOURCE = ROOT / "dependencies" / "input_owner_v11.py"
OUT = ROOT / "results" / "t3-01" / "raw.json"


class Lease:
    intent_token = "xvfb-t3-repeat-w"

    def __init__(self, expected_focus):
        self.expected_focus = expected_focus
        self.deadline = time.perf_counter_ns() + 10_000_000_000
        self.cancel = threading.Event()

    def check(self):
        if self.cancel.is_set() or time.perf_counter_ns() >= self.deadline:
            raise RuntimeError("T3 lease expired")


def mounted_tmpfs(path):
    for line in Path("/proc/self/mountinfo").read_text(encoding="utf-8").splitlines():
        left, separator, right = line.partition(" - ")
        if separator and left.split()[4] == path:
            return right.split()[0] == "tmpfs"
    return False


def verify_freeze(freeze, cases_bytes):
    source_hashes = freeze["sha256"]
    for name, path in {
        "candidate.py": Path(__file__),
        "cases.json": CASES,
        "dependencies/input_owner_v11.py": SOURCE,
    }.items():
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != source_hashes[name]:
            raise RuntimeError(f"frozen source hash mismatch: {name}")
    if hashlib.sha256(cases_bytes).hexdigest() != freeze["sha256"]["cases.json"]:
        raise RuntimeError("case hash mismatch")


def load_owner(display_name):
    executor = types.ModuleType("executor_v3")
    executor.Cancelled = type("Cancelled", (Exception,), {})
    executor.DecisionRequired = type("DecisionRequired", (Exception,), {})
    sys.modules["executor_v3"] = executor
    spec = importlib.util.spec_from_file_location("t3_instrumented_input_owner", SOURCE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.InputOwner(display_name)


def main():
    freeze_bytes = FREEZE.read_bytes()
    freeze = json.loads(freeze_bytes.decode("utf-8"))
    cases_bytes = CASES.read_bytes()
    cases = json.loads(cases_bytes.decode("utf-8"))
    verify_freeze(freeze, cases_bytes)

    socket_dir = Path("/tmp/.X11-unix")
    socket_mode = stat.S_IMODE(socket_dir.stat().st_mode)
    tmpfs = mounted_tmpfs("/tmp")
    if not tmpfs or socket_mode != 0o1777:
        raise RuntimeError("private tmpfs/socket-directory boundary is absent")

    auth_path = Path("/tmp") / f"xvfb-t3-{os.getpid()}.Xauthority"
    auth_path.write_bytes(b"")
    env = dict(os.environ, XAUTHORITY=str(auth_path))
    xvfb_args = ["Xvfb", "-displayfd", "1", "-screen", "0", "640x480x24",
                 "-nolisten", "tcp", "-ac"]
    proc = subprocess.Popen(xvfb_args, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, text=True, env=env)
    owner = None
    raw = None
    try:
        ready, _, _ = select.select([proc.stdout], [], [], 5)
        if not ready:
            raise RuntimeError("private Xvfb startup timeout")
        display_number = proc.stdout.readline().strip()
        if not display_number.isdecimal():
            raise RuntimeError("private Xvfb returned invalid display number")
        display_name = ":" + display_number

        from Xlib import display
        probe = display.Display(display_name)
        focus = probe.get_input_focus().focus
        expected_focus = focus.id if hasattr(focus, "id") else focus
        keycode_w = probe.keysym_to_keycode(ord("W"))
        probe.close()
        if keycode_w != cases["expected_keycode"]:
            raise RuntimeError("private Xvfb keymap differs from frozen W keycode")

        owner = load_owner(display_name)
        lease = Lease(expected_focus)
        admissions = [owner.call("down", lease, cases["expected_key"])]
        owner.call("up", lease, cases["expected_key"])
        admissions.append(owner.call("down", lease, cases["expected_key"]))
        owner.call("up", lease, cases["expected_key"])
        owner.close()
        if owner.thread.is_alive():
            raise RuntimeError("InputOwner thread did not stop")

        raw = {
            "schema": "map01-owner-occurrence-xvfb-raw-v1",
            "allocation_id": cases["allocation_id"],
            "main_sha": cases["main_sha"],
            "upstream_owner_commit": cases["upstream_owner_commit"],
            "upstream_owner_blob_sha1": cases["upstream_owner_blob_sha1"],
            "cases_sha256": hashlib.sha256(cases_bytes).hexdigest(),
            "instrumented_owner_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
            "candidate_invocations": 1,
            "retries": 0,
            "namespace_tmpfs": tmpfs,
            "socket_directory_mode": oct(socket_mode),
            "xvfb_argv": xvfb_args,
            "xvfb_tcp_enabled": False,
            "xvfb_display_number": int(display_number),
            "xvfb_pid": proc.pid,
            "xvfb_displayfd_ready": True,
            "xvfb_keycode_w": keycode_w,
            "admissions": admissions,
            "owner_id": owner.owner_id,
            "owner_records": owner.records,
            "scope": "isolated patched InputOwner against actual private Xvfb server via XTEST",
        }
    finally:
        if owner is not None and not owner.closed:
            owner.close()
        if proc.poll() is None:
            proc.terminate()
            proc.wait(timeout=3)
        stderr = proc.stderr.read() if proc.stderr else ""
        exit_code = proc.poll()
        if raw is not None:
            display_socket = Path("/tmp/.X11-unix") / ("X" + str(raw["xvfb_display_number"]))
            lock_file = Path("/tmp") / (".X" + str(raw["xvfb_display_number"]) + "-lock")
            raw["xvfb_exit_code_after_controlled_terminate"] = exit_code
            raw["xvfb_socket_removed"] = not display_socket.exists()
            raw["xvfb_lock_removed"] = not lock_file.exists()
            raw["xvfb_stderr_fatal"] = "Fatal server error" in stderr
            raw["xvfb_stderr"] = stderr
        if proc.stdout:
            proc.stdout.close()
        if proc.stderr:
            proc.stderr.close()
        auth_path.unlink(missing_ok=True)

    if raw is None:
        raise RuntimeError("candidate ended before producing a complete record")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(raw, sort_keys=True, indent=2) + "\n")
    print(json.dumps(raw, sort_keys=True))


if __name__ == "__main__":
    main()
