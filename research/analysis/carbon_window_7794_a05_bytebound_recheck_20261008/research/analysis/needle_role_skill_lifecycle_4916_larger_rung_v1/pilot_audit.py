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
ALLOCATION = "needle-role-skill-lifecycle-4916-larger-rung-20260928-01"
ROLES = ("A", "B", "C")
BLOCKS, REQUESTS = 15, 1000


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def f32(x: float) -> float:
    return struct.unpack("!f", struct.pack("!f", x))[0]


def matvec(weights: list, vector: list[float], bias: list[float]) -> list[float]:
    out = []
    for oi, row in enumerate(weights):
        acc = 0.0
        for ii, coefficient in enumerate(row):
            acc = f32(acc + f32(coefficient * vector[ii]))
        out.append(f32(acc + f32(bias[oi])))
    return out


def oracle(tensors: dict, role: str, row: list[float]) -> int:
    if role == "A":
        ew, eb, hw, hb = tensors["enc.0.weight"], tensors["enc.0.bias"], tensors["head.weight"], tensors["head.bias"]
    else:
        ew, eb, hw, hb = tensors["core.enc.0.weight"], tensors["core.enc.0.bias"], tensors["core.head.weight"], tensors["core.head.bias"]
    hidden = [f32(math.tanh(v)) for v in matvec(ew, [f32(v) for v in row], eb)]
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
        rows.append({"role": role, "index": index, "expected": expected["roles"][role]["pred"][index]})
    return rows


def validate(raw: dict, schedule: list[dict], expected: dict, tensors: dict,
             freeze: dict, freeze_sha: str, sources: dict, references: dict, inputs: dict) -> list[str]:
    errors = []
    if raw.get("schema") != "needle-role-skill-lifecycle-larger-rung-raw-v1" or raw.get("allocation") != ALLOCATION:
        errors.append("identity")
    if raw.get("status") != "RUN_COMPLETE" or raw.get("completed_blocks") != BLOCKS or len(raw.get("blocks", [])) != BLOCKS:
        errors.append("completion")
    if raw.get("schedule") != schedule or raw.get("requests_per_arm_block") != REQUESTS:
        errors.append("schedule")
    if raw.get("source_hashes") != sources or raw.get("reference_hashes") != references or raw.get("input_hashes") != inputs:
        errors.append("source_or_input_hashes")
    if raw.get("freeze_sha256") != freeze_sha:
        errors.append("freeze_hash")
    if raw.get("environment", {}).get("image_id") != freeze["container"]["image_id"]:
        errors.append("image")
    if raw.get("skill_sha256_after") != inputs.get("skill.json") or raw.get("expected_sha256_after") != inputs.get("expected.json"):
        errors.append("input_mutated")
    # Reject identity/completeness mutations before the expensive independent
    # 30,000-row recomputation. The unmodified baseline is still fully audited.
    if errors:
        return errors
    for bi, block in enumerate(raw.get("blocks", [])):
        order = ["RELOAD_EACH_REQUEST", "LOAD_ONCE_REUSE"] if bi % 2 == 0 else ["LOAD_ONCE_REUSE", "RELOAD_EACH_REQUEST"]
        if block.get("index") != bi or block.get("order") != order:
            errors.append(f"block_order:{bi}")
            continue
        arms = block.get("arms", {})
        if set(arms) != set(order):
            errors.append(f"arms:{bi}")
            continue
        for name, arm in arms.items():
            preds, durations = arm.get("predictions"), arm.get("request_ns")
            if not isinstance(preds, list) or not isinstance(durations, list) or len(preds) != REQUESTS or len(durations) != REQUESTS:
                errors.append(f"rows:{bi}:{name}")
                continue
            init = arm.get("initialization_ns")
            if name == "RELOAD_EACH_REQUEST" and init != 0:
                errors.append(f"reload_init:{bi}")
            if name == "LOAD_ONCE_REUSE" and (type(init) is not int or init <= 0):
                errors.append(f"reuse_init:{bi}")
            if any(type(t) is not int or t <= 0 for t in durations):
                errors.append(f"durations:{bi}:{name}")
            for ri, prediction in enumerate(preds):
                item = schedule[ri]
                actual = oracle(tensors[item["role"]], item["role"], expected["roles"][item["role"]]["inputs"][item["index"]])
                if type(prediction) is not int or prediction != item["expected"] or prediction != actual:
                    errors.append(f"prediction:{bi}:{name}:{ri}")
                    break
    return errors


