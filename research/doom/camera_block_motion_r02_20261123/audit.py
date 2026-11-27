from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

import numpy as np
from PIL import Image


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def rank_auc(values: list[float], labels: list[bool]) -> float:
    pos = [value for value, label in zip(values, labels) if label]
    neg = [value for value, label in zip(values, labels) if not label]
    numerator = 0.0
    for p in pos:
        for n in neg:
            numerator += 1 if p > n else .5 if p == n else 0
    return numerator / (len(pos) * len(neg))


def candidate_shift(src: np.ndarray, dst: np.ndarray, y: int, x: int, tile: int, bound: int) -> tuple[int, int]:
    patch = src[y:y + tile, x:x + tile]
    best_score = None
    best_delta = None
    for vertical in range(-bound, bound + 1):
        for horizontal in range(-bound, bound + 1):
            other = dst[y - vertical:y - vertical + tile, x - horizontal:x - horizontal + tile]
            p = patch - np.mean(patch)
            q = other - np.mean(other)
            energy = float(np.sum(p * p)) * float(np.sum(q * q))
            corr = float(np.sum(p * q) / math.sqrt(energy)) if energy else -1.0
            key = (corr, -(abs(horizontal) + abs(vertical)), -vertical, -horizontal)
            if best_score is None or key > best_score:
                best_score, best_delta = key, (vertical, horizontal)
    assert best_delta is not None
    return best_delta


