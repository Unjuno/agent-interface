"""Revalidate receipt dependencies before exposing one target point to input."""
import hashlib
import time

from PIL import ImageChops


AUTHORITY = "TARGET_REFERENCE_ONLY"
NO_AUTHORITY = "NO_TARGET_AUTHORITY"


def _integer(value):
    return type(value) is int


def _binding(observation):
    if type(observation) is not dict:
        raise ValueError("observation object required")
    if set(observation) < {"sequence", "capture_ns", "pointer_binding"}:
        raise ValueError("observation identity required")
    if not _integer(observation["sequence"]) or observation["sequence"] < 1:
        raise ValueError("positive observation sequence required")
    if not _integer(observation["capture_ns"]) or observation["capture_ns"] < 0:
        raise ValueError("nonnegative capture clock required")
    binding = observation["pointer_binding"]
    if type(binding) is not dict or set(binding) != {"focus", "surface", "geometry"}:
        raise ValueError("exact pointer binding required")
    if any(not _integer(binding[key]) or binding[key] in (0, 1)
           for key in ("focus", "surface")):
        raise ValueError("focus and surface identifiers required")
    geometry = binding["geometry"]
    if (type(geometry) is not list or len(geometry) != 4 or
            any(not _integer(value) for value in geometry) or
            geometry[2] <= 0 or geometry[3] <= 0):
        raise ValueError("integer positive surface geometry required")
    return binding


def _box(value, image):
    if (type(value) is not list or len(value) != 4 or
            any(not _integer(item) for item in value)):
        raise ValueError("integer half-open box required")
    left, top, right, bottom = value
    if (left < 0 or top < 0 or right <= left or bottom <= top or
            right > image.width or bottom > image.height):
        raise ValueError("box outside observation")
    if not 16 <= (right - left) * (bottom - top) <= 65536:
        raise ValueError("box area must be 16..65536")
    return tuple(value)


def _crop(image, box):
    if getattr(image, "mode", None) != "RGB":
        raise ValueError("RGB image required")
    return image.crop(tuple(box))


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def _refusal(reason, **details):
    return {"eligible": False, "status": "NEEDS_DECISION",
            "authority_class": NO_AUTHORITY, "point": None,
            "reason": reason, **details}


def validate(spec):
    required = {"target", "point_space", "motion_model", "point",
                "source_sequence", "decision_after_sequence", "ttl_ms",
                "freshness_ms", "checks"}
    if type(spec) is not dict or set(spec) != required:
        raise ValueError("invalid receipt-target specification fields")
    if type(spec["target"]) is not str or not spec["target"] or len(spec["target"]) > 128:
        raise ValueError("bounded nonempty target required")
    if spec["point_space"] != "source_observation_pixels":
        raise ValueError("source observation point space required")
    if spec["motion_model"] != "surface_origin_translation":
        raise ValueError("surface origin translation required")
    if (type(spec["point"]) is not list or len(spec["point"]) != 2 or
            any(not _integer(value) for value in spec["point"])):
        raise ValueError("point must be two integers")
    if (not _integer(spec["source_sequence"]) or spec["source_sequence"] < 1 or
            not _integer(spec["decision_after_sequence"]) or
            spec["decision_after_sequence"] < spec["source_sequence"]):
        raise ValueError("valid source and decision sequence required")
    if not _integer(spec["ttl_ms"]) or not 1 <= spec["ttl_ms"] <= 300000:
        raise ValueError("ttl_ms must be 1..300000")
    if not _integer(spec["freshness_ms"]) or not 1 <= spec["freshness_ms"] <= 5000:
        raise ValueError("freshness_ms must be 1..5000")
    checks = spec["checks"]
    if type(checks) is not list or not 1 <= len(checks) <= 8:
        raise ValueError("one to eight dependency checks required")
    for check in checks:
        if type(check) is not dict:
            raise ValueError("dependency check object required")
        if check.get("kind") == "exact_patch":
            if set(check) != {"kind", "source_sequence", "box"}:
                raise ValueError("invalid exact-patch check")
            if not _integer(check["source_sequence"]) or check["source_sequence"] < 1:
                raise ValueError("positive exact-patch source sequence required")
        elif check.get("kind") == "stable_change_mask":
            if set(check) != {"kind", "baseline_sequence", "receipt_sequence",
                              "box", "minimum_changed_pixels"}:
                raise ValueError("invalid stable-mask check")
            if any(not _integer(check[key]) or check[key] < 1
                   for key in ("baseline_sequence", "receipt_sequence")):
                raise ValueError("positive mask evidence sequences required")
            if (not _integer(check["minimum_changed_pixels"]) or
                    check["minimum_changed_pixels"] < 1):
                raise ValueError("positive minimum mask size required")
        else:
            raise ValueError("unsupported dependency check")


