"""Independent raw-only reconstruction for Issue #6410's retained WSLc run."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import platform
import statistics
import struct
import sys
from pathlib import Path


ROLES = ("A", "B", "C")
ALLOCATION = "NEEDLE-ROLE-SKILL-LIFECYCLE-WSLC-6410-AUDIT-20261002-03"
BLOCKS = 15
REQUESTS = 1000
RAW_SHA = "bef4b5fbd98f5743ca597406b83414bb695657aa611d2898063dc370f793cbcf"
OLD_FREEZE_SHA = "e0338a6c72afe8797e911653069d318373269cd5b642d2fab3cbce9cd9529ef9"
SCORER_SHA = "d8a7292430968f388159bb3dd1fb3f4523381d95691b07d99087f49553d4f8e3"
VALIDATOR_SHA = "e45a6b1ec6ad4995533c59d3ae560b9a91e2d31b2d7186c1cae5705f90602b80"
INPUT_SHA = {
    "skill.json": "2e7bff5a2c6ffd35935c5e3c88d08cb686fb736d332c8d5cdb24bb1b67dc873a",
    "expected.json": "5baca462abbcdd561dba4c790775a589f91a0fa15453e2f3e6c3bc74fb1b6f61",
}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def valid_base_commit(value: object) -> bool:
    return (isinstance(value, str) and len(value) == 40
            and all(char in "0123456789abcdef" for char in value))


def f32(value: float) -> float:
    return struct.unpack("!f", struct.pack("!f", value))[0]


def dot_rows(weights: list, vector: list[float], bias: list[float]) -> list[float]:
    result = []
    for row, intercept in zip(weights, bias, strict=True):
        acc = 0.0
        for coefficient, item in zip(row, vector, strict=True):
            acc = f32(acc + f32(coefficient * item))
        result.append(f32(acc + f32(intercept)))
    return result


def reconstruct(tensors_by_role: dict, role: str, row: list[float]) -> int:
    tensors = tensors_by_role[role]
    x = [f32(value) for value in row]
    if role == "A":
        ew, eb = tensors["enc.0.weight"], tensors["enc.0.bias"]
        hw, hb = tensors["head.weight"], tensors["head.bias"]
    else:
        ew, eb = tensors["core.enc.0.weight"], tensors["core.enc.0.bias"]
        hw, hb = tensors["core.head.weight"], tensors["core.head.bias"]
    hidden = [f32(math.tanh(value)) for value in dot_rows(ew, x, eb)]
    scores = dot_rows(hw, hidden, hb)
    if role != "A":
        rank = []
        for k in range(len(tensors["a"][0])):
            acc = 0.0
            for j, activation in enumerate(hidden):
                acc = f32(acc + f32(activation * tensors["a"][j][k]))
            rank.append(acc)
        for c in range(len(scores)):
            delta = 0.0
            for k, value in enumerate(rank):
                delta = f32(delta + f32(value * tensors["b"][k][c]))
            scores[c] = f32(scores[c] + f32(delta / 2.0))
    return max(range(len(scores)), key=scores.__getitem__)


def schedule_for(expected: dict) -> list[dict]:
    rows = []
    for i in range(REQUESTS):
        role = ROLES[i % len(ROLES)]
        index = (37 * i + 11) % 4096
        rows.append({"role": role, "index": index,
                     "expected": expected["roles"][role]["pred"][index]})
    return rows


def validate(raw: dict, *, old_freeze: dict, expected: dict, tensors: dict,
             source_hashes: dict, input_hashes: dict, refs: dict,
             reconstruct_predictions: bool = True) -> list[str]:
    errors: list[str] = []
    if type(raw.get("allocation")) is not str or raw["allocation"] != "NEEDLE-ROLE-SKILL-LIFECYCLE-WSLC-5084-T0-20261002-01":
        errors.append("allocation_identity")
    if raw.get("schema") != "needle-role-skill-lifecycle-wslc-t0-raw-v1":
        errors.append("raw_schema")
    if raw.get("status") != "RUN_COMPLETE" or raw.get("completed_blocks") != BLOCKS or raw.get("blocks_expected") != BLOCKS:
        errors.append("completion_markers")
    if type(raw.get("elapsed_ns")) is not int or raw["elapsed_ns"] <= 0:
        errors.append("elapsed_ns")
    if raw.get("requests_per_arm_block") != REQUESTS:
        errors.append("request_count")
    if raw.get("freeze_sha256") != OLD_FREEZE_SHA:
        errors.append("original_freeze_identity")
    if raw.get("source_hashes") != old_freeze.get("sources") or raw.get("source_hashes") != source_hashes:
        errors.append("candidate_source_identity")
    if raw.get("reference_hashes") != old_freeze.get("reference_sources_sha256") or raw.get("reference_hashes") != refs:
        errors.append("reference_identity")
    if refs != {"corrected_scorer.py": SCORER_SHA, "validator.py": VALIDATOR_SHA}:
        errors.append("reference_hash_mismatch")
    if raw.get("input_hashes") != INPUT_SHA or input_hashes != INPUT_SHA:
        errors.append("input_identity")
    if raw.get("skill_sha256_after") != INPUT_SHA["skill.json"] or raw.get("expected_sha256_after") != INPUT_SHA["expected.json"]:
        errors.append("input_mutation")
    env = raw.get("environment")
    if not isinstance(env, dict) or env.get("machine") != "x86_64" or env.get("image_id") != "sha256:9e87977b867847e186d066f531ef783b006d582a985c341c269446088d90f2c4" or not str(env.get("python", "")).startswith("3.12.14 "):
        errors.append("runtime_identity")

    schedule = schedule_for(expected)
    if raw.get("schedule") != schedule:
        errors.append("schedule_identity")
    blocks = raw.get("blocks")
    if not isinstance(blocks, list) or len(blocks) != BLOCKS:
        errors.append("block_count")
        return errors

    if not reconstruct_predictions:
        for bi, block in enumerate(blocks):
            if not isinstance(block, dict):
                errors.append(f"block_type:{bi}")
                continue
            arms = block.get("arms")
            if not isinstance(arms, dict):
                errors.append(f"arm_map:{bi}")
                continue
            for arm_name, arm in arms.items():
                if not isinstance(arm, dict):
                    errors.append(f"arm_type:{bi}:{arm_name}")
                    continue
                times = arm.get("request_ns")
                if not isinstance(times, list) or len(times) != REQUESTS:
                    errors.append(f"duration_length:{bi}:{arm_name}")
                elif any(type(value) is not int or value <= 0 for value in times):
                    errors.append(f"duration_value:{bi}:{arm_name}")
                preds = arm.get("predictions")
                if not isinstance(preds, list) or len(preds) != REQUESTS:
                    errors.append(f"prediction_length:{bi}:{arm_name}")
        return errors

    prediction_errors = []
    for bi, block in enumerate(blocks):
        expected_order = (["RELOAD_EACH_REQUEST", "LOAD_ONCE_REUSE"] if bi % 2 == 0
                          else ["LOAD_ONCE_REUSE", "RELOAD_EACH_REQUEST"])
        if not isinstance(block, dict) or block.get("index") != bi or block.get("order") != expected_order:
            errors.append(f"block_identity:{bi}")
            continue
        arms = block.get("arms")
        if not isinstance(arms, dict) or set(arms) != set(expected_order):
            errors.append(f"arm_set:{bi}")
            continue
        for arm_name in expected_order:
            arm = arms[arm_name]
            if not isinstance(arm, dict):
                errors.append(f"arm_type:{bi}:{arm_name}")
                continue
            preds, durations, init = arm.get("predictions"), arm.get("request_ns"), arm.get("initialization_ns")
            if not isinstance(preds, list) or len(preds) != REQUESTS:
                errors.append(f"prediction_length:{bi}:{arm_name}")
                continue
            if not isinstance(durations, list) or len(durations) != REQUESTS:
                errors.append(f"duration_length:{bi}:{arm_name}")
                continue
            if any(type(value) is not int or value <= 0 for value in durations):
                errors.append(f"duration_value:{bi}:{arm_name}")
            if arm_name == "RELOAD_EACH_REQUEST":
                if type(init) is not int or init != 0:
                    errors.append(f"reload_initialization:{bi}")
            elif type(init) is not int or init <= 0:
                errors.append(f"reuse_initialization:{bi}")
            for ri, observed in enumerate(preds):
                item = schedule[ri]
                oracle = reconstruct(tensors, item["role"], expected["roles"][item["role"]]["inputs"][item["index"]])
                if type(observed) is not int or observed != item["expected"] or observed != oracle:
                    prediction_errors.append(f"prediction:{bi}:{arm_name}:{ri}")
                    break
    return errors + prediction_errors


def mutate(raw: dict, case: str) -> dict:
    changed = copy.deepcopy(raw)
    if case == "prediction":
        changed["blocks"][0]["arms"]["LOAD_ONCE_REUSE"]["predictions"][0] = (changed["blocks"][0]["arms"]["LOAD_ONCE_REUSE"]["predictions"][0] + 1) % 4
    elif case == "truncate":
        changed["blocks"][0]["arms"]["RELOAD_EACH_REQUEST"]["predictions"].pop()
    elif case == "block":
        changed["blocks"].pop()
    elif case == "allocation":
        changed["allocation"] = "tampered"
    elif case == "source":
        changed["source_hashes"].pop(next(iter(changed["source_hashes"])))
    elif case == "schedule":
        changed["schedule"][0]["index"] = (changed["schedule"][0]["index"] + 1) % 4096
    elif case == "duration":
        changed["blocks"][0]["arms"]["LOAD_ONCE_REUSE"]["request_ns"][0] = True
    else:
        raise ValueError("unknown mutation")
    return changed


def adjudicate(args: argparse.Namespace) -> dict:
    freeze = json.loads(args.freeze.read_bytes())
    old_freeze_bytes = args.original_freeze.read_bytes()
    scorer_bytes = args.scorer.read_bytes()
    old_freeze = json.loads(old_freeze_bytes)
    raw_bytes = args.raw.read_bytes()
    raw = json.loads(raw_bytes)
    skill_bytes = args.skill.read_bytes()
    expected_bytes = args.expected.read_bytes()
    skill_obj = json.loads(skill_bytes)
    expected = json.loads(expected_bytes)
    tensors = skill_obj["tensors"]

    input_hashes = {"skill.json": sha(skill_bytes), "expected.json": sha(expected_bytes)}
    legacy_dir = args.legacy_sources
    source_hashes = {name: sha((legacy_dir / name).read_bytes()) for name in old_freeze["sources"]}
    validator_hash = sha(args.validator.read_bytes())
    refs = {"corrected_scorer.py": sha(scorer_bytes), "validator.py": validator_hash}
    own_source_hash = sha(Path(__file__).read_bytes())

    identity_errors = []
    if freeze.get("allocation") != ALLOCATION or freeze.get("issue") != 6410:
        identity_errors.append("audit_freeze_identity")
    if not valid_base_commit(freeze.get("base_commit")):
        identity_errors.append("audit_base_commit")
    if sha(raw_bytes) != RAW_SHA:
        identity_errors.append("raw_sha256")
    if sha(old_freeze_bytes) != OLD_FREEZE_SHA:
        identity_errors.append("original_freeze_sha256")
    if refs["corrected_scorer.py"] != SCORER_SHA:
        identity_errors.append("scorer_sha256")
    if refs["validator.py"] != VALIDATOR_SHA:
        identity_errors.append("validator_sha256")
    if input_hashes != INPUT_SHA:
        identity_errors.append("input_sha256")
    if source_hashes != old_freeze.get("sources"):
        identity_errors.append("original_source_sha256")
    if own_source_hash != freeze.get("audit_source_sha256"):
        identity_errors.append("audit_source_sha256")

    errors = identity_errors + validate(raw, old_freeze=old_freeze, expected=expected,
                                        tensors=tensors, source_hashes=source_hashes,
                                        input_hashes=input_hashes, refs=refs)
    controls = {}
    for case in ("prediction", "truncate", "block", "allocation", "source", "schedule", "duration"):
        controls[case] = bool(validate(mutate(raw, case), old_freeze=old_freeze,
                                       expected=expected, tensors=tensors,
                                       source_hashes=source_hashes,
                                       input_hashes=input_hashes, refs=refs,
                                       reconstruct_predictions=(case == "prediction")))
    if not all(controls.values()):
        errors.append("mutation_control_acceptance")

    ratios, crossings, wins = [], [], 0
    for block in raw.get("blocks", []):
        arms = block.get("arms", {})
        reload = arms.get("RELOAD_EACH_REQUEST", {})
        reuse = arms.get("LOAD_ONCE_REUSE", {})
        r_times, u_times = reload.get("request_ns", []), reuse.get("request_ns", [])
        if len(r_times) != REQUESTS or len(u_times) != REQUESTS:
            continue
        r_total = sum(r_times)
        u_init = reuse.get("initialization_ns", 0)
        u_total = u_init + sum(u_times)
        ratios.append(u_total / r_total)
        wins += int(u_total < r_total)
        r_cum = u_cum = 0
        crossing = REQUESTS + 1
        for i, (r_ns, u_ns) in enumerate(zip(r_times, u_times, strict=True), start=1):
            r_cum += r_ns
            u_cum += u_ns
            if u_init + u_cum < r_cum:
                crossing = i
                break
        crossings.append(crossing)

    median_ratio = statistics.median(ratios) if len(ratios) == BLOCKS else None
    median_crossing = statistics.median(crossings) if len(crossings) == BLOCKS else None
    prediction_failure = any(error.startswith("prediction:") for error in errors)
    integrity_errors = [error for error in errors if not error.startswith("prediction:")]
    gates_met = (wins >= 12 and median_ratio is not None and median_ratio <= 0.90
                 and median_crossing is not None and median_crossing <= REQUESTS)
    status = ("STOP_AUDIT_INTEGRITY" if integrity_errors else
              "FAIL_PREDICTION_MISMATCH" if prediction_failure else
              "PASS_AUDIT_SUCCESSOR_SCOPED" if gates_met else
              "HOLD_LIFECYCLE_GATE_NOT_MET")
    return {
        "issue": 6410,
        "allocation": ALLOCATION,
        "status": status,
        "errors": errors,
        "identity": {
            "raw_sha256": sha(raw_bytes),
            "original_freeze_sha256": sha(old_freeze_bytes),
            "scorer_sha256": refs["corrected_scorer.py"],
            "validator_sha256": refs["validator.py"],
            "candidate_source_hashes": source_hashes,
            "input_hashes": input_hashes,
            "audit_source_sha256": own_source_hash,
            "audit_freeze_sha256": sha(args.freeze.read_bytes()),
        },
        "reconstructed_prediction_count": sum(len(block.get("arms", {}).get(arm, {}).get("predictions", []))
                                                   for block in raw.get("blocks", [])
                                                   for arm in ("RELOAD_EACH_REQUEST", "LOAD_ONCE_REUSE")),
        "blocks": len(raw.get("blocks", [])),
        "reuse_wins": wins,
        "median_lifetime_cost_ratio": median_ratio,
        "block_lifetime_cost_ratios": ratios,
        "median_first_break_even_request": median_crossing,
        "first_break_even_censored_at_1001": crossings,
        "mutation_controls": {"rejected": sum(controls.values()), "total": len(controls), "cases": controls},
        "audit_runtime": {"python": sys.version, "platform": platform.platform()},
        "scope": "Read-only adjudication of one retained synthetic seed-3788 WSLc/CPython 3.12.14 run; candidate=0, retries=0; no timing rerun, training, GPU, cross-runtime or product claim.",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--freeze", type=Path, required=True)
    parser.add_argument("--raw", type=Path, required=True)
    parser.add_argument("--skill", type=Path, required=True)
    parser.add_argument("--expected", type=Path, required=True)
    parser.add_argument("--original-freeze", type=Path, required=True)
    parser.add_argument("--scorer", type=Path, required=True)
    parser.add_argument("--legacy-sources", type=Path, required=True)
    parser.add_argument("--validator", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    report = adjudicate(args)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    print("AUDIT_STATUS={status} PREDICTIONS={reconstructed_prediction_count} WINS={reuse_wins}/15 MEDIAN_RATIO={median_lifetime_cost_ratio} BREAK_EVEN={median_first_break_even_request} MUTATIONS={rejected}/{total}".format(
        status=report["status"], reconstructed_prediction_count=report["reconstructed_prediction_count"],
        reuse_wins=report["reuse_wins"], median_lifetime_cost_ratio=report["median_lifetime_cost_ratio"],
        median_first_break_even_request=report["median_first_break_even_request"],
        rejected=report["mutation_controls"]["rejected"], total=report["mutation_controls"]["total"]), flush=True)
    return 0 if report["status"] == "PASS_AUDIT_SUCCESSOR_SCOPED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
