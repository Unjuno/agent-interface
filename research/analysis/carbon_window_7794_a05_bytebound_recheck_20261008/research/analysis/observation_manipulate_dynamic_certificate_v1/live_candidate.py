"""Pixel-only candidate for the Issue 2918 X11 transfer experiment."""
from __future__ import annotations

from pathlib import Path
from PIL import Image

from . import model

CELLS = {"T": (60, 60), "D": (180, 60), "E": (300, 60), "S": (420, 60)}
PALETTE = {(0, 180, 0): 1, (220, 0, 0): 0, (128, 128, 128): None}
MAX_AGE_MS = 250


def pixels(artifact: dict) -> tuple[int, int, int, int]:
    image = Image.open(Path(artifact["path"])).convert("RGB")
    if image.size != (520, 160):
        raise ValueError("unexpected observation dimensions")
    vals = []
    for fact in model.DOMS:
        color = image.getpixel(CELLS[fact])
        if color not in PALETTE or PALETTE[color] is None:
            raise ValueError("missing or unknown fact pixel")
        vals.append(PALETTE[color])
    # A second D indicator is a deliberately contradictory sensor channel.
    duplicate = image.getpixel((180, 120))
    if duplicate in PALETTE and PALETTE[duplicate] is not None and PALETTE[duplicate] != vals[1]:
        raise ValueError("contradictory duplicate fact")
    return tuple(vals)


def decide(*, artifact, phase, binding, intent_epoch, captured_ns, now_ns,
           observed_xid=None, prior=None, partial=False, ambiguous=False):
    if partial or ambiguous or now_ns < captured_ns or (now_ns-captured_ns) > MAX_AGE_MS*1_000_000:
        return {"disposition": "YIELD", "reason": "uncertain_boundary"}
    if type(binding) is not dict or type(binding.get("xid")) is not int or binding["xid"] != observed_xid:
        return {"disposition": "YIELD", "reason": "observation_binding_mismatch"}
    if prior and (prior["binding"] != binding or prior["intent_epoch"] != intent_epoch):
        return {"disposition": "YIELD", "reason": "binding_or_intent_epoch_changed"}
    try:
        state = pixels(artifact)
        mask, _ = model.select_certificate(phase, state)
    except Exception as exc:
        return {"disposition": "YIELD", "reason": type(exc).__name__}
    cert = {"phase": phase, "state": state, "mask": sorted(mask),
            "binding": binding, "intent_epoch": intent_epoch,
            "certificate_generation_ns": now_ns, "observation_capture_ended_ns": captured_ns}
    if prior and prior["phase"] == phase:
        changed = model.changed(prior["state"], state)
        # Reuse is governed by the previously issued certificate, never by a
        # freshly selected mask computed from the new state.
        prior_mask = frozenset(prior["mask"])
        if changed.isdisjoint(prior_mask) and prior["binding"] == binding and prior["intent_epoch"] == intent_epoch:
            cert["disposition"] = "SUPPRESS"
            cert["reused_mask"] = sorted(prior_mask)
            cert["changed_facts"] = sorted(changed)
        else:
            cert["disposition"] = "FORWARD"
            cert["reused_mask"] = sorted(prior_mask)
            cert["changed_facts"] = sorted(changed)
    else:
        cert["disposition"] = "FORWARD"
    return cert
