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

ALLOCATION = "needle-role-skill-lifecycle-4916-larger-rung-20260928-04"
BLOCKS = 15
REQUESTS = 1000


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def durable_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    with temporary.open("wb") as stream:
        stream.write((json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode())
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)
    directory_fd = os.open(path.parent, os.O_RDONLY)
    try:
        os.fsync(directory_fd)
    finally:
        os.close(directory_fd)


def schedule_rows(expected: dict) -> list[dict]:
    return [
        {"role": ROLES[i % 3], "index": (i * 37 + 11) % 4096,
         "expected": expected["roles"][ROLES[i % 3]]["pred"][(i * 37 + 11) % 4096]}
        for i in range(REQUESTS)
    ]


def timed_arm(name: str, schedule: list[dict], expected: dict, skill: Path) -> dict:
    init_ns = 0
    if name == "LOAD_ONCE_REUSE":
        started = time.perf_counter_ns()
        artifact, _ = load_artifact(skill)
        models = build_all(artifact)
        init_ns = time.perf_counter_ns() - started
    durations, predictions = [], []
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
    source_hashes = {name: sha(ROOT / name) for name in freeze["sources"]}
    repo = ROOT.parents[2]
    reference_hashes = {name: sha(repo / path) for name, path in freeze["reference_sources"].items()}
    skill = repo / freeze["inputs"]["skill.json"]
    expected_path = repo / freeze["inputs"]["expected.json"]
    input_hashes = {"skill.json": sha(skill), "expected.json": sha(expected_path)}
    if (source_hashes != freeze["sources"] or reference_hashes != freeze["reference_sources_sha256"]
            or input_hashes != freeze["inputs_sha256"]
            or os.environ.get("CONTAINER_IMAGE_ID") != freeze["container"]["image_id"]):
        print("PILOT_STATUS=STOP_IDENTITY_MISMATCH", flush=True)
        return 2
    expected = expected_rows(expected_path)
    schedule = schedule_rows(expected)
    freeze_sha = hashlib.sha256(freeze_bytes).hexdigest()
    raw = {
        "schema": "needle-role-skill-lifecycle-larger-rung-raw-v1",
        "allocation": ALLOCATION,
        "status": "RUNNING",
        "environment": {"image_id": os.environ.get("CONTAINER_IMAGE_ID"), "python": sys.version,
                        "platform": platform.platform(), "machine": platform.machine()},
        "source_hashes": source_hashes,
        "reference_hashes": reference_hashes,
        "input_hashes": input_hashes,
        "freeze_sha256": freeze_sha,
        "started_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "blocks_expected": BLOCKS,
        "requests_per_arm_block": REQUESTS,
        "schedule": schedule,
        "blocks": [],
        "completed_blocks": 0,
    }
    durable_json(raw_path, raw)
    print("PILOT_STAGE=preflight STATUS=PASS", flush=True)
    started = time.perf_counter_ns()
    try:
        for block_index in range(BLOCKS):
            order = (["RELOAD_EACH_REQUEST", "LOAD_ONCE_REUSE"] if block_index % 2 == 0
                     else ["LOAD_ONCE_REUSE", "RELOAD_EACH_REQUEST"])
            arms = {arm: timed_arm(arm, schedule, expected, skill) for arm in order}
            raw["blocks"].append({"index": block_index, "order": order, "arms": arms})
            raw["completed_blocks"] = len(raw["blocks"])
            raw["runner_elapsed_ns"] = time.perf_counter_ns() - started
            durable_json(raw_path, raw)
            print(f"PILOT_BLOCK={block_index + 1}/{BLOCKS} STATUS=CHECKPOINTED", flush=True)
        raw["status"] = "RUN_COMPLETE"
        raw["skill_sha256_after"] = sha(skill)
        raw["expected_sha256_after"] = sha(expected_path)
        raw["runner_elapsed_ns"] = time.perf_counter_ns() - started
        durable_json(raw_path, raw)
        print(f"PILOT_STATUS=RUN_COMPLETE ROWS={BLOCKS * REQUESTS * 2}", flush=True)
        return 0
    except BaseException as error:
        raw["status"] = "STOP_RUNNER_EXCEPTION"
        raw["exception_type"] = type(error).__name__
        raw["exception"] = str(error)
        raw["runner_elapsed_ns"] = time.perf_counter_ns() - started
        durable_json(raw_path, raw)
        print(f"PILOT_STATUS=STOP_EXCEPTION TYPE={type(error).__name__}", flush=True)
        raise


if __name__ == "__main__":
    raise SystemExit(main())
