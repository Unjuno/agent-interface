#!/usr/bin/env python3
"""Verify sample selection, retained-source identity, pixel counts, and summary."""
import hashlib
import json
import random
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SAMPLE = json.loads((HERE / "SAMPLE.json").read_text(encoding="utf-8"))
FREEZE = json.loads((HERE / "SAMPLE_FREEZE.json").read_text(encoding="utf-8"))
LABELS_DOC = json.loads((HERE / "BLIND_LABELS.json").read_text(encoding="utf-8"))
OUTPUT = json.loads((HERE / "OUTPUT.json").read_text(encoding="utf-8"))
COMMIT = SAMPLE["commit"]
CURRENT = "1aaa633c4f1aeec25e4b4617d92dd93af3b20603"
BASE = "research/doom/results/map01-v39-coast-liveness-live-01"
checks = {}

manifest = json.loads(subprocess.run(
    ["git", "show", f"{CURRENT}:{BASE}/retention-manifest.json"],
    check=True, stdout=subprocess.PIPE).stdout)
manifest_files = {entry["path"]: entry for entry in manifest["files"]}
source_manifest = json.loads(subprocess.run(
    ["git", "show", f"{COMMIT}:{BASE}/retention-manifest.json"],
    check=True, stdout=subprocess.PIPE).stdout)
source_manifest_files = {entry["path"]: entry for entry in source_manifest["files"]}
population = [n for n in range(1, 219) if n != 151]
rng = random.Random(FREEZE["seed"])
sampled = sorted(rng.sample(population, FREEZE["sample_n"]))
permutation = list(range(FREEZE["sample_n"]))
rng.shuffle(permutation)
expected = {f"F{permutation[i] + 1:02d}": seq
            for i, seq in enumerate(sampled)}
checks["deterministic_sample_and_opaque_mapping"] = (
    {row["code"]: row["sequence"] for row in SAMPLE["entries"]} == expected)
checks["source_commit_pinned"] = (COMMIT == "dd9c2cde511a52cf21e80ecbb2eb9edb0dd6f2f8")
canonical_frame_hashes = "\n".join(
    f"{row['code']} {row['sha256']}" for row in sorted(SAMPLE["entries"],
                                                       key=lambda item: item["code"])) + "\n"
checks["sample_freeze_digest"] = hashlib.sha256(
    canonical_frame_hashes.encode()).hexdigest() == FREEZE["frames_sha256"]
checks["36_unique_frames"] = (
    len(SAMPLE["entries"]) == 36 and
    len({row["sequence"] for row in SAMPLE["entries"]}) == 36 and
    len({row["code"] for row in SAMPLE["entries"]}) == 36)
checks["known_missing_frame_excluded"] = 151 not in expected.values()

provenance_ok = True
for row in SAMPLE["entries"]:
    rel = f"runtime/{row['sequence']:03d}.png"
    retained = manifest_files.get(rel)
    frozen = source_manifest_files.get(rel)
    image = ROOT / BASE / rel
    if retained is None or frozen is None or not image.is_file():
        provenance_ok = False
        continue
    data = image.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    if (len(data) != row["bytes"] or digest != row["sha256"] or
            len(data) != retained["bytes"] or digest != retained["sha256"]):
        provenance_ok = False
    if len(data) != frozen["bytes"] or digest != frozen["sha256"]:
        provenance_ok = False
checks["sample_hashes_match_current_retention_manifest"] = provenance_ok

labels = {row["code"]: row["enemy_visible"] for row in LABELS_DOC["labels"]}
checks["complete_label_inventory"] = (
    len(labels) == 36 and set(labels) == set(expected) and
    all(value in {"present", "absent", "uncertain"} for value in labels.values()))
rows = OUTPUT["rows"]
checks["output_row_inventory"] = (
    len(rows) == 36 and {row["code"] for row in rows} == set(expected))
sample_by_code = {row["code"]: row for row in SAMPLE["entries"]}
checks["output_rows_bind_to_frozen_sources"] = all(
    row["sequence"] == sample_by_code[row["code"]]["sequence"] and
    row["source_sha256"] == sample_by_code[row["code"]]["sha256"]
    for row in rows)

# Independent recount through ImageMagick; labels remain untouched during recount.
recount_ok = True
for row in rows:
    path = ROOT / BASE / "runtime" / f"{row['sequence']:03d}.png"
    raw = subprocess.run(
        ["magick", str(path), "-crop", "380x270+450+250", "+repage",
         "-depth", "8", "RGB:-"], check=True, stdout=subprocess.PIPE).stdout
    if len(raw) != 380 * 270 * 3:
        recount_ok = False
        continue
    yellow = red = 0
    for i in range(0, len(raw), 3):
        r, g, b = raw[i:i + 3]
        yellow += r > 180 and g > 100 and b < 100 and r > 0.8 * g and g > 1.5 * b
        red += r > 70 and r > 1.25 * g and r > 1.25 * b
    if yellow != row["yellow_count"] or red != row["red_count"]:
        recount_ok = False
checks["independent_pixel_count_recomputation"] = recount_ok

known = [row for row in rows if labels[row["code"]] != "uncertain"]
tp = sum(row["yellow_gt_200"] and labels[row["code"]] == "present" for row in known)
fp = sum(row["yellow_gt_200"] and labels[row["code"]] == "absent" for row in known)
fn = sum(not row["yellow_gt_200"] and labels[row["code"]] == "present" for row in known)
tn = sum(not row["yellow_gt_200"] and labels[row["code"]] == "absent" for row in known)
checks["recorded_blind_labels_match_join"] = all(
    row["enemy_visible"] == labels[row["code"]] for row in rows)
checks["recorded_confusion_table"] = (tp, fp, fn, tn) == (3, 0, 13, 18)
checks["result_scope_is_exploratory"] = (
    "single-episode" in (HERE / "README.md").read_text(encoding="utf-8"))
status = "PASS_PROVENANCE_AND_RECOMPUTATION" if all(checks.values()) else "FAIL_AUDIT"
audit = {"status": status, "checks": checks,
         "confusion": {"tp": tp, "fp": fp, "fn": fn, "tn": tn,
                       "uncertain_excluded": sum(v == "uncertain" for v in labels.values())}}
(HERE / "AUDIT.json").write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
print(json.dumps(audit, indent=2))
raise SystemExit(0 if all(checks.values()) else 1)
