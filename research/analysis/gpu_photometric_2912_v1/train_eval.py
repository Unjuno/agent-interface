import hashlib
import json
import math
import os
import subprocess
import sys
import threading
import time
from pathlib import Path

import numpy as np
from PIL import Image
import torch
from torch import nn

HERE = Path(__file__).resolve().parent
ROOT = Path(os.environ.get("RESEARCH_REPO_ROOT", HERE.parents[2]))
OUT = Path(os.environ.get("RESEARCH_OUTPUT_DIR", HERE / "formal-output"))
PREREG = HERE / "preregistration.json"
FROZEN = HERE / "FROZEN_IMAGE.json"
METHOD = {"first_action": "enter_exact_token", "continue_when": "field_pixels_changed_and_submit_revalidated", "second_action": "activate_submit", "complete_when": "submission_pixels_changed_then_independent_score"}
TRAIN_IDS = ["task-1", "task-2", "task-4", "task-5"]
EVAL_IDS = ["task-3", "task-6"]

def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def image_tensor(path, factor):
    with Image.open(path) as im:
        im = im.convert("RGB")
        if factor != 1.0:
            a = np.asarray(im, dtype=np.uint16).astype(np.float64)
            a = np.clip(np.floor(a * factor), 0, 255).astype(np.uint8)
            im = Image.fromarray(a, "RGB")
        im = im.resize((64, 64), Image.Resampling.BILINEAR)
        a = np.asarray(im, dtype=np.float32) / np.float32(255.0)
    return np.transpose(a, (2, 0, 1)).copy()

class TinyCNN(nn.Module):
    def __init__(self):
        super().__init__()
        self.c1 = nn.Conv2d(3, 8, 3, padding=1)
        self.c2 = nn.Conv2d(8, 16, 3, padding=1)
        self.fc = nn.Linear(16 * 16 * 16, 2)
    def forward(self, x):
        x = nn.functional.max_pool2d(torch.relu(self.c1(x)), 2)
        x = nn.functional.max_pool2d(torch.relu(self.c2(x)), 2)
        return self.fc(torch.flatten(x, 1))

def softmax(logits):
    m = max(logits)
    exps = [math.exp(v - m) for v in logits]
    total = sum(exps)
    return [v / total for v in exps]

def route(probs):
    confidence = max(probs)
    predicted = int(np.argmax(np.asarray(probs)))
    return ("accept" if confidence >= .75 else "yield" if confidence >= .25 else "reject", predicted, confidence)

def candidate(predicted_layout):
    field, submit = ([649, 555], [688, 630]) if predicted_layout == "B" else ([225, 397], [376, 397])
    def target(point):
        return {"point_space": "source_observation_pixels", "point": {"x": point[0], "y": point[1]}, "motion_model": "surface_origin_translation"}
    return {"format": "compiled-form-grounding-v1", "field": target(field), "submit": target(submit), "method": METHOD.copy()}

def gpu_memory_sampler(stop, samples):
    while not stop.wait(.2):
        try:
            raw = subprocess.check_output(["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"], text=True, timeout=3)
            samples.append(int(raw.strip().splitlines()[0]))
        except Exception:
            samples.append(None)

