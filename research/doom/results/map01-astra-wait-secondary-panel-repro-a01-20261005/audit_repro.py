"""Read-only cross-environment replay of retained A01 decoded-frame hashes."""
import av
import hashlib
import io
import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
SOURCE_COMMIT = "81a59aed13492ba1d52ea80e03d48c3d8de7b2c5"
SOURCE_PATH = "research/doom/results/map01-astra-attempt-v1/map01-astra-live-01-2x.mp4"
SOURCE_BLOB = "983e2f43e878b56d0d05cd4d7db5125a55566cc8"
SOURCE_SHA256 = "201ab6aaa8ab5823285b44864ad1df899ebe5a19c97ec6e84b8cc5db063f6be4"
HISTORICAL = ROOT / "research/doom/results/map01-astra-wait-secondary-panel-a01-20261005"
FREEZE = json.loads((HISTORICAL / "FREEZE.json").read_text(encoding="utf-8"))
RAW = json.loads((HISTORICAL / "raw.json").read_text(encoding="utf-8"))


def git(*args):
    return subprocess.run(["git", *args], cwd=ROOT, check=True,
                          capture_output=True).stdout


assert FREEZE["repository_main"] == SOURCE_COMMIT
assert FREEZE["video_path"] == SOURCE_PATH
assert FREEZE["video_blob"] == RAW["video_blob"] == SOURCE_BLOB
data = git("show", f"{SOURCE_COMMIT}:{SOURCE_PATH}")
blob = git("rev-parse", f"{SOURCE_COMMIT}:{SOURCE_PATH}").decode().strip()
digest = hashlib.sha256(data).hexdigest()
assert blob == SOURCE_BLOB
assert digest == SOURCE_SHA256 == FREEZE["video_sha256"] == RAW["video_sha256"]
assert len(data) == FREEZE["video_bytes"] == RAW["video_bytes"]

container = av.open(io.BytesIO(data))
rows = []
for frame in container.decode(video=0):
    timestamp = float(frame.pts * frame.time_base)
    if FREEZE["interval"]["video_seconds_start"] <= timestamp <= FREEZE["interval"]["video_seconds_end"]:
        rgb = frame.to_image().convert("RGB")
        rows.append({
            "frame_index": round(timestamp * 10),
            "video_seconds": round(timestamp, 6),
            "game_seconds": round(timestamp * 2, 6),
            "width": rgb.width,
            "height": rgb.height,
            "rgb_sha256": hashlib.sha256(rgb.tobytes()).hexdigest(),
        })
container.close()

assert len(rows) == FREEZE["interval"]["expected_frames"] == len(RAW["frames"])
mismatches = [
    {"frame_index": actual["frame_index"],
     "actual_rgb_sha256": actual["rgb_sha256"],
     "frozen_rgb_sha256": frozen["rgb_sha256"]}
    for actual, frozen in zip(rows, RAW["frames"])
    if actual != frozen
]
result = {
    "disposition": "PASS_REPRODUCED" if not mismatches else "STOP_DECODER_REPRODUCIBILITY",
    "source_commit": SOURCE_COMMIT,
    "source_blob": blob,
    "source_sha256": digest,
    "pyav_version": av.__version__,
    "frame_count": len(rows),
    "matching_frame_count": len(rows) - len(mismatches),
    "mismatch_count": len(mismatches),
    "first_mismatches": mismatches[:5],
}
print(json.dumps(result, indent=2, sort_keys=True))
raise SystemExit(0 if not mismatches else 1)
