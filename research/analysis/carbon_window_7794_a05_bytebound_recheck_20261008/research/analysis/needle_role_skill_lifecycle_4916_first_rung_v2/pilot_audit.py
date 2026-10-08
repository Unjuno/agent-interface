from __future__ import annotations

import argparse
import hashlib
import json
import math
import statistics
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ROLES = ("A", "B", "C")
BLOCKS = 5
REQUESTS = 40
ALLOCATION = "needle-role-skill-lifecycle-4916-first-rung-20260928-02"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def f32(x: float) -> float:
    return struct.unpack("!f", struct.pack("!f", x))[0]


def matvec(weights: list, vector: list[float], bias: list[float]) -> list[float]:
    result = []
    for oi, row in enumerate(weights):
        acc = 0.0
        for ii, coefficient in enumerate(row):
            acc = f32(acc + f32(coefficient * vector[ii]))
        result.append(f32(acc + f32(bias[oi])))
    return result


def oracle(tensors: dict, role: str, row: list[float]) -> int:
    if role == "A":
        ew, eb = tensors["enc.0.weight"], tensors["enc.0.bias"]
        hw, hb = tensors["head.weight"], tensors["head.bias"]
    else:
        ew, eb = tensors["core.enc.0.weight"], tensors["core.enc.0.bias"]
        hw, hb = tensors["core.head.weight"], tensors["core.head.bias"]
    hidden = [f32(math.tanh(z)) for z in matvec(ew, [f32(z) for z in row], eb)]
    scores = matvec(hw, hidden, hb)
    if role != "A":
        rank = []
        for k in range(2):
            acc = 0.0
            for j in range(16):
                acc = f32(acc + f32(hidden[j] * tensors["a"][j][k]))
            rank.append(acc)
        for c in range(4):
            delta = 0.0
            for k in range(2):
                delta = f32(delta + f32(rank[k] * tensors["b"][k][c]))
            scores[c] = f32(scores[c] + f32(f32(delta / 2.0)))
    return max(range(4), key=scores.__getitem__)


def validate(raw: dict, expected: dict, tensors: dict, freeze: dict,
             freeze_sha: str, source_hashes: dict, reference_hashes: dict,
             input_hashes: dict) -> list[str]:
    errors = []
    if raw.get("schema") != "needle-role-skill-lifecycle-first-rung-raw-v2" or raw.get("allocation") != ALLOCATION:
        errors.append("identity")
    if raw.get("status") != "RUN_COMPLETE" or raw.get("completed_blocks") != BLOCKS or len(raw.get("blocks", [])) != BLOCKS:
        errors.append("completion")
    schedule = [{"role": ROLES[i % 3], "index": (i * 37 + 11) % 4096,
                 "expected": expected["roles"][ROLES[i % 3]]["pred"][(i * 37 + 11) % 4096]}
                for i in range(REQUESTS)]
    if raw.get("schedule") != schedule or raw.get("requests_per_arm_block") != REQUESTS:
        errors.append("schedule")
    if raw.get("source_hashes") != source_hashes or raw.get("reference_hashes") != reference_hashes:
        errors.append("source_hashes")
    if raw.get("input_hashes") != input_hashes or raw.get("freeze_sha256") != freeze_sha:
        errors.append("freeze_or_input_hashes")
    if raw.get("environment", {}).get("image_id") != freeze["container"]["image_id"]:
        errors.append("image_identity")
    if raw.get("skill_sha256_after") != input_hashes.get("skill.json") or raw.get("expected_sha256_after") != input_hashes.get("expected.json"):
        errors.append("post_run_input_identity")
    for bi, block in enumerate(raw.get("blocks", [])):
        order = ["RELOAD_EACH_REQUEST", "LOAD_ONCE_REUSE"] if bi % 2 == 0 else ["LOAD_ONCE_REUSE", "RELOAD_EACH_REQUEST"]
        if block.get("index") != bi or block.get("order") != order:
            errors.append(f"order:{bi}")
            continue
        arms = block.get("arms", {})
        if set(arms) != set(order):
            errors.append(f"arm_set:{bi}")
            continue
        for name, arm in arms.items():
            preds, durations = arm.get("predictions"), arm.get("request_ns")
            if not isinstance(preds, list) or not isinstance(durations, list) or len(preds) != REQUESTS or len(durations) != REQUESTS:
                errors.append(f"row_count:{bi}:{name}")
                continue
            init = arm.get("initialization_ns")
            if name == "RELOAD_EACH_REQUEST" and init != 0:
                errors.append(f"reload_init:{bi}")
            if name == "LOAD_ONCE_REUSE" and (type(init) is not int or init <= 0):
                errors.append(f"reuse_init:{bi}")
            if any(type(value) is not int or value <= 0 for value in durations):
                errors.append(f"duration:{bi}:{name}")
            for ri, value in enumerate(preds):
                item = schedule[ri]
                actual = oracle(tensors[item["role"]], item["role"], expected["roles"][item["role"]]["inputs"][item["index"]])
                if type(value) is not int or value != item["expected"] or value != actual:
                    errors.append(f"prediction:{bi}:{name}:{ri}")
                    break
    return errors


