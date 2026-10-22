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


def digest(path: Path, box: tuple[int, int, int, int]) -> str:
    with Image.open(path) as source:
        return hashlib.sha256(source.convert("RGB").crop(box).tobytes()).hexdigest()


grounding = json.loads(GROUNDING.read_text(encoding="utf-8"))
field = grounding["grounding"]["field_point"]
# The click remains inside the field, near its upper edge. A 4x4 guard patch
# samples the static top strip above the text baseline; the runtime enforces
# the schema's minimum supported region dimension of four pixels.
anchor = [field[0], field[1] - 20]
box = (anchor[0] - 2, anchor[1] - 2, anchor[0] + 2, anchor[1] + 2)
paths = [BASELINE, *sorted(IMAGES.glob("*.png"))]
digests = {path.name: digest(path, box) for path in paths}
unique = sorted(set(digests.values()))
baseline = digests[BASELINE.name]
result = {
    "schema": "agent-interface/chromium-field-click-strip-audit-v1",
    "run_id": "post-r03-field-click-strip-audit",
    "status": "PASS_STATIC_PATCH_UNCHANGED" if len(unique) == 1 else "FAIL_PATCH_CHANGED",
    "r03_disposition": "preserve execution failure; no replay or rerun",
    "source_call_id": "570abb0ffc914ed0b4c3d42213730458",
    "model_grounded_field_point": field,
    "candidate_input_click_anchor": anchor,
    "candidate_region_size": [4, 4],
    "candidate_patch_box_xyxy": list(box),
    "baseline_file": BASELINE.name,
    "baseline_patch_sha256": baseline,
    "compared_frame_count": len(paths),
    "compiled_capture_count": len(paths) - 1,
    "distinct_patch_digest_count": len(unique),
    "mismatches": [name for name, value in digests.items() if value != baseline],
    "patch_digest_by_frame": digests,
    "limits": [
        "offline audit of frames from one failed Chromium/Xvfb run",
        "does not prove that a click at the upper field edge focuses the input",
        "does not prove future patch stability or successful input",
        "does not qualify blocked-I/O release, task success, or reliability",
    ],
}
output = ROOT / "raw/audit-field-click-strip-r03.json"
output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps(result, indent=2, sort_keys=True))
raise SystemExit(0 if result["status"] == "PASS_STATIC_PATCH_UNCHANGED" else 1)
