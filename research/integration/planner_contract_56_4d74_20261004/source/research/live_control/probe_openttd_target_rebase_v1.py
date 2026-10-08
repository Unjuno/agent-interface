"""Replay persistent versus hover-conditioned OpenTTD target patches."""
import json
from pathlib import Path

from openttd_target_rebase_v1 import verify


HERE = Path(__file__).resolve().parent
ROOT = HERE / "results/openttd-hover-target-pair-01/2-stable-seed991004/runtime"
BINDING = {"focus": 10485762, "surface": 10485762,
           "geometry": [129, 40, 1024, 720]}


def observation(sequence, binding=BINDING):
    return {"sequence": sequence, "pointer_binding": binding,
            "focus_samples_match": True}


result = verify(observation(14), ROOT / "014.png",
                observation(21), ROOT / "021.png", [820, 51], [24, 14])
assert result["status"] == "REBASABLE"
invalid = [
    (observation(14), ROOT / "014.png", observation(23), ROOT / "023.png"),
    (observation(14), ROOT / "014.png",
     observation(21, {**BINDING, "focus": 9}), ROOT / "021.png"),
]
refused = 0
for source, source_image, current, current_image in invalid:
    try:
        verify(source, source_image, current, current_image, [820, 51], [24, 14])
    except ValueError:
        refused += 1
    else:
        raise AssertionError("invalid rebase accepted")
print(json.dumps({"persistent_patch_rebasable": True,
                  "invalid_rebases_refused": refused,
                  "box": result["box"], "patch_sha256": result["patch_sha256"]}))
