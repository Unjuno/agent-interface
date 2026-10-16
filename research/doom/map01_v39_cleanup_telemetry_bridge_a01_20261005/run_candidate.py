"""One-shot fake-display composition of V13 cleanup with the V39 bridge."""
from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
import platform
import sys
import time
import types
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SOURCE = HERE / "SOURCE"
OUT = HERE / "results" / "a01"
FREEZE = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))
V12_DIR = ROOT / "research/doom/map01_attack_onset_phase_allocation_02_v1/dependencies/v12"
sys.path[:0] = [str(V12_DIR), str(ROOT / "research/live_control")]


def install_import_stubs() -> None:
    xlib = types.ModuleType("Xlib")
    x = types.SimpleNamespace(KeyPress=2, KeyRelease=3, ButtonRelease=5,
                              Button1Mask=256, AnyPropertyType=0, IsViewable=2)
    xk = types.SimpleNamespace(string_to_keysym=lambda value: 1)
    error = types.SimpleNamespace(BadWindow=type("BadWindow", (Exception,), {}),
                                  BadDrawable=type("BadDrawable", (Exception,), {}))
    display = types.ModuleType("Xlib.display")
    display.Display = lambda name: None
    xtest = types.ModuleType("Xlib.ext.xtest")
    xtest.fake_input = lambda *args, **kwargs: None
    ext = types.ModuleType("Xlib.ext")
    ext.xtest = xtest
    xlib.X, xlib.XK, xlib.error, xlib.display = x, xk, error, display
    sys.modules.update({"Xlib": xlib, "Xlib.display": display,
                        "Xlib.ext": ext, "Xlib.ext.xtest": xtest})
    pil = types.ModuleType("PIL")
    pil.ImageGrab = types.SimpleNamespace(grab=lambda **kwargs: None)
    sys.modules["PIL"] = pil


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load frozen module: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def extract_function(path: Path, owner: str | None, name: str):
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    if owner is None:
        node = next(n for n in tree.body
                    if isinstance(n, ast.FunctionDef) and n.name == name)
    else:
        cls = next(n for n in tree.body
                   if isinstance(n, ast.ClassDef) and n.name == owner)
        node = next(n for n in cls.body
                    if isinstance(n, ast.FunctionDef) and n.name == name)
    namespace = {"hashlib": hashlib}
    exec(compile(ast.Module(body=[node], type_ignores=[]), str(path), "exec"), namespace)
    return namespace[name], ast.get_source_segment(source, node)


def main() -> None:
    if OUT.exists():
        raise SystemExit("STOP: candidate output already exists")
    if platform.python_version() != FREEZE["python_version"]:
        raise SystemExit("STOP: Python version differs from freeze")
    for name, expected in FREEZE["sources"].items():
        actual = hashlib.sha256((SOURCE / name).read_bytes()).hexdigest()
        if actual != expected:
            raise SystemExit(f"STOP: frozen source mismatch: {name}")
    bridge_raw, bridge_text = extract_function(SOURCE / "bridge.py", "Backend", "raw")
    projector, projector_text = extract_function(
        SOURCE / "controller_v39_projector.py", None, "input_edge_receipts")
    if hashlib.sha256(bridge_text.encode()).hexdigest() != FREEZE["bridge_raw_function_sha256"]:
        raise SystemExit("STOP: bridge raw function identity mismatch")
    if hashlib.sha256(projector_text.encode()).hexdigest() != FREEZE["projector_function_sha256"]:
        raise SystemExit("STOP: projector function identity mismatch")

    install_import_stubs()
    harness_module = load_module("input_owner_v12_harness", V12_DIR / "test_input_owner_v12.py")
    owner_module = harness_module.load(
        "input_owner_v13_candidate", SOURCE / "input_owner_v13.py")
    harness = harness_module.Harness(owner_module)
    keysym = owner_module.XK
    old_keysym = keysym.string_to_keysym
    keysym.string_to_keysym = lambda value: 1 if value == "F8" else 0
    harness.d.keysym_to_keycode = lambda sym: 74 if sym == 1 else 0
    lease = harness_module.Lease(intent="cleanup-bridge-a01")
    emitted: list[dict] = []
    backend = types.SimpleNamespace(
        owner=harness.owner, lease=lease, held=set(),
        _input_event_context=(FREEZE["run_id"], 0), emit=emitted.append)
    try:
        bridge_raw(backend, "F8", True)
        lease.cancel.set()
        cleanup = None
        for _ in range(1000):
            cleanup = next((row for row in harness.owner.records
                            if row.get("event") == "owner_release"
                            and row.get("reason") == "cancelled"), None)
            if cleanup is not None:
                break
            time.sleep(0.001)
        if cleanup is None:
            raise RuntimeError("STOP: owner-thread cancellation cleanup did not arrive")
        bridge_raw(backend, "F8", False)
        projected = projector(emitted)
        OUT.mkdir(parents=True)
        raw = {
            "run_id": FREEZE["run_id"],
            "bridge_emitted_events": emitted,
            "owner_cleanup_record": cleanup,
            "fake_physical_keys_after_cleanup": sorted(harness.d.physical),
            "projected_receipts": projected,
        }
        (OUT / "RAW.json").write_text(
            json.dumps(raw, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        cleanup_measurements = cleanup.get("per_key_release_measurements", [])
        result = {
            "run_id": FREEZE["run_id"],
            "status": "PENDING_INDEPENDENT_AUDIT",
            "owner_cleanup_verified": cleanup.get("verified") is True,
            "owner_cleanup_measurement_count": len(cleanup_measurements),
            "owner_cleanup_key": cleanup_measurements[0].get("key") if cleanup_measurements else None,
            "owner_cleanup_classification": cleanup_measurements[0].get("classification") if cleanup_measurements else None,
            "owner_cleanup_actuation_id": cleanup_measurements[0].get("actuation_id") if cleanup_measurements else None,
            "bridge_event_types": [row.get("event") for row in emitted],
            "bridge_emitted_release_adapter_edge": (
                emitted[-1].get("physical_key_measurement", {}).get("adapter_edge")
                if emitted else None),
            "projected_receipts": projected,
            "fake_physical_keys_after_cleanup": sorted(harness.d.physical),
            "authority_granted": False,
            "application_effect_observed": False,
            "scope": FREEZE["scope"],
        }
        (OUT / "RESULT.json").write_text(
            json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps(result, sort_keys=True))
    finally:
        harness.close()
        keysym.string_to_keysym = old_keysym


if __name__ == "__main__":
    main()
