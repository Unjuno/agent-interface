"""Validate bounded visual memory with action, effect, and recovery provenance.

The receipt is planner evidence only.  It cannot authorize input, establish that
the current target still exists, or turn an old semantic result into a current
one.  Callers must retain the source artifact and independently refresh current
observations before acting.
"""
import copy
import hashlib
import json
from pathlib import Path, PurePosixPath


SCHEMA = "action-grounded-visual-memory-v1"
MAX_TRACE = 16
MAX_MODEL_CALLS = 8


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf-8")


def sha256_bytes(value):
    return hashlib.sha256(value).hexdigest()


def _hex(value):
    return isinstance(value, str) and len(value) == 64 and all(
        char in "0123456789abcdef" for char in value)


def _positive_int(value):
    return type(value) is int and value > 0


def validate(receipt):
    required = {"schema", "memory_id", "task", "source", "target", "action",
                "effect", "recovery", "artifact", "retention", "authority"}
    if type(receipt) is not dict or set(receipt) != required:
        raise ValueError("exact action-grounded memory fields required")
    if receipt["schema"] != SCHEMA or receipt["authority"] != "none":
        raise ValueError("non-authoritative v1 receipt required")
    if not isinstance(receipt["memory_id"], str) or not receipt["memory_id"]:
        raise ValueError("memory identity required")

    task = receipt["task"]
    if (type(task) is not dict or set(task) != {"task_id", "environment_id"}
            or not all(isinstance(task[key], str) and task[key] for key in task)):
        raise ValueError("bounded task identity required")

    source = receipt["source"]
    source_fields = {"session_id", "sequence", "capture_ns", "exact", "surface",
                     "geometry", "frame_size", "image_name", "image_sha256", "rgb_sha256"}
    if type(source) is not dict or set(source) != source_fields:
        raise ValueError("exact source observation fields required")
    if (not isinstance(source["session_id"], str) or not source["session_id"]
            or not _positive_int(source["sequence"])
            or not _positive_int(source["capture_ns"]) or source["exact"] is not True
            or not _positive_int(source["surface"])
            or type(source["geometry"]) is not list or len(source["geometry"]) != 4
            or any(type(value) is not int for value in source["geometry"])
            or type(source["frame_size"]) is not list or len(source["frame_size"]) != 2
            or any(not _positive_int(value) for value in source["frame_size"])
            or not isinstance(source["image_name"], str) or not source["image_name"]
            or Path(source["image_name"]).name != source["image_name"]
            or not _hex(source["image_sha256"]) or not _hex(source["rgb_sha256"])):
        raise ValueError("invalid exact source observation")

    target = receipt["target"]
    target_fields = {"name", "handle", "point", "crop_box", "patch_sha256"}
    if type(target) is not dict or set(target) != target_fields:
        raise ValueError("exact target fields required")
    if (not all(isinstance(target[key], str) and target[key]
                for key in ("name", "handle"))
            or type(target["point"]) is not list or len(target["point"]) != 2
            or any(type(value) is not int for value in target["point"])
            or type(target["crop_box"]) is not list or len(target["crop_box"]) != 4
            or any(type(value) is not int for value in target["crop_box"])
            or not _hex(target["patch_sha256"])):
        raise ValueError("invalid target provenance")
    left, top, right, bottom = target["crop_box"]
    width, height = source["frame_size"]
    if not (0 <= left < right <= width and 0 <= top < bottom <= height):
        raise ValueError("target crop outside source frame")
    if not (left <= target["point"][0] < right and top <= target["point"][1] < bottom):
        raise ValueError("target point outside crop")

    action = receipt["action"]
    action_fields = {"id", "program_sha256", "accepted_ns", "terminal_ns",
                     "status", "release_verified", "keys_down", "buttons_down"}
    if type(action) is not dict or set(action) != action_fields:
        raise ValueError("exact admitted action fields required")
    if (not isinstance(action["id"], str) or not action["id"]
            or not _hex(action["program_sha256"])
            or not _positive_int(action["accepted_ns"])
            or not _positive_int(action["terminal_ns"])
            or action["terminal_ns"] < action["accepted_ns"]
            or action["status"] != "completed" or action["release_verified"] is not True
            or action["keys_down"] != [] or action["buttons_down"] != []):
        raise ValueError("completed admitted action with empty verified release required")
    if action["accepted_ns"] <= source["capture_ns"]:
        raise ValueError("action acceptance must follow the source observation")

    effect = receipt["effect"]
    effect_fields = {"predicate_id", "sequence", "capture_ns", "success", "reason",
                     "frame_sha256", "artifact_sha256", "reconciled_exact",
                     "independent_output_sha256"}
    if type(effect) is not dict or set(effect) != effect_fields:
        raise ValueError("exact effect fields required")
    if (not isinstance(effect["predicate_id"], str) or not effect["predicate_id"]
            or not _positive_int(effect["sequence"]) or not _positive_int(effect["capture_ns"])
            or effect["sequence"] <= source["sequence"] or effect["success"] is not True
            or not isinstance(effect["reason"], str) or not effect["reason"]
            or not _hex(effect["frame_sha256"]) or not _hex(effect["artifact_sha256"])
            or effect["reconciled_exact"] is not True
            or not _hex(effect["independent_output_sha256"])):
        raise ValueError("independently scored exact effect required")
    if not action["accepted_ns"] <= effect["capture_ns"] <= action["terminal_ns"]:
        raise ValueError("effect capture must occur within the admitted action lifetime")

    recovery = receipt["recovery"]
    recovery_fields = {"path", "route", "trace", "model_call_ids",
                       "attempted_model_calls", "completed_model_calls", "model_wait_ns"}
    if type(recovery) is not dict or set(recovery) != recovery_fields:
        raise ValueError("exact recovery fields required")
    if (recovery["path"] not in {"none", "local", "model_reacquisition"}
            or not isinstance(recovery["route"], str) or not recovery["route"]
            or type(recovery["trace"]) is not list or len(recovery["trace"]) > MAX_TRACE
            or not all(type(row) is dict for row in recovery["trace"])
            or type(recovery["model_call_ids"]) is not list
            or len(recovery["model_call_ids"]) > MAX_MODEL_CALLS
            or not all(isinstance(value, str) and value for value in recovery["model_call_ids"])
            or type(recovery["attempted_model_calls"]) is not int
            or type(recovery["completed_model_calls"]) is not int
            or not 0 <= recovery["completed_model_calls"] <= recovery["attempted_model_calls"]
            or recovery["completed_model_calls"] != len(recovery["model_call_ids"])
            or type(recovery["model_wait_ns"]) is not int or recovery["model_wait_ns"] < 0):
        raise ValueError("invalid bounded recovery provenance")

    artifact = receipt["artifact"]
    artifact_fields = {"path", "width", "height", "png_sha256", "rgb_sha256"}
    if type(artifact) is not dict or set(artifact) != artifact_fields:
        raise ValueError("exact artifact fields required")
    artifact_path = PurePosixPath(artifact["path"]) if isinstance(artifact["path"], str) else None
    if (artifact_path is None or not artifact["path"] or artifact_path.is_absolute()
            or ".." in artifact_path.parts
            or "\\" in artifact["path"] or len(artifact_path.parts) > 3
            or artifact["width"] != right - left or artifact["height"] != bottom - top
            or not _hex(artifact["png_sha256"]) or not _hex(artifact["rgb_sha256"])
            or artifact["rgb_sha256"] != target["patch_sha256"]):
        raise ValueError("artifact does not bind the target patch")

    retention = receipt["retention"]
    if retention != {"class": "conditional_visual_reference",
                      "requires_current_observation": True,
                      "requires_fresh_input_admission": True}:
        raise ValueError("safe conditional retention policy required")
    return copy.deepcopy(receipt)


