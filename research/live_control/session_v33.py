"""Mint a handle from a model point only after an exact fresh-patch check."""
import copy
import hashlib
import time

from coordinate_frame_transform_v1 import translation
from executor_v3 import DecisionRequired
from model_point_target_v1 import OPERATION, derive, patch, validate_step
from session_v32 import Backend as Previous, suite


class Backend(Previous):
    def __init__(self, session, out, emit):
        super().__init__(session, out, emit)
        self.point_source_history = {}

    def snapshot(self, identifier, index):
        result = super().snapshot(identifier, index)
        observation = copy.deepcopy(self.observation())
        self.point_source_history[observation["sequence"]] = {
            "observation": observation,
            "image": self.image().copy(),
        }
        while len(self.point_source_history) > 16:
            del self.point_source_history[next(iter(self.point_source_history))]
        return result

    def validate(self, steps):
        rewritten = []
        for step in steps:
            if not isinstance(step, dict) or step.get("op") != OPERATION:
                rewritten.append(step)
                continue
            validate_step(step)
            derived = derive(step["point"], step["region_size"])
            rewritten.append({
                "op": "target_handle_mint", "name": step["name"],
                "coordinate_frame": step["coordinate_frame"],
                "box": derived["box"], "ttl_ms": step["ttl_ms"],
                "freshness_ms": step["freshness_ms"],
                "search_radius": step["search_radius"],
                "allowed_transformations": step["allowed_transformations"],
            })
        super().validate(rewritten)

    def _refuse_point_mint(self, identifier, index, reason, **details):
        self.emit({"event": "target_handle_mint_from_point_refused",
                   "id": identifier, "step": index, "reason": reason,
                   "handle_created": False,
                   "authority": "refusal only; grants no input authority",
                   **details})
        raise DecisionRequired("point-derived target " + reason)

    def execute(self, step, cancel, identifier, index):
        if step["op"] != OPERATION:
            return super().execute(step, cancel, identifier, index)
        retained = self.point_source_history.get(step["source_sequence"])
        if retained is None:
            self._refuse_point_mint(identifier, index, "source_observation_not_retained",
                                    source_sequence=step["source_sequence"],
                                    retained_sequences=list(self.point_source_history))
        source = retained["observation"]
        source_image = retained["image"]
        derived = derive(step["point"], step["region_size"])
        source_box = derived["box"]
        try:
            source_pixels = patch(source_image, source_box)
        except ValueError:
            self._refuse_point_mint(identifier, index, "source_region_outside_observation")
        source_binding = source["pointer_binding"]
        source_digest = hashlib.sha256(source_pixels).hexdigest()
        self.snapshot(identifier, index)
        current = self.observation()
        current_binding = current["pointer_binding"]
        if (current_binding["focus"] != source_binding["focus"]
                or current_binding["surface"] != source_binding["surface"]):
            self._refuse_point_mint(identifier, index, "focus_or_surface_changed",
                                    source_sequence=source["sequence"],
                                    current_sequence=current["sequence"])
        try:
            delta = translation(step["coordinate_frame"], source_binding["geometry"],
                                current_binding["geometry"])
            current_box = [source_box[0] + delta[0], source_box[1] + delta[1],
                           source_box[2], source_box[3]]
            current_pixels = patch(self.image(), current_box)
        except ValueError:
            self._refuse_point_mint(identifier, index, "current_region_outside_observation")
        current_digest = hashlib.sha256(current_pixels).hexdigest()
        if current_pixels != source_pixels:
            self._refuse_point_mint(
                identifier, index, "source_patch_changed",
                source_sequence=source["sequence"], current_sequence=current["sequence"],
                source_patch_sha256=source_digest,
                current_patch_sha256=current_digest,
                predicted_box=current_box,
            )
        now_ns = time.perf_counter_ns()
        record = self.handles.mint(
            step["name"], step["coordinate_frame"], current_box,
            current, self.image(), now_ns, step["ttl_ms"], step["freshness_ms"],
            step["search_radius"], tuple(step["allowed_transformations"]))
        enriched = {
            **record,
            "derivation": "centered_region_from_model_point",
            "source_point": step["point"],
            "source_sequence": source["sequence"],
            "fresh_sequence": current["sequence"],
            "derived_box": current_box,
            "derived_offset": derived["offset"],
            "source_patch_sha256": source_digest,
            "fresh_patch_sha256": current_digest,
            "fresh_patch_exact": True,
        }
        self.emit({"event": "target_handle_minted_from_point", "id": identifier,
                   "step": index, "minted_ns": now_ns, **enriched})
        return enriched
