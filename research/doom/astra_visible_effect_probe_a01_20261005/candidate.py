#!/usr/bin/env python3
"""Frozen pixel-transition probe for one retained, edited MAP01 video interval."""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import numpy as np

VIDEO = Path(sys.argv[1])
RAW_OUT = Path(sys.argv[2])
WIDTH, HEIGHT, FPS = 320, 280, 5
START, END = 21.5, 23.5
THRESHOLD = 40

cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-ss", str(START), "-i", str(VIDEO), "-t", str(END-START), "-vf", f"fps={FPS},scale={WIDTH}:{HEIGHT}", "-f", "rawvideo", "-pix_fmt", "rgb24", "pipe:1"]
proc = subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
frame_bytes = WIDTH * HEIGHT * 3
if len(proc.stdout) % frame_bytes:
    raise SystemExit("STOP_PARTIAL_FRAME_STREAM")
frames = np.frombuffer(proc.stdout, dtype=np.uint8).reshape((-1, HEIGHT, WIDTH, 3))
rows = []
prev = None
for i, frame in enumerate(frames):
    rgb = frame.astype(np.int16)
    roi = np.zeros((HEIGHT, WIDTH), dtype=bool)
    roi[30:230, :] = True
    roi[145:230, 130:190] = False
    red, green, blue = rgb[:,:,0], rgb[:,:,1], rgb[:,:,2]
    warm = roi & (red >= 170) & (green >= 45) & (green <= 190) & (blue <= 95) & (red >= green * 1.25)
    newly_warm = warm if prev is None else (warm & ~prev)
    count = int(newly_warm.sum())
    ts = START + i / FPS
    rows.append({"frame": i, "video_time_s": round(ts, 3), "new_warm_pixels": count,
                 "trigger": bool(prev is not None and count >= THRESHOLD)})
    prev = warm
payload = {"format": "astra_visible_effect_probe_a01_v1", "source_video_sha256": hashlib.sha256(VIDEO.read_bytes()).hexdigest(),
           "command": cmd, "frame_count": len(frames), "threshold": THRESHOLD, "rows": rows}
RAW_OUT.write_text(json.dumps(payload, indent=2) + "\n")
print(json.dumps({"frame_count": len(frames), "first_trigger": next((r for r in rows if r["trigger"]), None),
                  "baseline_triggers": [r for r in rows if r["trigger"] and r["video_time_s"] < 22.0],
                  "positive_window_triggers": [r for r in rows if r["trigger"] and 22.0 <= r["video_time_s"] < 23.5],
                  "source_video_sha256": payload["source_video_sha256"]}, indent=2))
