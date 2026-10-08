"""One-shot Windows native candidate-broker serve() matrix with durable junction fixtures."""
from __future__ import annotations

import ctypes
from ctypes import wintypes
import hashlib
import json
import os
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import time
from types import SimpleNamespace

import broker_under_test as broker

ALLOCATION = "broker-path-serve-windows-4882-20260928-05"
SOURCE_MAIN = "5670372e20065d3d8286105ed4ea9615952b116f"
IO_REPARSE_TAG_MOUNT_POINT = 0xA0000003
FSCTL_SET_REPARSE_POINT = 0x000900A4
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

FIELDS = ("schema", "image", "working")
KINDS = ("traversal", "encoded_traversal", "absolute", "missing",
         "external_junction", "ambiguous_separator")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_freeze(package: Path, output: Path) -> None:
    freeze = json.loads((package / "FREEZE.json").read_text(encoding="utf-8"))
    if freeze.get("allocation") != ALLOCATION or freeze.get("source_main") != SOURCE_MAIN:
        raise RuntimeError("allocation/source freeze identity mismatch")
    if not output.as_posix().replace("\\", "/").endswith("results/allocation-05/RAW.json"):
        raise RuntimeError("output is outside frozen allocation path")
    for name, expected in freeze["files"].items():
        if sha(package / name) != expected:
            raise RuntimeError("frozen source hash mismatch: " + name)
    manifest = output.parent / "FIXTURE_MANIFEST.json"
    if output.exists() or manifest.exists():
        raise FileExistsError("refusing to overwrite allocation-05 output")
    if any((output.parent / ("ipc-case-" + f"{index:02d}")).exists() for index in range(23)):
        raise FileExistsError("allocation-05 IPC scratch path already exists")


def mount_payload(target: Path) -> bytes:
    printable = str(target.resolve(strict=True)).encode("utf-16-le")
    substitute = ("\\??\\" + str(target.resolve(strict=True))).encode("utf-16-le")
    print_offset = len(substitute) + 2
    data_length = 8 + len(substitute) + 2 + len(printable) + 2
    return (struct.pack("<IHHHHHH", IO_REPARSE_TAG_MOUNT_POINT, data_length, 0,
                        0, len(substitute), print_offset, len(printable)) +
            substitute + b"\0\0" + printable + b"\0\0")


def set_junction(link: Path, target: Path) -> dict:
    payload = mount_payload(target)
    handle = KERNEL32.CreateFileW(str(link), 0x40000000, 0x7, None, 3,
                                  0x02000000 | 0x00200000, None)
    if handle == INVALID_HANDLE_VALUE:
        return {"ok": False, "stage": "CreateFileW", "winerror": ctypes.get_last_error()}
    try:
        buffer = ctypes.create_string_buffer(payload)
        returned = wintypes.DWORD()
        ok = KERNEL32.DeviceIoControl(handle, FSCTL_SET_REPARSE_POINT, buffer, len(payload),
                                      None, 0, ctypes.byref(returned), None)
        if not ok:
            return {"ok": False, "stage": "FSCTL_SET_REPARSE_POINT",
                    "winerror": ctypes.get_last_error()}
        return {"ok": True, "stage": "FSCTL_SET_REPARSE_POINT"}
    finally:
        KERNEL32.CloseHandle(handle)


def inventory(base: Path) -> list[dict]:
    rows = []
    for current, dirs, files in os.walk(base, followlinks=False):
        for name in sorted(dirs + files):
            path = Path(current) / name
            info = path.lstat()
            relative = path.relative_to(base).as_posix()
            if path.is_junction():
                rows.append({"path": relative, "kind": "junction",
                             "target_relative": path.resolve(strict=True).relative_to(base.resolve(strict=True)).as_posix(),
                             "sha256": None})
            elif path.is_symlink():
                rows.append({"path": relative, "kind": "symlink", "target_relative": os.readlink(path), "sha256": None})
            elif path.is_dir():
                rows.append({"path": relative, "kind": "directory", "target_relative": None, "sha256": None})
            elif path.is_file():
                rows.append({"path": relative, "kind": "file", "target_relative": None,
                             "sha256": sha(path)})
            else:
                rows.append({"path": relative, "kind": "other", "target_relative": None, "sha256": None})
    return sorted(rows, key=lambda row: row["path"])


def schedule(outside: Path) -> list[dict]:
    rows = [
        {"case_id": "valid_repo", "field": None, "kind": "valid_repo", "paths":
         {"schema": "/repo/internal/schema.json", "image": "/repo/internal/image.png", "working": "/repo/internal/work"}},
        {"case_id": "valid_workspace", "field": None, "kind": "valid_workspace", "paths":
         {"schema": "/workspace/internal/schema.json", "image": "/workspace/internal/image.png", "working": "/workspace/internal/work"}},
    ]
    for field, filename in (("schema", "schema.json"), ("image", "image.png"), ("working", "work")):
        paths = {"schema": "/repo/internal/schema.json", "image": "/repo/internal/image.png", "working": "/repo/internal/work"}
        paths[field] = "/repo/in-junction/" + filename if field != "working" else "/repo/in-junction/work"
        rows.append({"case_id": field + "_inside_junction", "field": field,
                     "kind": "inside_junction", "paths": paths})
    for field in FIELDS:
        for kind in KINDS:
            paths = {"schema": "/repo/internal/schema.json", "image": "/repo/internal/image.png", "working": "/repo/internal/work"}
            if kind == "traversal":
                paths[field] = "/repo/../outside/" + ("work" if field == "working" else ("image.png" if field == "image" else "schema.json"))
            elif kind == "encoded_traversal":
                paths[field] = "/repo/%252e%252e/outside/" + ("work" if field == "working" else ("image.png" if field == "image" else "schema.json"))
            elif kind == "absolute":
                name = "work" if field == "working" else ("image.png" if field == "image" else "schema.json")
                paths[field] = str(outside / name)
            elif kind == "missing":
                paths[field] = "/repo/not-present"
            elif kind == "external_junction":
                name = "work" if field == "working" else ("image.png" if field == "image" else "schema.json")
                paths[field] = "/repo/external-junction/" + name
            else:
                paths[field] = "/repo/sub\\..\\outside"
            rows.append({"case_id": field + "_" + kind, "field": field,
                         "kind": kind, "paths": paths})
    return rows


