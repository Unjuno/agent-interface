from __future__ import annotations

import json
import sys
import subprocess
import time
import types
from pathlib import Path

from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
PACKAGE = HERE.parent
REPO = HERE.parents[3]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from runtime.guarded_x11_v1.handles import TargetHandleStore


SIZE_BY_TASK = {2: [64, 22], 3: [64, 22], 4: [64, 40], 5: [64, 36], 6: [64, 36]}
ALIAS_BY_TASK = {task: f"field_task_{task}" for task in SIZE_BY_TASK}
POINT_VALIDATOR_BLOB = "45b3d57e7ef873e92e88107e7019d64376061216"
POINT_VALIDATOR_PATH = "research/live_control/model_point_target_v1.py"
V33_BACKEND_BLOB = "34e738489619967a0be95d0b90de58d6490455a7"
V33_BACKEND_PATH = "research/live_control/session_v33.py"


def _load_pinned_validator():
    raw = subprocess.check_output(["git", "cat-file", "blob", POINT_VALIDATOR_BLOB], cwd=REPO)
    actual = subprocess.check_output(["git", "hash-object", "--stdin"], input=raw, cwd=REPO).decode().strip()
    if actual != POINT_VALIDATOR_BLOB:
        raise RuntimeError("pinned point validator blob did not verify")
    import types
    module = types.ModuleType("a04_pinned_model_point_target_v1")
    exec(compile(raw, f"git-blob:{POINT_VALIDATOR_BLOB}:{POINT_VALIDATOR_PATH}", "exec"), module.__dict__)
    return module


PINNED_VALIDATOR = _load_pinned_validator()


class _InertDecisionRequired(Exception):
    pass


class _InertSessionBase:
    """Small fake IO base for executing the pinned v33 route without X11."""
    def __init__(self, session, out, emit):
        self.session = session
        self.out = out
        self._emit = emit
        self._cursor = -1
        self.handles = session["handles"]

    def validate(self, steps):
        return None

    def snapshot(self, identifier, index):
        self._cursor = min(self._cursor + 1, len(self.session["observations"]) - 1)
        return {"event": "inert_snapshot", "id": identifier, "step": index}

    def observation(self):
        return self.session["observations"][self._cursor]

    def image(self):
        return self.session["images"][self._cursor]

    def emit(self, event):
        self._emit(event)


def _execute_pinned_v33_route(command: dict, source_image: Image.Image, fresh_image: Image.Image,
                              source_obs: dict, fresh_obs: dict, store: TargetHandleStore) -> dict:
    raw = subprocess.check_output(["git", "cat-file", "blob", V33_BACKEND_BLOB], cwd=REPO)
    actual = subprocess.check_output(["git", "hash-object", "--stdin"], input=raw, cwd=REPO).decode().strip()
    if actual != V33_BACKEND_BLOB:
        raise RuntimeError("pinned v33 backend blob did not verify")
    fake_frame = types.ModuleType("coordinate_frame_transform_v1")
    from runtime.guarded_x11_v1.frames import translation
    fake_frame.translation = translation
    fake_executor = types.ModuleType("executor_v3")
    fake_executor.DecisionRequired = _InertDecisionRequired
    fake_model = types.ModuleType("model_point_target_v1")
    fake_model.OPERATION = PINNED_VALIDATOR.OPERATION
    fake_model.derive = PINNED_VALIDATOR.derive
    fake_model.patch = PINNED_VALIDATOR.patch
    fake_model.validate_step = PINNED_VALIDATOR.validate_step
    fake_session = types.ModuleType("session_v32")
    fake_session.Backend = _InertSessionBase
    fake_session.suite = lambda: None
    replacements = {"coordinate_frame_transform_v1": fake_frame, "executor_v3": fake_executor,
                    "model_point_target_v1": fake_model, "session_v32": fake_session}
    prior = {name: sys.modules.get(name) for name in replacements}
    events: list[dict] = []
    try:
        sys.modules.update(replacements)
        backend_module = types.ModuleType("a04_pinned_session_v33")
        exec(compile(raw, f"git-blob:{V33_BACKEND_BLOB}:{V33_BACKEND_PATH}", "exec"), backend_module.__dict__)
        session = {"observations": [source_obs, fresh_obs], "images": [source_image, fresh_image], "handles": store}
        backend = backend_module.Backend(session, None, events.append)
        backend.validate([command])
        backend.snapshot("a04", 0)
        result = backend.execute(command, lambda: False, "a04", 0)
        return {"executed": True, "accepted": True, "result": result, "events": events}
    except _InertDecisionRequired as exc:
        return {"executed": True, "accepted": False, "reason": str(exc), "events": events}
    finally:
        for name, module in prior.items():
            if module is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = module


def observation(sequence: int, capture_ns: int, image_size: tuple[int, int], *,
                focus: int = 101, surface: int = 202) -> dict:
    return {"sequence": sequence, "capture_ns": capture_ns,
            "pointer_binding": {"focus": focus, "surface": surface,
                                "geometry": [0, 0, image_size[0], image_size[1]]}}


def _validate_point_command(step: dict) -> dict:
    """Execute the exact frozen model_point_target_v1 shape rules."""
    PINNED_VALIDATOR.validate_step(step)
    return PINNED_VALIDATOR.derive(step["point"], step["region_size"])


def _source_cases() -> list[dict]:
    return json.loads((HERE / "INPUTS.json").read_text(encoding="utf-8"))["cases"]


