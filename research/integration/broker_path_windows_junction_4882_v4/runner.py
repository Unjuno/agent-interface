"""Single native Windows NTFS allocation using the documented mount-point reparse API."""
from __future__ import annotations

import ctypes
from ctypes import wintypes
import hashlib
import json
import os
from pathlib import Path
import struct
import sys
import tempfile
import time

from path_policy import resolve_host_path

ALLOCATION = "broker-path-windows-junction-4882-20260928-04"
SOURCE_MAIN = "ceda253410ce738571580a5980a4e26dc1c3352a"
CANDIDATE_BLOB = "cdd0e3d57e08a316fc9df6b55abca8c740db070d"
IO_REPARSE_TAG_MOUNT_POINT = 0xA0000003
FSCTL_SET_REPARSE_POINT = 0x000900A4
GENERIC_WRITE = 0x40000000
OPEN_EXISTING = 3
FILE_FLAG_BACKUP_SEMANTICS = 0x02000000
FILE_FLAG_OPEN_REPARSE_POINT = 0x00200000
INVALID_HANDLE_VALUE = ctypes.c_void_p(-1).value
KERNEL32 = ctypes.WinDLL("kernel32", use_last_error=True)
KERNEL32.CreateFileW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD,
                                 wintypes.LPVOID, wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE]
KERNEL32.CreateFileW.restype = wintypes.HANDLE
KERNEL32.DeviceIoControl.argtypes = [wintypes.HANDLE, wintypes.DWORD, wintypes.LPVOID,
                                     wintypes.DWORD, wintypes.LPVOID, wintypes.DWORD,
                                     ctypes.POINTER(wintypes.DWORD), wintypes.LPVOID]
KERNEL32.DeviceIoControl.restype = wintypes.BOOL
KERNEL32.CloseHandle.argtypes = [wintypes.HANDLE]
KERNEL32.CloseHandle.restype = wintypes.BOOL

CASES = [
    ("repo_root", "/repo", "accept-root"),
    ("workspace_root", "/workspace", "accept-root"),
    ("regular_file", "/repo/input.txt", "accept-file"),
    ("in_root_junction", "/workspace/in-junction/data.txt", "accept-file"),
    ("external_junction", "/repo/external-junction/secret.txt", "reject-value-error"),
    ("lexical_traversal", "/repo/../outside/secret.txt", "reject-value-error"),
    ("encoded_traversal", "/repo/%2e%2e/outside/secret.txt", "reject-value-error"),
    ("absolute_host_path", None, "reject-value-error"),
    ("missing_path", "/repo/missing.txt", "reject-file-not-found"),
]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_freeze(package: Path, output: Path) -> None:
    freeze = json.loads((package / "FREEZE.json").read_text(encoding="utf-8"))
    if freeze.get("allocation") != ALLOCATION or freeze.get("source_main") != SOURCE_MAIN:
        raise RuntimeError("allocation/main freeze identity mismatch")
    if output.as_posix().replace("\\", "/").endswith("results/allocation-04/RAW.json") is False:
        raise RuntimeError("output is outside frozen allocation-04 path")
    for name, expected in freeze["files"].items():
        if sha(package / name) != expected:
            raise RuntimeError("frozen source hash mismatch: " + name)


def build_mount_payload(target_abs: str) -> bytes:
    substitute = ("\\??\\" + target_abs).encode("utf-16-le")
    printable = target_abs.encode("utf-16-le")
    # MountPointReparseBuffer: tag/data length/reserved, four USHORT offsets/lengths,
    # then substitute name + NUL + print name + NUL (Microsoft MS-FSCC layout).
    print_offset = len(substitute) + 2
    data_length = 8 + len(substitute) + 2 + len(printable) + 2
    return (struct.pack("<IHHHHHH", IO_REPARSE_TAG_MOUNT_POINT, data_length, 0,
                        0, len(substitute), print_offset, len(printable)) +
            substitute + b"\0\0" + printable + b"\0\0")


