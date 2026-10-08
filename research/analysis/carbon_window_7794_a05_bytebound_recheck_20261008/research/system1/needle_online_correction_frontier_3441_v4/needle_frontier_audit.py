"""Independent raw-only auditor; does not import the trainer."""
from __future__ import annotations

import copy
import hashlib
import json
import platform
import sys
from pathlib import Path

import torch
from torch.nn import functional as F

torch.set_num_threads(1)

SEEDS = (65117, 65229, 65341)
N = 256
ARRIVALS = 32
WIDTH = 16
IMAGE_ID = "sha256:6ab7a93188dd60d3832a0be8b5266418e0de1253159c5c66e64562a85fd4a10e"
STREAMS = {"train_A": 41017, "heldout_A": 42043, "heldout_B": 43051, "support_B": 44059}


def expected_split(seed: int, name: str) -> tuple[list, list]:
    gen = torch.Generator(device="cpu").manual_seed(seed * 1009 + STREAMS[name])
    if name == "support_B":
        batches = []
        for _ in range(ARRIVALS):
            batch = torch.rand((8, 8), generator=gen)
            batch[:4, 0] = 0.0
            batch[4:, 0] = 1.0
            batches.append(batch[torch.randperm(8, generator=gen)])
        x = torch.stack(batches).reshape(N, 8)
    else:
        x = torch.rand((N, 8), generator=gen)
        x[: N // 2, 0] = 0.0
        x[N // 2 :, 0] = 1.0
        x = x[torch.randperm(N, generator=gen)]
    y = (1 - x[:, 0].long()) if name in ("heldout_B", "support_B") else x[:, 0].long()
    return x.tolist(), y.tolist()


def digest_state(state: dict[str, list]) -> str:
    result = hashlib.sha256()
    for name in sorted(state):
        result.update(name.encode("utf-8") + b"\0")
        raw = torch.tensor(state[name], dtype=torch.float32).contiguous().view(torch.uint8).flatten().tolist()
        result.update(bytes(raw))
    return result.hexdigest()


def bad(condition: bool, message: str) -> None:
    if condition:
        raise ValueError(message)


def logits_from(base: dict[str, list], adapter: dict, features: torch.Tensor) -> torch.Tensor:
    h = torch.tanh(F.linear(features, torch.tensor(base["l1.weight"]), torch.tensor(base["l1.bias"])))
    base_logits = F.linear(h, torch.tensor(base["l2.weight"]), torch.tensor(base["l2.bias"]))
    a = torch.tensor(adapter["a"], dtype=torch.float32)
    b = torch.tensor(adapter["b"], dtype=torch.float32)
    return base_logits + (h @ b.T @ a.T) * 0.25


def audit_core(doc: dict) -> list[dict]:
    errors: list[dict] = []
    try:
        bad(doc.get("schema") != "needle-online-correction-frontier-v4", "schema")
        bad(doc.get("authority") is not False or doc.get("input_emissions") != 0, "authority boundary")
        runtime = doc.get("runtime", {})
        bad(runtime.get("image_id") != IMAGE_ID, "image identity")
        bad(runtime.get("platform") != "linux/amd64", "platform")
        bad(runtime.get("python") != "3.12.14" or platform.python_version() != "3.12.14", "python identity")
        bad(runtime.get("torch") != "2.5.1+cpu" or torch.__version__ != "2.5.1+cpu", "torch identity")
        bad(runtime.get("device") != "cpu" or runtime.get("threads") != 1 or torch.get_num_threads() != 1, "compute identity")
        bad(runtime.get("network") != "none", "network policy")
        bad(doc.get("stream_salts") != STREAMS, "stream salts")
        runs = doc.get("runs", [])
        bad([row.get("seed") for row in runs] != list(SEEDS), "seed schedule")

        for run in runs:
            seed = run["seed"]
            bad(run.get("base_train_steps") != 400, f"base schedule {seed}")
            expected_indices = [(step * 17 + seed) % N for step in range(400)]
            bad(run.get("base_train_indices") != expected_indices, f"base index schedule {seed}")
            names = ("train_A", "heldout_A", "heldout_B", "support_B")
            expected = {name: expected_split(seed, name) for name in names}
            for field, key in (("train_x", "train_A"), ("x_a", "heldout_A"), ("x_b", "heldout_B")):
                bad(run.get(field) != expected[key][0], f"seeded data {field} {seed}")
            bad(run.get("train_y") != expected["train_A"][1], f"seeded labels train {seed}")
            bad(run.get("y_a") != expected["heldout_A"][1], f"seeded labels A {seed}")
            bad(run.get("y_b") != expected["heldout_B"][1], f"seeded labels B {seed}")
            support_x, support_y = expected["support_B"]
            expected_sx = [support_x[i * 8 : (i + 1) * 8] for i in range(ARRIVALS)]
            expected_sy = [support_y[i * 8 : (i + 1) * 8] for i in range(ARRIVALS)]
            bad(run.get("support_x") != expected_sx or run.get("support_y") != expected_sy, f"seeded support {seed}")

            data_sets = [
                [tuple(row) for row in run["train_x"]],
                [tuple(row) for row in run["x_a"]],
                [tuple(row) for row in run["x_b"]],
                [tuple(row) for batch in run["support_x"] for row in batch],
            ]
            for index, rows in enumerate(data_sets):
                bad(len(set(rows)) != N, f"duplicate rows split {index} seed {seed}")
                for later in data_sets[index + 1 :]:
                    bad(bool(set(rows) & set(later)), f"cross-split row overlap seed {seed}")
            bad(sum(run["train_y"]) != N // 2, f"train balance {seed}")
            bad(sum(run["y_a"]) != N // 2 or sum(run["y_b"]) != N // 2, f"heldout balance {seed}")
            for batch, labels in zip(run["support_x"], run["support_y"]):
                bad(len(batch) != 8 or sum(int(row[0]) for row in batch) != 4, f"support balance {seed}")
                bad(labels != [1 - int(row[0]) for row in batch], f"support labels {seed}")

            base = run.get("base_state", {})
            required = {"l1.weight", "l1.bias", "l2.weight", "l2.bias"}
            bad(set(base) != required, f"base tensors {seed}")
            base_hash = digest_state(base)
            bad(base_hash != run.get("base_state_sha256") or base_hash != run.get("base_after_sha256"), f"base digest {seed}")
            curve = run.get("curve", [])
            snapshots = run.get("snapshots", [])
            bad(len(curve) != ARRIVALS + 1 or len(snapshots) != ARRIVALS + 1, f"curve count {seed}")
            bad(len(run.get("update_ms", [])) != ARRIVALS or len(run.get("inference_ms", [])) != ARRIVALS + 1, f"timing count {seed}")
            bad(any(not isinstance(v, (int, float)) or v < 0 for v in run["update_ms"] + run["inference_ms"]), f"timings {seed}")
            xa = torch.tensor(run["x_a"], dtype=torch.float32)
            ya = torch.tensor(run["y_a"], dtype=torch.long)
            xb = torch.tensor(run["x_b"], dtype=torch.float32)
            yb = torch.tensor(run["y_b"], dtype=torch.long)
            for index, (snapshot, point) in enumerate(zip(snapshots, curve)):
                bad(point.get("step") != index or point.get("n") != N, f"curve index/denominator {seed}:{index}")
                if index == 0:
                    bad(torch.count_nonzero(torch.tensor(snapshot["b"])).item() != 0, f"initial zero adapter {seed}")
                pa = logits_from(base, snapshot, xa)
                pb = logits_from(base, snapshot, xb)
                bad(not torch.allclose(pa, torch.tensor(point["logits_a"]), atol=1e-6, rtol=1e-6), f"A logits {seed}:{index}")
                bad(not torch.allclose(pb, torch.tensor(point["logits_b"]), atol=1e-6, rtol=1e-6), f"B logits {seed}:{index}")
                ac = int((pa.argmax(-1) == ya).sum())
                bc = int((pb.argmax(-1) == yb).sum())
                bad(pa.argmax(-1).tolist() != point.get("pred_a"), f"A predictions {seed}:{index}")
                bad(pb.argmax(-1).tolist() != point.get("pred_b"), f"B predictions {seed}:{index}")
                cea = float(F.cross_entropy(pa, ya))
                ceb = float(F.cross_entropy(pb, yb))
                bad((ac, bc) != (point.get("a_correct"), point.get("b_correct")), f"accuracy {seed}:{index}")
                bad(abs(cea - point.get("ce_a", float("inf"))) > 1e-6, f"A CE {seed}:{index}")
                bad(abs(ceb - point.get("ce_b", float("inf"))) > 1e-6, f"B CE {seed}:{index}")
                base_logits = logits_from(base, {"a": snapshot["a"], "b": [[0.0] * WIDTH for _ in range(2)]}, xa)
                base_acc = int((base_logits.argmax(-1) == ya).sum())
                bad(base_acc != point.get("base_a_correct"), f"base A metric {seed}:{index}")

            controls = run.get("controls", [])
            bad(len(controls) != 3, f"control count {seed}")
            bad(controls[0].get("decision") != "PROPOSAL" or controls[0].get("authority") is not False or controls[0].get("model_calls") != 1, f"valid control {seed}")
            bad(any(c.get("decision") != "YIELD" or c.get("authority") is not False or c.get("model_calls") != 0 or c.get("logits") is not None for c in controls[1:]), f"yield control {seed}")
        return errors
    except Exception as exc:
        errors.append({"type": "AUDIT_ERROR", "detail": str(exc)})
        return errors


def corruption_controls(doc: dict) -> list[dict]:
    mutations = [
        ("seed", lambda x: x["runs"][0].update(seed=0)),
        ("train_data", lambda x: x["runs"][0]["train_x"][0].__setitem__(1, 0.123)),
        ("heldout_label", lambda x: x["runs"][0]["y_a"].__setitem__(0, 1 - x["runs"][0]["y_a"][0])),
        ("support_row", lambda x: x["runs"][0]["support_x"][0][0].__setitem__(2, 0.321)),
        ("logit", lambda x: x["runs"][0]["curve"][0]["logits_a"][0].__setitem__(0, 999.0)),
        ("metric", lambda x: x["runs"][0]["curve"][0].update(a_correct=x["runs"][0]["curve"][0]["a_correct"] + 1)),
        ("base_tensor", lambda x: x["runs"][0]["base_state"]["l1.bias"].__setitem__(0, 123.0)),
        ("environment", lambda x: x["runtime"].update(image_id="wrong")),
        ("guard", lambda x: x["runs"][0]["controls"][1].update(decision="PROPOSAL", model_calls=1)),
    ]
    outcomes = []
    for name, edit in mutations:
        altered = copy.deepcopy(doc)
        edit(altered)
        outcomes.append({"mutation": name, "rejected": bool(audit_core(altered))})
    return outcomes


def audit_file(path: Path) -> dict:
    torch.use_deterministic_algorithms(True)
    doc = json.loads(path.read_text(encoding="utf-8"))
    errors = audit_core(doc)
    controls = corruption_controls(doc) if not errors else []
    missed = [case["mutation"] for case in controls if not case["rejected"]]
    if missed:
        errors.append({"type": "CORRUPTION_MISSED", "cases": missed})
    return {
        "schema": "needle-online-correction-frontier-audit-v4",
        "decision": "AUDIT_PASS" if not errors else "STOP_AUDIT",
        "errors": errors,
        "seed_count": len(doc.get("runs", [])),
        "curve_points": sum(len(run.get("curve", [])) for run in doc.get("runs", [])),
        "corruption_controls": controls,
    }


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("raw", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = audit_file(args.raw)
    payload = json.dumps(result, sort_keys=True, indent=2) + "\n"
    if args.output:
        args.output.write_text(payload, encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0 if result["decision"] == "AUDIT_PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
