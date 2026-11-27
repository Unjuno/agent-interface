from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import math
from pathlib import Path

import numpy as np
from PIL import Image


HERE = Path(__file__).resolve().parent
FREEZE = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def auc(scores: list[float], labels: list[bool]) -> float:
    positives = [x for x, label in zip(scores, labels) if label]
    negatives = [x for x, label in zip(scores, labels) if not label]
    return sum(1.0 if p > n else 0.5 if p == n else 0.0 for p in positives for n in negatives) / (len(positives) * len(negatives))


def best_global_shift(a: np.ndarray, b: np.ndarray, limit: int) -> tuple[int, int]:
    best = None
    h, w = a.shape
    for dy in range(-limit, limit + 1):
        for dx in range(-limit, limit + 1):
            y0, y1 = max(0, dy), min(h, h + dy)
            x0, x1 = max(0, dx), min(w, w + dx)
            left = a[y0:y1, x0:x1]
            right = b[y0 - dy:y1 - dy, x0 - dx:x1 - dx]
            left = left - left.mean()
            right = right - right.mean()
            den = math.sqrt(float(np.sum(left * left)) * float(np.sum(right * right)))
            corr = float(np.sum(left * right) / den) if den else -1.0
            choice = (corr, -abs(dx) - abs(dy), -dy, -dx, dy, dx)
            if best is None or choice > best:
                best = choice
    return best[4], best[5]


def global_residual(a: np.ndarray, b: np.ndarray, dy: int, dx: int) -> float:
    h, w = a.shape[:2]
    y0, y1 = max(0, dy), min(h, h + dy)
    x0, x1 = max(0, dx), min(w, w + dx)
    left = a[y0:y1, x0:x1].astype(np.int16)
    right = b[y0 - dy:y1 - dy, x0 - dx:x1 - dx].astype(np.int16)
    return float(np.abs(left - right).mean())


