"""Finite, input-free execution of four source-pinned admission contracts."""
from __future__ import annotations
from copy import deepcopy
from dataclasses import asdict
import gzip
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
ARMS = ("main", "enum", "scalar", "combined")
MANIFEST_NAMES = (
    "linux", "windows", "macos", "os_list", "os_object", "os_integer",
    "os_boolean", "os_unknown", "state_list", "state_object", "state_integer",
    "state_boolean", "state_unknown", "frame_list", "frame_object", "frame_integer",
    "frame_boolean", "frame_unknown", "frame_duplicate", "permission", "unknown",
    "unsupported", "frame_mismatch", "permission_and_release_unsupported",
)
NOW = (9, 10, 11, True, 10.0)
OBS = (1, 2, True, 1.0, None)
BIND = (1, 2, True, 1.0, {})

def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()

def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()

def program(index):
    value = {"schema": "agent-interface/program-v1", "program_id": "composition",
             "source": {"observation_seq": 1, "binding_revision": 1},
             "authority": {"lease_id": "fixture", "expires_at_ns": 10},
             "terminal": {"release_all_required": True},
             "ops": [{"op": "pointer_move", "frame": "window_client", "x": 0, "y": 0},
                     {"op": "observe", "frame": "window_client", "x": 0, "y": 0, "w": 1, "h": 1},
                     {"op": "release_all"}]}
    if index == 1:
        value["ops"].pop()
    elif index == 2:
        value["source"]["observation_seq"] = True
    return value

def manifest(name):
    value = {"schema": "agent-interface/backend-v1", "backend_id": "fixture",
             "platform": {"os": "linux", "backend": "inert"},
             "capabilities": {cap: {"state": "supported", "detail": ""} for cap in
                              ("capture.frame", "display.geometry", "input.pointer", "input.release_all")},
             "coordinate_frames": ["window_client"], "clock": {"unit": "ns", "monotonic": True},
             "permissions": []}
    objects = {"list": [], "object": {}, "integer": 0, "boolean": False, "unknown": "invalid"}
    if name in ("linux", "windows", "macos"):
        value["platform"]["os"] = name
    elif name.startswith("os_"):
        value["platform"]["os"] = objects[name[3:]]
    elif name.startswith("state_"):
        value["capabilities"]["input.pointer"]["state"] = objects[name[6:]]
    elif name == "frame_duplicate":
        value["coordinate_frames"].append("window_client")
    elif name.startswith("frame_") and name != "frame_mismatch":
        value["coordinate_frames"] = [objects[name[6:]]]
    elif name == "frame_mismatch":
        value["coordinate_frames"] = ["screen_physical_px"]
    else:
        state = {"permission": "permission_required", "unknown": "unknown", "unsupported": "unsupported",
                 "permission_and_release_unsupported": "permission_required"}[name]
        value["capabilities"]["input.pointer"]["state"] = state
        if name == "permission_and_release_unsupported":
            value["capabilities"]["input.release_all"]["state"] = "unsupported"
    return value

def cases():
    for mi, pi, ni, oi, bi in itertools.product(range(24), range(3), range(5), range(5), range(5)):
        yield {"id": f"m{mi:02d}-p{pi}-n{ni}-o{oi}-b{bi}", "manifest_name": MANIFEST_NAMES[mi],
               "program": program(pi), "manifest": manifest(MANIFEST_NAMES[mi]),
               "evidence": {"now_ns": NOW[ni], "current_observation_seq": OBS[oi],
                            "current_binding_revision": BIND[bi]}}

def load_source(arm):
    name = "composition_contract_" + arm
    spec = importlib.util.spec_from_file_location(name, ROOT / "sources" / (arm + ".py"))
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module

def evaluate(module, case):
    value = deepcopy(case)
    before = digest(value)
    try:
        result = asdict(module.admit_program(value["program"], value["manifest"], **value["evidence"]))
        result["required_capabilities"] = list(result["required_capabilities"])
    except Exception as error:
        result = {"exception": type(error).__name__, "message": str(error)}
    return {"id": case["id"], "input_sha256": before, "output": result,
            "unchanged": before == digest(value)}

def write_gzip(path, values):
    with path.open("xb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as out:
            for value in values:
                out.write(canonical(value) + b"\n")

def main():
    freeze = json.loads((ROOT / "FREEZE.json").read_bytes())
    for name, expected in freeze["source_sha256"].items():
        if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != expected:
            raise RuntimeError("frozen source mismatch: " + name)
    output = ROOT / "raw"
    output.mkdir(exist_ok=False)
    write_gzip(output / "cases.jsonl.gz", cases())
    modules = {arm: load_source(arm) for arm in ARMS}
    def rows():
        for case in cases():
            for arm in ARMS:
                yield {"arm": arm, **evaluate(modules[arm], case)}
    write_gzip(output / "results.jsonl.gz", rows())
    receipt = {"schema": "core-composition-raw-v1", "cases": 9000, "rows": 36000,
               "arms": list(ARMS), "raw_sha256": {path.name: hashlib.sha256(path.read_bytes()).hexdigest()
                                                   for path in output.iterdir()},
               "python": sys.version, "backend_invocations": 0}
    (output / "RECEIPT.json").write_bytes(json.dumps(receipt, indent=2).encode() + b"\n")
    print(json.dumps(receipt, indent=2))

if __name__ == "__main__":
    main()