def main():
    if OUT.exists() and any(OUT.iterdir()):
        raise RuntimeError("output directory is not empty; refusing to overwrite evidence")
    OUT.mkdir(parents=True, exist_ok=True)
    if not FROZEN.is_file():
        raise RuntimeError("frozen runtime receipt is missing")
    frozen = json.loads(FROZEN.read_text(encoding="utf-8"))
    runtime = f"python=3.11.9;torch={torch.__version__};numpy={np.__version__};pillow={Image.__version__}"
    if frozen.get("runtime") != runtime or os.environ.get("EXPECTED_RUNTIME") != frozen.get("runtime"):
        raise RuntimeError("expected frozen runtime mismatch")
    for rel, expected in frozen.get("source_sha256", {}).items():
        target = (HERE / rel).resolve()
        if sha256(target) != expected:
            raise RuntimeError(f"frozen source changed: {rel}")
    prereg = json.loads(PREREG.read_text(encoding="utf-8"))
    manifest_path = ROOT / prereg["manifest"]["path"]
    if sha256(manifest_path) != prereg["manifest"]["sha256"]:
        raise RuntimeError("manifest hash mismatch")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    by_id = {r["task_id"]: r for r in manifest["records"]}
    for spec in prereg["source_images"]:
        path = ROOT / spec["path"]
        if not path.is_file() or sha256(path) != spec["sha256"]:
            raise RuntimeError(f"missing or mismatched source image: {spec['task_id']}")
        row = by_id.get(spec["task_id"])
        if not row or row["image_sha256"] != spec["sha256"] or row["image"] != spec["path"]:
            raise RuntimeError(f"manifest/source disagreement: {spec['task_id']}")
    if not torch.cuda.is_available() or "GeForce RTX 3080" not in torch.cuda.get_device_name(0):
        raise RuntimeError("CUDA device mismatch or unavailable")
    torch.use_deterministic_algorithms(True)
    torch.backends.cudnn.benchmark = False
    torch.backends.cudnn.deterministic = True
    if not set(TRAIN_IDS + EVAL_IDS).issubset(by_id):
        raise RuntimeError("fixed split is incomplete")
    x_np = np.stack([image_tensor(ROOT / by_id[i]["image"], 1.0) for i in TRAIN_IDS])
    y_np = np.asarray([0 if by_id[i]["layout"] == "A" else 1 for i in TRAIN_IDS], dtype=np.int64)
    device = torch.device("cuda:0")
    x_train = torch.tensor(x_np, device=device)
    y_train = torch.tensor(y_np, device=device)
    try:
        baseline = int(subprocess.check_output(["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"], text=True, timeout=3).strip().splitlines()[0])
    except Exception as e:
        raise RuntimeError("nvidia-smi unavailable before formal allocation") from e
    stop, samples = threading.Event(), []
    sampler = threading.Thread(target=gpu_memory_sampler, args=(stop, samples), daemon=True)
    sampler.start()
    arms, timings = {}, {}
    sys.path.insert(0, str(ROOT / "research" / "live_control"))
    from compiled_form_grounding_v1 import validate
    for arm in ["no_augmentation", "brightness_augmentation"]:
        torch.manual_seed(3682)
        torch.cuda.manual_seed_all(3682)
        model = TinyCNN().to(device).train()
        optim = torch.optim.Adam(model.parameters(), lr=.001)
        started = time.monotonic()
        for step in range(200):
            optim.zero_grad(set_to_none=True)
            if arm == "brightness_augmentation":
                factors = torch.tensor([.85 if (step + row) % 2 == 0 else 1.15 for row in range(4)], dtype=torch.float32, device=device).reshape(4, 1, 1, 1)
                xb = torch.clamp(x_train * factors, 0, 1)
            else:
                xb = x_train
            loss = nn.functional.cross_entropy(model(xb), y_train)
            loss.backward()
            optim.step()
            if not math.isfinite(float(loss.detach().item())):
                raise RuntimeError(f"non-finite loss at {arm} step {step}")
        torch.cuda.synchronize()
        timings[arm] = time.monotonic() - started
        rows = []
        model.eval()
        for task_id in EVAL_IDS:
            record = by_id[task_id]
            for factor in (1.0, .85, 1.15):
                inp = image_tensor(ROOT / record["image"], factor)
                with torch.no_grad():
                    raw_logits = model(torch.tensor(inp[None, ...], device=device)).cpu().numpy()[0].astype(float).tolist()
                probs = softmax(raw_logits)
                decision, predicted_class, confidence = route(probs)
                predicted_layout = "A" if predicted_class == 0 else "B"
                form = candidate(predicted_layout)
                validated = validate(form)
                exact = predicted_layout == record["layout"] and validated["field_point"] == record["field_point"] and validated["submit_point"] == record["submit_point"]
                rows.append({"task_id": task_id, "layout_gold": record["layout"], "factor": factor,
                    "raw_logits": raw_logits, "probabilities_recomputed": probs, "decision": decision,
                    "predicted_layout": predicted_layout, "confidence": confidence, "candidate": form,
                    "validator_output": validated, "accepted_exact": decision == "accept" and exact,
                    "accepted_wrong": decision == "accept" and not exact})
        arms[arm] = rows
    stop.set()
    sampler.join(timeout=2)
    gpu_name = subprocess.check_output(["nvidia-smi", "--query-gpu=name,driver_version", "--format=csv,noheader"], text=True, timeout=3).strip()
    report = {"schema": "gpu-photometric-grounding-result-v1", "issue": 3682, "status": "formal allocation completed",
        "runtime": frozen["runtime"], "device": "cuda:0", "gpu": gpu_name,
        "gpu_memory_mib": {"before": baseline, "sampled_peak": max([baseline] + [x for x in samples if x is not None]), "samples": len(samples)},
        "training_seconds": timings, "arms": arms, "evaluation_rows": 6, "perturbed_rows": 4}
    (OUT / "RESULT.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

if __name__ == "__main__":
    main()
