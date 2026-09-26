#!/usr/bin/env python3
"""One-shot local CUDA comparison of narrow vs broad template diversity."""
import argparse
import datetime
import hashlib
import json
import math
import os
import platform
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import torch
import PIL
from PIL import Image
from torch import nn


HERE = Path(__file__).resolve().parent
SEEDS = (29121, 29122, 29123)
STEPS = 500
BATCH = 16
NARROW_FAMILIES = ("T01", "T02")
BROAD_FAMILIES = tuple(f"T{i:02d}" for i in range(1, 9))
HELDOUT_FAMILIES = tuple(f"T{i:02d}" for i in range(9, 13))
SOURCE_WIDTH = 1280
SOURCE_HEIGHT = 800
GRID_WIDTH = 160
GRID_HEIGHT = 100


def sha256(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical_file_sha256(path):
    return sha256(Path(path).read_bytes().replace(b"\r\n", b"\n"))


class FixedPool(nn.Module):
    """Separable fixed-matrix equivalent of adaptive average pooling."""
    def __init__(self):
        super().__init__()

        def matrix(source, target):
            weights = torch.zeros((target, source), dtype=torch.float32)
            for oi in range(target):
                start = (oi * source) // target
                end = ((oi + 1) * source + target - 1) // target
                weights[oi, start:end] = 1.0 / (end - start)
            return weights

        self.register_buffer("height_weights", matrix(25, 8))
        self.register_buffer("width_weights", matrix(40, 10))

    def forward(self, value):
        if tuple(value.shape[-2:]) != (25, 40):
            raise ValueError(f"expected feature map 25x40, got {tuple(value.shape[-2:])}")
        return torch.einsum("oh,nchw,pw->ncop", self.height_weights, value, self.width_weights)


class TinyGrounder(nn.Module):
    def __init__(self):
        super().__init__()
        self.features = nn.Sequential(
            nn.Conv2d(1, 8, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2),
            nn.Conv2d(8, 16, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2),
            FixedPool(), nn.Flatten(), nn.Linear(1280, 32), nn.ReLU(),
            nn.Linear(32, 4), nn.Sigmoid(),
        )

    def forward(self, value):
        return self.features(value)


def load_rows(repo, manifest):
    rows = []
    for record in manifest["records"]:
        raw = (repo / "research/analysis/gpu_grounding_template_diversity_2912_v1" / record["image"]).read_bytes()
        if sha256(raw) != record["image_sha256"]:
            raise ValueError(f"image hash mismatch: {record['record_id']}")
        with Image.open(repo / "research/analysis/gpu_grounding_template_diversity_2912_v1" / record["image"]) as image:
            pixels = image.convert("RGB").convert("L").resize((160, 100), Image.Resampling.BILINEAR)
            array = np.asarray(pixels, dtype=np.float32) / 255.0
        target = [record["field_point"][0] / SOURCE_WIDTH,
                  record["field_point"][1] / SOURCE_HEIGHT,
                  record["submit_point"][0] / SOURCE_WIDTH,
                  record["submit_point"][1] / SOURCE_HEIGHT]
        rows.append({"record": record, "x": torch.from_numpy(array.copy()).unsqueeze(0),
                     "y": torch.tensor(target, dtype=torch.float32)})
    return rows


def compile_candidate(points):
    def target(point):
        return {"point_space": "source_observation_pixels",
                "point": {"x": int(point[0]), "y": int(point[1])},
                "motion_model": "surface_origin_translation"}
    return {"format": "compiled-form-grounding-v1",
            "field": target(points[:2]), "submit": target(points[2:]),
            "method": {"first_action": "enter_exact_token",
                       "continue_when": "field_pixels_changed_and_submit_revalidated",
                       "second_action": "activate_submit",
                       "complete_when": "submission_pixels_changed_then_independent_score"}}


def configure_determinism(seed):
    if os.environ.get("CUBLAS_WORKSPACE_CONFIG") != ":4096:8":
        raise RuntimeError("CUBLAS_WORKSPACE_CONFIG must be set before process start")
    torch.set_num_threads(1)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    torch.use_deterministic_algorithms(True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=HERE.parents[2])
    parser.add_argument("--out", type=Path, default=HERE / "results/formal01")
    args = parser.parse_args()
    repo, out = args.repo.resolve(), args.out.resolve()
    if out.exists() and any(out.iterdir()):
        raise RuntimeError("formal output path must be absent or empty; no overwrite/retry")
    out.mkdir(parents=True, exist_ok=True)

    root = repo / "research/analysis/gpu_grounding_template_diversity_2912_v1"
    freeze = json.loads((root / "FREEZE.json").read_text(encoding="utf-8"))
    manifest_raw = (root / "corpus/manifest.json").read_bytes()
    if sha256(manifest_raw) != freeze["manifest_sha256"]:
        raise ValueError("frozen manifest hash mismatch")
    manifest = json.loads(manifest_raw)
    if manifest["generator_sha256"] != freeze["generator_sha256"]:
        raise ValueError("generator hash in manifest does not match freeze")
    if manifest["template_spec_sha256"] != freeze["template_spec_sha256"]:
        raise ValueError("template specification hash in manifest does not match freeze")
    if canonical_file_sha256(__file__) != freeze["runner_sha256"]:
        raise ValueError("runner hash does not match freeze")
    source_paths = {
        ".gitattributes": root / ".gitattributes",
        "README.md": root / "README.md",
        "generate_corpus.py": root / "generate_corpus.py",
        "templates.json": root / "templates.json",
        "train_eval.py": root / "train_eval.py",
        "audit.py": root / "audit.py",
        "test_construction.py": root / "test_construction.py",
        "PREREGISTRATION.md": root / "PREREGISTRATION.md",
        "compiled_form_grounding_v1.py": repo / "research/live_control/compiled_form_grounding_v1.py",
        "compiled_form_grounding_schema_v1.json": repo / "research/live_control/compiled_form_grounding_schema_v1.json",
    }
    for name, path in source_paths.items():
        if canonical_file_sha256(path) != freeze["source_hashes"][name]:
            raise ValueError(f"frozen source hash mismatch: {name}")
    if platform.python_version() != "3.11.9" or np.__version__ != "2.4.6" or PIL.__version__ != "10.4.0":
        raise RuntimeError("unfrozen Python/NumPy/Pillow environment")
    if not torch.cuda.is_available():
        raise RuntimeError("local CUDA device unavailable")
    if torch.__version__ != "2.5.1+cu121" or torch.version.cuda != "12.1":
        raise RuntimeError("unfrozen host PyTorch/CUDA version")
    if not os.environ.get("LOCAL_GPU_FORMAL_ACK") == "4546-one-shot" :
        raise RuntimeError("formal one-shot environment acknowledgement missing")

    sys.path.insert(0, str(repo / "research/live_control"))
    from compiled_form_grounding_v1 import validate

    records = load_rows(repo, manifest)
    by_family = {}
    for row in records:
        by_family.setdefault(row["record"]["family_id"], []).append(row)
    if any(len(by_family.get(family, [])) != 20 for family in HELDOUT_FAMILIES):
        raise ValueError("held-out family denominator mismatch")
    device = torch.device("cuda:0")
    if "RTX 3080" not in torch.cuda.get_device_name(device):
        raise RuntimeError("formal allocation requires the local RTX 3080")
    runs = []
    model_runs = []
    started_at_utc = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="milliseconds")
    total_started = time.perf_counter()
    for seed in SEEDS:
        configure_determinism(seed)
        initial_model = TinyGrounder()
        initial_state = {key: value.detach().clone() for key, value in initial_model.state_dict().items()}
        # Shared uniform variates give both arms the same sampling schedule seed.
        schedule_generator = torch.Generator(device="cpu").manual_seed(seed + 101)
        uniforms = torch.rand((STEPS, BATCH), generator=schedule_generator)
        for arm, families in (("narrow_2_families", NARROW_FAMILIES),
                              ("broad_8_families", BROAD_FAMILIES)):
            train_rows = [row for row in records if row["record"]["family_id"] in families]
            if not train_rows:
                raise ValueError(f"empty training arm: {arm}")
            train_x = torch.stack([row["x"] for row in train_rows])
            train_y = torch.stack([row["y"] for row in train_rows])
            model = TinyGrounder().to(device)
            model.load_state_dict(initial_state)
            optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
            criterion = nn.SmoothL1Loss(beta=0.02)
            torch.cuda.reset_peak_memory_stats(device)
            torch.cuda.synchronize(device)
            started = time.perf_counter()
            model.train()
            first_loss = None
            for step in range(STEPS):
                indexes = torch.floor(uniforms[step] * len(train_rows)).long().clamp_max(len(train_rows) - 1)
                batch_x = train_x[indexes].to(device)
                batch_y = train_y[indexes].to(device)
                optimizer.zero_grad(set_to_none=True)
                prediction = model(batch_x)
                loss = criterion(prediction, batch_y)
                if first_loss is None:
                    first_loss = float(loss.detach().cpu())
                loss.backward()
                optimizer.step()
            torch.cuda.synchronize(device)
            train_seconds = time.perf_counter() - started
            peak_bytes = torch.cuda.max_memory_allocated(device)
            model_runs.append({"seed": seed, "arm": arm, "training_families": list(families),
                               "unique_training_images": len(train_rows), "optimizer_steps": STEPS,
                               "sampled_examples": STEPS * BATCH, "train_seconds": train_seconds,
                               "first_sampled_batch_loss": first_loss,
                               "last_sampled_batch_loss": float(loss.detach().cpu()),
                               "peak_cuda_allocated_bytes": peak_bytes})
            model.eval()
            with torch.no_grad():
                for family in HELDOUT_FAMILIES:
                    for row in by_family[family]:
                        normalized = model(row["x"].unsqueeze(0).to(device))[0].cpu().tolist()
                        cells = []
                        for i in range(4):
                            extent = 160 if i % 2 == 0 else 100
                            cells.append(max(0, min(extent - 1,
                                                    int(math.floor(normalized[i] * extent + 0.5)))))
                        points = [cells[0] * 8, cells[1] * 8, cells[2] * 8, cells[3] * 8]
                        candidate = compile_candidate(points)
                        expected = row["record"]
                        gold = expected["field_point"] + expected["submit_point"]
                        try:
                            validated = validate(candidate)
                            validator, validator_points, validator_error = (
                                "accept", validated["field_point"] + validated["submit_point"], None)
                        except ValueError as exc:
                            validator, validator_points, validator_error = "reject", None, str(exc)
                        runs.append({"seed": seed, "arm": arm, "family_id": family,
                                     "record_id": expected["record_id"], "image_sha256": expected["image_sha256"],
                                     "prediction_normalized": normalized, "predicted_points": points,
                                     "gold_points": gold, "candidate": candidate,
                                     "validator_points": validator_points, "validator": validator,
                                     "validator_error": validator_error, "exact_coordinates": points == gold})
            del model, optimizer, criterion, train_x, train_y
            torch.cuda.empty_cache()

    torch.cuda.synchronize(device)
    props = torch.cuda.get_device_properties(device)
    driver = None
    try:
        driver = subprocess.check_output(["nvidia-smi", "--query-gpu=driver_version", "--format=csv,noheader"],
                                         text=True, timeout=10).strip().splitlines()[0]
    except Exception:
        driver = "unavailable"
    result = {"format": "gpu-grounding-template-diversity-result-v1",
              "issue": 4546, "allocation": "gpu-grounding-template-diversity-2912-successor-01",
              "formal_invocations": 1, "retries": 0, "training_steps_per_model": STEPS,
              "models": len(SEEDS) * 2, "manifest_sha256": freeze["manifest_sha256"],
              "source_commit": freeze["source_commit"], "started_at_utc": started_at_utc,
              "completed_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="milliseconds"),
              "runner_sha256": canonical_file_sha256(__file__),
              "source_hashes": freeze["source_hashes"],
              "split": {"narrow_families": list(NARROW_FAMILIES), "broad_families": list(BROAD_FAMILIES),
                        "heldout_families": list(HELDOUT_FAMILIES)},
              "environment": {"python": platform.python_version(), "numpy": np.__version__,
                              "pillow": PIL.__version__, "torch": torch.__version__,
                              "cuda": torch.version.cuda, "driver": driver, "device": props.name,
                              "total_memory_bytes": props.total_memory,
                              "deterministic_algorithms": torch.are_deterministic_algorithms_enabled(),
                              "cudnn_deterministic": torch.backends.cudnn.deterministic,
                              "tf32": torch.backends.cuda.matmul.allow_tf32,
                              "cublas_workspace_config": os.environ["CUBLAS_WORKSPACE_CONFIG"],
                              "execution_boundary": "PC-local Windows host CUDA; pre-existing Docker image was CPU-only"},
              "model_runs": model_runs, "total_wall_seconds": time.perf_counter() - total_started,
              "predictions": runs,
              "scope": "synthetic source-template-heldout coordinates only; no GUI/authority"}
    target = out / "results.json"
    target.write_text(json.dumps(result, sort_keys=True, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({"formal_invocations": 1, "models": result["models"],
                      "predictions": len(runs), "total_wall_seconds": result["total_wall_seconds"],
                      "peak_cuda_allocated_bytes": max(row["peak_cuda_allocated_bytes"] for row in model_runs)},
                     sort_keys=True))


if __name__ == "__main__":
    main()