def mutation(raw: dict, case: str) -> dict:
    changed = json.loads(json.dumps(raw))
    if case == "prediction":
        changed["blocks"][0]["arms"]["LOAD_ONCE_REUSE"]["predictions"][0] = (changed["blocks"][0]["arms"]["LOAD_ONCE_REUSE"]["predictions"][0] + 1) % 4
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
    freeze_path = ROOT / "FREEZE.json"
    freeze_bytes = freeze_path.read_bytes()
    freeze = json.loads(freeze_bytes)
    repo = ROOT.parents[2]
    sources = {name: sha(ROOT / name) for name in freeze["sources"]}
    references = {name: sha(repo / path) for name, path in freeze["reference_sources"].items()}
    skill = repo / freeze["inputs"]["skill.json"]
    expected_path = repo / freeze["inputs"]["expected.json"]
    inputs = {"skill.json": sha(skill), "expected.json": sha(expected_path)}
    expected = json.loads(expected_path.read_bytes())
    tensors = json.loads(skill.read_bytes())["tensors"]
    schedule = schedule_for(expected)
    raw = json.loads(args.raw.read_bytes())
    freeze_sha = hashlib.sha256(freeze_bytes).hexdigest()
    errors = []
    if sources != freeze["sources"] or references != freeze["reference_sources_sha256"] or inputs != freeze["inputs_sha256"]:
        errors.append("auditor_preflight_hash_mismatch")
    errors += validate(raw, schedule, expected, tensors, freeze, freeze_sha, sources, references, inputs)
    controls = {name: bool(validate(mutation(raw, name), schedule, expected, tensors, freeze, freeze_sha, sources, references, inputs))
                for name in ("prediction", "truncate", "block", "allocation", "source", "schedule", "duration")}
    if not all(controls.values()):
        errors.append("mutation_controls")
    ratios, wins, crossings = [], 0, []
    for block in raw.get("blocks", []):
        arms = block.get("arms", {})
        reload, reuse = arms.get("RELOAD_EACH_REQUEST", {}), arms.get("LOAD_ONCE_REUSE", {})
        if len(reload.get("request_ns", [])) != REQUESTS or len(reuse.get("request_ns", [])) != REQUESTS:
            continue
        base_total = sum(reload["request_ns"])
        reuse_total = reuse.get("initialization_ns", 0) + sum(reuse["request_ns"])
        ratios.append(reuse_total / base_total)
        wins += reuse_total < base_total
        cumulative_base = cumulative_reuse = 0
        crossing = 1001
        for index, (base_ns, reuse_ns) in enumerate(zip(reload["request_ns"], reuse["request_ns"]), 1):
            cumulative_base += base_ns
            cumulative_reuse += reuse_ns
            if reuse.get("initialization_ns", 0) + cumulative_reuse < cumulative_base:
                crossing = index
                break
        crossings.append(crossing)
    median_ratio = statistics.median(ratios) if ratios else None
    median_break_even = statistics.median(crossings) if crossings else None
    passed = not errors and wins >= 12 and median_ratio is not None and median_ratio <= 0.90 and median_break_even is not None and median_break_even <= REQUESTS
    status = "PASS_LIFECYCLE_AMORTIZATION_SCOPED" if passed else ("STOP_AUDIT_INTEGRITY" if errors else "HOLD_LIFECYCLE_GATE_NOT_MET")
    report = {"allocation": ALLOCATION, "status": status, "errors": errors,
              "reconciled_predictions": sum(len(b.get("arms", {}).get(a, {}).get("predictions", [])) for b in raw.get("blocks", []) for a in ("RELOAD_EACH_REQUEST", "LOAD_ONCE_REUSE")),
              "paired_blocks_won": wins, "median_lifetime_ratio": median_ratio, "block_ratios": ratios,
              "median_first_break_even_request": median_break_even, "first_break_even_by_block_censored_1001": crossings,
              "mutation_controls": {"rejected": sum(controls.values()), "total": len(controls), "cases": controls},
              "freeze_sha256": freeze_sha, "raw_sha256": sha(args.raw), "source_hashes": sources,
              "reference_hashes": references, "input_hashes": inputs,
              "scope": "single synthetic seed-3788 package, pure-Python scorer, fifteen paired 1,000-request blocks; no broader performance or product claim",
              "auditor_python": sys.version}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    print(f"AUDIT_STATUS={status} ROWS={report['reconciled_predictions']} WINS={wins}/{BLOCKS} MEDIAN_RATIO={median_ratio} BREAK_EVEN={median_break_even} MUTATIONS={sum(controls.values())}/{len(controls)}", flush=True)
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
