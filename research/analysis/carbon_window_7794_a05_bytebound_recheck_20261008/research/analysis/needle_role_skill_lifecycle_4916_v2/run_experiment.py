"""Frozen paired reload-versus-reuse lifecycle experiment."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import sys
import time
import datetime
from pathlib import Path

from lifecycle import ROLES, build_all, build_role, expected_rows, load_artifact, predict

ALLOCATION = "needle-role-skill-lifecycle-4916-v2-20260928-01"
BLOCKS = 15
REQUESTS = 1000


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def schedule(expected: dict) -> list[dict]:
    rows = []
    for i in range(REQUESTS):
        role = ROLES[i % len(ROLES)]
        index = (i * 37 + 11) % 4096
        record = expected["roles"][role]
        rows.append({"role": role, "index": index, "input": record["inputs"][index], "expected": record["pred"][index]})
    return rows


def run_arm(arm: str, requests: list[dict], skill_path: Path) -> dict:
    initialization_ns = 0
    if arm == "LOAD_ONCE_REUSE":
        before = time.perf_counter_ns()
        artifact, _ = load_artifact(skill_path)
        models = build_all(artifact)
        initialization_ns = time.perf_counter_ns() - before
    durations = []
    predictions = []
    for request in requests:
        before = time.perf_counter_ns()
        if arm == "RELOAD_EACH_REQUEST":
            artifact, _ = load_artifact(skill_path)
            model = build_role(artifact, request["role"])
        else:
            model = models[request["role"]]
        predictions.append(predict(model, request["input"]))
        durations.append(time.perf_counter_ns() - before)
    return {"initialization_ns": initialization_ns, "request_ns": durations, "predictions": predictions}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skill", required=True, type=Path)
    parser.add_argument("--expected", required=True, type=Path)
    parser.add_argument("--freeze", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    started = time.perf_counter_ns()
    skill_sha = sha256(args.skill)
    expected_sha = sha256(args.expected)
    freeze_bytes = args.freeze.read_bytes()
    freeze = json.loads(freeze_bytes)
    source_hashes = {name: sha256(args.freeze.parent / name) for name in freeze["sources"]}
    if source_hashes != freeze["sources"]:
        raise SystemExit("STOP_SOURCE_HASH_MISMATCH")
    if skill_sha != freeze["inputs"]["skill_sha256"] or expected_sha != freeze["inputs"]["expected_sha256"]:
        raise SystemExit("STOP_INPUT_HASH_MISMATCH")
    expected = expected_rows(args.expected)
    requests = schedule(expected)
    blocks = []
    raw = {
        "schema": "needle-role-skill-lifecycle-raw-v1",
        "allocation": ALLOCATION,
        "status": "RUNNING",
        "environment": {"python": sys.version, "platform": platform.platform(), "machine": platform.machine()},
        "started_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "source_hashes": source_hashes,
        "freeze_sha256": hashlib.sha256(freeze_bytes).hexdigest(),
        "skill_sha256": skill_sha,
        "skill_size": args.skill.stat().st_size,
        "expected_sha256": expected_sha,
        "requests_per_arm_block": REQUESTS,
        "schedule": [{"role": item["role"], "index": item["index"], "expected": item["expected"]} for item in requests],
        "blocks": blocks,
        "completed_blocks": 0,
        "argv": sys.argv,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(raw, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    for index in range(BLOCKS):
        order = ["RELOAD_EACH_REQUEST", "LOAD_ONCE_REUSE"] if index % 2 == 0 else ["LOAD_ONCE_REUSE", "RELOAD_EACH_REQUEST"]
        arms = {}
        for arm in order:
            arms[arm] = run_arm(arm, requests, args.skill)
        blocks.append({"index": index, "order": order, "arms": arms})
        raw["completed_blocks"] = len(blocks)
        raw["runner_elapsed_ns"] = time.perf_counter_ns() - started
        args.out.write_text(json.dumps(raw, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    raw["status"] = "RUN_COMPLETE"
    raw["skill_sha256_after"] = sha256(args.skill)
    raw["expected_sha256_after"] = sha256(args.expected)
    raw["runner_elapsed_ns"] = time.perf_counter_ns() - started
    args.out.write_text(json.dumps(raw, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    print(f"FORMAL_ROWS={BLOCKS * REQUESTS * 2} BLOCKS={BLOCKS} ALLOCATION={ALLOCATION}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
