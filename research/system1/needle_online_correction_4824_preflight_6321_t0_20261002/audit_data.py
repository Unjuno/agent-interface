"""Independent target/split audit; deliberately does not import make_data."""
import copy
import json
import sys
from pathlib import Path

EXPECTED_SEEDS = [2026100201, 2026100202, 2026100203]
EXPECTED_COUNTS = {"a_support": 64, "b_arrival": 8, "a_heldout": 128, "b_heldout": 128}
SPLIT_ROLE = {"a_support": "A", "a_heldout": "A", "b_arrival": "B", "b_heldout": "B"}


def inspect(data):
    errors = []
    if data.get("schema") != "unjuno.needle4824.label-preflight.v1":
        errors.append("schema")
    seeds = data.get("seeds")
    if not isinstance(seeds, list) or [s.get("seed") for s in seeds] != EXPECTED_SEEDS:
        errors.append("seed_inventory")
        return errors
    for block in seeds:
        seed = block["seed"]
        splits = block.get("splits")
        if not isinstance(splits, dict) or set(splits) != set(EXPECTED_COUNTS):
            errors.append(f"split_inventory:{seed}")
            continue
        seen_ids = set()
        seen_features = {"A": set(), "B": set()}
        for split, role in SPLIT_ROLE.items():
            rows = splits[split]
            if not isinstance(rows, list) or len(rows) != EXPECTED_COUNTS[split]:
                errors.append(f"row_count:{seed}:{split}")
                continue
            bit_counts = [0, 0]
            for row in rows:
                vector = row.get("features")
                if row.get("seed") != seed or row.get("role") != role or row.get("split") != split:
                    errors.append(f"lineage:{seed}:{split}")
                if not isinstance(vector, list) or len(vector) != 8 or any(v not in (0, 1) for v in vector):
                    errors.append(f"feature_shape:{seed}:{split}")
                    continue
                sid = row.get("id")
                if sid in seen_ids:
                    errors.append(f"duplicate_id:{seed}:{sid}")
                seen_ids.add(sid)
                tup = tuple(vector)
                if tup in seen_features[role]:
                    errors.append(f"duplicate_feature:{seed}:{role}:{tup}")
                seen_features[role].add(tup)
                bit_counts[vector[0]] += 1
                expected = 0 if role == "A" else int(vector[0] == 1)
                if row.get("label") != expected:
                    errors.append(f"target_mismatch:{seed}:{split}:{sid}")
            if bit_counts != [EXPECTED_COUNTS[split] // 2] * 2:
                errors.append(f"bit_balance:{seed}:{split}")
    return errors


def mutations(data):
    cases = []
    def changed(name, edit):
        sample = copy.deepcopy(data)
        edit(sample)
        cases.append({"case": name, "rejected": bool(inspect(sample))})
    changed("invert_A_using_B_rule", lambda d: d["seeds"][0]["splits"]["a_heldout"][0].update(label=1))
    changed("invert_B_label", lambda d: d["seeds"][0]["splits"]["b_heldout"][0].update(label=1-d["seeds"][0]["splits"]["b_heldout"][0]["label"]))
    changed("delete_row", lambda d: d["seeds"][0]["splits"]["b_arrival"].pop())
    changed("duplicate_row", lambda d: d["seeds"][0]["splits"]["a_support"].__setitem__(1, d["seeds"][0]["splits"]["a_support"][0].copy()))
    changed("wrong_split", lambda d: d["seeds"][0]["splits"]["a_support"][0].update(split="b_arrival"))
    changed("alter_feature", lambda d: d["seeds"][0]["splits"]["b_heldout"][0]["features"].__setitem__(0, 1-d["seeds"][0]["splits"]["b_heldout"][0]["features"][0]))
    changed("substitute_seed", lambda d: d["seeds"][1].update(seed=2026100999))
    return cases


if __name__ == "__main__":
    raw = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    result = {"status": "PASS_LABEL_PREFLIGHT_SCOPED" if not inspect(raw) else "FAIL_LABEL_PREFLIGHT",
              "errors": inspect(raw), "seed_count": len(raw.get("seeds", [])),
              "row_count": sum(len(rows) for seed in raw.get("seeds", []) for rows in seed.get("splits", {}).values()),
              "mutations": mutations(raw)}
    Path(sys.argv[2]).write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "errors": result["errors"], "mutations_rejected": sum(m["rejected"] for m in result["mutations"])}))
    if result["errors"] or not all(m["rejected"] for m in result["mutations"]):
        raise SystemExit(1)