def downsample(gray: np.ndarray, factor: int) -> np.ndarray:
    h = (gray.shape[0] // factor) * factor
    w = (gray.shape[1] // factor) * factor
    return gray[:h, :w].reshape(h // factor, factor, w // factor, factor).mean((1, 3))


def best_tile_shift(a: np.ndarray, b: np.ndarray, y: int, x: int, size: int, radius: int) -> tuple[int, int]:
    source = a[y:y + size, x:x + size]
    best = None
    for dy in range(-radius, radius + 1):
        for dx in range(-radius, radius + 1):
            yy, xx = y - dy, x - dx
            target = b[yy:yy + size, xx:xx + size]
            left = source - source.mean()
            right = target - target.mean()
            den = math.sqrt(float(np.sum(left * left)) * float(np.sum(right * right)))
            corr = float(np.sum(left * right) / den) if den else -1.0
            choice = (corr, -abs(dx) - abs(dy), -dy, -dx, dy, dx)
            if best is None or choice > best:
                best = choice
    return best[4], best[5]


def block_residual(a_gray: np.ndarray, b_gray: np.ndarray, a_rgb: np.ndarray, b_rgb: np.ndarray,
                   factor: int, size: int, radius: int, rows: int, columns: int) -> tuple[float, list[dict]]:
    tile_rows, tile_columns = a_gray.shape[0] // size, a_gray.shape[1] // size
    shifts: list[dict] = []
    residuals: list[float] = []
    for row in range(rows, tile_rows - rows):
        for col in range(columns, tile_columns - columns):
            y, x = row * size, col * size
            dy, dx = best_tile_shift(a_gray, b_gray, y, x, size, radius)
            y0, x0 = y * factor, x * factor
            span = size * factor
            yy, xx = y0 - dy * factor, x0 - dx * factor
            left = a_rgb[y0:y0 + span, x0:x0 + span].astype(np.int16)
            right = b_rgb[yy:yy + span, xx:xx + span].astype(np.int16)
            residual = float(np.abs(left - right).mean())
            residuals.append(residual)
            shifts.append({"row": row, "column": col, "dy_downsampled": dy, "dx_downsampled": dx,
                           "residual_rgb_mae": residual})
    expected = (tile_rows - 2 * rows) * (tile_columns - 2 * columns)
    if len(residuals) != expected or expected != 32:
        raise ValueError(f"unexpected fixed interior tile count: {len(residuals)} (expected {expected})")
    return float(np.mean(residuals)), shifts


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", required=True, type=Path)
    args = parser.parse_args()
    root = args.repo_root.resolve()
    run = root / "research/doom/results" / FREEZE["episode"]
    manifest_bytes = (run / "retention-manifest.json").read_bytes()
    events_bytes = (run / "runtime/events.jsonl").read_bytes()
    if sha(manifest_bytes) != FREEZE["source_hashes"]["manifest_sha256"]:
        raise ValueError("retention manifest hash changed")
    if sha(events_bytes) != FREEZE["source_hashes"]["events_sha256"]:
        raise ValueError("event log hash changed")
    manifest = json.loads(manifest_bytes)
    declared = {row["path"]: row["sha256"] for row in manifest["files"]}
    events = [json.loads(line) for line in events_bytes.splitlines() if line.strip()]
    sequences = FREEZE["evaluation"]["sequences"]
    typed = {row["sequence"]: row for row in events if row.get("event") == "typed_observation" and row.get("sequence") in sequences}
    plain = {row["sequence"]: row for row in events if row.get("event") == "observation" and row.get("sequence") in sequences}
    if len(typed) != 53 or len(plain) != 53:
        raise ValueError("expected 53 typed and plain observations")
    x0, y0, x1, y1 = FREEZE["candidate"]["world_crop_xyxy"]
    factor = FREEZE["candidate"]["downsample_factor"]
    tile_size = FREEZE["candidate"]["tile_size_downsampled_px"]
    radius = FREEZE["candidate"]["search_radius_downsampled_px"]
    rows = FREEZE["candidate"]["grid"]["exclude_border_rows"]
    cols = FREEZE["candidate"]["grid"]["exclude_border_columns"]
    frames: dict[int, np.ndarray] = {}
    frame_hashes: dict[int, str] = {}
    for seq in sequences:
        rel = f"runtime/{seq:03d}.png"
        path = run / rel
        raw = path.read_bytes()
        if sha(raw) != declared[rel]:
            raise ValueError(f"PNG hash mismatch for {rel}")
        image = np.asarray(Image.open(path).convert("RGB"))
        if sha(image.tobytes()) != typed[seq]["frame_rgb_sha256"]:
            raise ValueError(f"typed RGB hash mismatch for sequence {seq}")
        frames[seq] = image[y0:y1, x0:x1].copy()
        frame_hashes[seq] = sha(raw)
    pair_rows: list[dict] = []
    raw_scores: list[float] = []
    global_scores: list[float] = []
    block_scores: list[float] = []
    labels: list[bool] = []
    for first, second in zip(sequences[:-1], sequences[1:]):
        a_rgb, b_rgb = frames[first], frames[second]
        raw = float(np.abs(a_rgb.astype(np.int16) - b_rgb.astype(np.int16)).mean())
        a_gray = downsample(a_rgb[:, :, 0] * .299 + a_rgb[:, :, 1] * .587 + a_rgb[:, :, 2] * .114, factor)
        b_gray = downsample(b_rgb[:, :, 0] * .299 + b_rgb[:, :, 1] * .587 + b_rgb[:, :, 2] * .114, factor)
        g_dy, g_dx = best_global_shift(a_gray, b_gray, radius)
        global_score = global_residual(a_rgb, b_rgb, g_dy * factor, g_dx * factor)
        block_score, tile_shifts = block_residual(a_gray, b_gray, a_rgb, b_rgb, factor, tile_size, radius, rows, cols)
        loss_points = typed[first]["signals"]["health"]["value"] - typed[second]["signals"]["health"]["value"]
        label = loss_points > 0
        row = {"from": first, "to": second, "from_png_sha256": frame_hashes[first], "to_png_sha256": frame_hashes[second],
               "health_loss_points": loss_points, "health_loss": label, "world_raw_rgb_mae": raw,
               "global_translation_rgb_mae": global_score, "global_shift_downsampled": {"dy": g_dy, "dx": g_dx},
               "blockwise_rgb_mae": block_score, "tiles": tile_shifts}
        pair_rows.append(row)
        raw_scores.append(raw)
        global_scores.append(global_score)
        block_scores.append(block_score)
        labels.append(label)
    if len(pair_rows) != 52 or sum(labels) != 4:
        raise ValueError("unexpected pair or health-loss count")
    no_loss = [score for score, label in zip(block_scores, labels) if not label]
    threshold = float(np.median(no_loss))
    above = sum(score > threshold for score, label in zip(block_scores, labels) if label)
    raw_auc, global_auc, block_auc = auc(raw_scores, labels), auc(global_scores, labels), auc(block_scores, labels)
    criterion = block_auc >= .75 and block_auc - raw_auc >= .10 and above >= 3
    result = {
        "schema": "issue59-camera-block-motion-r02-v1",
        "status": "PASS_SCOPED" if criterion else "FAIL_SCOPED",
        "freeze": FREEZE,
        "n_pairs": len(pair_rows),
        "n_health_loss_pairs": sum(labels),
        "metrics": {"world_raw_auc": raw_auc, "global_translation_auc": global_auc,
                    "blockwise_compensated_auc": block_auc, "auc_gain_vs_raw": block_auc - raw_auc,
                    "health_loss_pairs_above_blockwise_no_loss_median": above,
                    "blockwise_no_loss_median": threshold,
                    "scored_tiles_per_pair": 32, "full_resolution_pixels_per_pair": 32 * 64 * 64},
        "criterion_met": criterion,
        "rows": pair_rows,
        "scope": "same single retained V39 episode as R01; objective typed health-loss labels only; exploratory offline method screen, not independent data, semantic threat detector, live control, task effect, or causal gameplay evidence"
    }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