def argv_paths(args: list[str], fixture: Path) -> dict:
    def relative(value: str) -> str:
        path = Path(value).resolve(strict=True)
        return path.relative_to(fixture.resolve(strict=True)).as_posix()
    return {"schema": relative(args[args.index("--output-schema") + 1]),
            "image": relative(args[args.index("--image") + 1]),
            "working": relative(args[args.index("-C") + 1])}


def main(output: Path) -> int:
    package = Path(__file__).resolve().parent
    verify_freeze(package, output)
    output.parent.mkdir(parents=True, exist_ok=True)
    fixture = Path(tempfile.mkdtemp(prefix="broker-path-serve-windows-4882-05-"))
    root, outside, internal = fixture / "repo", fixture / "outside", fixture / "repo" / "internal"
    internal.mkdir(parents=True)
    outside.mkdir()
    for base, content in ((internal, "inside"), (outside, "outside")):
        (base / "schema.json").write_text('{"type":"object"}', encoding="utf-8")
        (base / "image.png").write_bytes((content + "-image").encode("ascii"))
        (base / "work").mkdir()
    inside_link, outside_link = root / "in-junction", root / "external-junction"
    inside_link.mkdir(); outside_link.mkdir()
    setup = [set_junction(inside_link, internal), set_junction(outside_link, outside)]
    fixture_manifest = {"schema": "broker_path_serve_windows_fixture_v1",
                        "base_relative": ".", "entries": inventory(fixture)}
    manifest_path = output.parent / "FIXTURE_MANIFEST.json"
    manifest_bytes = (json.dumps(fixture_manifest, sort_keys=True, indent=2) + "\n").encode()
    manifest_path.write_bytes(manifest_bytes)
    common = {"schema": "broker_path_serve_windows_4882_raw_v1", "allocation": ALLOCATION,
              "source_main": SOURCE_MAIN, "upstream_broker_git_blob": "5734f54f318db9ac5e96b2bed6f6bed105ac39ff",
              "fixture_id": fixture.name, "fixture_manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
              "environment": {"python": sys.version, "platform": sys.platform, "os_name": os.name},
              "junction_setup": setup, "subprocess_mocked": True}
    if not all(receipt["ok"] for receipt in setup):
        result = {**common, "status": "STOP_SETUP_JUNCTION_UNAVAILABLE", "rows": [],
                  "fixture_unchanged": None}
        output.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"status": result["status"], "rows": 0, "fixture_id": fixture.name}))
        return 2
    rows, calls = [], []
    def recorder(args, **kwargs):
        calls.append(list(args))
        return SimpleNamespace(returncode=0, stdout='{"mock":"ok"}', stderr="")
    broker.subprocess.run = recorder
    cases = schedule(outside)
    for index, case in enumerate(cases):
        request_id = f"case-{index:02d}"
        ipc = output.parent / ("ipc-" + request_id)
        ipc.mkdir()
        request_paths = dict(case["paths"])
        absolute_fields = [name for name, value in request_paths.items()
                           if not value.startswith(("/repo", "/workspace"))]
        request = {"request_id": request_id, **request_paths, "prompt": "inert path-boundary test"}
        (ipc / f"{request_id}.request.json").write_text(json.dumps(request), encoding="utf-8")
        before = len(calls)
        exit_code = broker.serve(ipc, root, once=True)
        added = calls[before:]
        receipt = json.loads((ipc / f"{request_id}.broker.json").read_text(encoding="utf-8"))
        response = (ipc / f"{request_id}.response.jsonl").read_text(encoding="utf-8")
        call_paths = argv_paths(added[0], fixture) if added else None
        row_paths = dict(request_paths)
        row_path_hashes = {key: hashlib.sha256(value.encode("utf-8")).hexdigest()
                           for key, value in request_paths.items() if key in absolute_fields}
        for key in absolute_fields:
            row_paths[key] = "<absolute-outside>"
        rows.append({"case_id": case["case_id"], "field": case["field"], "kind": case["kind"],
                     "expected": "accept" if case["kind"] in ("valid_repo", "valid_workspace", "inside_junction") else "reject",
                     "request_paths": row_paths, "absolute_input_sha256": row_path_hashes,
                     "exit_code": exit_code, "receipt": receipt, "response": response,
                     "subprocess_calls": len(added), "argv_paths_relative_to_fixture": call_paths,
                     "request_id_count": len(list(ipc.glob("*.request.json"))),
                     "broker_receipt_count": len(list(ipc.glob("*.broker.json")))})
        for child in ipc.iterdir():
            child.unlink()
        ipc.rmdir()
    after_inventory = inventory(fixture)
    result = {**common, "status": "RUN_COMPLETE", "case_count": len(rows), "rows": rows,
              "fixture_unchanged": fixture_manifest["entries"] == after_inventory,
              "fixture_after_entries": after_inventory,
              "subprocess_call_count": len(calls),
              "broker_subprocess_invocations": len(calls)}
    output.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"allocation": ALLOCATION, "status": result["status"],
                      "rows": len(rows), "mock_calls": len(calls), "fixture_id": fixture.name}))
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: runner.py RAW.json")
    raise SystemExit(main(Path(sys.argv[1])))
