"""Independent raw-evidence auditor; imports neither builder nor loader."""
import argparse
import hashlib
import json
from pathlib import Path

SEEDS = [2026092700, 2026092800, 2026092900, 2026093000, 2026093100,
         2026093200, 2026093300, 2026093400, 2026093500, 2026093600]
EXPECTED_CONTROLS = {
    "tampered_digest": "YIELD", "wrong_adapter_version": "YIELD",
    "skipped_edge": "YIELD", "wrong_scope": "YIELD",
    "unverified_outcome": "YIELD", "unknown_destination": "YIELD",
    "truncated": "YIELD", "unknown_schema": "YIELD",
    "duplicate_receipt": "ADVANCE", "duplicate_receipt_second": "YIELD",
}


def canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def digest(data):
    return hashlib.sha256(data).hexdigest()


def git_blob_sha(data):
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def source_bytes(path, expected):
    raw = Path(path).read_bytes()
    for candidate in (raw, raw.rstrip(b"\n"), raw.rstrip(b"\n") + b"\n"):
        if digest(candidate) == expected:
            return candidate
    raise ValueError("source_hash:" + str(path))


def accuracy(pred, gold):
    if not isinstance(pred, list) or not isinstance(gold, list) or len(pred) != 4096 or len(gold) != 4096:
        raise ValueError("prediction_row_count")
    return sum(a == b for a, b in zip(pred, gold)) / 4096


def audit(root, source, freeze):
    root, source = Path(root), Path(source)
    project = source.parent
    errors, result_rows = [], []
    for name, expected in freeze["source_sha256"].items():
        try:
            source_bytes(project / name, expected)
        except Exception as exc:
            errors.append("freeze_source:" + name + ":" + str(exc))
    parent_freeze = (source / "FREEZE.json").read_bytes()
    if not any(git_blob_sha(candidate) == freeze.get("parent_freeze_blob_sha1")
               for candidate in (parent_freeze, parent_freeze.rstrip(b"\n"), parent_freeze.rstrip(b"\n") + b"\n")):
        errors.append("parent_freeze_git_blob")
    formal_path = root / "FORMAL_RUN.json"
    try:
        formal = json.loads(formal_path.read_text(encoding="utf-8"))
        if formal.get("formal_orchestrations") != 1 or formal.get("retries") != 0:
            errors.append("formal_invocation_or_retry_count")
        if formal.get("image_id") != freeze["image_id"]:
            errors.append("runtime_image_id")
        if [x.get("seed") for x in formal.get("seeds", [])] != SEEDS:
            errors.append("seed_schedule")
    except Exception as exc:
        errors.append("formal_run_unreadable:" + repr(exc))
        formal = {"seeds": []}
    records = {x.get("seed"): x for x in formal.get("seeds", [])}
    for seed in SEEDS:
        rec = records.get(seed)
        d = root / f"seed-{seed}"
        if rec is None:
            errors.append(f"{seed}:missing_seed_record")
            continue
        if rec.get("typed_stop"):
            errors.append(f"{seed}:typed_stop:{rec['typed_stop']}")
            continue
        if rec.get("builder", {}).get("returncode") != 0:
            errors.append(f"{seed}:builder_failed")
            continue
        try:
            raw = (d / "builder" / "skill.json").read_bytes()
            artifact = json.loads(raw)
            expected = json.loads((d / "builder" / "expected.json").read_text(encoding="utf-8"))
            payload = artifact.pop("payload_sha256")
            if digest(canonical(artifact)) != payload:
                errors.append(f"{seed}:artifact_payload_digest")
            artifact["payload_sha256"] = payload
            if artifact.get("schema") != "unjuno.role-skill.numeric-json.v1" or artifact.get("generation") != seed:
                errors.append(f"{seed}:artifact_identity")
            if artifact.get("provenance", {}).get("seed") != seed:
                errors.append(f"{seed}:artifact_provenance")
            if expected.get("seed") != seed or expected.get("base_immutable") is not True:
                errors.append(f"{seed}:expected_or_base_immutability")
            role_scores = {}
            for role in ("A", "B", "C"):
                data = expected["roles"][role]
                score = accuracy(data.get("pred"), data.get("expected"))
                role_scores[role] = score
                if score < 0.90:
                    errors.append(f"{seed}:{role}:competence")
                if len(data.get("inputs", [])) != 4096:
                    errors.append(f"{seed}:{role}:input_rows")
            before = rec.get("package_sha256_before")
            after = rec.get("package_sha256_after_all_loaders")
            if before != digest(raw) or after != before:
                errors.append(f"{seed}:package_mutated")
            loaders = rec.get("loaders", [])
            if [x.get("name") for x in loaders] != ["load1", "load2"]:
                errors.append(f"{seed}:loader_count_or_identity")
            for ld in loaders:
                if ld.get("returncode") != 0 or not ld.get("loader_json_exists"):
                    errors.append(f"{seed}:{ld.get('name')}:loader_failed")
                    continue
                if ld.get("package_sha256_after") != before:
                    errors.append(f"{seed}:{ld.get('name')}:package_mutated")
                loaded = json.loads((d / ld["name"] / "loader.json").read_text(encoding="utf-8"))
                if loaded.get("accepted") is not True or loaded.get("artifact_sha256") != before:
                    errors.append(f"{seed}:{ld['name']}:artifact_not_loaded")
                if loaded.get("predictions") != {r: expected["roles"][r]["pred"] for r in ("A", "B", "C")}:
                    errors.append(f"{seed}:{ld['name']}:prediction_parity")
                graphs = loaded.get("graphs", [])
                if len(graphs) != 2:
                    errors.append(f"{seed}:{ld['name']}:generation_count")
                for g in graphs:
                    if g.get("flow") != ["ADVANCE", "ADVANCE"] or g.get("cursor") != "C" or g.get("old_receipt") != "YIELD":
                        errors.append(f"{seed}:{ld['name']}:graph_flow")
                    if g.get("controls") != EXPECTED_CONTROLS:
                        errors.append(f"{seed}:{ld['name']}:negative_controls")
                    if g.get("fixture_emissions") != 2:
                        errors.append(f"{seed}:{ld['name']}:fixture_emissions")
            result_rows.append({"seed": seed, "accuracy": role_scores,
                                "artifact_sha256": before, "loader_count": len(loaders)})
        except Exception as exc:
            errors.append(f"{seed}:evidence_parse:{type(exc).__name__}:{exc}")
    report = {"schema": "needle-role-skill-robustness-v3-audit-v1",
              "status": "PASS_ROLE_SKILL_ROBUSTNESS_SCOPED" if not errors else "FAIL_OR_STOP_AUDIT",
              "errors": errors, "seeds": result_rows, "error_count": len(errors)}
    (root / "AUDIT.json").write_text(json.dumps(report, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    return report


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--root", required=True)
    p.add_argument("--source", required=True)
    p.add_argument("--freeze", required=True)
    a = p.parse_args()
    out = audit(a.root, a.source, json.loads(Path(a.freeze).read_text(encoding="utf-8")))
    print(json.dumps(out, sort_keys=True, separators=(",", ":")))
    raise SystemExit(0 if not out["errors"] else 1)
