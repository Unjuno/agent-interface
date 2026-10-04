from __future__ import annotations

import hashlib
import importlib.util
import json
import runpy
import sys
import time
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.core_v1 import compiled_gui
from runtime.guarded_x11_v1.handles import TargetHandleStore


def _module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_a03 = runpy.run_path(str(HERE / "source" / "a03_candidate.py"),
                      run_name="pinned_a03_source")
_adapter = _module(HERE / "source" / "compiled_form_adapter_v2.py",
                   "pinned_compiled_form_adapter_v2")


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def _binding(width, height):
    return {"focus": 101, "surface": 202, "geometry": [0, 0, width, height]}


class SyntheticClock:
    def __init__(self):
        self.value = 2_100_000

    def __call__(self):
        self.value += 1_000
        return self.value


def _mint_handles(case_a03, case_a02, image, store):
    field_point = case_a03["field_point"]
    box = _a03["bounded_box"](case_a03, image, _a03["PAD"])
    initial = {"sequence": 1, "capture_ns": 2_000_000,
               "pointer_binding": _binding(*image.size)}
    field = store.mint("field", "window_content", box, initial, image,
                       2_001_000, ttl_ms=300_000, freshness_ms=1_500,
                       search_radius=0,
                       allowed_transformations=("window_translation",))
    sx, sy = case_a02["submit_point"]
    submit_box = [sx - 12, sy - 12, 24, 24]
    submit = store.mint("submit", "window_content", submit_box, initial,
                        image, 2_001_000, ttl_ms=300_000, freshness_ms=1_500,
                        search_radius=0,
                        allowed_transformations=("window_translation",))
    return {
        "field": (field["handle"], [field_point[0] - box[0],
                                    field_point[1] - box[1]], box),
        "submit": (submit["handle"], [12, 12], submit_box),
    }


def _replace(image, box):
    x, y, width, height = box
    ImageDraw.Draw(image).rectangle((x, y, x + width - 1, y + height - 1),
                                    fill=(255, 255, 255))


def run_scenario(case_a03, case_a02, mode):
    screenshot = HERE / "inputs" / (Path(case_a02["image_file"]).name)
    with Image.open(screenshot) as source:
        image = source.convert("RGB")
    store = TargetHandleStore("offline-compose-a01",
                              id_factory=iter(("private-field", "private-submit")).__next__)
    handles = _mint_handles(case_a03, case_a02, image, store)
    field_id, field_offset, field_box = handles["field"]
    submit_id, submit_offset, submit_box = handles["submit"]
    clock = SyntheticClock()
    simulator = {"typed": False, "submitted": False}
    journal = []
    executions = []
    admission_checks = []
    sequence = 0

    def resolve(alias, offset, obs, at_ns):
        result = store.resolve_point(alias, offset, obs, image, at_ns,
                                     session_scope="offline-compose-a01")
        return result

    def observe(_request):
        nonlocal sequence
        sequence += 1
        captured_ns = clock()
        handle_obs = {"sequence": sequence, "capture_ns": captured_ns,
                      "pointer_binding": _binding(*image.size)}
        field = resolve(field_id, field_offset, handle_obs, clock())
        submit = resolve(submit_id, submit_offset, handle_obs, clock())
        predicates = {
            "field_pixels_changed": False,
            "field_value_matches_task": simulator["typed"],
            "field_target_present": field["eligible"],
            "submit_target_present": submit["eligible"],
            "submission_pixels_changed": simulator["submitted"],
        }
        evidence = image.tobytes() + json.dumps(
            predicates, sort_keys=True, separators=(",", ":")).encode()
        return {
            "sequence": sequence, "captured_ns": captured_ns,
            "surface": "retained-fixture-surface", "predicates": predicates,
            "evidence_ref": f"test-double/task-{case_a02['task']}/observation-{sequence}",
            "evidence_digest": _sha(evidence),
        }

    def admit(request):
        action = request["action"]
        if mode == "field_race" and action == "enter_token":
            _replace(image, field_box)
        if mode == "submit_race" and action == "submit_form":
            _replace(image, submit_box)
        obs = request["observation"]
        handle_obs = {"sequence": obs["sequence"],
                      "capture_ns": obs["captured_ns"],
                      "pointer_binding": _binding(*image.size)}
        alias = request["symbol"]["target_reference"]
        target = handles[alias]
        result = resolve(target[0], target[1], handle_obs, clock())
        admission_checks.append({"action": action,
                                 "pixel_resolution_status": result["status"],
                                 "eligible": result["eligible"]})
        if not result["eligible"]:
            status = {"MISSING": "missing", "STALE": "stale",
                      "SCOPE_MISMATCH": "association_changed"}.get(
                          result["status"], "authority_unavailable")
            return {"eligible": False, "status": status,
                    "authorization": "", "expected_sequence": obs["sequence"],
                    "valid_until_ns": 0}
        return {"eligible": True, "status": "revalidated",
                "authorization": f"synthetic-admission-{action}-{obs['sequence']}",
                "expected_sequence": obs["sequence"],
                "valid_until_ns": result["valid_until_ns"]}

    def execute(request):
        executions.append(request["operation"])
        if request["operation"] == "enter_exact_token":
            simulator["typed"] = True
        elif request["operation"] == "activate_submit":
            simulator["submitted"] = True
        return {"status": "completed", "action_id": f"synthetic-action-{len(executions)}",
                "effect_ref": f"synthetic-effect-{len(executions)}",
                "release": {"verified": True, "keys_down": [], "buttons_down": []}}

    def verify_effect(request):
        return {"status": "succeeded",
                "evidence_ref": f"test-double/effect/{request['action']}"}

    receipt = compiled_gui.run(
        _adapter.compile_form_method(
            interface_id=f"composition-task-{case_a02['task']}-{mode}",
            session_scope="offline-compose-a01",
            surface="retained-fixture-surface",
            field_handle="field", submit_handle="submit",
            method_contract=_adapter.EXPECTED_METHOD_CONTRACT),
        {"observe": observe, "admit": admit, "execute": execute,
         "verify_effect": verify_effect, "cancelled": lambda: False,
         "journal": journal.append},
        clock=clock)
    return {
        "task": case_a02["task"], "mode": mode,
        "field_box": field_box, "submit_box": submit_box,
        "outcome": receipt["outcome"], "reason": receipt["reason"],
        "completed_transitions": receipt["completed_transitions"],
        "execute_operations": executions,
        "admission_checks": admission_checks,
        "release_verified_all_executions": all(
            row.get("release_verified") is True
            for row in receipt["critical_events"]
            if row.get("event") == "action_terminal"),
        "receipt": receipt,
    }


def main():
    a02 = json.loads((HERE / "inputs" / "A02_INPUTS.json").read_text())
    a03 = json.loads((HERE / "inputs" / "A03_INPUTS.json").read_text())
    rows = []
    for case_a03, case_a02 in zip(a03["cases"], a02["tasks"], strict=True):
        rows.extend(run_scenario(case_a03, case_a02, mode) for mode in
                    ("baseline", "field_race", "submit_race"))
    return {
        "schema": "compiled-handle-graph-composition-candidate-v1",
        "source_main": "41df296f3ce4d03c801c998d38f6e537e64a83ab",
        "case_count": len(a02["tasks"]), "scenario_count": len(rows),
        "adapter_calls_are_test_doubles": True,
        "live_gui_calls": 0, "model_calls": 0, "input_dispatch_calls": 0,
        "rows": rows,
    }


if __name__ == "__main__":
    print(json.dumps(main(), sort_keys=True, indent=2))
