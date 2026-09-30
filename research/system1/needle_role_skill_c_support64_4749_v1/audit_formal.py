"""Independent paired re-fit and artifact/loader audit; imports no experiment modules."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import random
import sys

import torch
from torch import nn

ALLOCATION = "needle-role-skill-c-support64-4749-v1"
SEEDS = (7865101, 7865201, 7865301, 7865401, 7865501,
         7865601, 7865701, 7865801, 7865901, 7866001)
ARMS = ("control16", "treatment64")
ROLES = ("A", "B", "C")
D, H, C, RANK = 8, 16, 4, 2


def canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def data(n, seed):
    return torch.randn(n, D, generator=torch.Generator(device="cpu").manual_seed(seed))


def labels(x, role):
    a, b = (x[:, 0] > 0).long(), (x[:, 1] > 0).long()
    if role == "B":
        a = 1 - a
    if role == "C":
        b = 1 - b
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
        self.a = nn.Parameter(torch.randn(H, RANK) * .04)
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


def regenerate(seed):
    random.seed(seed)
    torch.manual_seed(seed)
    xa, xb, xc64, ea, eb, ec = [data(n, seed + i) for i, n in enumerate((512, 16, 64, 4096, 4096, 4096), 1)]
    base = Core()
    train(base, xa, labels(xa, "A"), list(base.parameters()), 400, .025, seed + 10)
    base_before = tensor_map(base)
    template = LoRA(base)
    initial = {k: v.clone() for k, v in template.state_dict().items()}
    bmodel = LoRA(base)
    bmodel.load_state_dict(initial)
    train(bmodel, xb, labels(xb, "B"), [bmodel.a, bmodel.b], 120, .04, seed + 11)
    result = {}
    for arm, xc in (("control16", xc64[:16]), ("treatment64", xc64)):
        cmodel = LoRA(base)
        cmodel.load_state_dict(initial)
        train(cmodel, xc, labels(xc, "C"), [cmodel.a, cmodel.b], 120, .04, seed + 12)
        models, held = {"A": base, "B": bmodel, "C": cmodel}, {"A": ea, "B": eb, "C": ec}
        roles = {}
        for role in ROLES:
            x = held[role]
            with torch.no_grad():
                roles[role] = {"state": tensor_map(models[role]),
                               "pred": models[role](x).argmax(-1).tolist(),
                               "expected": labels(x, role).tolist(), "inputs": x.tolist()}
        result[arm] = {"roles": roles, "base_immutable": tensor_map(base) == base_before,
                       "support16_prefix_of_64": torch.equal(xc64[:16], data(16, seed + 3))}
    return result


def verify_loader(path, expected, arm, seed):
    report = json.loads(Path(path).read_text(encoding="utf-8"))
    digest = hashlib.sha256((Path(path).parents[2] / "builder" / arm / "skill.json").read_bytes()).hexdigest()
    expected_predictions = {r: expected["roles"][r]["pred"] for r in ROLES}
    assert report.get("accepted") is True and report.get("artifact_sha256") == digest
    assert report.get("predictions") == expected_predictions
    graphs = report.get("graphs", [])
    assert len(graphs) == 2
    controls = {"tampered_digest": "YIELD", "wrong_adapter_version": "YIELD",
                "skipped_edge": "YIELD", "wrong_scope": "YIELD", "unverified_outcome": "YIELD",
                "unknown_destination": "YIELD", "truncated": "YIELD", "unknown_schema": "YIELD",
                "duplicate_receipt": "ADVANCE", "duplicate_receipt_second": "YIELD"}
    for generation, graph in zip((seed, seed + 1), graphs):
        assert graph.get("generation") == generation
        assert graph.get("flow") == ["ADVANCE", "ADVANCE"]
        assert graph.get("cursor") == "C" and graph.get("old_receipt") == "YIELD"
        assert graph.get("fixture_emissions") == 2 and graph.get("controls") == controls
    return report


def audit(raw, out, baseline):
    root = Path(raw)
    errors, results = [], []
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    torch.use_deterministic_algorithms(True)
    # Verify exact upstream hashes against the merged #3890 public freeze.
    upstream_freeze = json.loads((Path(baseline) / "FREEZE.json").read_text(encoding="utf-8"))
    for name, key in (("runner.py", "runner_sha256"), ("loader.py", "loader_sha256"),
                      ("audit.py", "auditor_sha256"), ("PREREGISTRATION.md", "preregistration_sha256")):
        if hashlib.sha256((Path(baseline) / name).read_bytes()).hexdigest() != upstream_freeze[key]:
            errors.append(f"upstream_hash:{name}")
    for seed in SEEDS:
        try:
            regenerated = regenerate(seed)
            per_seed = {"seed": seed, "arms": {}}
            packages = {}
            for arm in ARMS:
                arm_dir = root / f"seed-{seed}" / "builder" / arm
                raw_bytes = (arm_dir / "skill.json").read_bytes()
                artifact = json.loads(raw_bytes, object_pairs_hook=lambda pairs: _no_dupes(pairs))
                expected = json.loads((arm_dir / "expected.json").read_text(encoding="utf-8"))
                payload = artifact.pop("payload_sha256")
                if payload != hashlib.sha256(canonical(artifact)).hexdigest():
                    raise ValueError(f"{arm}:payload_digest")
                artifact["payload_sha256"] = payload
                if artifact["schema"] != "unjuno.role-skill.numeric-json.v1" or artifact["generation"] != seed:
                    raise ValueError(f"{arm}:identity")
                if artifact["provenance"] != {"allocation": ALLOCATION, "predecessor_issue": 4619,
                                               "seed": seed, "family": "synthetic-role-adapter-v1",
                                               "role_c_support_rows": 16 if arm == "control16" else 64}:
                    raise ValueError(f"{arm}:provenance")
                if artifact["graph"]["edges"] != [["A", "B"], ["B", "C"]]:
                    raise ValueError(f"{arm}:graph")
                reference = regenerated[arm]
                if expected["seed"] != seed or expected["arm"] != arm or not expected["base_immutable"] or not expected["support16_prefix_of_64"]:
                    raise ValueError(f"{arm}:builder_metadata")
                if artifact["tensors"] != {r: reference["roles"][r]["state"] for r in ROLES}:
                    raise ValueError(f"{arm}:independent_training_replay")
                for role in ROLES:
                    if expected["roles"][role] != reference["roles"][role]:
                        raise ValueError(f"{arm}:{role}:raw_prediction_or_input")
                for loader in ("load1", "load2"):
                    verify_loader(root / f"seed-{seed}" / arm / loader / "loader.json", reference, arm, seed)
                metrics = {r: sum(a == b for a, b in zip(reference["roles"][r]["pred"],
                                                               reference["roles"][r]["expected"])) / 4096 for r in ROLES}
                per_seed["arms"][arm] = {"accuracy": metrics, "artifact_sha256": hashlib.sha256(raw_bytes).hexdigest(),
                                         "loaders_exact": 2}
                packages[arm] = artifact
            for role in ("A", "B"):
                if packages["control16"]["tensors"][role] != packages["treatment64"]["tensors"][role]:
                    raise ValueError(f"paired:{role}_state_changed")
            per_seed["paired_C_delta"] = (per_seed["arms"]["treatment64"]["accuracy"]["C"] -
                                           per_seed["arms"]["control16"]["accuracy"]["C"])
            results.append(per_seed)
        except Exception as exc:
            errors.append(f"{seed}:{type(exc).__name__}:{exc}")
    complete = len(results) == len(SEEDS) and not errors
    treatment_scores = [x["arms"]["treatment64"]["accuracy"]["C"] for x in results]
    control_scores = [x["arms"]["control16"]["accuracy"]["C"] for x in results]
    mean_t = sum(treatment_scores) / len(treatment_scores) if treatment_scores else None
    mean_c = sum(control_scores) / len(control_scores) if control_scores else None
    delta = mean_t - mean_c if treatment_scores and control_scores else None
    quality_pass = bool(complete and all(x >= .90 for x in treatment_scores) and delta is not None and delta >= .01)
    status = "PASS_ROLE_C_SUPPORT64_SCOPED" if quality_pass else (
        "FAIL_ROLE_C_SUPPORT64" if complete else "STOP_OR_AUDIT_INCOMPLETE")
    result = {"schema": "needle-role-skill-c-support64-audit-v1", "allocation": ALLOCATION,
              "status": status, "integrity_pass": complete, "errors": errors,
              "formal_seeds": list(SEEDS), "n_seeds_checked": len(results), "n_role_seed_cells": len(results) * 6,
              "treatment_C": {"mean": mean_t, "min": min(treatment_scores) if treatment_scores else None,
                              "below_0_90": sum(x < .90 for x in treatment_scores)},
              "control_C": {"mean": mean_c, "min": min(control_scores) if control_scores else None,
                            "below_0_90": sum(x < .90 for x in control_scores)},
              "paired_mean_C_delta": delta, "seeds": results,
              "notice": "Synthetic held-out skill-package evidence only; no model/runtime promotion."}
    Path(out).mkdir(parents=True, exist_ok=True)
    (Path(out) / "AUDIT.json").write_bytes(canonical(result) + b"\n")
    print(json.dumps({"status": status, "seeds": len(results), "errors": len(errors),
                      "mean_C_delta": delta}, sort_keys=True), flush=True)
    if not complete:
        raise SystemExit(2)


def _no_dupes(pairs):
    obj = {}
    for key, value in pairs:
        if key in obj:
            raise ValueError("duplicate_key")
        obj[key] = value
    return obj


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--raw", required=True)
    p.add_argument("--baseline", required=True)
    p.add_argument("--out", required=True)
    args = p.parse_args()
    audit(args.raw, args.out, args.baseline)
