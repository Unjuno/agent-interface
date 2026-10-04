from __future__ import annotations

import hashlib
import json
import sys
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
PACKAGE = HERE.parent
REPO = HERE.parents[3]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from runtime.guarded_x11_v1.handles import TargetHandleStore


NOW_NS = 2_000_000
SIZE_BY_TASK = {2: [64, 22], 3: [64, 22], 4: [64, 40], 5: [64, 36], 6: [64, 36]}
ALIAS_BY_TASK = {task: f"field_task_{task}" for task in SIZE_BY_TASK}
POINT_VALIDATOR_BLOB = "45b3d57e7ef873e92e88107e7019d64376061216"
POINT_VALIDATOR_PATH = "research/live_control/model_point_target_v1.py"


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
    source_obs = observation(1, 1_000_000, image.size)
    fresh_obs = observation(2, NOW_NS, image.size)
    fresh = image.copy()
    if mutation == "changed_patch":
        x, y, width, height = derived["box"]
        ImageDraw.Draw(fresh).rectangle((x, y, x + width - 1, y + height - 1), fill=(255, 255, 255))
    elif mutation == "focus_changed":
        fresh_obs = observation(2, NOW_NS, image.size, focus=303)
    elif mutation == "surface_changed":
        fresh_obs = observation(2, NOW_NS, image.size, surface=404)
    elif mutation == "stale":
        fresh_obs = observation(2, NOW_NS, image.size)
    store = TargetHandleStore(f"a04-task-{case['task']}", id_factory=lambda: f"private-{case['task']}")
    source_patch = image.crop((derived["box"][0], derived["box"][1], derived["box"][0] + derived["box"][2], derived["box"][1] + derived["box"][3])).tobytes()
    current_patch = fresh.crop((derived["box"][0], derived["box"][1], derived["box"][0] + derived["box"][2], derived["box"][1] + derived["box"][3])).tobytes()
    if source_patch != current_patch:
        return {"accepted": False, "action_specs": [], "stage": "fresh_patch_check", "status": "MISSING",
                "source_patch_sha256": hashlib.sha256(source_patch).hexdigest(),
                "fresh_patch_sha256": hashlib.sha256(current_patch).hexdigest()}
    minted = store.mint(command["name"], command["coordinate_frame"], derived["box"], source_obs, image, NOW_NS,
                        ttl_ms=command["ttl_ms"], freshness_ms=command["freshness_ms"],
                        search_radius=command["search_radius"],
                        allowed_transformations=tuple(command["allowed_transformations"]))
    actual_alias = ALIAS_BY_TASK[case["task"]] if mutation != "wrong_alias" else "unrelated_alias"
    offset = derived["offset"]
    if mutation == "fixed_offset":
        offset = [12, 19]
    resolve_now_ns = NOW_NS + 1_500_000_001 if mutation == "stale" else NOW_NS + 1_000_000
    resolution = store.resolve_point(actual_alias, offset, fresh_obs, fresh, resolve_now_ns)
    sink: list[dict] = []
    if not resolution["eligible"]:
        return {"accepted": False, "action_specs": sink, "stage": "fresh_resolution", "status": resolution["status"],
                "reason": resolution.get("reason"), "mint": minted, "resolution": resolution}
    if (actual_alias != command["name"] or offset != derived["offset"] or
            resolution.get("point") != command["point"] or
            resolution.get("patch_sha256") != minted["patch_sha256"]):
        return {"accepted": False, "action_specs": sink, "stage": "identity_consistency", "status": "MISSING",
                "mint": minted, "resolution": resolution}
    action_spec = {"op": "pointer_click_target", "target_handle": actual_alias,
                   "offset": list(offset), "button": 1, "duration_ms": 80,
                   "point": list(resolution["point"]), "box": list(derived["box"]),
                   "patch_sha256": minted["patch_sha256"]}
    sink.append(action_spec)
    return {"accepted": True, "action_specs": sink, "stage": "action_specification_sink",
            "status": resolution["status"], "mint": minted, "resolution": resolution,
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
