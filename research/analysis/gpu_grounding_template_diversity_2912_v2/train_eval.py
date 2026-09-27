"""Single frozen local training/evaluation allocation for Issue #4561."""
from __future__ import annotations

import copy
import hashlib
import json
import os
import time
from pathlib import Path

import numpy as np
import PIL
import torch
from PIL import Image

from adapter import candidate
from freeze_corpus import EXPECTED_PILLOW
from model import TinyCoordinateGrounder, loss_for
from render import FAMILIES, render, source_family_sha256


ROOT = Path(__file__).resolve().parent
OUTPUT = Path(os.environ.get("ISSUE4561_OUTPUT", ROOT / "results" / "formal01"))
SEEDS = (456101, 456102, 456103)
ARMS = ("narrow_2_families", "broad_8_families")
UPDATES = 400
BATCH = 16
LEARNING_RATE = 0.001
ACCEPT_MIN = 0.75
DEVICE = "cuda:0"


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def configure_determinism():
    if os.environ.get("CUBLAS_WORKSPACE_CONFIG") not in (":4096:8", ":16:8"):
        raise RuntimeError("CUBLAS_WORKSPACE_CONFIG must be set before Python starts")
    torch.use_deterministic_algorithms(True)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False


def corpus():
    frozen = json.loads((ROOT / "corpus_manifest.json").read_text(encoding="utf-8"))
    if PIL.__version__ != EXPECTED_PILLOW or frozen.get("pillow") != EXPECTED_PILLOW:
        raise RuntimeError("Pillow version does not match the pre-formal corpus freeze")
    frozen_rows = {row["image_id"]: row for row in frozen["images"]}
    if len(frozen_rows) != 48:
        raise RuntimeError("frozen corpus manifest must contain exactly 48 images")
    rows = []
    images = {}
    for spec in FAMILIES:
        for variant in range(4):
            image, label = render(spec, variant)
            raw = image.tobytes()
            key = f"{spec['id']}/variant-{variant}"
            image_path = OUTPUT / "corpus" / f"{spec['id']}__variant-{variant}.png"
            image_path.parent.mkdir(parents=True, exist_ok=True)
            image.save(image_path, format="PNG", optimize=False, compress_level=9)
            encoded = image_path.read_bytes()
            with Image.open(image_path) as check:
                decoded = np.asarray(check.convert("L"), dtype=np.uint8)
            if decoded.tobytes() != raw:
                raise ValueError(f"PNG round trip changed pixels: {key}")
            frozen_row = frozen_rows.get(key)
            if frozen_row is None or frozen_row["png_sha256"] != digest(encoded) or frozen_row["pixel_sha256"] != digest(raw):
                raise ValueError(f"rendered image differs from pre-formal frozen corpus: {key}")
            if any(frozen_row[field] != label[field] for field in
                   ("family_id", "family_sha256", "variant", "field_cell", "submit_cell", "field_point", "submit_point")):
                raise ValueError(f"rendered label differs from pre-formal frozen corpus: {key}")
            tensor = torch.from_numpy(decoded.copy()).float().div_(255.0).unsqueeze(0)
            images[key] = tensor
            rows.append({**label, "image_id": key, "image_path": image_path.relative_to(OUTPUT).as_posix(),
                         "pixel_sha256": digest(raw), "png_sha256": digest(encoded)})
    return rows, images


def family_split():
    return {"train_families": [f["id"] for f in FAMILIES[:8]],
            "heldout_families": [f["id"] for f in FAMILIES[8:]],
            "narrow_families": [f["id"] for f in FAMILIES[:2]]}