def set_junction(link: Path, target: Path) -> dict:
    # Empty link directory was made by this runner beneath its unique fixture.
    target_abs = str(target.resolve(strict=True))
    payload = build_mount_payload(target_abs)
    handle = KERNEL32.CreateFileW(
        str(link), GENERIC_WRITE, 0x7, None, OPEN_EXISTING,
        FILE_FLAG_BACKUP_SEMANTICS | FILE_FLAG_OPEN_REPARSE_POINT, None)
    if handle == INVALID_HANDLE_VALUE:
        error = ctypes.get_last_error()
        return {"ok": False, "stage": "CreateFileW", "winerror": error}
    try:
        buf = ctypes.create_string_buffer(payload)
        returned = wintypes.DWORD()
        ok = KERNEL32.DeviceIoControl(
            handle, FSCTL_SET_REPARSE_POINT, buf, len(payload), None, 0,
            ctypes.byref(returned), None)
        if not ok:
            error = ctypes.get_last_error()
            return {"ok": False, "stage": "FSCTL_SET_REPARSE_POINT", "winerror": error}
        return {"ok": True, "stage": "FSCTL_SET_REPARSE_POINT"}
    finally:
        KERNEL32.CloseHandle(handle)


def run(output: Path) -> int:
    package = Path(__file__).resolve().parent
    verify_freeze(package, output)
    if output.exists():
        raise FileExistsError("refusing to overwrite frozen output")
    output.parent.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter_ns()
    fixture = Path(tempfile.mkdtemp(prefix="broker-path-junction-4882-04-"))
    root, outside = fixture / "repo", fixture / "outside"
    (root / "internal").mkdir(parents=True)
    outside.mkdir()
    (root / "input.txt").write_text("inside\n", encoding="utf-8")
    (root / "internal" / "data.txt").write_text("inside junction\n", encoding="utf-8")
    (outside / "secret.txt").write_text("outside\n", encoding="utf-8")
    in_link, out_link = root / "in-junction", root / "external-junction"
    in_link.mkdir()
    out_link.mkdir()
    setup = [set_junction(in_link, root / "internal"), set_junction(out_link, outside)]
    fixture_info = {"root_relative": "repo", "outside_relative": "outside",
                    "setup": setup, "broker_subprocess_invocations": 0}
    common = {"schema": "broker_path_windows_junction_4882_v4_raw_v1", "allocation": ALLOCATION,
              "source_main": SOURCE_MAIN, "candidate_git_blob": CANDIDATE_BLOB,
              "candidate_sha256": sha(Path(__file__).with_name("path_policy.py")),
              "runner_sha256": sha(Path(__file__).resolve()), "fixture": fixture_info,
              "environment": {"python": sys.version, "platform": sys.platform, "os_name": os.name}}
    if not all(item["ok"] for item in setup):
        result = {**common, "status": "STOP_SETUP_JUNCTION_UNAVAILABLE", "rows": [],
                  "started_ns": started, "ended_ns": time.perf_counter_ns()}
        output.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"allocation": ALLOCATION, "status": result["status"], "rows": 0,
                          "fixture_id": fixture.name}))
        return 2
    rows = []
    absolute = str(outside / "secret.txt")
    for case_id, value, expected in CASES:
        value = absolute if case_id == "absolute_host_path" else value
        try:
            resolved = Path(resolve_host_path(value, root)).resolve(strict=True)
            rel = resolved.relative_to(fixture.resolve()).as_posix()
            rows.append({"case_id": case_id, "input": "<absolute-outside-secret>" if case_id == "absolute_host_path" else value,
                         "input_sha256": hashlib.sha256(value.encode()).hexdigest() if case_id == "absolute_host_path" else None,
                         "expected": expected, "outcome": "accepted", "actual_relative_to_fixture": rel,
                         "exception": None})
        except Exception as exc:
            rows.append({"case_id": case_id, "input": "<absolute-outside-secret>" if case_id == "absolute_host_path" else value,
                         "input_sha256": hashlib.sha256(value.encode()).hexdigest() if case_id == "absolute_host_path" else None,
                         "expected": expected, "outcome": "rejected", "actual_relative_to_fixture": None,
                         "exception": type(exc).__name__})
    result = {**common, "status": "RUN_COMPLETE", "rows": rows, "started_ns": started,
              "ended_ns": time.perf_counter_ns(), "cleanup": "pending independent audit"}
    output.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"allocation": ALLOCATION, "status": result["status"], "rows": len(rows),
                      "fixture_id": fixture.name}))
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: runner.py RAW.json")
    raise SystemExit(run(Path(sys.argv[1])))
