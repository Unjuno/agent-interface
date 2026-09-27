"""Paired construction probe: change only role-C support rows, 16 versus 64."""
import hashlib
import importlib.util
import json
import os
import random
from pathlib import Path

import torch

ALLOCATION = "needle-role-skill-c-support64-4749-v1"
PREDECESSOR_ISSUE = 4619
SCHEMA = "unjuno.role-skill.numeric-json.v1"


def load_upstream(path):
    spec = importlib.util.spec_from_file_location("immutable_3890_runner", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def build(upstream, seed, out):
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)
    random.seed(seed)
    torch.manual_seed(seed)
    xa = upstream.data(upstream.N_BASE, seed + 1)
    xb = upstream.data(upstream.N_SUPPORT, seed + 2)
    xc64 = upstream.data(64, seed + 3)
    ea, eb, ec = [upstream.data(upstream.N_HELDOUT, seed + i) for i in (4, 5, 6)]

    base = upstream.Core()
    upstream.train(base, xa, upstream.labels(xa, "A"), list(base.parameters()),
                   upstream.BASE_STEPS, upstream.LR_BASE, seed + 10)
    base_before = upstream.tensor_map(base)
    template = upstream.LoRA(base)
    initial = {k: v.clone() for k, v in template.state_dict().items()}

    bmodel = upstream.LoRA(base)
    bmodel.load_state_dict(initial)
    upstream.train(bmodel, xb, upstream.labels(xb, "B"), [bmodel.a, bmodel.b],
                   upstream.ADAPTER_STEPS, upstream.LR_ADAPTER, seed + 11)
    paired = {}
    for arm, rows in (("control16", xc64[:16]), ("treatment64", xc64)):
        cmodel = upstream.LoRA(base)
        cmodel.load_state_dict(initial)
        upstream.train(cmodel, rows, upstream.labels(rows, "C"), [cmodel.a, cmodel.b],
                       upstream.ADAPTER_STEPS, upstream.LR_ADAPTER, seed + 12)
        models = {"A": base, "B": bmodel, "C": cmodel}
        held = {"A": ea, "B": eb, "C": ec}
        roles = {}
        for role, x in held.items():
            with torch.no_grad():
                roles[role] = {"state": upstream.tensor_map(models[role]),
                               "pred": models[role](x).argmax(-1).tolist(),
                               "expected": upstream.labels(x, role).tolist(),
                               "inputs": x.tolist()}
        artifact = {
            "schema": SCHEMA,
            "generation": seed,
            "architecture": {"input": 8, "hidden": 16, "classes": 4,
                             "rank": 2, "roles": ["A", "B", "C"]},
            "graph": {"nodes": [{"id": r, "version": r + "-v1"} for r in ("A", "B", "C")],
                      "edges": [["A", "B"], ["B", "C"]],
                      "scope": "synthetic-fixture-v1"},
            "provenance": {"allocation": ALLOCATION, "predecessor_issue": PREDECESSOR_ISSUE,
                           "seed": seed, "family": "synthetic-role-adapter-v1",
                           "role_c_support_rows": 16 if arm == "control16" else 64},
            "tensors": {r: data["state"] for r, data in roles.items()}}
        artifact["payload_sha256"] = hashlib.sha256(canonical(artifact)).hexdigest()
        target = Path(out) / arm
        target.mkdir(parents=True, exist_ok=True)
        (target / "skill.json").write_bytes(canonical(artifact))
        expected = {"seed": seed, "arm": arm, "role_c_support_rows": 16 if arm == "control16" else 64,
                    "roles": roles, "base_immutable": upstream.tensor_map(base) == base_before,
                    "support16_prefix_of_64": torch.equal(xc64[:16], upstream.data(16, seed + 3)),
                    "shared_A_B": True}
        (target / "expected.json").write_bytes(canonical(expected))
        paired[arm] = expected
    if paired["control16"]["roles"]["A"] != paired["treatment64"]["roles"]["A"]:
        raise ValueError("A_changed")
    if paired["control16"]["roles"]["B"] != paired["treatment64"]["roles"]["B"]:
        raise ValueError("B_changed")
    summary = {"seed": seed, "allocation": ALLOCATION,
               "c_support_rows": {"control16": 16, "treatment64": 64},
               "per_role_accuracy": {arm: {r: sum(a == b for a, b in
                    zip(v["pred"], v["expected"])) / len(v["expected"])
                    for r, v in data["roles"].items()} for arm, data in paired.items()},
               "A_B_exactly_unchanged": True,
               "C_support_prefix_equal": all(paired[arm]["support16_prefix_of_64"] for arm in paired)}
    (Path(out) / "construction-result.json").write_bytes(canonical(summary))
    print(json.dumps(summary, sort_keys=True), flush=True)


def main():
    if "NEEDLE_SEED" not in os.environ or "NEEDLE_OUTPUT" not in os.environ:
        raise SystemExit("STOP_MISSING_NEEDLE_ENV")
    seed = int(os.environ["NEEDLE_SEED"])
    out = os.environ["NEEDLE_OUTPUT"]
    if seed != 7865001 or not Path(out).is_dir() or any(Path(out).iterdir()):
        raise SystemExit("STOP_CONSTRUCTION_ALLOCATION_OR_OUTPUT")
    upstream = load_upstream("/src/source/runner.py")
    build(upstream, seed, out)


if __name__ == "__main__":
    main()
