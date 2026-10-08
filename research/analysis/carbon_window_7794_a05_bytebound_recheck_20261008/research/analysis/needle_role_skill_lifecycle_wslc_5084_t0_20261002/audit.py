from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import platform
import statistics
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ALLOCATION = "NEEDLE-ROLE-SKILL-LIFECYCLE-WSLC-5084-T0-20261002-01"
ROLES = ("A", "B", "C")
BLOCKS, REQUESTS = 15, 1000


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def f32(value: float) -> float:
    return struct.unpack("!f", struct.pack("!f", value))[0]


def matvec(weights: list, vector: list[float], bias: list[float]) -> list[float]:
    result = []
    for row, intercept in zip(weights, bias):
        acc = 0.0
        for coefficient, item in zip(row, vector):
            acc = f32(acc + f32(coefficient * item))
        result.append(f32(acc + f32(intercept)))
    return result


def oracle(tensors: dict, role: str, row: list[float]) -> int:
    if role == "A":
        ew, eb = tensors["enc.0.weight"], tensors["enc.0.bias"]
        hw, hb = tensors["head.weight"], tensors["head.bias"]
    else:
        ew, eb = tensors["core.enc.0.weight"], tensors["core.enc.0.bias"]
        hw, hb = tensors["core.head.weight"], tensors["core.head.bias"]
    hidden = [f32(math.tanh(value)) for value in
              matvec(ew, [f32(value) for value in row], eb)]
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


def schedule_for(expected: dict) -> list[dict]:
    rows = []
    for i in range(REQUESTS):
        role = ROLES[i % 3]
        index = (i * 37 + 11) % 4096
        rows.append({"role": role, "index": index,
                     "expected": expected["roles"][role]["pred"][index]})
    return rows


def validate(raw: dict, freeze: dict, freeze_sha: str, sources: dict,
             refs: dict, inputs: dict, schedule: list[dict],
             expected: dict, tensors: dict) -> list[str]:
    errors = []
    if raw.get("schema") != "needle-role-skill-lifecycle-wslc-t0-raw-v1":
        errors.append("schema")
    if raw.get("allocation") != ALLOCATION:
        errors.append("allocation")
    if raw.get("status") != "RUN_COMPLETE" or raw.get("completed_blocks") != BLOCKS:
        errors.append("completion")
    if len(raw.get("blocks", [])) != BLOCKS:
        errors.append("block_count")
    if raw.get("schedule") != schedule or raw.get("requests_per_arm_block") != REQUESTS:
        errors.append("schedule")
    if raw.get("freeze_sha256") != freeze_sha:
        errors.append("freeze_hash")
    if raw.get("source_hashes") != sources:
        errors.append("source_hashes")
    if raw.get("reference_hashes") != refs:
        errors.append("reference_hashes")
    if raw.get("input_hashes") != inputs:
        errors.append("input_hashes")
    env = raw.get("environment", {})
    if env.get("image_id") != freeze["container"]["image_id"]:
        errors.append("image_id")
    if not str(env.get("python", "")).startswith("3.12.14 ") or env.get("machine") != "x86_64":
        errors.append("runtime_identity")
    if raw.get("skill_sha256_after") != inputs.get("skill.json"):
        errors.append("skill_mutated")
    if raw.get("expected_sha256_after") != inputs.get("expected.json"):
        errors.append("expected_mutated")
    if errors:
        return errors

    for bi, block in enumerate(raw["blocks"]):
        order = (["RELOAD_EACH_REQUEST", "LOAD_ONCE_REUSE"] if bi % 2 == 0
                 else ["LOAD_ONCE_REUSE", "RELOAD_EACH_REQUEST"])
        if block.get("index") != bi or block.get("order") != order:
            errors.append(f"block_identity:{bi}")
            continue
        arms = block.get("arms", {})
        if set(arms) != set(order):
            errors.append(f"arm_set:{bi}")
            continue
        for arm_name in order:
            arm = arms[arm_name]
            preds = arm.get("predictions")
            times = arm.get("request_ns")
            init = arm.get("initialization_ns")
            if not isinstance(preds, list) or len(preds) != REQUESTS:
                errors.append(f"prediction_count:{bi}:{arm_name}")
                continue
            if not isinstance(times, list) or len(times) != REQUESTS:
                errors.append(f"duration_count:{bi}:{arm_name}")
                continue
            if any(type(t) is not int or t <= 0 for t in times):
                errors.append(f"duration_type:{bi}:{arm_name}")
                continue
            if arm_name == "RELOAD_EACH_REQUEST" and init != 0:
                errors.append(f"reload_init:{bi}")
            if arm_name == "LOAD_ONCE_REUSE" and (type(init) is not int or init <= 0):
                errors.append(f"reuse_init:{bi}")
            for ri, predicted in enumerate(preds):
                item = schedule[ri]
                oracle_prediction = oracle(
                    tensors,
                    item["role"],
                    expected["roles"][item["role"]]["inputs"][item["index"]],
                )
                if type(predicted) is not int or predicted != item["expected"] or predicted != oracle_prediction:
                    errors.append(f"prediction:{bi}:{arm_name}:{ri}")
                    break
    return errors