def altered(raw: dict, case: str) -> dict:
    value = json.loads(json.dumps(raw))
    if case == "prediction":
        value["blocks"][0]["arms"]["LOAD_ONCE_REUSE"]["predictions"][0] = (value["blocks"][0]["arms"]["LOAD_ONCE_REUSE"]["predictions"][0] + 1) % 4
    elif case == "truncate":
        value["blocks"][0]["arms"]["RELOAD_EACH_REQUEST"]["predictions"].pop()
    elif case == "block":
        value["blocks"].pop()
    elif case == "allocation":
        value["allocation"] = "wrong"
    elif case == "source":
        value["source_hashes"].pop(next(iter(value["source_hashes"])))
    elif case == "schedule":
        value["schedule"][0]["index"] += 1
    elif case == "duration":
        value["blocks"][0]["arms"]["LOAD_ONCE_REUSE"]["request_ns"][0] = True
    return value


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    freeze_path = ROOT / "FREEZE.json"
    freeze_bytes = freeze_path.read_bytes()
    freeze = json.loads(freeze_bytes)
    repo = ROOT.parents[2]
    source_hashes = {name: sha(ROOT / name) for name in freeze["sources"]}
    reference_hashes = {name: sha(repo / path) for name, path in freeze["reference_sources"].items()}
    skill = repo / freeze["inputs"]["skill.json"]
    expected_path = repo / freeze["inputs"]["expected.json"]
    input_hashes = {"skill.json": sha(skill), "expected.json": sha(expected_path)}
    expected = json.loads(expected_path.read_bytes())
    artifact = json.loads(skill.read_bytes())
    tensors = artifact["tensors"]
    raw = json.loads(args.raw.read_bytes())
    freeze_sha = hashlib.sha256(freeze_bytes).hexdigest()
    errors = []
    if source_hashes != freeze["sources"] or reference_hashes != freeze["reference_sources_sha256"] or input_hashes != freeze["inputs_sha256"]:
        errors.append("auditor_preflight_hash_mismatch")
    errors += validate(raw, expected, tensors, freeze, freeze_sha, source_hashes, reference_hashes, input_hashes)
    mutation_results = {case: bool(validate(altered(raw, case), expected, tensors, freeze, freeze_sha, source_hashes, reference_hashes, input_hashes))
                        for case in ("prediction", "truncate", "block", "allocation", "source", "schedule", "duration")}
    if not all(mutation_results.values()):
        errors.append("mutation_controls")
    ratios, wins = [], 0
    for block in raw.get("blocks", []):
        arms = block.get("arms", {})
        reload = arms.get("RELOAD_EACH_REQUEST", {})
        reuse = arms.get("LOAD_ONCE_REUSE", {})
        if len(reload.get("request_ns", [])) == REQUESTS and len(reuse.get("request_ns", [])) == REQUESTS:
            reload_total = sum(reload["request_ns"])
            reuse_total = reuse.get("initialization_ns", 0) + sum(reuse["request_ns"])
            ratios.append(reuse_total / reload_total)
            wins += reuse_total < reload_total
    median = statistics.median(ratios) if ratios else None
    passed = not errors and wins == BLOCKS and median is not None and median <= 0.90
    report = {
        "allocation": ALLOCATION,
        "status": "PASS_LIFECYCLE_FIRST_RUNG_SCOPED" if passed else ("STOP_AUDIT_INTEGRITY" if errors else "HOLD_FIRST_RUNG_NO_MATERIAL_GAIN"),
        "errors": errors,
        "reconciled_predictions": sum(len(block.get("arms", {}).get(arm, {}).get("predictions", [])) for block in raw.get("blocks", []) for arm in ("RELOAD_EACH_REQUEST", "LOAD_ONCE_REUSE")),
        "paired_blocks_won": wins,
        "median_reuse_to_reload_lifetime_ratio": median,
        "block_ratios": ratios,
        "mutation_controls": {"rejected": sum(mutation_results.values()), "total": len(mutation_results), "cases": mutation_results},
        "freeze_sha256": freeze_sha,
        "raw_sha256": sha(args.raw),
        "source_hashes": source_hashes,
        "reference_hashes": reference_hashes,
        "input_hashes": input_hashes,
        "scope": "single synthetic seed-3788 first-rung pilot; five paired blocks; 40 requests per arm per block; no broader performance or product claim",
        "auditor_python": sys.version,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    print(f"AUDIT_STATUS={report['status']} ROWS={report['reconciled_predictions']} WINS={wins}/{BLOCKS} MUTATIONS={sum(mutation_results.values())}/{len(mutation_results)}", flush=True)
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
