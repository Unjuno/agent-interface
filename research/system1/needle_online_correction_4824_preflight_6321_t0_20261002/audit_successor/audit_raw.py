"""Independent read-only audit of frozen #6321 data; no candidate imports."""
import copy
import hashlib
import json
import argparse
from pathlib import Path

SEEDS = [2026100201, 2026100202, 2026100203]
COUNTS = {"a_support": 64, "b_arrival": 8, "a_heldout": 128, "b_heldout": 128}
ROLE = {"a_support": "A", "a_heldout": "A", "b_arrival": "B", "b_heldout": "B"}
EXPECTED_INPUT = "dad06f71a4a7acfd4ce110852ce5ee82f5e2ce654e1cf0f1d4401106f2edd188"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def validate(doc):
    errors = []
    if doc.get("schema") != "unjuno.needle4824.label-preflight.v1":
        errors.append("schema")
    groups = doc.get("seeds")
    if not isinstance(groups, list) or [x.get("seed") for x in groups] != SEEDS:
        errors.append("seed_sequence")
        return errors
    for group in groups:
        seed, splits = group["seed"], group.get("splits", {})
        if set(splits) != set(COUNTS):
            errors.append(f"split_names:{seed}")
            continue
        ids, features_by_role = set(), {"A": set(), "B": set()}
        for split, n in COUNTS.items():
            entries = splits[split]
            if not isinstance(entries, list) or len(entries) != n:
                errors.append(f"count:{seed}:{split}")
                continue
            bit_counts = [0, 0]
            role = ROLE[split]
            for row in entries:
                x = row.get("features")
                if row.get("seed") != seed or row.get("role") != role or row.get("split") != split:
                    errors.append(f"binding:{seed}:{split}")
                if not isinstance(x, list) or len(x) != 8 or any(v not in (0, 1) for v in x):
                    errors.append(f"vector:{seed}:{split}")
                    continue
                if row.get("id") in ids:
                    errors.append(f"duplicate_id:{seed}:{split}")
                ids.add(row.get("id"))
                key = tuple(x)
                if key in features_by_role[role]:
                    errors.append(f"feature_overlap:{seed}:{role}")
                features_by_role[role].add(key)
                bit_counts[x[0]] += 1
                target = 0 if role == "A" else x[0]
                if row.get("label") != target:
                    errors.append(f"label:{seed}:{split}:{row.get('id')}")
            if bit_counts != [n // 2, n // 2]:
                errors.append(f"balance:{seed}:{split}")
    return errors


def controls(doc):
    cases = []
    def probe(name, mutate):
        altered = copy.deepcopy(doc)
        mutate(altered)
        cases.append({"name": name, "rejected": bool(validate(altered))})
    probe("invert_A_target", lambda d: d["seeds"][0]["splits"]["a_heldout"][0].update(label=1))
    probe("invert_B_target", lambda d: d["seeds"][0]["splits"]["b_heldout"][0].update(label=1-d["seeds"][0]["splits"]["b_heldout"][0]["label"]))
    probe("drop_row", lambda d: d["seeds"][0]["splits"]["a_support"].pop())
    probe("duplicate_id_and_row", lambda d: d["seeds"][0]["splits"]["b_arrival"].__setitem__(1, d["seeds"][0]["splits"]["b_arrival"][0].copy()))
    probe("wrong_role", lambda d: d["seeds"][0]["splits"]["a_support"][0].update(role="B"))
    probe("feature_label_disagreement", lambda d: d["seeds"][0]["splits"]["b_heldout"][0]["features"].__setitem__(0, 1-d["seeds"][0]["splits"]["b_heldout"][0]["features"][0]))
    probe("wrong_seed", lambda d: d["seeds"][2].update(seed=7))
    return cases


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--freeze", required=True)
    args = parser.parse_args()
    src, dst, freeze_path = Path(args.input), Path(args.output), Path(args.freeze)
    freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
    if freeze.get("status") != "FROZEN_PRE_AUDIT" or freeze.get("audit_source_sha256") != sha(Path(__file__)):
        raise SystemExit("STOP_FROZEN_AUDIT_SOURCE_MISMATCH")
    digest = sha(src)
    if digest != EXPECTED_INPUT or digest != freeze.get("input_sha256"):
        raise SystemExit("STOP_INPUT_HASH_MISMATCH:" + digest)
    raw = json.loads(src.read_text(encoding="utf-8"))
    errors = validate(raw)
    mutations = controls(raw)
    n = sum(len(v) for group in raw.get("seeds", []) for v in group.get("splits", {}).values())
    result = {"allocation": "NEEDLE-ONLINE-CORRECTION-4824-DATA-AUDIT-SUCCESSOR-20261002-01",
              "input_sha256": digest, "input_bytes": src.stat().st_size,
              "auditor_source_sha256": sha(Path(__file__)),
              "freeze_sha256": sha(freeze_path),
              "status": "PASS_DATA_AUDIT_SUCCESSOR_SCOPED" if not errors and all(x["rejected"] for x in mutations) else "HOLD_OR_FAIL",
              "errors": errors, "seed_count": len(raw.get("seeds", [])), "rows": n,
              "mutations": mutations, "candidate_invocations": 0, "auditor_invocations": 1,
              "retries": 0}
    dst.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "errors": errors,
                      "rows": n, "mutations_rejected": sum(x["rejected"] for x in mutations)}))
    if result["status"] != "PASS_DATA_AUDIT_SUCCESSOR_SCOPED":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
