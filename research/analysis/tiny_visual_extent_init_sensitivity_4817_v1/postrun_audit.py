"""Post-run provenance check for the immutable Issue #4983 allocation.

Run from the repository root:
  python research/analysis/tiny_visual_extent_init_sensitivity_4817_v1/postrun_audit.py

This supplements, and does not rewrite, the frozen formal runner, RAW.json, or AUDIT.json.
"""
from __future__ import annotations
import ast
import base64
import hashlib
import io
import json
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parent
RESULT = ROOT / "construction_01"
RAW_SHA256 = "27f2b35a6e1f99812c996e8e059b7484700e8dab512e435a80e11ea27f291e6e"
INITIAL_WEIGHTS_SHA256 = "d62bdd9216c0b969b7872b1da7c11a517a376b04ff351b46d6629a5ef2cb32f9"
INIT_SEED = 58100472

def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def main() -> None:
    raw_bytes = (RESULT / "RAW.json").read_bytes()
    raw = json.loads(raw_bytes)
    b64_bytes = (RESULT / "INITIAL_WEIGHTS.npz.b64").read_bytes()
    initial_bytes = base64.b64decode(b64_bytes, validate=True)
    weights = np.load(io.BytesIO(initial_bytes), allow_pickle=False)

    seed_checks = {}
    for arm, extent in (("max_only", False), ("max_mean", True)):
        rng = np.random.default_rng(INIT_SEED)
        kernel = rng.normal(0, .04, (4, 1, 3, 3)).astype(np.float32)
        bias = np.zeros(4, np.float32)
        dense = np.zeros(8 if extent else 4, np.float32)
        dense[:4] = rng.normal(0, .04, 4).astype(np.float32)
        output_bias = np.float32(0)
        for name, expected in zip(("kernel", "bias", "dense", "output_bias"),
                                  (kernel, bias, dense, output_bias)):
            key = f"{arm}_{name}"
            seed_checks[key] = bool(np.array_equal(weights[key], expected))

    runner = (ROOT / "run_cuda.py").read_text(encoding="utf-8")
    tree = ast.parse(runner)
    held = None
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "HELD"
            for target in node.targets
        ):
            held = ast.literal_eval(node.value)
            break
    if held is None:
        raise RuntimeError("HELD constant not found in frozen runner")
    packed_centers = [list(ast.literal_eval(key)) for key in sorted(map(str, held))]
    recorded_centers = raw.get("held_centers")
    mismatch_indices = [
        index for index, pair in enumerate(zip(packed_centers, recorded_centers or []))
        if pair[0] != pair[1]
    ]
    checks = {
        "raw_sha256": sha(raw_bytes) == RAW_SHA256,
        "initial_weights_sha256": sha(initial_bytes) == INITIAL_WEIGHTS_SHA256,
        "allocation": raw.get("allocation") == "tiny-visual-extent-init-sensitivity-4817-20260928-01",
        "init_seed": raw.get("init_seed") == INIT_SEED,
        "all_initial_tensors_match_seed": all(seed_checks.values()),
        "held_center_count": len(packed_centers) == 8 and len(recorded_centers or []) == 8,
        "known_label_mismatch_reproduced": mismatch_indices == [0, 2, 4, 6, 7],
    }
    result = {
        "schema": "issue-4983-postrun-audit-v1",
        "status": "PASS_SEED_BINDING_WITH_CENTER_LABEL_CORRECTION"
                  if all(checks.values()) else "HOLD_POSTRUN_PROVENANCE",
        "scientific_disposition": "STOP_NO_CONSTRUCTION_COMPETENCE",
        "historical_integrity": "Original FREEZE.json, RAW.json, and AUDIT.json remain unchanged.",
        "checks": checks,
        "seed_tensor_checks": seed_checks,
        "held_centers": {
            "recorded_raw_order": recorded_centers,
            "actual_packed_array_order": packed_centers,
            "mislabeled_indices_zero_based": mismatch_indices,
            "mislabel_count": len(mismatch_indices),
        },
        "interpretation": "Initial weights bind exactly to INIT_SEED. The raw per-center labels are misordered; use actual_packed_array_order when mapping held_i arrays. This correction does not change the frozen aggregate STOP disposition.",
        "raw_sha256": sha(raw_bytes),
        "initial_weights_sha256": sha(initial_bytes),
    }
    print(json.dumps(result, sort_keys=True, indent=2))
    if not all(checks.values()):
        raise SystemExit(2)

if __name__ == "__main__":
    main()