def train_arm(initial_state, seed, arm, rows, images):
    families = set(family_split()["narrow_families"] if arm == ARMS[0] else family_split()["train_families"])
    training = [r for r in rows if r["family_id"] in families]
    model = TinyCoordinateGrounder().to(DEVICE)
    model.load_state_dict(copy.deepcopy(initial_state))
    optimizer = torch.optim.Adam(model.parameters(), lr=LEARNING_RATE)
    gen = torch.Generator(device="cpu").manual_seed(seed + (10000 if arm == ARMS[0] else 20000))
    model.train()
    torch.cuda.reset_peak_memory_stats()
    started = time.perf_counter()
    loss_trace = []
    for step in range(UPDATES):
        picks = torch.randint(len(training), (BATCH,), generator=gen).tolist()
        selected = [training[i] for i in picks]
        x = torch.stack([images[r["image_id"]] for r in selected]).to(DEVICE)
        logits = model(x)
        loss = loss_for(logits, selected)
        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        optimizer.step()
        if step in (0, 99, 199, 299, 399):
            loss_trace.append({"step": step + 1, "loss": float(loss.detach().cpu())})
    seconds = time.perf_counter() - started
    peak = torch.cuda.max_memory_allocated()
    return model.eval(), {"steps": UPDATES, "seconds": seconds, "peak_vram_bytes": peak,
                          "loss_trace": loss_trace, "train_image_count": len(training),
                          "train_family_ids": sorted(families)}


def evaluate(model, rows, images, arm, seed):
    heldout = [r for r in rows if r["family_id"] in set(family_split()["heldout_families"])]
    output = []
    model.eval()
    with torch.no_grad():
        for row in heldout:
            logits = model(images[row["image_id"]].unsqueeze(0).to(DEVICE))[0]
            probs = torch.softmax(logits.flatten(1), dim=1)
            flat = probs.argmax(dim=1)
            predicted = [[int(v.item()) // 10, int(v.item()) % 10] for v in flat]
            confidence = [float(probs[i, flat[i]].item()) for i in range(2)]
            accepted = min(confidence) >= ACCEPT_MIN
            correct = predicted == [row["field_cell"], row["submit_cell"]]
            candidate_valid = False
            parsed = None
            if accepted:
                _, parsed = candidate(predicted[0], predicted[1])
                candidate_valid = True
            output.append({"seed": seed, "arm": arm, "family_id": row["family_id"],
                           "image_id": row["image_id"], "target_cells": [row["field_cell"], row["submit_cell"]],
                           "predicted_cells": predicted, "target_points": [row["field_point"], row["submit_point"]],
                           "confidence": confidence, "accepted": accepted,
                           "candidate_valid": candidate_valid, "parsed_candidate": parsed,
                           "exact_pair_correct": correct, "accepted_wrong": accepted and not correct})
    return output


def main():
    configure_determinism()
    if not torch.cuda.is_available() or torch.cuda.get_device_name(0) != "NVIDIA GeForce RTX 3080 Laptop GPU":
        raise RuntimeError("frozen local RTX 3080 CUDA device is unavailable")
    OUTPUT.mkdir(parents=True, exist_ok=False)
    rows, images = corpus()
    split = family_split()
    results, metadata = [], []
    for seed in SEEDS:
        torch.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)
        cpu_initial = TinyCoordinateGrounder()
        initial_state = copy.deepcopy(cpu_initial.state_dict())
        for arm in ARMS:
            model, timing = train_arm(initial_state, seed, arm, rows, images)
            metadata.append({"seed": seed, "arm": arm, **timing})
            results.extend(evaluate(model, rows, images, arm, seed))
    matrix = {"seed": SEEDS, "arms": ARMS, "updates_per_arm": UPDATES, "batch": BATCH,
              "learning_rate": LEARNING_RATE, "accept_min": ACCEPT_MIN}
    raw = {"schema": "issue4561-template-diversity-formal-v1", "split": split,
           "renderer": {"id": "issue4561-pillow-10.4.0-raster-v1", "families": [
               {"family_id": f["id"], "family_sha256": source_family_sha256(f)} for f in FAMILIES]},
           "matrix": matrix, "metadata": metadata, "cases": results,
           "environment": {"python_torch": torch.__version__, "cuda": torch.version.cuda,
                           "gpu": torch.cuda.get_device_name(0), "device": DEVICE}}
    path = OUTPUT / "results.json"
    path.write_text(json.dumps(raw, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "FORMAL_COMPLETE", "case_count": len(results),
                      "updates_total": len(metadata) * UPDATES, "result_sha256": digest(path.read_bytes())},
                     sort_keys=True))


if __name__ == "__main__":
    main()
