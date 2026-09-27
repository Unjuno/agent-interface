from __future__ import annotations

import argparse
import base64
import hashlib
import io
import json
import os
import platform
import sys
import time
from pathlib import Path

import numpy as np

from prepare import (ALLOCATION, ARMS, FORMAL_SEEDS, make_tiles, training_data,
                     evaluation_data, digest)


EXPECTED_IMAGE_ID = "sha256:ba509e8a38d311c07539c49a7a2970b6f19869de42b8008be07a85568e2c9824"
SOURCE_FILES = ("prepare.py", "train.py", "audit.py", "test_protocol.py")
LR = np.float32(0.8)
STEPS = 250
HIDDEN = 16


def normalized_payload(path: Path, expected_sha: str) -> bytes:
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() == expected_sha:
        return raw
    if raw.endswith(b"\r\n") and hashlib.sha256(raw[:-2]).hexdigest() == expected_sha:
        return raw[:-2]
    raise ValueError(f"frozen payload mismatch: {path.name}")


def verify_freeze(root: Path) -> dict:
    freeze_bytes = root.joinpath("FREEZE.json").read_bytes()
    side = root.joinpath("FREEZE.sha256").read_bytes()
    if side.endswith(b"\r\n"):
        side = side[:-2]
    expected_freeze = side.decode("ascii").split()[0]
    if hashlib.sha256(freeze_bytes).hexdigest() != expected_freeze:
        if not (freeze_bytes.endswith(b"\r\n") and hashlib.sha256(freeze_bytes[:-2]).hexdigest() == expected_freeze):
            raise ValueError("FREEZE.json / sidecar mismatch")
        freeze_bytes = freeze_bytes[:-2]
    freeze = json.loads(freeze_bytes)
    if freeze.get("allocation") != ALLOCATION or freeze.get("formal_seeds") != FORMAL_SEEDS:
        raise ValueError("FREEZE allocation/seed binding mismatch")
    if set(freeze.get("source_sha256", {})) != set(SOURCE_FILES):
        raise ValueError("FREEZE source inventory mismatch")
    if freeze.get("model") != {"inputs": 1200, "hidden_relu": 16, "outputs": 1,
                                "optimizer": "full_batch_gradient_descent", "steps": 250,
                                "learning_rate": 0.8}:
        raise ValueError("FREEZE model recipe mismatch")
    if freeze.get("decision_thresholds") != {"accept_min": 0.75, "yield_min": 0.25, "classification": 0.5}:
        raise ValueError("FREEZE decision thresholds mismatch")
    if freeze.get("resource_limits") != {"network": "none", "cpus": 1, "memory": "2g",
                                         "pids": 64, "rootfs_readonly": True, "gpu": False}:
        raise ValueError("FREEZE resource/scope mismatch")
    for name, expected in freeze["source_sha256"].items():
        normalized_payload(root / name, expected)
    pre = root.joinpath("PREFORMAL.json").read_bytes()
    pre_side = root.joinpath("PREFORMAL.sha256").read_bytes()
    if pre_side.endswith(b"\r\n"):
        pre_side = pre_side[:-2]
    expected_pre = pre_side.decode("ascii").split()[0]
    if hashlib.sha256(pre).hexdigest() != expected_pre:
        if not (pre.endswith(b"\r\n") and hashlib.sha256(pre[:-2]).hexdigest() == expected_pre):
            raise ValueError("PREFORMAL.json / sidecar mismatch")
        pre = pre[:-2]
    pre_obj = json.loads(pre)
    if pre_obj["allocation"] != ALLOCATION or pre_obj["formal_seeds"] != FORMAL_SEEDS:
        raise ValueError("PREFORMAL allocation/seed binding mismatch")
    if hashlib.sha256(pre).hexdigest() != freeze.get("preformal_sha256"):
        raise ValueError("FREEZE/PREFORMAL digest binding mismatch")
    if freeze["image_id"] != EXPECTED_IMAGE_ID:
        raise ValueError("Docker image identity mismatch")
    return freeze


def init_model(seed: int):
    rng = np.random.default_rng(seed)
    w1 = rng.normal(0, 0.04, (1200, HIDDEN)).astype(np.float32)
    b1 = np.zeros(HIDDEN, np.float32)
    w2 = rng.normal(0, 0.04, HIDDEN).astype(np.float32)
    b2 = np.float32(0)
    init_digest = hashlib.sha256(w1.tobytes() + b1.tobytes() + w2.tobytes() + b2.tobytes()).hexdigest()
    return (w1, b1, w2, b2), init_digest


def fit(x: np.ndarray, y: np.ndarray, seed: int):
    (w1, b1, w2, b2), init_digest = init_model(seed)
    for _ in range(STEPS):
        h0 = x @ w1 + b1
        h = np.maximum(h0, 0)
        z = h @ w2 + b2
        p = 1 / (1 + np.exp(-np.clip(z, -30, 30)))
        dz = (p - y) / len(y)
        dw2 = h.T @ dz
        db2 = dz.sum()
        dh = dz[:, None] * w2
        dh[h0 <= 0] = 0
        dw1 = x.T @ dh
        db1 = dh.sum(0)
        w2 -= LR * dw2
        b2 -= LR * db2
        w1 -= LR * dw1
        b1 -= LR * db1
    return (w1, b1, w2, b2), init_digest


