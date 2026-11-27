"""Post-hoc OCR ROI diagnostic on the retained R03 screenshot; no browser run."""
import hashlib
import json
from pathlib import Path

from research.live_control.windows_ocr_observer_v1 import (
    WindowsOcrObserver,
    exact_token_state,
)


ROOT = Path(__file__).resolve().parent
FRAME = ROOT / "raw/normal/positive/frame-7.png"
TOKEN = "t991025-4"
ROIS = [
    {"region": [148, 98, 230, 34], "scale": 3},
    {"region": [148, 98, 230, 34], "scale": 4},
    {"region": [145, 95, 240, 40], "scale": 3},
]

with WindowsOcrObserver(timeout_seconds=12) as observer:
    rows = []
    for candidate in ROIS:
        result = observer.recognize(FRAME, region=candidate["region"],
                                    scale=candidate["scale"])
        rows.append({**candidate, "text": result["text"],
                     "exact_token_state": exact_token_state(result["text"], TOKEN),
                     "elapsed_ns": result["elapsed_ns"]})

output = {
    "scope": "post-hoc crop/scale OCR only; no Edge/browser/input/provider call",
    "source_frame": FRAME.name,
    "source_sha256": hashlib.sha256(FRAME.read_bytes()).hexdigest(),
    "token": TOKEN,
    "candidates": rows,
}
(ROOT / "raw/ocr_roi_diagnostic.json").write_text(
    json.dumps(output, indent=2) + "\n", encoding="utf-8", newline="\n")
print(json.dumps(output, indent=2))
