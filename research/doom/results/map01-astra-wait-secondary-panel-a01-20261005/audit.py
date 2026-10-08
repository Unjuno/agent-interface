"""Independent source/frame-identity audit; does not adjudicate visual labels."""
import av
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import subprocess
from PIL import Image


ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
FREEZE = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))
RAW = json.loads((HERE / "raw.json").read_text(encoding="utf-8"))
VIDEO_PATH = FREEZE["video_path"]
COMMIT = FREEZE["repository_main"]


def git(*args):
    return subprocess.run(["git", *args], cwd=ROOT, check=True,
                          capture_output=True).stdout


data = git("show", f"{COMMIT}:{VIDEO_PATH}")
blob = git("rev-parse", f"{COMMIT}:{VIDEO_PATH}").decode().strip()
assert blob == FREEZE["video_blob"] == RAW["video_blob"]
assert len(data) == FREEZE["video_bytes"] == RAW["video_bytes"]
assert hashlib.sha256(data).hexdigest() == FREEZE["video_sha256"] == RAW["video_sha256"]

container = av.open(io.BytesIO(data))
rows = []
for packet in container.demux(video=0):
    for decoded in packet.decode():
        timestamp = float(decoded.pts * decoded.time_base)
        if FREEZE["interval"]["video_seconds_start"] <= timestamp <= FREEZE["interval"]["video_seconds_end"]:
            rgb = decoded.to_image().convert("RGB")
            rows.append({
                "frame_index": round(timestamp * 10),
                "video_seconds": round(timestamp, 6),
                "game_seconds": round(timestamp * 2, 6),
                "width": rgb.width, "height": rgb.height,
                "rgb_sha256": hashlib.sha256(rgb.tobytes()).hexdigest(),
            })
container.close()

assert len(rows) == FREEZE["interval"]["expected_frames"] == len(RAW["frames"])
assert rows == RAW["frames"]
assert rows[0]["frame_index"] == 223 and rows[-1]["frame_index"] == 282
assert all(row["width"] == 640 and row["height"] == 560 for row in rows)

for index in (223, 248, 252, 281, 282):
    path = HERE / "samples" / f"frame-{index:03d}.png"
    with Image.open(path) as image:
        rgb = image.convert("RGB")
        expected = rows[index - 223]["rgb_sha256"]
        assert hashlib.sha256(rgb.tobytes()).hexdigest() == expected

manual = json.loads((HERE / "MANUAL_REVIEW.json").read_text(encoding="utf-8"))
assert manual["disposition"] == RAW["manual_review_disposition"] == "OBSERVED_PANEL_ONLY"
assert manual["review_labels_are_independent_audit"] is False

result = {
    "passed": True,
    "scope": "video blob, decoded frame cadence, and selected still identities only; manual labels not independently verified",
    "source_commit": COMMIT,
    "source_blob": blob,
    "video_sha256": hashlib.sha256(data).hexdigest(),
    "frame_count": len(rows),
    "first_frame": rows[0]["frame_index"],
    "last_frame": rows[-1]["frame_index"],
    "manual_review_disposition": manual["disposition"],
    "audited_at_utc": datetime.now(timezone.utc).isoformat(),
}
(HERE / "audit-result.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
print(json.dumps(result, indent=2))
