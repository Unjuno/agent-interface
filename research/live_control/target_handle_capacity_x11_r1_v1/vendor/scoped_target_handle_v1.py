"""Scoped exact-pixel target handles; revalidation evidence, never input authority."""
import hashlib
import secrets

from coordinate_frame_transform_v1 import translation


STATUSES = {"VALID", "REVALIDATED", "AMBIGUOUS", "MOVED", "MISSING",
            "STALE", "SCOPE_MISMATCH"}


def _integer(value):
    return type(value) is int


def _binding(observation):
    if type(observation) is not dict:
        raise ValueError("observation object required")
    binding = observation.get("pointer_binding")
    if type(binding) is not dict or set(binding) != {"focus", "surface", "geometry"}:
        raise ValueError("exact pointer binding required")
    if any(not _integer(binding[key]) or binding[key] in (0, 1)
           for key in ("focus", "surface")):
        raise ValueError("focus and surface identifiers required")
    geometry = binding["geometry"]
    translation("window_content", geometry, geometry)
    sequence = observation.get("sequence")
    capture_ns = observation.get("capture_ns")
    if not _integer(sequence) or sequence < 1:
        raise ValueError("positive observation sequence required")
    if not _integer(capture_ns) or capture_ns < 0:
        raise ValueError("nonnegative capture clock required")
    return binding, sequence, capture_ns


def _image(image):
    if getattr(image, "mode", None) != "RGB":
        raise ValueError("RGB image required")
    return image


def _box(value, image):
    if (type(value) is not list or len(value) != 4 or
            any(not _integer(item) for item in value)):
        raise ValueError("integer [x,y,width,height] box required")
    x, y, width, height = value
    if not (4 <= width <= 96 and 4 <= height <= 96):
        raise ValueError("handle region dimensions must be 4..96")
    if x < 0 or y < 0 or x + width > image.width or y + height > image.height:
        raise ValueError("handle region outside observation")
    return tuple(value)


def _inside(box, image):
    x, y, width, height = box
    return x >= 0 and y >= 0 and x + width <= image.width and y + height <= image.height


def _patch(image, box):
    x, y, width, height = box
    return image.crop((x, y, x + width, y + height)).tobytes()