def _image_for(case: dict) -> Image.Image:
    return Image.open((PACKAGE / "a02-retained-screenshot-grounding" / case["image_file"]).resolve()).convert("RGB")


def _proposal(case: dict, image: Image.Image) -> tuple[dict, dict, Image.Image]:
    task = case["task"]
    alias = ALIAS_BY_TASK[task]
    point = list(case["field_point"])
    size = SIZE_BY_TASK[task]
    command = {"op": "target_handle_mint_from_point", "name": alias,
               "coordinate_frame": "window_content", "source_sequence": 1,
               "point": point, "region_size": size, "ttl_ms": 300_000,
               "freshness_ms": 1_500, "search_radius": 0,
               "allowed_transformations": ["window_translation"]}
    derived = _validate_point_command(command)
    box = derived["box"]
    x0, y0, width, height = box
    context = next(row for row in json.loads((PACKAGE / "a03-context-crops" / "RESULT.json").read_text(encoding="utf-8"))["cases"] if row["task"] == task)["padded_crop"]["box"]
    assert x0 >= context[0] and y0 >= context[1] and x0 + width <= context[0] + context[2] and y0 + height <= context[1] + context[3]
    assert 0 <= x0 and 0 <= y0 and x0 + width <= image.width and y0 + height <= image.height
    return command, derived, image


def _compose(case: dict, *, mutation: str | None = None) -> dict:
    image = _image_for(case)
    command, derived, image = _proposal(case, image)
    source_obs = observation(1, time.perf_counter_ns() - 2_000_000, image.size)
    fresh_obs = observation(2, time.perf_counter_ns() - 100_000, image.size)
    fresh = image.copy()
    if mutation == "changed_patch":
        x, y, width, height = derived["box"]
        ImageDraw.Draw(fresh).rectangle((x, y, x + width - 1, y + height - 1), fill=(255, 255, 255))
    elif mutation == "focus_changed":
        fresh_obs = observation(2, time.perf_counter_ns() - 100_000, image.size, focus=303)
    elif mutation == "surface_changed":
        fresh_obs = observation(2, time.perf_counter_ns() - 100_000, image.size, surface=404)
    elif mutation == "stale":
        fresh_obs = observation(2, time.perf_counter_ns() - 100_000, image.size)
    store = TargetHandleStore(f"a04-task-{case['task']}", id_factory=lambda: f"private-{case['task']}")
    route = _execute_pinned_v33_route(command, image, fresh, source_obs, fresh_obs, store)
    if not route["accepted"]:
        event = route["events"][-1]
        reason = event.get("reason")
        status = "MISSING" if reason == "source_patch_changed" else "SCOPE_MISMATCH"
        return {"accepted": False, "action_specs": [], "stage": "source_mint_route",
                "status": status, "reason": reason, "mint_route": route}
    minted = route["result"]
    actual_alias = ALIAS_BY_TASK[case["task"]] if mutation != "wrong_alias" else "unrelated_alias"
    offset = derived["offset"]
    if mutation == "fixed_offset":
        offset = [12, 19]
    resolve_now_ns = fresh_obs["capture_ns"] + 1_500_000_001 if mutation == "stale" else time.perf_counter_ns()
    resolution = store.resolve_point(actual_alias, offset, fresh_obs, fresh, resolve_now_ns)
    sink: list[dict] = []
    if not resolution["eligible"]:
        return {"accepted": False, "action_specs": sink, "stage": "fresh_resolution", "status": resolution["status"],
                "reason": resolution.get("reason"), "mint": minted, "mint_route": route, "resolution": resolution}
    if (actual_alias != command["name"] or offset != derived["offset"] or
            resolution.get("point") != command["point"] or
            resolution.get("patch_sha256") != minted["patch_sha256"]):
        return {"accepted": False, "action_specs": sink, "stage": "identity_consistency", "status": "MISSING",
                "mint": minted, "mint_route": route, "resolution": resolution}
    action_spec = {"op": "pointer_click_target", "target_handle": actual_alias,
                   "offset": list(offset), "button": 1, "duration_ms": 80,
                   "point": list(resolution["point"]), "box": list(derived["box"]),
                   "patch_sha256": minted["patch_sha256"]}
    sink.append(action_spec)
    return {"accepted": True, "action_specs": sink, "stage": "action_specification_sink",
            "status": resolution["status"], "mint": minted, "mint_route": route, "resolution": resolution,
            "command": command, "alias": command["name"], "proposal_point": list(command["point"]),
            "box": list(derived["box"]), "offset": list(derived["offset"]),
            "patch_sha256": minted["patch_sha256"], "action_spec": action_spec}


def run_composition() -> dict:
    rows = []
    for case in _source_cases():
        row = _compose(case)
        row["task"] = case["task"]
        rows.append(row)
    representative = next(case for case in _source_cases() if case["task"] == 3)
    negative = {"fixed_offset": _compose(representative, mutation="fixed_offset"),
                "wrong_alias": _compose(representative, mutation="wrong_alias")}
    ineligible = {name: _compose(representative, mutation=name)
                  for name in ("changed_patch", "focus_changed", "surface_changed", "stale")}
    return {"schema": "a04-point-click-composition-v1", "cases": rows,
            "negative_cases": negative, "ineligible_cases": ineligible,
            "input_dispatch_count": 0, "gui_call_count": 0, "model_call_count": 0,
            "interpretation": "offline source-bound handle composition to inert action-specification sink; no semantic target or task-effect claim"}
