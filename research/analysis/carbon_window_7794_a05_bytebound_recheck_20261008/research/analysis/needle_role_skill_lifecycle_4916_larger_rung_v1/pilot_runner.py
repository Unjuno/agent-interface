from __future__ import annotations

import datetime
import hashlib
import json
import os
import platform
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from lifecycle_corrected import ROLES, build_all, build_role, expected_rows, load_artifact, predict  # noqa: E402

ALLOCATION = "needle-role-skill-lifecycle-4916-larger-rung-20260928-01"
BLOCKS = 15
REQUESTS = 1000


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def durable_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + ".tmp")
    with temp.open("wb") as stream:
        stream.write((json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode())
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temp, path)
    fd = os.open(path.parent, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def make_schedule(expected: dict) -> list[dict]:
    result = []
    for i in range(REQUESTS):
        role = ROLES[i % 3]
        index = (i * 37 + 11) % 4096
        result.append({"role": role, "index": index,
                       "expected": expected["roles"][role]["pred"][index]})
    return result


def run_arm(name: str, schedule: list[dict], expected: dict, skill: Path) -> dict:
    init_ns = 0
    if name == "LOAD_ONCE_REUSE":
        started = time.perf_counter_ns()
        artifact, _ = load_artifact(skill)
        models = build_all(artifact)
        init_ns = time.perf_counter_ns() - started
    predictions, durations = [], []
    for item in schedule:
        started = time.perf_counter_ns()
        if name == "RELOAD_EACH_REQUEST":
            artifact, _ = load_artifact(skill)
            model = build_role(artifact, item["role"])
        else:
            model = models[item["role"]]
        predictions.append(predict(model, expected["roles"][item["role"]]["inputs"][item["index"]]))
        durations.append(time.perf_counter_ns() - started)
    return {"initialization_ns": init_ns, "request_ns": durations, "predictions": predictions}


def main() -> int:
    out = Path(os.environ["OUT_DIR"])
    raw_path = out / "raw.json"
    freeze_path = ROOT / "FREEZE.json"
    freeze_bytes = freeze_path.read_bytes()
    freeze = json.loads(freeze_bytes)
    sources = {name: sha(ROOT / name) for name in freeze["sources"]}
    references = {name: sha(ROOT.parents[2] / path) for name, path in freeze["reference_sources"].items()}
    skill = ROOT.parents[2] / freeze["inputs"]["skill.json"]
    expected_path = ROOT.parents[2] / freeze["inputs"]["expected.json"]
    inputs = {"skill.json": sha(skill), "expected.json": sha(expected_path)}
    if (sources != freeze["sources"] or references != freeze["reference_sources_sha256"]
            or inputs != freeze["inputs_sha256"]
            or os.environ.get("CONTAINER_IMAGE_ID") != freeze["container"]["image_id"]):
        print("PILOT_STATUS=STOP_IDENTITY_MISMATCH", flush=True)
        return 2
    expected = expected_rows(expected_path)
    schedule = make_schedule(expected)
    freeze_sha = hashlib.sha256(freeze_bytes).hexdigest()
    raw = {"schema": "needle-role-skill-lifecycle-larger-rung-raw-v1",
           "allocation": ALLOCATION, "status": "RUNNING",
           "environment": {"image_id": os.environ.get("CONTAINER_IMAGE_ID"), "python": sys.version,
                           "platform": platform.platform(), "machine": platform.machine()},
           "source_hashes": sources, "reference_hashes": references, "input_hashes": inputs,
           "freeze_sha256": freeze_sha, "started_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
           "blocks_expected": BLOCKS, "requests_per_arm_block": REQUESTS,
           "schedule": schedule, "blocks": [], "completed_blocks": 0}
    durable_json(raw_path, raw)
    print("PILOT_STAGE=preflight STATUS=PASS", flush=True)
    started_all = time.perf_counter_ns()
    try:
        for bi in range(BLOCKS):
            order = (["RELOAD_EACH_REQUEST", "LOAD_ONCE_REUSE"] if bi % 2 == 0
                     else ["LOAD_ONCE_REUSE", "RELOAD_EACH_REQUEST"])
            arms = {name: run_arm(name, schedule, expected, skill) for name in order}
            raw["blocks"].append({"index": bi, "order": order, "arms": arms})
            raw["completed_blocks"] = bi + 1
            raw["elapsed_ns"] = time.perf_counter_ns() - started_all
            durable_json(raw_path, raw)
            print(f"PILOT_BLOCK={bi + 1}/{BLOCKS} STATUS=CHECKPOINTED", flush=True)
        raw["status"] = "RUN_COMPLETE"
        raw["skill_sha256_after"] = sha(skill)
        raw["expected_sha256_after"] = sha(expected_path)
        raw["elapsed_ns"] = time.perf_counter_ns() - started_all
        durable_json(raw_path, raw)
        print(f"PILOT_STATUS=RUN_COMPLETE ROWS={BLOCKS * REQUESTS * 2}", flush=True)
        return 0
    except BaseException as error:
        raw["status"] = "STOP_RUNNER_EXCEPTION"
        raw["exception_type"] = type(error).__name__
        raw["exception"] = str(error)
        raw["elapsed_ns"] = time.perf_counter_ns() - started_all
        durable_json(raw_path, raw)
        print(f"PILOT_STATUS=STOP_EXCEPTION TYPE={type(error).__name__}", flush=True)
        raise


if __name__ == "__main__":
    raise SystemExit(main())