def audit(repo: Path, result_path: Path) -> dict:
    result = json.loads(result_path.read_text(encoding="utf-8"))
    freeze = json.loads((result_path.parent / "FREEZE.json").read_text(encoding="utf-8"))
    if result.get("freeze") != freeze:
        raise ValueError("result does not match the committed freeze")
    episode = repo / "research/doom/results" / freeze["episode"]
    manifest_data = (episode / "retention-manifest.json").read_bytes()
    event_data = (episode / "runtime/events.jsonl").read_bytes()
    if digest(manifest_data) != freeze["source_hashes"]["manifest_sha256"]:
        raise ValueError("retention manifest SHA-256 mismatch")
    if digest(event_data) != freeze["source_hashes"]["events_sha256"]:
        raise ValueError("event stream SHA-256 mismatch")
    manifest = json.loads(manifest_data)
    file_hashes = {entry["path"]: entry["sha256"] for entry in manifest["files"]}
    events = [json.loads(line) for line in event_data.splitlines() if line.strip()]
    sequences = freeze["evaluation"]["sequences"]
    typed = {event["sequence"]: event for event in events
             if event.get("event") == "typed_observation" and event.get("sequence") in sequences}
    if len(typed) != 53:
        raise ValueError("expected 53 unique typed observations")
    x0, y0, x1, y1 = freeze["candidate"]["world_crop_xyxy"]
    factor = freeze["candidate"]["downsample_factor"]
    tile = freeze["candidate"]["tile_size_downsampled_px"]
    radius = freeze["candidate"]["search_radius_downsampled_px"]
    border_y = freeze["candidate"]["grid"]["exclude_border_rows"]
    border_x = freeze["candidate"]["grid"]["exclude_border_columns"]
    frames: dict[int, np.ndarray] = {}
    for seq in sequences:
        rel = f"runtime/{seq:03d}.png"
        raw = (episode / rel).read_bytes()
        if digest(raw) != file_hashes[rel]:
            raise ValueError(f"PNG hash mismatch: {rel}")
        rgb = np.asarray(Image.open(episode / rel).convert("RGB"))
        if digest(rgb.tobytes()) != typed[seq]["frame_rgb_sha256"]:
            raise ValueError(f"typed RGB hash mismatch: {seq}")
        frames[seq] = rgb[y0:y1, x0:x1].copy()
    rows = result["rows"]
    if len(rows) != 52:
        raise ValueError("expected 52 adjacent pairs")
    raw_values: list[float] = []
    global_values: list[float] = []
    block_values: list[float] = []
    labels: list[bool] = []
    for index, (first, second) in enumerate(zip(sequences[:-1], sequences[1:])):
        row = rows[index]
        if (row["from"], row["to"]) != (first, second):
            raise ValueError(f"sequence mismatch in row {index}")
        a, b = frames[first], frames[second]
        loss = typed[first]["signals"]["health"]["value"] - typed[second]["signals"]["health"]["value"]
        label = loss > 0
        raw = float(np.mean(np.abs(a.astype(np.int16) - b.astype(np.int16))))
        ga = a[:, :, 0] * .299 + a[:, :, 1] * .587 + a[:, :, 2] * .114
        gb = b[:, :, 0] * .299 + b[:, :, 1] * .587 + b[:, :, 2] * .114
        height = (ga.shape[0] // factor) * factor
        width = (ga.shape[1] // factor) * factor
        ga = ga[:height, :width].reshape(height // factor, factor, width // factor, factor).mean((1, 3))
        gb = gb[:height, :width].reshape(height // factor, factor, width // factor, factor).mean((1, 3))

        # Recompute the R01 global-translation anchor with its full-crop overlap.
        best = None
        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
                ya, yb = max(0, dy), min(ga.shape[0], ga.shape[0] + dy)
                xa, xb = max(0, dx), min(ga.shape[1], ga.shape[1] + dx)
                left, right = ga[ya:yb, xa:xb], gb[ya - dy:yb - dy, xa - dx:xb - dx]
                left, right = left - left.mean(), right - right.mean()
                den = math.sqrt(float(np.sum(left * left)) * float(np.sum(right * right)))
                corr = float(np.sum(left * right) / den) if den else -1.0
                key = (corr, -abs(dx) - abs(dy), -dy, -dx, dy, dx)
                if best is None or key > best:
                    best = key
        gdy, gdx = best[4] * factor, best[5] * factor
        ya, yb = max(0, gdy), min(a.shape[0], a.shape[0] + gdy)
        xa, xb = max(0, gdx), min(a.shape[1], a.shape[1] + gdx)
        aligned_a = a[ya:yb, xa:xb].astype(np.int16)
        aligned_b = b[ya - gdy:yb - gdy, xa - gdx:xb - gdx].astype(np.int16)
        global_mae = float(np.mean(np.abs(aligned_a - aligned_b)))

        # Independent exhaustive local tile recomputation.
        block_rows, block_columns = ga.shape[0] // tile, ga.shape[1] // tile
        tile_maes: list[float] = []
        shifts: list[dict] = []
        for tr in range(border_y, block_rows - border_y):
            for tc in range(border_x, block_columns - border_x):
                dy, dx = candidate_shift(ga, gb, tr * tile, tc * tile, tile, radius)
                y, x = tr * tile * factor, tc * tile * factor
                span = tile * factor
                source = a[y:y + span, x:x + span].astype(np.int16)
                target = b[y - dy * factor:y - dy * factor + span,
                           x - dx * factor:x - dx * factor + span].astype(np.int16)
                score = float(np.mean(np.abs(source - target)))
                tile_maes.append(score)
                shifts.append({"row": tr, "column": tc, "dy_downsampled": dy,
                               "dx_downsampled": dx, "residual_rgb_mae": score})
        block_mae = float(np.mean(tile_maes))
        for field, actual in (("health_loss_points", loss), ("health_loss", label),
                              ("world_raw_rgb_mae", raw), ("global_translation_rgb_mae", global_mae),
                              ("blockwise_rgb_mae", block_mae)):
            expected = row[field]
            if isinstance(actual, float):
                if not math.isclose(expected, actual, rel_tol=1e-12, abs_tol=1e-12):
                    raise ValueError(f"{field} mismatch row {index}: {expected} != {actual}")
            elif expected != actual:
                raise ValueError(f"{field} mismatch row {index}")
        if row["tiles"] != shifts:
            raise ValueError(f"per-tile shift/raw mismatch row {index}")
        raw_values.append(raw)
        global_values.append(global_mae)
        block_values.append(block_mae)
        labels.append(label)
    raw_auc = rank_auc(raw_values, labels)
    global_auc = rank_auc(global_values, labels)
    block_auc = rank_auc(block_values, labels)
    median = float(np.median([value for value, label in zip(block_values, labels) if not label]))
    above = sum(value > median for value, label in zip(block_values, labels) if label)
    criterion = block_auc >= .75 and block_auc - raw_auc >= .10 and above >= 3
    if not math.isclose(raw_auc, 5 / 12, abs_tol=1e-12) or not math.isclose(global_auc, 13 / 32, abs_tol=1e-12):
        raise ValueError(f"R01 anchor mismatch: raw={raw_auc}, global={global_auc}")
    if criterion != result["criterion_met"] or result["metrics"]["blockwise_compensated_auc"] != block_auc:
        raise ValueError("frozen criterion or AUC does not match recomputation")
    return {"schema": "issue59-camera-block-motion-r02-audit-v1", "status": "PASS_EVIDENCE_AND_RECOMPUTATION_SCOPED",
            "source_main": freeze["current_main"], "pairs_recomputed": len(rows), "health_loss_pairs": sum(labels),
            "metrics_recomputed": {"world_raw_auc": raw_auc, "global_translation_auc": global_auc,
                                   "blockwise_compensated_auc": block_auc, "gain_vs_raw": block_auc - raw_auc,
                                   "loss_pairs_above_median": above},
            "checks": ["source manifest/event SHA-256", "all source PNG hashes", "typed RGB hashes and health labels",
                       "52 raw/global/blockwise scores", "all 1,664 per-tile selected offsets and RGB residuals",
                       "original R01 raw/global AUC anchor", "frozen acceptance criterion"],
            "scope": "same single offline episode as R01; not independent data or semantic threat/control evidence"}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", required=True, type=Path)
    parser.add_argument("--result", required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(audit(args.repo_root.resolve(), args.result.resolve()), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