class TargetHandleStore:
    """Session-local handle registry with bounded exact-region revalidation."""

    def __init__(self, session_scope, id_factory=None):
        if type(session_scope) is not str or not session_scope or len(session_scope) > 128:
            raise ValueError("nonempty session scope required")
        self.session_scope = session_scope
        self.id_factory = id_factory or (lambda: secrets.token_hex(16))
        self._entries = {}

    def mint(self, name, coordinate_frame, box, observation, image, now_ns,
             ttl_ms=30000, freshness_ms=1000, search_radius=0,
             allowed_transformations=("window_translation",)):
        image = _image(image)
        binding, sequence, capture_ns = _binding(observation)
        if type(name) is not str or not name or len(name) > 128:
            raise ValueError("bounded nonempty target name required")
        if coordinate_frame not in ("screen_chrome", "window_content"):
            raise ValueError("supported coordinate frame required")
        region = _box(box, image)
        if not _integer(now_ns) or now_ns < capture_ns:
            raise ValueError("mint clock cannot precede capture")
        if not _integer(ttl_ms) or not 1 <= ttl_ms <= 300000:
            raise ValueError("ttl_ms must be 1..300000")
        if not _integer(freshness_ms) or not 1 <= freshness_ms <= 5000:
            raise ValueError("freshness_ms must be 1..5000")
        if not _integer(search_radius) or not 0 <= search_radius <= 64:
            raise ValueError("search_radius must be 0..64")
        allowed = tuple(allowed_transformations)
        if (not allowed or len(set(allowed)) != len(allowed) or
                any(item not in ("window_translation", "local_translation") for item in allowed) or
                "window_translation" not in allowed):
            raise ValueError("bounded allowed transformations required")
        pixels = _patch(image, region)
        handle_id = self.id_factory()
        if type(handle_id) is not str or not handle_id or handle_id in self._entries:
            raise ValueError("unique runtime handle id required")
        expires_ns = now_ns + ttl_ms * 1_000_000
        self._entries[handle_id] = {
            "name": name, "coordinate_frame": coordinate_frame, "box": region,
            "binding": {key: (list(value) if key == "geometry" else value)
                        for key, value in binding.items()},
            "sequence": sequence, "capture_ns": capture_ns, "pixels": pixels,
            "digest": hashlib.sha256(pixels).hexdigest(), "expires_ns": expires_ns,
            "freshness_ms": freshness_ms, "search_radius": search_radius,
            "allowed": allowed,
        }
        return {"handle": handle_id, "name": name, "status": "VALID",
                "created_sequence": sequence, "expires_ns": expires_ns,
                "allowed_transformations": list(allowed),
                "patch_sha256": self._entries[handle_id]["digest"],
                "authority": "observational reference only; grants no input authority"}

    def resolve_point(self, handle_id, offset, observation, image, now_ns,
                      session_scope=None):
        def outcome(status, **extra):
            if status not in STATUSES:
                raise AssertionError(status)
            return {"eligible": status in ("VALID", "REVALIDATED"),
                    "status": status, "handle": handle_id,
                    "authority": "resolution only; ordinary admission remains required",
                    **extra}

        if type(handle_id) is not str or handle_id not in self._entries:
            return outcome("MISSING", reason="unknown_handle")
        entry = self._entries[handle_id]
        if session_scope is not None and session_scope != self.session_scope:
            return outcome("SCOPE_MISMATCH", reason="session_scope_changed")
        try:
            image = _image(image)
            binding, sequence, capture_ns = _binding(observation)
        except ValueError:
            return outcome("SCOPE_MISMATCH", reason="invalid_observation_scope")
        if (not _integer(now_ns) or now_ns < capture_ns or now_ns > entry["expires_ns"] or
                now_ns - capture_ns > entry["freshness_ms"] * 1_000_000 or
                sequence < entry["sequence"]):
            return outcome("STALE", reason="expired_or_nonfresh_observation")
        source_binding = entry["binding"]
        if (binding["focus"] != source_binding["focus"] or
                binding["surface"] != source_binding["surface"]):
            return outcome("SCOPE_MISMATCH", reason="focus_or_surface_changed")
        if (type(offset) is not list or len(offset) != 2 or
                any(not _integer(value) for value in offset)):
            return outcome("MISSING", reason="invalid_point_relation")
        width, height = entry["box"][2:]
        if not (0 <= offset[0] < width and 0 <= offset[1] < height):
            return outcome("MISSING", reason="point_relation_outside_region")
        try:
            delta = translation(entry["coordinate_frame"], source_binding["geometry"],
                                binding["geometry"])
        except ValueError:
            return outcome("SCOPE_MISMATCH", reason="unsupported_geometry_change")
        source_x, source_y, width, height = entry["box"]
        predicted = (source_x + delta[0], source_y + delta[1], width, height)
        if not _inside(predicted, image):
            return outcome("MISSING", reason="predicted_region_outside_observation")
        matches = []
        radius = entry["search_radius"]
        for y in range(max(0, predicted[1] - radius),
                       min(image.height - height, predicted[1] + radius) + 1):
            for x in range(max(0, predicted[0] - radius),
                           min(image.width - width, predicted[0] + radius) + 1):
                candidate = (x, y, width, height)
                if _patch(image, candidate) == entry["pixels"]:
                    matches.append(candidate)
        if not matches:
            return outcome("MISSING", reason="region_pixels_missing",
                           predicted_box=list(predicted))
        if len(matches) > 1:
            return outcome("AMBIGUOUS", reason="multiple_exact_region_matches",
                           matches=len(matches), predicted_box=list(predicted))
        resolved = matches[0]
        local_delta = [resolved[0] - predicted[0], resolved[1] - predicted[1]]
        if local_delta != [0, 0] and "local_translation" not in entry["allowed"]:
            return outcome("MOVED", reason="local_translation_not_allowed",
                           predicted_box=list(predicted), observed_box=list(resolved),
                           local_translation=local_delta)
        status = "VALID" if delta == [0, 0] and local_delta == [0, 0] else "REVALIDATED"
        return outcome(status, reason="exact_region_match", name=entry["name"],
                       point=[resolved[0] + offset[0], resolved[1] + offset[1]],
                       observed_box=list(resolved), binding_translation=delta,
                       local_translation=local_delta, sequence=sequence,
                       valid_until_ns=min(entry["expires_ns"],
                                          capture_ns + entry["freshness_ms"] * 1_000_000),
                       patch_sha256=entry["digest"])