def predict(model, x):
    w1, b1, w2, b2 = model
    z = np.maximum(x @ w1 + b1, 0) @ w2 + b2
    return 1 / (1 + np.exp(-np.clip(z, -30, 30)))


def write_jsonl(path: Path, rows):
    with path.open("w", encoding="utf-8", newline="\n") as stream:
        for row in rows:
            stream.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")


def gate_fixture() -> list[dict]:
    fixtures = [
        {"case_id": "current_matching_positive", "model_probability": 0.99, "receipt_matches": True, "fresh": True, "positive": True},
        {"case_id": "stale_high_positive", "model_probability": 0.99, "receipt_matches": True, "fresh": False, "positive": True},
        {"case_id": "digest_mismatch_high_positive", "model_probability": 0.99, "receipt_matches": False, "fresh": True, "positive": True},
        {"case_id": "current_negative", "model_probability": 0.01, "receipt_matches": True, "fresh": True, "positive": False},
    ]
    for row in fixtures:
        row["model_decision"] = "ACCEPT" if row["model_probability"] >= 0.75 else (
            "REJECT" if row["model_probability"] < 0.25 else "YIELD")
        row["final_accept"] = row["model_decision"] == "ACCEPT" and row["receipt_matches"] and row["fresh"] and row["positive"]
    return fixtures


def run(root: Path, out: Path):
    freeze = verify_freeze(root)
    if out.exists() and any(out.iterdir()):
        raise FileExistsError("formal output directory must be empty; no retry/reuse")
    out.mkdir(parents=True, exist_ok=True)
    (out / "weights").mkdir()
    predictions, training_manifests, evaluation_manifests, receipts = [], [], [], []
    start_all = time.perf_counter()
    for seed in FORMAL_SEEDS:
        models = {}
        for arm in ARMS:
            x, y, meta = training_data(seed + 1, arm)
            init_seed = seed + 5
            started = time.perf_counter()
            model, init_sha = fit(x, y.astype(np.float32), init_seed)
            elapsed = time.perf_counter() - started
            buff = io.BytesIO()
            np.savez_compressed(buff, w1=model[0], b1=model[1], w2=model[2], b2=np.asarray(model[3], dtype=np.float32))
            weight_bytes = buff.getvalue()
            weight_sha = hashlib.sha256(weight_bytes).hexdigest()
            weight_path = out / "weights" / f"{seed}-{arm}.npz.b64"
            weight_path.write_text(base64.b64encode(weight_bytes).decode("ascii") + "\n", encoding="ascii", newline="\n")
            models[arm] = (model, weight_sha)
            for row in meta:
                training_manifests.append({"seed": seed, "arm": arm, **row})
            receipts.append({"seed": seed, "arm": arm, "init_seed": init_seed,
                             "init_weights_sha256": init_sha, "final_weights_sha256": weight_sha,
                             "training_inputs_sha256": hashlib.sha256(x.tobytes(order="C")).hexdigest(),
                             "training_rows": int(len(y)), "positive_rows": int(y.sum()),
                             "negative_rows": int(len(y) - y.sum()), "steps": STEPS,
                             "learning_rate": float(LR), "fit_seconds": elapsed,
                             "python": platform.python_version(), "numpy": np.__version__,
                             "openblas_threads": os.environ.get("OPENBLAS_NUM_THREADS")})
        for stratum_index, (stratum, stream_offset) in enumerate((("base", 2), ("translation_a", 3), ("translation_b", 4))):
            x, y, meta = evaluation_data(seed + stream_offset, stratum)
            for row in meta:
                evaluation_manifests.append({"seed": seed, "stratum": stratum, **row})
            for arm in ARMS:
                model, weight_sha = models[arm]
                probs = predict(model, x)
                for row, label, prob in zip(meta, y.tolist(), probs.tolist()):
                    predictions.append({"seed": seed, "arm": arm, "stratum": stratum,
                                        "case_id": row["case_id"], "label": int(label),
                                        "image_sha256": row["image_sha256"], "weight_sha256": weight_sha,
                                        "probability": float(prob), "model_decision": "ACCEPT" if prob >= 0.75 else (
                                            "YIELD" if prob >= 0.25 else "REJECT"),
                                        "classification": int(prob >= 0.5)})
    write_jsonl(out / "training_manifest.jsonl", training_manifests)
    write_jsonl(out / "evaluation_manifest.jsonl", evaluation_manifests)
    write_jsonl(out / "predictions.jsonl", predictions)
    write_jsonl(out / "training_receipts.jsonl", receipts)
    (out / "gate_fixture.json").write_text(json.dumps(gate_fixture(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    env = {"allocation": ALLOCATION, "formal_seeds": FORMAL_SEEDS,
           "image_id": freeze["image_id"], "python": platform.python_version(),
           "numpy": np.__version__, "platform": platform.platform(), "network_expected": "none",
           "fits": len(receipts), "prediction_rows": len(predictions),
           "training_wall_seconds": time.perf_counter() - start_all,
           "external_model_api_requests": 0, "local_model_fits": len(receipts),
           "host_gui_or_authority": False}
    (out / "environment.json").write_text(json.dumps(env, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return env


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(run(args.root, args.out), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

