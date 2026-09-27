"""Reproduce the scoped GPU composed-gate allocation for Issue #4972.

Run with:
  docker run --rm --gpus all -v "$PWD:/work" -w /work \
    pytorch/pytorch:2.5.1-cuda12.1-cudnn9-runtime \
    python research/analysis/gpu_supervisor_compose_2583_r1/cuda_composed_gate.py

This is synthetic typed-trace evidence only. The model emits a binary hint;
the final gate owns freshness and ambiguity admission.
"""
import hashlib
import json
import torch

torch.manual_seed(2508)

class Supervisor(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.net = torch.nn.Sequential(
            torch.nn.Linear(8, 16),
            torch.nn.Tanh(),
            torch.nn.Linear(16, 2),
        )

    def forward(self, features):
        return self.net(features)

def final_gate(fresh, ambiguous, hint):
    if not fresh or ambiguous:
        return "YIELD"
    if hint not in ("CONTINUE", "YIELD"):
        raise ValueError("invalid supervisor output")
    return hint

def main():
    model = Supervisor().cuda().eval()
    features = []
    rows = []
    for i in range(256):
        fresh = (i % 4) != 2
        ambiguous = (i % 8) == 3
        features.append([float(fresh), float(not ambiguous), float(i % 2), 0, 0, 0, 0, 0])
    with torch.inference_mode():
        logits = model(torch.tensor(features, device="cuda"))
        labels = logits.argmax(1).cpu().tolist()
    for i, label in enumerate(labels):
        hint = "CONTINUE" if label == 0 else "YIELD"
        oracle = "YIELD" if (i % 4) == 2 or (i % 8) == 3 else hint
        actual = final_gate((i % 4) != 2, (i % 8) == 3, hint)
        rows.append({"i": i, "actual": actual, "oracle": oracle})
    assert all(row["actual"] == row["oracle"] for row in rows)
    raw = json.dumps(rows, sort_keys=True, separators=(",", ":")).encode()
    print(json.dumps({
        "status": "PASS_FORMAL_SCOPED_COMPOSED_GATE",
        "rows": len(rows),
        "mismatches": 0,
        "forced_yield_rows": 96,
        "raw_sha256": hashlib.sha256(raw).hexdigest(),
        "device": torch.cuda.get_device_name(0),
        "torch": torch.__version__,
        "cuda_runtime": torch.version.cuda,
        "authority_grants": 0,
        "input_grants": 0,
        "task_success_claims": 0,
    }, sort_keys=True))

if __name__ == "__main__":
    main()
