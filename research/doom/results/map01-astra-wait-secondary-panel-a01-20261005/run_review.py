"""Decode and retain the frozen decision-4 video interval for manual review."""
import av
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import subprocess
from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
SOURCE_COMMIT = "81a59aed13492ba1d52ea80e03d48c3d8de7b2c5"
VIDEO_PATH = "research/doom/results/map01-astra-attempt-v1/map01-astra-live-01-2x.mp4"
VIDEO_BLOB = "983e2f43e878b56d0d05cd4d7db5125a55566cc8"
VIDEO_SHA256 = "201ab6aaa8ab5823285b44864ad1df899ebe5a19c97ec6e84b8cc5db063f6be4"
START = 22.3
END = 28.2
SAMPLE_INDICES = {223, 248, 252, 281, 282}


def source_bytes():
    blob = subprocess.run(
        ["git", "rev-parse", f"{SOURCE_COMMIT}:{VIDEO_PATH}"],
        cwd=ROOT, check=True, capture_output=True, text=True).stdout.strip()
    if blob != VIDEO_BLOB:
        raise RuntimeError(f"video blob mismatch: {blob}")
    data = subprocess.run(
        ["git", "show", f"{SOURCE_COMMIT}:{VIDEO_PATH}"],
        cwd=ROOT, check=True, capture_output=True).stdout
    if hashlib.sha256(data).hexdigest() != VIDEO_SHA256:
        raise RuntimeError("video SHA-256 mismatch")
    return data


def main():
    data = source_bytes()
    container = av.open(io.BytesIO(data))
    selected = []
    rows = []
    thumbs = []
    for index, frame in enumerate(container.decode(video=0)):
        timestamp = float(frame.pts * frame.time_base)
        if START <= timestamp <= END:
            image = frame.to_image().convert("RGB")
            row = {
                "frame_index": index,
                "video_seconds": round(timestamp, 6),
                "game_seconds": round(timestamp * 2, 6),
                "width": image.width, "height": image.height,
                "rgb_sha256": hashlib.sha256(image.tobytes()).hexdigest(),
            }
            rows.append(row)
            thumbs.append(image.resize((320, 280), Image.Resampling.LANCZOS))
            if index in SAMPLE_INDICES:
                selected.append((row, image))
    container.close()

    if len(rows) != 60 or rows[0]["frame_index"] != 223 or rows[-1]["frame_index"] != 282:
        raise RuntimeError("frozen interval did not decode to the expected 60 frames")

    frames_dir = HERE / "samples"
    frames_dir.mkdir(exist_ok=True)
    for row, image in selected:
        image.save(frames_dir / f"frame-{row['frame_index']:03d}.png")

    sheets_dir = HERE / "contact-sheets"
    sheets_dir.mkdir(exist_ok=True)
    for sheet_index in range(5):
        group_rows = rows[sheet_index * 12:(sheet_index + 1) * 12]
        sheet = Image.new("RGB", (960, 1200), (24, 24, 24))
        draw = ImageDraw.Draw(sheet)
        for offset, row in enumerate(group_rows):
            thumb = thumbs[sheet_index * 12 + offset]
            x, y = (offset % 3) * 320, (offset // 3) * 300
            sheet.paste(thumb, (x, y + 20))
            draw.text((x + 5, y + 3),
                      f"frame {row['frame_index']} | game {row['game_seconds']:.1f}s",
                      fill="white")
        sheet.save(sheets_dir / f"sheet-{sheet_index + 1}.png")

    review = json.loads((HERE / "MANUAL_REVIEW.json").read_text(encoding="utf-8"))
    raw = {
        "schema": "map01-astra-secondary-panel-raw-v1",
        "experiment_id": "map01-astra-wait-secondary-panel-a01-20261005",
        "source_commit": SOURCE_COMMIT,
        "video_path": VIDEO_PATH,
        "video_blob": VIDEO_BLOB,
        "video_bytes": len(data),
        "video_sha256": hashlib.sha256(data).hexdigest(),
        "pyav_version": av.__version__,
        "completed_at_utc": datetime.now(timezone.utc).isoformat(),
        "interval": {"video_seconds": [START, END], "game_seconds": [START * 2, END * 2],
                     "decoded_frame_count": len(rows)},
        "frames": rows,
        "manual_review_disposition": review["disposition"],
        "scope": "posthoc full-frame video review; panel source and controller availability unknown",
    }
    raw_path = HERE / "raw.json"
    if raw_path.exists():
        raise RuntimeError("raw.json exists; refusing to overwrite retained output")
    raw_path.write_text(json.dumps(raw, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"video_sha256": raw["video_sha256"],
                      "frame_count": len(rows),
                      "selected": [row for row, _ in selected],
                      "manual_review_disposition": raw["manual_review_disposition"],
                      "raw": str(HERE / "raw.json")}, indent=2))


if __name__ == "__main__":
    main()
