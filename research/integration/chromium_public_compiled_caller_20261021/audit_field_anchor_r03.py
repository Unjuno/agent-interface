from __future__ import annotations

import hashlib
import json
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parent
CALL = ROOT / "raw/r03/mcp/570abb0ffc914ed0b4c3d42213730458"
IMAGES = CALL / "compiled/images"
BASELINE = ROOT / "raw/r03/post-model-fresh-observation.png"
GROUNDING = ROOT / "raw/r03/provider-call-01/result.json"


def patch_digest(path: Path, box: tuple[int, int, int, int]) -> str:
    with Image.open(path) as source:
        image = source.convert("RGB")
        crop = image.crop(box)
        return hashlib.sha256(crop.tobytes()).hexdigest()


grounding = json.loads(GROUNDING.read_text(encoding="utf-8"))
field = grounding["grounding"]["field_point"]
anchor = [field[0] + 120, field[1]]
box = (anchor[0] - 16, anchor[1] - 16, anchor[0] + 16, anchor[1] + 16)
paths = [BASELINE, *sorted(IMAGES.glob("*.png"))]
digests = {path.name: patch_digest(path, box) for path in paths}
unique = sorted(set(digests.values()))
baseline = digests[BASELINE.name]
result = {
    "schema": "agent-interface/chromium-field-alias-anchor-audit-v1",
    "run_id": "post-r03-static-anchor-audit",
    "status": "PASS_STATIC_PATCH_UNCHANGED" if len(unique) == 1 else "FAIL_PATCH_CHANGED",
    "r03_disposition": "preserve execution failure; no replay or rerun",
    "source_call_id": "570abb0ffc914ed0b4c3d42213730458",
    "model_grounded_field_point": field,
    "candidate_input_anchor": anchor,
    "candidate_patch_box_xyxy": list(box),
    "baseline_file": BASELINE.name,
    "baseline_patch_sha256": baseline,
    "compared_frame_count": len(paths),
    "compiled_capture_count": len(paths) - 1,
    "distinct_patch_digest_count": len(unique),
    "mismatches": [name for name, digest in digests.items() if digest != baseline],
    "patch_digest_by_frame": digests,
    "limits": [
        "offline audit of frames from one failed Chromium/Xvfb run",
        "does not prove click admission or successful future input",
        "does not qualify release while platform I/O is blocked",
        "does not establish task success or reliability",
    ],
}
output = ROOT / "raw/audit-field-anchor-r03.json"
output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps(result, indent=2, sort_keys=True))
raise SystemExit(0 if result["status"] == "PASS_STATIC_PATCH_UNCHANGED" else 1)
