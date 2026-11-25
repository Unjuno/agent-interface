"""WSL owner and Windows Job launcher for the Golden native App Server."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

if __package__:
    from .native_preflight_job_v1 import JOB_KILL_EXIT_CODE, LeaseMonitor, LeaseReader, LeaseWriter, run_in_job, valid_hex
else:
    from native_preflight_job_v1 import JOB_KILL_EXIT_CODE, LeaseMonitor, LeaseReader, LeaseWriter, run_in_job, valid_hex


APP_SERVER_JOB_RECEIPT = "windows-app-server-job.json"
APP_SERVER_JOB_START = "windows-app-server-start.json"
STOP_FILE = "windows-app-server-stop.txt"
APP_SERVER_LIFETIME = 600


def own_app_server(root, nonce, argv, *, timeout=APP_SERVER_LIFETIME):
    lease = LeaseReader(root, nonce)
    lease.await_owner()
    stop = root / STOP_FILE

    def stop_requested():
        try:
            return stop.read_text(encoding="ascii").strip() == nonce
        except OSError:
            return False

    with LeaseMonitor(lease, stop_requested) as monitor:
        result = run_in_job(argv, (sys.stdin, sys.stdout, sys.stderr), timeout=timeout,
                            owner_lost=monitor.retired)
    if result["status"] == "OWNER_LOST" and monitor.requested_stop.is_set():
        if result["exit_code"] == JOB_KILL_EXIT_CODE and result["termination_requested"]:
            result["status"] = "STOP_REQUESTED"
        elif result["exit_code"] == 0 and not result["termination_requested"]:
            result["status"] = "COMPLETED"
    result.update(schema="native-app-server-windows-job-v1", run_nonce=nonce,
                  owner_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    with (root / APP_SERVER_JOB_RECEIPT).open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(result, stream, indent=2)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    return 0 if retired_app_server(result, nonce, result["owner_sha256"]) else 124


def retired_app_server(receipt, nonce, owner_sha256):
    return (type(receipt) is dict and receipt.get("schema") == "native-app-server-windows-job-v1"
            and receipt.get("ownership") == "create-process-job-list"
            and valid_hex(nonce, 32) and valid_hex(owner_sha256, 64)
            and receipt.get("run_nonce") == nonce and receipt.get("owner_sha256") == owner_sha256
            and receipt.get("status") in ("COMPLETED", "STOP_REQUESTED")
            and type(receipt.get("exit_code")) is int
            and (receipt["status"] == "COMPLETED" and receipt["exit_code"] == 0
                 or receipt["status"] == "STOP_REQUESTED" and receipt["exit_code"] == JOB_KILL_EXIT_CODE
                 and receipt.get("termination_requested") is True)
            and receipt.get("job_empty") is True
            and type(receipt.get("active_processes")) is int and receipt["active_processes"] == 0
            and type(receipt.get("total_processes")) is int and receipt["total_processes"] >= 1)


class WindowsAppServerOwner:
    def __init__(self, windows_python, convert, session_root):
        self.windows_python = windows_python
        self.convert = convert
        self.root = session_root
        self.lease = LeaseWriter(self.root)
        self.hash = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
        self.reference = None

    def launch(self, command, options, journal):
        if "env" not in options:
            raise ValueError("native App Server job requires WSL Codex environment")
        owner = self.convert(Path(__file__).resolve())
        root = self.convert(self.root.resolve())
        executable = self.convert(Path(command[0]).resolve())
        self.reference = {"run_nonce": self.lease.nonce, "owner_sha256": self.hash,
                          "windows_executable": executable}
        with (self.root / APP_SERVER_JOB_START).open("x", encoding="utf-8") as stream:
            json.dump(self.reference, stream)
        journal("windows_job_owner", self.reference)
        self.lease.__enter__()
        try:
            argv = [str(self.windows_python), "-B", owner, root, self.lease.nonce,
                    executable, *command[1:]]
            return subprocess.Popen(argv, **options)
        except BaseException:
            self.lease.__exit__()
            raise

    def retire(self, process, timeout):
        try:
            (self.root / STOP_FILE).write_text(self.lease.nonce + "\n", encoding="ascii")
            if process.wait(timeout=timeout) != 0:
                raise RuntimeError("Windows App Server job did not retire normally")
            receipt = json.loads((self.root / APP_SERVER_JOB_RECEIPT).read_bytes())
            if not retired_app_server(receipt, self.lease.nonce, self.hash):
                raise RuntimeError("Windows App Server job retirement is unverified")
        finally:
            self.lease.__exit__()


if __name__ == "__main__":
    destination, nonce, executable, *arguments = sys.argv[1:]
    path = Path(executable)
    if not path.is_absolute() or path.suffix.lower() != ".exe" or arguments[:2] != ["app-server", "--stdio"]:
        raise SystemExit("absolute Windows App Server executable and stdio arguments required")
    raise SystemExit(own_app_server(Path(destination), nonce, [executable, *arguments]))