def evaluate(spec, history, current_observation, current_image, now_ns):
    validate(spec)
    if type(history) is not dict:
        raise ValueError("history mapping required")
    if not _integer(now_ns) or now_ns < 0:
        raise ValueError("nonnegative revalidation clock required")
    try:
        current_binding = _binding(current_observation)
        _crop(current_image, [0, 0, current_image.width, current_image.height])
    except ValueError as error:
        return _refusal("current_evidence_unavailable", detail=str(error))
    required_sequences = {spec["source_sequence"]}
    for check in spec["checks"]:
        required_sequences.update(value for key, value in check.items()
                                  if key.endswith("_sequence"))
    if any(sequence not in history for sequence in required_sequences):
        return _refusal("historical_evidence_unavailable",
                        missing_sequences=sorted(required_sequences - set(history)))
    retained = {}
    try:
        for sequence in required_sequences:
            item = history[sequence]
            if type(item) is not dict or set(item) != {"observation", "image"}:
                raise ValueError("exact history item required")
            if item["observation"].get("sequence") != sequence:
                raise ValueError("history sequence association mismatch")
            binding = _binding(item["observation"])
            _crop(item["image"], [0, 0, item["image"].width, item["image"].height])
            retained[sequence] = (item["observation"], binding, item["image"])
    except ValueError as error:
        return _refusal("historical_evidence_unavailable", detail=str(error))
    source_observation, source_binding, source_image = retained[spec["source_sequence"]]
    if not (0 <= spec["point"][0] < source_image.width and
            0 <= spec["point"][1] < source_image.height):
        return _refusal("source_point_outside_observation")
    source_geometry = source_binding["geometry"]
    if not (source_geometry[0] <= spec["point"][0] < source_geometry[0] + source_geometry[2]
            and source_geometry[1] <= spec["point"][1] < source_geometry[1] + source_geometry[3]):
        return _refusal("source_point_outside_bound_surface")
    if (now_ns < current_observation["capture_ns"] or
            now_ns - current_observation["capture_ns"] > spec["freshness_ms"] * 1_000_000):
        return _refusal("current_evidence_stale")
    if (now_ns < source_observation["capture_ns"] or
            now_ns - source_observation["capture_ns"] > spec["ttl_ms"] * 1_000_000):
        return _refusal("receipt_expired")
    if current_observation["sequence"] <= spec["decision_after_sequence"]:
        return _refusal("no_post_decision_observation")
    if (current_binding["focus"] != source_binding["focus"] or
            current_binding["surface"] != source_binding["surface"]):
        return _refusal("focus_or_surface_changed")
    current_geometry = current_binding["geometry"]
    if source_geometry[2:] != current_geometry[2:]:
        return _refusal("surface_size_changed")
    delta = [current_geometry[0] - source_geometry[0],
             current_geometry[1] - source_geometry[1]]
    point = [spec["point"][0] + delta[0], spec["point"][1] + delta[1]]
    if not (0 <= point[0] < current_image.width and 0 <= point[1] < current_image.height):
        return _refusal("translated_point_outside_observation")
    evidence = []
    for index, check in enumerate(spec["checks"]):
        sequences = [value for key, value in check.items() if key.endswith("_sequence")]
        if any(retained[sequence][1] != source_binding for sequence in sequences):
            return _refusal("historical_binding_mismatch", check_index=index)
        historical_image = retained[sequences[0]][2]
        try:
            box = _box(check["box"], historical_image)
            current_box = [box[0] + delta[0], box[1] + delta[1],
                           box[2] + delta[0], box[3] + delta[1]]
            current_crop = _crop(current_image, current_box)
            if check["kind"] == "exact_patch":
                source_crop = _crop(retained[check["source_sequence"]][2], box)
                if source_crop.tobytes() != current_crop.tobytes():
                    return _refusal("exact_dependency_changed", check_index=index,
                                    source_sha256=_sha(source_crop.tobytes()),
                                    current_sha256=_sha(current_crop.tobytes()))
                evidence.append({"kind": "exact_patch", "check_index": index,
                                 "box": list(box), "current_box": current_box,
                                 "sha256": _sha(current_crop.tobytes())})
            else:
                baseline = _crop(retained[check["baseline_sequence"]][2], box)
                receipt = _crop(retained[check["receipt_sequence"]][2], box)
                receipt_difference = ImageChops.difference(baseline, receipt)
                current_difference = ImageChops.difference(baseline, current_crop)
                receipt_mask = bytes(pixel != (0, 0, 0)
                                     for pixel in receipt_difference.getdata())
                current_mask = bytes(pixel != (0, 0, 0)
                                     for pixel in current_difference.getdata())
                changed = sum(receipt_mask)
                if changed < check["minimum_changed_pixels"]:
                    return _refusal("source_mask_insufficient", check_index=index,
                                    changed_pixels=changed)
                if receipt_mask != current_mask:
                    return _refusal("stable_change_mask_changed", check_index=index,
                                    receipt_mask_sha256=_sha(receipt_mask),
                                    current_mask_sha256=_sha(current_mask))
                evidence.append({"kind": "stable_change_mask", "check_index": index,
                                 "box": list(box), "current_box": current_box,
                                 "changed_pixels": changed,
                                 "mask_sha256": _sha(current_mask)})
        except ValueError as error:
            return _refusal("dependency_evidence_unavailable", check_index=index,
                            detail=str(error))
    return {"eligible": True, "status": "REVALIDATED",
            "authority_class": AUTHORITY, "reason": "all_dependencies_revalidated",
            "target": spec["target"], "point": point,
            "source_sequence": spec["source_sequence"],
            "current_sequence": current_observation["sequence"],
            "binding_translation": delta,
            "valid_until_ns": current_observation["capture_ns"] +
                              spec["freshness_ms"] * 1_000_000,
            "evidence": evidence}


def dispatch(spec, history, current_observation, current_image, now_ns, adapter,
             clock=time.perf_counter_ns):
    if not callable(adapter):
        raise ValueError("target adapter callable required")
    outcome = evaluate(spec, history, current_observation, current_image, now_ns)
    if not outcome["eligible"]:
        return {**outcome, "adapter_called": False,
                "check_to_adapter_ns": None, "adapter_result": None}
    checked_ns = clock()
    result = adapter(outcome["point"], outcome["valid_until_ns"])
    called_ns = clock()
    return {**outcome, "adapter_called": True,
            "check_to_adapter_ns": called_ns - checked_ns,
            "adapter_result": result}
