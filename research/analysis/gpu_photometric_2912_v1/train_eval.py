#!/usr/bin/env python3
"""One-shot, source-bound two-arm GPU photometric augmentation comparison."""
import hashlib
import json
import math
import os
import platform
import sys
import time
from pathlib import Path

import numpy as np
import torch
from PIL import Image
from torch import nn


SEED = 2912
STEPS = 300
BATCH = 16
LAYOUTS = ("A", "B")
TRAIN_IDS = ("task-1", "task-2", "task-4", "task-5")
HELD_IDS = ("task-3", "task-6")
EVAL_TRANSFORMS = (("original", 1.0), ("dark_0.85", 0.85), ("bright_1.15", 1.15))
EXPECTED_MANIFEST_SHA256 = "5af3901c0d579bf1e65ff9d36931fa033f116de5f66a156670d8d650851497b0"
EXPECTED_IMAGES = {
    "task-1": "3fd0c515a1f0358fb4afa328f60d2a1b82a748018ff4295fad5ec3922f3640ec",
    "task-2": "8ce9f5bdb642592122e0f7ed2c84656729564ced3d25c14af6b787c71ef8ce7a",
    "task-3": "3e81cc92439d01aeabd69c8cfd9f2a2eb842b3433f41771fe3b0409e331f9349",
    "task-4": "ae2974269932d767fbfba536287c2f8c02c1ffb77efaed6c3c87b20c250fbad4",
    "task-5": "7216758322e41ff158751f70623401089df7080011fdac5c9ea59ea7b49b559a",
    "task-6": "ccc8662251de86ee477e8ff149ce19c67de8e26bb93f5ead264fe268438118bd",
}


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def read_image(repo, record, factor=1.0):
    path = repo / record["image"]
    raw = path.read_bytes()
    actual = sha256(raw)
    if actual != EXPECTED_IMAGES[record["task_id"]] or actual != record["image_sha256"]:
        raise ValueError(f"source image hash mismatch: {record['task_id']}")
    with Image.open(path) as im:
        original_size = list(im.size)
        arr = np.asarray(im.convert("RGB"), dtype=np.uint8)
    if factor != 1.0:
        arr = np.clip(np.floor(arr.astype(np.float32) * factor + 0.5), 0, 255).astype(np.uint8)
    image = Image.fromarray(arr, mode="RGB").convert("L").resize((160, 100), Image.Resampling.BILINEAR)
    x = np.asarray(image, dtype=np.float32) / 255.0
    return torch.from_numpy(x.copy()).unsqueeze(0), sha256(arr.tobytes()), original_size


class TinyGrounder(nn.Module):
    def __init__(self):
        super().__init__()
        self.features = nn.Sequential(
            nn.Conv2d(1, 8, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2),
            nn.Conv2d(8, 16, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2),
            nn.AdaptiveAvgPool2d((8, 10)), nn.Flatten(),
            nn.Linear(1280, 32), nn.ReLU(), nn.Linear(32, 2),
        )

    def forward(self, x):
        return self.features(x)


def compile_candidate(layout, points):
    field, submit = points[layout]
    method = {
        "first_action": "enter_exact_token",
        "continue_when": "field_pixels_changed_and_submit_revalidated",
        "second_action": "activate_submit",
        "complete_when": "submission_pixels_changed_then_independent_score",
    }
    def target(point):
        return {"point_space": "source_observation_pixels",
                "point": {"x": int(point[0]), "y": int(point[1])},
                "motion_model": "surface_origin_translation"}
    return {"format": "compiled-form-grounding-v1",
            "field": target(field), "submit": target(submit), "method": method}


