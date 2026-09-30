"""Independent raw-only Stage-0 schedule-contract auditor."""
from __future__ import annotations

import hashlib
import json


EXPECTED_ALLOCATION = "needle-role-router-online-lora-audit-v2-20260928-stage0"
EXPECTED_SCHEMA = "needle-role-router-stage0-fixture-v1"
EXPECTED_SEEDS = (17, 29, 43)
EXPECTED_ARMS = (
    "SHARED_B_ONLY",
    "SHARED_A_REPLAY",
    "ROUTED_SHARED_ADAPTER",
    "ROUTED_SEPARATE_SKILLS",
)


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate_json_key:" + key)
        result[key] = value
    return result


def _canonical(value: object) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")


def _sha(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _expected_base_schedule(seed: int) -> list[int]:
    # Deliberately duplicated rather than imported from fixture_builder.
    result: list[int] = []
    for position in range(400):
        result.append((17 * seed + 37 * position + position // 7) % 256)
    return result


def _expected_arm_schedule(seed: int, arm: str) -> list[list[int]]:
    result: list[list[int]] = []
    for arrival in range(16):
        support_row = (seed + 13 * arrival) % 16
        for update in range(8):
            if arm == "SHARED_A_REPLAY":
                result.append([support_row, (seed + 8 * arrival + update) % 16])
            else:
                result.append([support_row])
    return result


def audit_bytes(raw_bytes: bytes) -> dict[str, object]:
    errors: list[str] = []
    try:
        parsed = json.loads(raw_bytes, object_pairs_hook=_unique_object)
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        return {"accepted": False, "errors": ["parse:" + str(exc)]}

    if not isinstance(parsed, dict):
        return {"accepted": False, "errors": ["root_type"]}
    if raw_bytes != _canonical(parsed) + b"\n":
        errors.append("noncanonical_bytes")
    if parsed.get("schema") != EXPECTED_SCHEMA:
        errors.append("schema")
    if parsed.get("allocation") != EXPECTED_ALLOCATION:
        errors.append("allocation")
    if parsed.get("fixture_seeds") != list(EXPECTED_SEEDS):
        errors.append("seed_denominator")
    if parsed.get("arms") != list(EXPECTED_ARMS):
        errors.append("arm_denominator")
    if type(parsed.get("fit_invocations")) is not int or parsed["fit_invocations"] != 0:
        errors.append("fit_invocations")
    if type(parsed.get("optimizer_updates")) is not int or parsed["optimizer_updates"] != 0:
        errors.append("optimizer_updates")

    runs = parsed.get("runs")
    if not isinstance(runs, list) or len(runs) != len(EXPECTED_SEEDS):
        errors.append("run_denominator")
        runs = []
    observed_seeds: list[object] = []
    audited_arms = 0
    for run in runs:
        if not isinstance(run, dict):
            errors.append("run_type")
            continue
        seed = run.get("seed")
        observed_seeds.append(seed)
        if seed not in EXPECTED_SEEDS:
            errors.append("run_seed")
            continue
        expected_base = _expected_base_schedule(seed)
        actual_base = run.get("base_row_indices")
        if actual_base != expected_base:
            errors.append(f"{seed}:base_row_indices")
        digest_map = run.get("dataset_sha256")
        if not isinstance(digest_map, dict):
            errors.append(f"{seed}:dataset_sha256_type")
        else:
            if set(digest_map) != {"base_row_indices"}:
                errors.append(f"{seed}:dataset_digest_key_set")
            if digest_map.get("base_row_indices") != _sha(_canonical(expected_base)):
                errors.append(f"{seed}:base_row_indices_digest")

        arm_rows = run.get("arms")
        if not isinstance(arm_rows, list) or len(arm_rows) != len(EXPECTED_ARMS):
            errors.append(f"{seed}:arm_denominator")
            continue
        seen_arms: list[object] = []
        for arm_row in arm_rows:
            if not isinstance(arm_row, dict):
                errors.append(f"{seed}:arm_type")
                continue
            arm = arm_row.get("arm")
            seen_arms.append(arm)
            if arm not in EXPECTED_ARMS or arm_row.get("seed") != seed:
                errors.append(f"{seed}:arm_seed_identity")
                continue
            expected_updates = _expected_arm_schedule(seed, arm)
            actual_updates = arm_row.get("batch_row_indices")
            if actual_updates != expected_updates:
                errors.append(f"{seed}:{arm}:batch_row_indices")
            if type(arm_row.get("update_count")) is not int or arm_row.get("update_count") != 128:
                errors.append(f"{seed}:{arm}:update_count")
            if arm_row.get("schedule_sha256") != _sha(_canonical(expected_updates)):
                errors.append(f"{seed}:{arm}:schedule_digest")
            audited_arms += 1
        if seen_arms != list(EXPECTED_ARMS):
            errors.append(f"{seed}:arm_identity_order")
    if observed_seeds != list(EXPECTED_SEEDS):
        errors.append("run_identity_order")
    return {
        "accepted": not errors,
        "errors": errors,
        "seeds": len(observed_seeds),
        "arm_rows": audited_arms,
        "base_schedule_rows": len(EXPECTED_SEEDS) * 400,
        "optimizer_updates": 0,
    }


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        raise SystemExit("usage: raw_auditor.py RAW_FIXTURE.json")
    from pathlib import Path

    outcome = audit_bytes(Path(sys.argv[1]).read_bytes())
    print(json.dumps(outcome, sort_keys=True))
    raise SystemExit(0 if outcome["accepted"] else 2)
