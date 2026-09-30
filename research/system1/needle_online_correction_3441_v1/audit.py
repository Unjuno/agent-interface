"""Independent raw-only auditor for Issue #4824; does not import runner.py."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import random
from pathlib import Path

import torch

ALLOCATION = "needle-online-correction-forgetting-3441-v1"
IMAGE_ID = "sha256:6ab7a93188dd60d3832a0be8b5266418e0de1253159c5c66e64562a85fd4a10e"
SEEDS = (68117, 68229, 68341)


def expected_data(seed: int, salt: int, n: int) -> tuple[list[list[int]], list[int]]:
    rng = random.Random(seed * 1009 + salt)
    first = [0, 1] * (n // 2)
    if salt != 101:
        rng.shuffle(first)
    rows = [[bit, *[rng.randrange(2) for _ in range(7)]] for bit in first]
    return rows, [int(row[0] == 1) for row in rows]


def tensor_digest(values: list[list[float]] | list[float]) -> str:
    tensor = torch.tensor(values, dtype=torch.float32).contiguous().view(torch.uint8).flatten()
    return hashlib.sha256(bytes(tensor.tolist())).hexdigest()


def fail_if(condition: bool, errors: list[str], label: str) -> None:
    if condition:
        errors.append(label)


def audit_core(raw: dict) -> list[str]:
    errors: list[str] = []
    fail_if(raw.get("schema") != "needle-online-correction-raw-v1", errors, "schema")
    fail_if(raw.get("allocation") != ALLOCATION or raw.get("image_id") != IMAGE_ID, errors, "identity")
    fail_if(raw.get("platform") != "linux/amd64" or raw.get("device") != "cpu" or raw.get("threads") != 1,
            errors, "environment")
    fail_if(raw.get("seeds") is None or [x.get("seed") for x in raw.get("seeds", [])] != list(SEEDS), errors, "seed_schedule")
    fail_if(raw.get("authority") is not False or raw.get("input_emissions") != 0, errors, "authority_boundary")

    for seed_row in raw.get("seeds", []):
        seed = seed_row.get("seed")
        if seed not in SEEDS:
            errors.append("seed_identity")
            continue
        sx, sy = expected_data(seed, 101, 16)
        ax, ay = expected_data(seed, 211, 256)
        bx, by = expected_data(seed, 307, 256)
        fail_if(seed_row.get("support_features") != sx, errors, f"support_features_{seed}")
        fail_if(seed_row.get("heldout_A_features") != ax or seed_row.get("heldout_A_targets") != [0] * 256,
                errors, f"heldout_A_{seed}")
        fail_if(seed_row.get("heldout_B_features") != bx or seed_row.get("heldout_B_targets") != by,
                errors, f"heldout_B_{seed}")
        fail_if(seed_row.get("base_train_steps") != 400 or len(seed_row.get("correction_rows", [])) != 8,
                errors, f"training_schedule_{seed}")
        fail_if(len(seed_row.get("curves", [])) != 9 or len(seed_row.get("adapter_snapshots", [])) != 9,
                errors, f"curve_count_{seed}")

        base = seed_row.get("base_parameters", [])
        if len(base) != 4:
            errors.append(f"base_parameter_count_{seed}")
            continue
        digest = hashlib.sha256()
        for value in base:
            tensor = torch.tensor(value, dtype=torch.float32).contiguous().view(torch.uint8).flatten()
            digest.update(bytes(tensor.tolist()))
        base_hash = digest.hexdigest()
        fail_if(base_hash != seed_row.get("base_sha256_before") or
                seed_row.get("base_sha256_before") != seed_row.get("base_sha256_after"), errors, f"base_immutability_{seed}")

        w1, b1, w2, b2 = [torch.tensor(value, dtype=torch.float32) for value in base]
        held_a = torch.tensor(ax, dtype=torch.float32)
        held_b = torch.tensor(bx, dtype=torch.float32)
        target_a = torch.tensor([0] * 256, dtype=torch.long)
        target_b = torch.tensor(by, dtype=torch.long)
        corrections = seed_row.get("correction_rows", [])
        for i, row in enumerate(corrections):
            fail_if(row.get("arrival") != i + 1 or row.get("features") != sx[i] or
                    row.get("target") != sx[i][0], errors, f"correction_{seed}_{i}")

        snapshots = seed_row.get("adapter_snapshots", [])
        curves = seed_row.get("curves", [])
        for i, snapshot in enumerate(snapshots[:9]):
            try:
                adapter_a = torch.tensor(snapshot["A"], dtype=torch.float32)
                adapter_b = torch.tensor(snapshot["B"], dtype=torch.float32)
                hidden_a = torch.tanh(held_a @ w1 + b1)
                hidden_b = torch.tanh(held_b @ w1 + b1)
                logits_a = hidden_a @ w2 + b2 + (hidden_a @ adapter_a @ adapter_b) / 2.0
                logits_b = hidden_b @ w2 + b2 + (hidden_b @ adapter_a @ adapter_b) / 2.0
                retained_a = curves[i]["A_logits"]
                retained_b = curves[i]["B_logits"]
                fail_if(not torch.allclose(logits_a, torch.tensor(retained_a), atol=1e-6, rtol=1e-6),
                        errors, f"A_logits_recompute_{seed}_{i}")
                fail_if(not torch.allclose(logits_b, torch.tensor(retained_b), atol=1e-6, rtol=1e-6),
                        errors, f"B_logits_recompute_{seed}_{i}")
                for label, logits, targets in (("A", logits_a, target_a), ("B", logits_b, target_b)):
                    measured = curves[i][label]
                    acc = float((logits.argmax(1) == targets).float().mean().item())
                    loss = float(torch.nn.functional.cross_entropy(logits, targets).item())
                    fail_if(measured.get("n") != 256 or abs(measured.get("accuracy", -1) - acc) > 1e-7 or
                            abs(measured.get("cross_entropy", -1) - loss) > 1e-6,
                            errors, f"{label}_metrics_{seed}_{i}")
                fail_if(curves[i].get("step") != i, errors, f"step_index_{seed}_{i}")
            except Exception:
                errors.append(f"recompute_exception_{seed}_{i}")

        controls = seed_row.get("scope_controls", [])
        fail_if(len(controls) != 9, errors, f"control_count_{seed}")
        for i, control in enumerate(controls):
            fail_if(control.get("step") != i, errors, f"control_step_{seed}_{i}")
            for key in ("unknown_scope", "stale_epoch"):
                receipt = control.get(key, {})
                fail_if(receipt.get("decision") != "YIELD" or receipt.get("authority") is not False or
                        receipt.get("model_calls") != 0, errors, f"yield_{key}_{seed}_{i}")
            for key in ("base_route_A", "online_route_B"):
                receipt = control.get(key, {})
                fail_if(receipt.get("decision") != "PROPOSAL" or receipt.get("authority") is not False or
                        receipt.get("model_calls") != 1, errors, f"proposal_{key}_{seed}_{i}")
            fail_if(control.get("model_calls_total") != 2, errors, f"model_call_total_{seed}_{i}")
    return errors


def corruption_controls(raw: dict) -> dict:
    mutations = []

    def changed(name: str, edit) -> None:
        altered = copy.deepcopy(raw)
        edit(altered)
        mutations.append((name, altered))

    changed("schema", lambda x: x.update(schema="wrong"))
    changed("image", lambda x: x.update(image_id="sha256:" + "0" * 64))
    changed("authority", lambda x: x.update(authority=True))
    changed("seed", lambda x: x["seeds"][0].update(seed=1))
    changed("heldout_feature", lambda x: x["seeds"][0]["heldout_A_features"][0].__setitem__(0, 1 - x["seeds"][0]["heldout_A_features"][0][0]))
    changed("target", lambda x: x["seeds"][0]["heldout_B_targets"].__setitem__(0, 1 - x["seeds"][0]["heldout_B_targets"][0]))
    changed("logit", lambda x: x["seeds"][0]["curves"][0]["A_logits"][0].__setitem__(0, x["seeds"][0]["curves"][0]["A_logits"][0][0] + 1.0))
    changed("metric", lambda x: x["seeds"][0]["curves"][0]["A"].update(accuracy=0.123))
    changed("base_hash", lambda x: x["seeds"][0].update(base_sha256_after="0" * 64))
    changed("scope_yield", lambda x: x["seeds"][0]["scope_controls"][0]["unknown_scope"].update(decision="PROPOSAL", model_calls=1))
    changed("input_emission", lambda x: x.update(input_emissions=1))
    rejected = []
    for name, altered in mutations:
        rejected.append({"mutation": name, "rejected": bool(audit_core(altered))})
    return {"attempted": len(rejected), "rejected": sum(int(x["rejected"]) for x in rejected), "cases": rejected}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("raw", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    raw = json.loads(args.raw.read_text(encoding="utf-8"))
    errors = audit_core(raw)
    controls = corruption_controls(raw)
    if controls["rejected"] != controls["attempted"]:
        errors.append("corruption_controls")
    result = {"schema": "needle-online-correction-audit-v1", "decision": "PASS_RAW_AUDIT" if not errors else "STOP_AUDIT",
              "errors": errors, "seed_count": len(raw.get("seeds", [])),
              "curves_per_seed": [len(x.get("curves", [])) for x in raw.get("seeds", [])],
              "recomputed_predictions": 3 * 9 * 2 * 256, "corruption_controls": controls,
              "scope": raw.get("scope")}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
