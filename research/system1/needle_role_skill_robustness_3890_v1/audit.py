"""Independent audit; does not import runner.py, loader.py, or formal.py."""
import gzip
import hashlib
import json
import math
from pathlib import Path
import statistics
import sys

import torch
import torch.nn.functional as F

ALLOCATION = "needle-role-skill-robustness-3890-v1"
ISSUE = 4479
CONTRACT_SHA256 = "872022a1f2eec0b83f48f3704e2c3df7eedeeaaba9deb5128f74f3f4880cc691"
SEEDS = (3792, 3892, 3992, 4092, 4192, 4292, 4392, 4492, 4592, 4692)
ROLES = ("A", "B", "C")
IMAGE_ID = "sha256:6ab7a93188dd60d3832a0be8b5266418e0de1253159c5c66e64562a85fd4a10e"


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def no_duplicate_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate_json_key")
        result[key] = value
    return result


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"), object_pairs_hook=no_duplicate_pairs)


def digest_file(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def independently_generated_rows(seed):
    return [torch.randn(n, 8, generator=torch.Generator(device="cpu").manual_seed(seed + offset))
            for offset, n in enumerate((512, 16, 16, 4096, 4096, 4096), 1)]


def teacher(x, role):
    a = (x[:, 0] > 0).long()
    b = (x[:, 1] > 0).long()
    if role == "B":
        a = 1 - a
    if role == "C":
        b = 1 - b
    return (a * 2 + b).tolist()


def read_state_tensor(value):
    tensor = torch.tensor(value, dtype=torch.float32)
    if not torch.isfinite(tensor).all():
        raise ValueError("nonfinite_weight")
    return tensor


def reconstruct_predictions(artifact, role, rows):
    state = artifact["tensors"][role]
    x = torch.tensor(rows, dtype=torch.float32)
    if not torch.isfinite(x).all() or x.shape != (4096, 8):
        raise ValueError("heldout_input_shape_or_value")
    if role == "A":
        h = torch.tanh(F.linear(x, read_state_tensor(state["enc.0.weight"]),
                                read_state_tensor(state["enc.0.bias"])))
        logits = F.linear(h, read_state_tensor(state["head.weight"]),
                          read_state_tensor(state["head.bias"]))
    else:
        h = torch.tanh(F.linear(x, read_state_tensor(state["core.enc.0.weight"]),
                                read_state_tensor(state["core.enc.0.bias"])))
        logits = F.linear(h, read_state_tensor(state["core.head.weight"]),
                          read_state_tensor(state["core.head.bias"]))
        logits = logits + h @ read_state_tensor(state["a"]) @ read_state_tensor(state["b"]) / 2
    return logits.argmax(-1).tolist()


def audit(root):
    root = Path(root)
    source = Path(__file__).resolve().parent
    freeze = load_json(source / "FREEZE.json")
    errors, scientific_failures, reports = [], [], []
    expected_source_keys = ("runner.py", "loader.py", "formal.py", "audit.py",
                            "test_construction.py", "PREREGISTRATION.md",
                            "ISSUE_CONTRACT.md", "SOURCE_PROVENANCE.md",
                            "CONSTRUCTION.md", "README.md")
    for name in expected_source_keys:
        if digest_file(source / name) != freeze.get("source_sha256", {}).get(name):
            errors.append("freeze_source:" + name)
    freeze_digest = (source / "FREEZE.sha256").read_text(encoding="ascii").strip()
    if digest_file(source / "FREEZE.json") != freeze_digest:
        errors.append("freeze_manifest_hash")
    contract_file = (source / "ISSUE_CONTRACT.md").read_bytes()
    if not contract_file.endswith(b"\n") or contract_file.endswith(b"\n\n"):
        errors.append("contract_snapshot_newline")
        public_bytes = contract_file
    else:
        public_bytes = contract_file[:-1]
    local_body_hash = hashlib.sha256(public_bytes).hexdigest()
    if local_body_hash != CONTRACT_SHA256 or freeze.get("public_issue_body_sha256") != CONTRACT_SHA256:
        errors.append("public_issue_contract_hash")
    if hashlib.sha256(contract_file).hexdigest() != freeze.get("issue_contract_snapshot_sha256"):
        errors.append("issue_contract_snapshot_hash")
    if freeze.get("allocation") != ALLOCATION or freeze.get("issue") != ISSUE:
        errors.append("allocation_identity")
    if tuple(freeze.get("seeds", [])) != SEEDS:
        errors.append("seed_schedule")
    if freeze.get("docker_image_id") != IMAGE_ID:
        errors.append("image_identity")
    invocation_path = root / "FORMAL_INVOCATION.json"
    if not invocation_path.exists():
        return {"audit": "FAIL_AUDIT", "errors": errors + ["formal_invocation_missing"],
                "scientific_decision": "HOLD_EVIDENCE_INCOMPLETE"}
    invocation = load_json(invocation_path)
    if (invocation.get("status") != "COMPLETE" or invocation.get("allocation") != ALLOCATION
            or invocation.get("issue") != ISSUE or tuple(invocation.get("seeds", [])) != SEEDS
            or invocation.get("image_id") != IMAGE_ID or invocation.get("formal_orchestrations") != 1
            or invocation.get("retries") != 0 or len(invocation.get("invocations", [])) != 30):
        errors.append("formal_invocation_contract")
    role_values = {role: [] for role in ROLES}
    artifact_hashes = set()
    for seed in SEEDS:
        directory = root / f"seed-{seed}"
        try:
            builder_log = json.loads((directory / f"seed-{seed}-builder.stdout.txt").read_text(encoding="utf-8"))
        except Exception:
            builder_log = None
        if not isinstance(builder_log, dict) or builder_log.get("seed") != seed:
            errors.append(f"{seed}:builder_log")
        package_path = directory / "builder" / "skill.json"
        raw_package = package_path.read_bytes()
        package_sha = hashlib.sha256(raw_package).hexdigest()
        artifact = json.loads(raw_package, object_pairs_hook=no_duplicate_pairs)
        claimed = artifact.pop("payload_sha256", None)
        payload_sha = hashlib.sha256(canonical(artifact)).hexdigest()
        artifact["payload_sha256"] = claimed
        artifact_hashes.add(package_sha)
        if claimed != payload_sha or artifact.get("schema") != "unjuno.role-skill.numeric-json.v1":
            errors.append(f"{seed}:artifact_payload_digest_or_schema")
        if artifact.get("generation") != seed or artifact.get("provenance") != {
            "allocation": ALLOCATION, "issue": ISSUE, "issue_contract_sha256": CONTRACT_SHA256,
            "predecessor_issue": 3890, "seed": seed, "family": "synthetic-role-adapter-v1"
        }:
            errors.append(f"{seed}:artifact_provenance")
        if artifact.get("graph", {}).get("edges") != [["A", "B"], ["B", "C"]]:
            errors.append(f"{seed}:graph_manifest")
        if artifact.get("architecture") != {
            "input": 8, "hidden": 16, "classes": 4, "rank": 2, "roles": ["A", "B", "C"]
        }:
            errors.append(f"{seed}:architecture")
        if not builder_log or builder_log.get("artifact_sha256") != claimed:
            errors.append(f"{seed}:builder_artifact_binding")
        expected_path = directory / "builder" / "expected.json.gz"
        expected_raw = gzip.decompress(expected_path.read_bytes())
        expected = json.loads(expected_raw, object_pairs_hook=no_duplicate_pairs)
        if (not builder_log or hashlib.sha256(expected_raw).hexdigest()
                != builder_log.get("expected_sha256")):
            errors.append(f"{seed}:expected_digest")
        if expected.get("seed") != seed or expected.get("base_immutable") is not True:
            errors.append(f"{seed}:builder_identity_or_base_mutation")
        if set(expected.get("roles", {})) != set(ROLES) or set(artifact.get("tensors", {})) != set(ROLES):
            errors.append(f"{seed}:role_set")
            continue
        generated = independently_generated_rows(seed)
        for role_index, role in enumerate(ROLES):
            row = expected["roles"][role]
            expected_inputs = generated[3 + role_index]
            observed_inputs = torch.tensor(row.get("inputs", []), dtype=torch.float32)
            if observed_inputs.shape != (4096, 8) or not torch.equal(observed_inputs, expected_inputs):
                errors.append(f"{seed}:{role}:input_generation")
            gold = teacher(expected_inputs, role)
            if row.get("expected") != gold:
                errors.append(f"{seed}:{role}:independent_label")
            if artifact["tensors"][role] != row.get("state"):
                errors.append(f"{seed}:{role}:package_tensor_state_mismatch")
            independent = reconstruct_predictions(artifact, role, row["inputs"])
            if row.get("pred") != independent:
                errors.append(f"{seed}:{role}:builder_prediction_reconstruction")
            correct = sum(a == b for a, b in zip(independent, gold))
            accuracy = correct / 4096
            role_values[role].append(accuracy)
            if accuracy < 0.90:
                scientific_failures.append(f"{seed}:{role}:accuracy={accuracy:.6f}")
        before_path = directory / "artifact.before-load.sha256"
        after_path = directory / "artifact.after-load.sha256"
        before = before_path.read_text(encoding="ascii").strip()
        after = after_path.read_text(encoding="ascii").strip()
        if before != package_sha or after != package_sha or before != after:
            errors.append(f"{seed}:package_changed")
        seed_report = {"seed": seed, "artifact_sha256": package_sha, "roles": {}}
        for role in ROLES:
            row = expected["roles"][role]
            independent = reconstruct_predictions(artifact, role, row["inputs"])
            gold = teacher(torch.tensor(row["inputs"], dtype=torch.float32), role)
            seed_report["roles"][role] = {
                "accuracy": sum(a == b for a, b in zip(independent, gold)) / 4096,
                "rows": len(independent),
            }
        for loader_name in ("load1", "load2"):
            loaded = load_json(directory / loader_name / "loader.json")
            if loaded.get("accepted") is not True:
                errors.append(f"{seed}:{loader_name}:load_rejected")
            if loaded.get("artifact_sha256") != package_sha:
                errors.append(f"{seed}:{loader_name}:raw_artifact_sha_mismatch")
            if loaded.get("payload_sha256") != claimed:
                errors.append(f"{seed}:{loader_name}:payload_sha_mismatch")
            if loaded.get("package_sha256_before") != package_sha or loaded.get("package_sha256_after") != package_sha:
                errors.append(f"{seed}:{loader_name}:package_immutability")
            if loaded.get("predictions") != {r: expected["roles"][r]["pred"] for r in ROLES}:
                errors.append(f"{seed}:{loader_name}:builder_prediction_mismatch")
            if loaded.get("predictions") != {r: reconstruct_predictions(artifact, r, expected["roles"][r]["inputs"]) for r in ROLES}:
                errors.append(f"{seed}:{loader_name}:independent_prediction_mismatch")
            graphs = loaded.get("graphs", [])
            if len(graphs) != 2:
                errors.append(f"{seed}:{loader_name}:graph_generation_count")
            for ix, graph in enumerate(graphs):
                expected_generation = seed + (100 if ix else 0)
                want_controls = {
                    "wrong_adapter_version": "YIELD", "skipped_edge": "YIELD",
                    "wrong_scope": "YIELD", "unverified_outcome": "YIELD",
                    "unknown_destination": "YIELD", "stale_generation": "YIELD",
                    "duplicate_receipt": "ADVANCE", "duplicate_receipt_replay": "YIELD",
                }
                if (graph.get("generation") != expected_generation
                        or graph.get("controls") != want_controls
                        or graph.get("flow") != ["ADVANCE", "ADVANCE"]
                        or graph.get("cursor") != "C" or graph.get("fixture_emissions") != 2):
                    errors.append(f"{seed}:{loader_name}:graph_contract:{ix}")
        # Tie the retained predictions and labels back to the builder's exact
        # inference path, so a self-consistent but incorrect builder record
        # cannot pass solely by being repeated by both loaders.
        for role in ROLES:
            row = expected["roles"][role]
            gold = teacher(torch.tensor(row["inputs"], dtype=torch.float32), role)
            if row.get("expected") != gold:
                errors.append(f"{seed}:{role}:retained_label_mismatch")
            if row.get("pred") != reconstruct_predictions(artifact, role, row["inputs"]):
                errors.append(f"{seed}:{role}:retained_prediction_mismatch")
        reports.append(seed_report)
    if len(artifact_hashes) != len(SEEDS):
        errors.append("artifact_seed_uniqueness")
    role_summary = {}
    for role, values in role_values.items():
        role_summary[role] = {"n_seeds": len(values), "mean_accuracy": statistics.mean(values) if values else None,
                              "min_accuracy": min(values) if values else None,
                              "max_accuracy": max(values) if values else None,
                              "population_sd": statistics.pstdev(values) if values else None}
    scientific = ("FAIL_ROLE_SKILL_ROBUSTNESS" if scientific_failures
                  else "PASS_ROLE_SKILL_ROBUSTNESS_SCOPED")
    return {"audit": "PASS_AUDIT" if not errors else "FAIL_AUDIT",
            "scientific_decision": scientific if not errors else "HOLD_AUDIT_INTEGRITY",
            "errors": errors, "scientific_failures": scientific_failures,
            "role_summary": role_summary, "seed_reports": reports,
            "seeds": list(SEEDS), "n_role_seed_cells": sum(len(v) for v in role_values.values()),
            "threshold": 0.90, "issue_contract_sha256": CONTRACT_SHA256}


def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: audit.py FORMAL_OUTPUT")
    report = audit(sys.argv[1])
    out = Path(sys.argv[1]) / "AUDIT.json"
    with open(out, "x", encoding="utf-8") as f:
        json.dump(report, f, sort_keys=True, separators=(",", ":"), allow_nan=False)
        f.write("\n")
    print(json.dumps({"audit": report["audit"], "scientific_decision": report["scientific_decision"],
                      "errors": len(report["errors"]),
                      "scientific_failures": len(report["scientific_failures"])}, sort_keys=True))
    return 0 if report["audit"] == "PASS_AUDIT" else 2


if __name__ == "__main__":
    raise SystemExit(main())
