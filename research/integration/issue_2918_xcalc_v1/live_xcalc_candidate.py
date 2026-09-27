"""Frozen XCalc screenshot adapter around the unchanged #1904 certificate compiler."""
from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path

from PIL import Image

from research.analysis.observation_manipulate_dynamic_certificate_v1 import model

TEMPLATE = json.loads(Path("research/integration/issue_2918_xcalc_v1/display_templates.json").read_text())
MAX_AGE_NS = 250_000_000


def read_state(artifact: dict):
    im = Image.open(Path(artifact["path"])).convert("RGB")
    if im.size != (244, 410):
        raise ValueError("incomplete_or_unexpected_xcalc_surface")
    c = TEMPLATE["capture"]
    box = (c["x"], c["y"], c["x"] + c["width"], c["y"] + c["height"])
    digest = hashlib.sha256(im.crop(box).tobytes()).hexdigest()
    value = TEMPLATE["sha256_to_value"].get(digest)
    if value is None:
        raise ValueError("unrecognized_or_missing_display_value")
    return tuple((value >> bit) & 1 for bit in (3, 2, 1, 0)), digest


def decide(*, artifact, phase, binding, intent_epoch, captured_ns, now_ns,
           observed_xid=None, observed_client_pid=None,
           observed_client_resource_base=None, observation_epoch=None,
           prior=None, ambiguous=False):
    if ambiguous:
        return {"disposition": "YIELD", "reason": "ambiguous_target"}
    if not isinstance(artifact, dict) or not artifact.get("path"):
        return {"disposition": "YIELD", "reason": "observation_missing"}
    if now_ns < captured_ns or now_ns - captured_ns > MAX_AGE_NS:
        return {"disposition": "YIELD", "reason": "stale_observation"}
    if (not isinstance(binding, dict) or type(binding.get("xid")) is not int
            or binding["xid"] != observed_xid
            or binding.get("client_pid") != observed_client_pid
            or binding.get("client_resource_base") != observed_client_resource_base):
        return {"disposition": "YIELD", "reason": "observation_binding_mismatch"}
    if prior and (prior.get("binding") != binding or prior.get("intent_epoch") != intent_epoch):
        return {"disposition": "YIELD", "reason": "binding_or_intent_epoch_changed"}
    try:
        state, pixel_digest = read_state(artifact)
        mask, _ = model.select_certificate(phase, state)
    except Exception as exc:
        return {"disposition": "YIELD", "reason": str(exc) or type(exc).__name__}
    cert = {"phase": phase, "state": state, "mask": sorted(mask),
            "binding": binding, "intent_epoch": intent_epoch,
            "observation_epoch": observation_epoch,
            "certificate_generation_ns": time.monotonic_ns(),
            "observation_capture_ended_ns": captured_ns,
            "dependency_provenance": {
                "public_artifact_sha256": artifact.get("sha256"),
                "display_roi_pixel_sha256": pixel_digest,
                "display_roi": {k: TEMPLATE["capture"][k] for k in ("x", "y", "width", "height")},
                "value_to_facts": {name: value for name, value in zip(model.DOMS, state)},
                "required_facts": list(model.DOMS),
                "phase_support": sorted(model.PHASE_SUPPORT[phase]),
            }}
    if prior and prior.get("phase") == phase:
        changed = model.changed(prior["state"], state)
        pmask = frozenset(prior["mask"])
        cert["changed_facts"] = sorted(changed)
        cert["reused_mask"] = sorted(pmask)
        cert["disposition"] = "SUPPRESS" if changed.isdisjoint(pmask) else "FORWARD"
    else:
        cert["disposition"] = "FORWARD"
    return cert