def main():
    repo = Path(os.environ.get("REPO_ROOT", "/repo")).resolve()
    out = Path(os.environ.get("RESULT_ROOT", "/out")).resolve()
    out.mkdir(parents=True, exist_ok=True)
    manifest_path = repo / "research/analysis/local_model_2912_image_manifest.json"
    manifest_bytes = manifest_path.read_bytes()
    if sha256(manifest_bytes) != EXPECTED_MANIFEST_SHA256:
        raise ValueError("source manifest hash mismatch")
    manifest = json.loads(manifest_bytes)
    records = {r["task_id"]: r for r in manifest["records"]}
    if set(records) != set(EXPECTED_IMAGES):
        raise ValueError("source manifest task set mismatch")
    if tuple(x for x in records if x in TRAIN_IDS) != TRAIN_IDS:
        raise ValueError("training task order mismatch")
    for task_id, digest in EXPECTED_IMAGES.items():
        if records[task_id]["image_sha256"] != digest:
            raise ValueError(f"manifest source digest mismatch: {task_id}")
    if tuple(records[x]["layout"] for x in TRAIN_IDS) != ("A", "A", "B", "B"):
        raise ValueError("training split is not class balanced")
    if tuple(records[x]["layout"] for x in HELD_IDS) != ("A", "B"):
        raise ValueError("held-out split mismatch")

    if not torch.cuda.is_available():
        raise RuntimeError("CUDA device unavailable in container")
    if os.environ.get("CUBLAS_WORKSPACE_CONFIG") != ":4096:8":
        raise RuntimeError("CUBLAS_WORKSPACE_CONFIG was not set before process start")
    torch.manual_seed(SEED)
    torch.cuda.manual_seed_all(SEED)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    torch.use_deterministic_algorithms(True)
    device = torch.device("cuda:0")

    sys.path.insert(0, str(repo / "research/live_control"))
    from compiled_form_grounding_v1 import validate

    train_x, train_y = [], []
    points = {}
    train_images = {}
    for task_id in TRAIN_IDS:
        rec = records[task_id]
        x, variant_sha, _ = read_image(repo, rec)
        train_x.append(x)
        train_y.append(LAYOUTS.index(rec["layout"]))
        train_images[task_id] = variant_sha
        target = (rec["field_point"], rec["submit_point"])
        if rec["layout"] in points and points[rec["layout"]] != target:
            raise ValueError("training layout has inconsistent manifest coordinates")
        points[rec["layout"]] = target
    train_x = torch.stack(train_x)
    train_y = torch.tensor(train_y, dtype=torch.long)

    eval_rows = []
    for task_id in HELD_IDS:
        rec = records[task_id]
        for transform_name, factor in EVAL_TRANSFORMS:
            x, variant_sha, _ = read_image(repo, rec, factor)
            eval_rows.append({"task_id": task_id, "layout": rec["layout"],
                              "transform": transform_name, "factor": factor,
                              "input_sha256": variant_sha, "x": x})

    # Identical balanced sample order for both arms, generated before training.
    schedule_gen = torch.Generator(device="cpu").manual_seed(SEED + 1)
    factor_gen = torch.Generator(device="cpu").manual_seed(SEED + 2)
    per_batch = torch.tensor([0, 1, 2, 3] * (BATCH // 4), dtype=torch.long)
    schedules, factors = [], []
    for _ in range(STEPS):
        perm = torch.randperm(BATCH, generator=schedule_gen)
        schedules.append(per_batch[perm])
        factors.append(0.70 + 0.60 * torch.rand(BATCH, generator=factor_gen))

    initial = TinyGrounder().state_dict()
    init_copy = {k: v.detach().clone() for k, v in initial.items()}
    arms = []
    for arm_name, use_brightness_aug in (("no_augmentation", False), ("brightness_augmentation", True)):
        model = TinyGrounder()
        model.load_state_dict(init_copy)
        model.to(device)
        optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
        criterion = nn.CrossEntropyLoss()
        torch.cuda.reset_peak_memory_stats(device)
        torch.cuda.synchronize(device)
        started = time.perf_counter()
        model.train()
        for step in range(STEPS):
            idx = schedules[step]
            batch = train_x[idx].clone()
            if use_brightness_aug:
                batch *= factors[step][:, None, None, None]
                batch.clamp_(0.0, 1.0)
            batch = batch.to(device)
            labels = train_y[idx].to(device)
            optimizer.zero_grad(set_to_none=True)
            logits = model(batch)
            loss = criterion(logits, labels)
            loss.backward()
            optimizer.step()
        torch.cuda.synchronize(device)
        train_seconds = time.perf_counter() - started
        peak_memory = torch.cuda.max_memory_allocated(device)
        model.eval()
        predictions = []
        with torch.no_grad():
            for row in eval_rows:
                logits = model(row["x"].unsqueeze(0).to(device))[0].cpu().to(torch.float64)
                pred = int(torch.argmax(logits).item())
                top = float(torch.softmax(logits, dim=0)[pred].item())
                route = "accept" if top >= 0.75 else ("yield" if top >= 0.25 else "reject")
                layout = LAYOUTS[pred]
                candidate = compile_candidate(layout, points)
                validated = validate(candidate)
                expected = records[row["task_id"]]
                exact = (validated["field_point"] == expected["field_point"] and
                         validated["submit_point"] == expected["submit_point"])
                predictions.append({
                    "task_id": row["task_id"], "true_layout": row["layout"],
                    "transform": row["transform"], "factor": row["factor"],
                    "input_sha256": row["input_sha256"], "logits": [float(x) for x in logits],
                    "predicted_layout": layout, "top_class_confidence": top,
                    "route": route, "candidate": candidate,
                    "validator_points": validated, "validator": "accept",
                    "exact_coordinates": bool(exact),
                })
        arms.append({"arm": arm_name, "brightness_augmentation": use_brightness_aug,
                     "parameter_count": sum(p.numel() for p in model.parameters()),
                     "train_seconds": train_seconds, "peak_cuda_bytes": peak_memory,
                     "train_task_ids": list(TRAIN_IDS), "train_source_hashes": train_images,
                     "predictions": predictions})
        del model, optimizer, criterion
        torch.cuda.empty_cache()

    props = torch.cuda.get_device_properties(device)
    result = {
        "format": "gpu-photometric-grounding-result-v1",
        "source_commit": "d9776a90662e1d7f901a025395aa27e28d9d4d00",
        "manifest_sha256": sha256(manifest_bytes),
        "image_sha256": EXPECTED_IMAGES,
        "split": {"train": list(TRAIN_IDS), "held_out": list(HELD_IDS)},
        "schedule": {"seed": SEED, "steps": STEPS, "batch_size": BATCH,
                     "training_brightness_range": [0.70, 1.30],
                     "evaluation_factors": [1.0, 0.85, 1.15]},
        "environment": {"python": platform.python_version(), "platform": platform.platform(),
                        "torch": torch.__version__, "cuda": torch.version.cuda,
                        "device": props.name, "total_memory_bytes": props.total_memory,
                        "deterministic_algorithms": torch.are_deterministic_algorithms_enabled(),
                        "cudnn_deterministic": torch.backends.cudnn.deterministic,
                        "cudnn_benchmark": torch.backends.cudnn.benchmark,
                        "tf32_matmul": torch.backends.cuda.matmul.allow_tf32,
                        "cublas_workspace_config": os.environ["CUBLAS_WORKSPACE_CONFIG"]},
        "arms": arms,
        "scope": "two-source-image-per-layout held-out brightness robustness; no GUI/action/authority",
    }
    payload = json.dumps(result, sort_keys=True, indent=2, allow_nan=False) + "\n"
    target = out / "results.json"
    temp = out / "results.json.tmp"
    temp.write_text(payload, encoding="utf-8")
    temp.replace(target)
    print(payload, end="")


if __name__ == "__main__":
    main()
