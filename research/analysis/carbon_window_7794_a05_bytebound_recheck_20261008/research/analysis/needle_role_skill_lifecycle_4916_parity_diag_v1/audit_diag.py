from __future__ import annotations

import hashlib
import json
import math
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ROLES = ("A", "B", "C")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def f32(value: float) -> float:
    return struct.unpack("!f", struct.pack("!f", value))[0]


def product_rows(weights: list, vector: list[float], bias: list[float]) -> list[float]:
    result = []
    for out_index in range(len(weights)):
        accum = 0.0
        for in_index in range(len(vector)):
            accum = f32(accum + f32(weights[out_index][in_index] * vector[in_index]))
        result.append(f32(accum + f32(bias[out_index])))
    return result


def independent_prediction(tensors: dict, role: str, row: list[float]) -> int:
    if role == "A":
        enc_w, enc_b = tensors["enc.0.weight"], tensors["enc.0.bias"]
        head_w, head_b = tensors["head.weight"], tensors["head.bias"]
    else:
        enc_w, enc_b = tensors["core.enc.0.weight"], tensors["core.enc.0.bias"]
        head_w, head_b = tensors["core.head.weight"], tensors["core.head.bias"]
    hidden = [f32(math.tanh(z)) for z in product_rows(enc_w, [f32(z) for z in row], enc_b)]
    scores = product_rows(head_w, hidden, head_b)
    if role != "A":
        # Explicit column-wise accumulation implements h @ A @ B, with B
        # stored as rank x output (2 x 4).
        rank = []
        for k in range(2):
            acc = 0.0
            for j in range(16):
                acc = f32(acc + f32(hidden[j] * tensors["a"][j][k]))
            rank.append(acc)
        delta = []
        for c in range(4):
            acc = 0.0
            for k in range(2):
                acc = f32(acc + f32(rank[k] * tensors["b"][k][c]))
            delta.append(f32(acc / 2.0))
        scores = [f32(value + change) for value, change in zip(scores, delta)]
    return max(range(4), key=scores.__getitem__)


def main() -> int:
    evidence = ROOT / "results/diag-01"
    freeze_path = ROOT / "FREEZE.json"
    freeze_bytes = freeze_path.read_bytes()
    freeze = json.loads(freeze_bytes)
    receipt = json.loads((evidence / "receipt.json").read_bytes())
    stderr = (evidence / "stderr.log").read_text(encoding="utf-8")
    repo = ROOT.parents[2]
    skill_path = repo / freeze["inputs"]["skill.json"]
    expected_path = repo / freeze["inputs"]["expected.json"]
    artifact = json.loads(skill_path.read_bytes())
    expected = json.loads(expected_path.read_bytes())

    checks = {}
    checks["receipt_status"] = receipt.get("status") == "PASS_ALL_12288_PARITY" and receipt.get("exit_code") == 0
    checks["freeze_binding"] = receipt.get("freeze_sha256") == hashlib.sha256(freeze_bytes).hexdigest()
    checks["image_binding"] = receipt.get("image_id") == freeze["container"]["image_id"]
    checks["source_binding"] = receipt.get("source_hashes") == freeze["sources"]
    checks["reference_binding"] = receipt.get("reference_hashes") == freeze["reference_sources_sha256"]
    checks["input_binding"] = receipt.get("input_hashes") == freeze["inputs_sha256"]
    checks["test_receipt"] = "Ran 2 tests" in stderr and "OK" in stderr
    mismatches = []
    compared = 0
    for role in ROLES:
        saved = expected["roles"][role]
        state = artifact["tensors"][role]
        for index, row in enumerate(saved["inputs"]):
            prediction = independent_prediction(state, role, row)
            compared += 1
            if prediction != saved["pred"][index]:
                mismatches.append({"role": role, "index": index, "actual": prediction, "expected": saved["pred"][index]})
    checks["independent_12288_parity"] = compared == 12288 and not mismatches
    report = {
        "allocation": freeze["allocation"],
        "status": "PASS_INDEPENDENT_PARITY_AUDIT" if all(checks.values()) else "FAIL_INDEPENDENT_PARITY_AUDIT",
        "checks": checks,
        "rows_recomputed": compared,
        "mismatch_count": len(mismatches),
        "mismatch_examples": mismatches[:10],
        "freeze_sha256": sha(freeze_path),
        "receipt_sha256": sha(evidence / "receipt.json"),
        "container_stdout_sha256": sha(evidence / "stdout.log"),
        "container_stderr_sha256": sha(evidence / "stderr.log"),
        "skill_sha256": sha(skill_path),
        "expected_sha256": sha(expected_path),
        "audit_implementation_sha256": sha(Path(__file__)),
    }
    out = evidence / "independent_audit.json"
    out.write_text(json.dumps(report, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    print(f"AUDIT_STATUS={report['status']} ROWS={compared} MISMATCHES={len(mismatches)} CHECKS={sum(checks.values())}/{len(checks)}")
    return 0 if report["status"] == "PASS_INDEPENDENT_PARITY_AUDIT" else 1


if __name__ == "__main__":
    raise SystemExit(main())