def mutate(raw: dict, case: str) -> dict:
    changed = json.loads(json.dumps(raw))
    if case == "prediction":
        changed["blocks"][0]["arms"]["LOAD_ONCE_REUSE"]["predictions"][0] = (
            changed["blocks"][0]["arms"]["LOAD_ONCE_REUSE"]["predictions"][0] + 1) % 4
    elif case == "truncate":
        changed["blocks"][0]["arms"]["RELOAD_EACH_REQUEST"]["predictions"].pop()
    elif case == "block":
        changed["blocks"].pop()
    elif case == "allocation":
        changed["allocation"] = "wrong"
    elif case == "source":
        changed["source_hashes"].pop(next(iter(changed["source_hashes"])))
    elif case == "schedule":
        changed["schedule"][0]["index"] += 1
    elif case == "duration":
        changed["blocks"][0]["arms"]["LOAD_ONCE_REUSE"]["request_ns"][0] = True
    return changed


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    inputs_dir = Path(os.environ["INPUTS_DIR"])
    refs_root = Path(os.environ["REFERENCE_ROOT"])
    freeze_bytes = (ROOT / "FREEZE.json").read_bytes()
    freeze = json.loads(freeze_bytes)
    sources = {name: sha(ROOT / name) for name in freeze["sources"]}
    refs = {name: sha(refs_root / rel) for name, rel in freeze["reference_sources"].items()}
    inputs = {name: sha(inputs_dir / name) for name in freeze["inputs"]}
    expected = json.loads((inputs_dir / "expected.json").read_bytes())
    tensors = json.loads((inputs_dir / "skill.json").read_bytes())["tensors"]
    schedule = schedule_for(expected)
    freeze_sha = hashlib.sha256(freeze_bytes).hexdigest()
    raw = json.loads(args.raw.read_bytes())
    errors = []
    if sources != freeze["sources"] or refs != freeze["reference_sources_sha256"] or inputs != freeze["inputs_sha256"]:
        errors.append("auditor_preflight_hash_mismatch")
    errors.extend(validate(raw, freeze, freeze_sha, sources, refs, inputs,
                           schedule, expected, tensors))
    controls = {case: bool(validate(mutate(raw, case), freeze, freeze_sha,
                                    sources, refs, inputs, schedule,
                                    expected, tensors))
                for case in ("prediction", "truncate", "block", "allocation",
                             "source", "schedule", "duration")}
    if not all(controls.values()):
        errors.append("mutation_controls")
    ratios, wins, crossings = [], 0, []
    for block in raw.get("blocks", []):
        arms = block.get("arms", {})
        reload = arms.get("RELOAD_EACH_REQUEST", {})
        reuse = arms.get("LOAD_ONCE_REUSE", {})
        if len(reload.get("request_ns", [])) != REQUESTS or len(reuse.get("request_ns", [])) != REQUESTS:
            continue
        reload_total = sum(reload["request_ns"])
        reuse_total = reuse.get("initialization_ns", 0) + sum(reuse["request_ns"])
        ratios.append(reuse_total / reload_total)
        wins += reuse_total < reload_total
        cum_reload = cum_reuse = 0
        crossing = REQUESTS + 1
        for i, (r_ns, u_ns) in enumerate(zip(reload["request_ns"], reuse["request_ns"]), 1):
            cum_reload += r_ns
            cum_reuse += u_ns
            if reuse.get("initialization_ns", 0) + cum_reuse < cum_reload:
                crossing = i
                break
        crossings.append(crossing)
    median_ratio = statistics.median(ratios) if ratios else None
    median_crossing = statistics.median(crossings) if crossings else None
    passed = (not errors and len(ratios) == BLOCKS and wins >= 12
              and median_ratio is not None and median_ratio <= 0.90
              and median_crossing is not None and median_crossing <= REQUESTS)
    status = "PASS_LIFECYCLE_AMORTIZATION_WSLC_SCOPED" if passed else (
        "STOP_AUDIT_INTEGRITY" if errors else "HOLD_LIFECYCLE_GATE_NOT_MET")
    report = {
        "allocation": ALLOCATION, "status": status, "errors": errors,
        "candidate_blocks": len(raw.get("blocks", [])),
        "reconciled_predictions": sum(len(b.get("arms", {}).get(a, {}).get("predictions", []))
                                        for b in raw.get("blocks", [])
                                        for a in ("RELOAD_EACH_REQUEST", "LOAD_ONCE_REUSE")),
        "paired_blocks_won": wins, "median_lifetime_ratio": median_ratio,
        "block_ratios": ratios, "median_first_break_even_request": median_crossing,
        "first_break_even_censored_at_1001": crossings,
        "mutation_controls": {"rejected": sum(controls.values()),
                              "total": len(controls), "cases": controls},
        "freeze_sha256": freeze_sha, "raw_sha256": sha(args.raw),
        "source_hashes": sources, "reference_hashes": refs, "input_hashes": inputs,
        "scope": "one retained synthetic seed-3788 package, WSLc 3.0.1, CPython 3.12.14, pure-Python scorer, 15 paired 1,000-request blocks; no cross-runtime or product claim",
        "auditor_python": sys.version, "auditor_platform": platform.platform(),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    print(f"AUDIT_STATUS={status} ROWS={report['reconciled_predictions']} WINS={wins}/{BLOCKS} MEDIAN_RATIO={median_ratio} BREAK_EVEN={median_crossing} MUTATIONS={sum(controls.values())}/{len(controls)}", flush=True)
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