def verify_artifact(receipt, root):
    """Check the retained crop bytes; this grants no current-state authority."""
    checked = validate(receipt)
    path = Path(root) / checked["artifact"]["path"]
    if not path.is_file() or sha256_bytes(path.read_bytes()) != checked["artifact"]["png_sha256"]:
        raise ValueError("retained crop bytes unavailable or changed")
    from PIL import Image
    with Image.open(path) as opened:
        image = opened.convert("RGB")
    if ([image.width, image.height] != [checked["artifact"]["width"],
                                       checked["artifact"]["height"]]
            or sha256_bytes(image.tobytes()) != checked["artifact"]["rgb_sha256"]):
        raise ValueError("retained crop pixels unavailable or changed")
    return {"status": "VERIFIED_ARCHIVED_REFERENCE", "memory_id": checked["memory_id"],
            "authority": "none", "current_target_status": "unknown"}


def retrieve(receipt, context):
    """Return a reference only for the same task/session/surface identity."""
    checked = validate(receipt)
    required = {"task_id", "environment_id", "session_id", "surface", "target_name",
                "current_observation_exact"}
    if type(context) is not dict or set(context) != required:
        raise ValueError("exact retrieval context required")
    matches = {
        "task": context["task_id"] == checked["task"]["task_id"],
        "environment": context["environment_id"] == checked["task"]["environment_id"],
        "session": context["session_id"] == checked["source"]["session_id"],
        "surface": context["surface"] == checked["source"]["surface"],
        "target_name": context["target_name"] == checked["target"]["name"],
        "current_observation_exact": context["current_observation_exact"] is True,
    }
    if not all(matches.values()):
        return {"status": "NOT_ELIGIBLE", "matches": matches, "reference": None,
                "authority": "none"}
    return {"status": "ELIGIBLE_VISUAL_REFERENCE", "matches": matches,
            "reference": checked, "current_target_status": "must_be_revalidated",
            "input_admission": "must_be_fresh", "authority": "none"}
