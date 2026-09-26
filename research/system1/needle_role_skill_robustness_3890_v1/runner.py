"""One seed's role-skill builder; source is mounted read-only in Docker."""
import gzip
import hashlib
import json
import os
import platform
import random
import sys
import time

import torch
from torch import nn

SEED = int(os.environ.get("NEEDLE_SEED", "0"))
OUT = os.environ.get("NEEDLE_OUTPUT", "")
ALLOCATION = "needle-role-skill-robustness-3890-v1"
ISSUE = 4479
ISSUE_CONTRACT_SHA256 = "872022a1f2eec0b83f48f3704e2c3df7eedeeaaba9deb5128f74f3f4880cc691"
D, H, C, RANK = 8, 16, 4, 2
N_BASE, N_SUPPORT, N_HELDOUT = 512, 16, 4096
BASE_STEPS, ADAPTER_STEPS = 400, 120
LR_BASE, LR_ADAPTER = 0.025, 0.04
SCHEMA = "unjuno.role-skill.numeric-json.v1"


def data(n, seed):
    return torch.randn(n, D, generator=torch.Generator(device="cpu").manual_seed(seed))


def labels(x, role):
    a, b = (x[:, 0] > 0).long(), (x[:, 1] > 0).long()
    if role == "B": a = 1 - a
    if role == "C": b = 1 - b
    return a * 2 + b


class Core(nn.Module):
    def __init__(self):
        super().__init__()
        self.enc = nn.Sequential(nn.Linear(D, H), nn.Tanh())
        self.head = nn.Linear(H, C)

    def forward(self, x):
        return self.head(self.enc(x))


class LoRA(nn.Module):
    def __init__(self, core):
        super().__init__()
        self.core = core
        for p in core.parameters():
            p.requires_grad_(False)
        self.a = nn.Parameter(torch.randn(H, RANK) * 0.04)
        self.b = nn.Parameter(torch.zeros(RANK, C))

    def forward(self, x):
        h = self.core.enc(x)
        return self.core.head(h) + (h @ self.a @ self.b) / RANK


def train(model, x, y, params, steps, lr, seed):
    opt = torch.optim.AdamW(params, lr=lr)
    rng = torch.Generator(device="cpu").manual_seed(seed)
    model.train()
    for _ in range(steps):
        ix = torch.randint(len(x), (32,), generator=rng)
        loss = nn.functional.cross_entropy(model(x[ix]), y[ix])
        opt.zero_grad(set_to_none=True)
        loss.backward()
        opt.step()


def tensor_map(model):
    return {k: v.detach().cpu().tolist() for k, v in model.state_dict().items()}


def digest(obj):
    raw = json.dumps(obj, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    return hashlib.sha256(raw).hexdigest()


def write_new(path, raw):
    with open(path, "xb") as f:
        f.write(raw)


def main():
    if not OUT or not os.path.isdir(OUT) or os.listdir(OUT):
        raise SystemExit("builder output must exist and be empty")
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)
    random.seed(SEED)
    torch.manual_seed(SEED)
    xa, xb, xc, ea, eb, ec = [
        data(n, SEED + i) for i, n in enumerate(
            (N_BASE, N_SUPPORT, N_SUPPORT, N_HELDOUT, N_HELDOUT, N_HELDOUT), 1)
    ]
    base = Core()
    train(base, xa, labels(xa, "A"), list(base.parameters()), BASE_STEPS, LR_BASE, SEED + 10)
    before = {k: v.clone() for k, v in base.state_dict().items()}
    template = LoRA(base)
    initial = {k: v.clone() for k, v in template.state_dict().items()}
    adapters = {}
    for role, x, offset in (("B", xb, 11), ("C", xc, 12)):
        model = LoRA(base)
        model.load_state_dict(initial)
        train(model, x, labels(x, role), [model.a, model.b],
              ADAPTER_STEPS, LR_ADAPTER, SEED + offset)
        adapters[role] = model
    models = {"A": base, **adapters}
    roles = {}
    for role, x in (("A", ea), ("B", eb), ("C", ec)):
        with torch.no_grad():
            roles[role] = {
                "state": tensor_map(models[role]),
                "pred": models[role](x).argmax(-1).tolist(),
                "expected": labels(x, role).tolist(),
                "inputs": x.tolist(),
            }
    artifact = {
        "schema": SCHEMA,
        "generation": SEED,
        "architecture": {"input": 8, "hidden": 16, "classes": 4,
                         "rank": 2, "roles": ["A", "B", "C"]},
        "graph": {"nodes": [{"id": r, "version": r + "-v1"} for r in ("A", "B", "C")],
                  "edges": [["A", "B"], ["B", "C"]], "scope": "synthetic-fixture-v1"},
        "provenance": {"allocation": ALLOCATION, "issue": ISSUE,
                       "issue_contract_sha256": ISSUE_CONTRACT_SHA256,
                       "predecessor_issue": 3890, "seed": SEED,
                       "family": "synthetic-role-adapter-v1"},
        "tensors": {r: value["state"] for r, value in roles.items()},
    }
    artifact["payload_sha256"] = digest(artifact)
    expected = {"seed": SEED, "roles": roles,
                "base_immutable": all(torch.equal(v, before[k])
                                      for k, v in base.state_dict().items())}
    artifact_raw = (json.dumps(artifact, sort_keys=True, separators=(",", ":"),
                               allow_nan=False) + "\n").encode()
    expected_raw = (json.dumps(expected, sort_keys=True, separators=(",", ":"),
                               allow_nan=False) + "\n").encode()
    write_new(os.path.join(OUT, "skill.json"), artifact_raw)
    with open(os.path.join(OUT, "expected.json.gz"), "xb") as f:
        with gzip.GzipFile(fileobj=f, mode="wb", mtime=0) as gz:
            gz.write(expected_raw)
    print(json.dumps({"seed": SEED, "artifact_sha256": artifact["payload_sha256"],
                      "artifact_bytes": len(artifact_raw),
                      "expected_sha256": hashlib.sha256(expected_raw).hexdigest(),
                      "expected_gzip_bytes": os.path.getsize(os.path.join(OUT, "expected.json.gz")),
                      "environment": {"platform": platform.platform(),
                                      "python": platform.python_version(),
                                      "torch": torch.__version__, "device": "cpu",
                                      "threads": torch.get_num_threads()}}, sort_keys=True))


if __name__ == "__main__":
    main()
