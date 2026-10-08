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
ALLOCATION = "NEEDLE-ROLE-SKILL-LIFECYCLE-WSLC-5084-T0-20261002-01"
BLOCKS = 15
REQUESTS = 1000


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def atomic_json(path: Path, value: dict) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    data = (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()
    with tmp.open("wb") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(tmp, path)


def identity(freeze: dict, inputs_dir: Path, refs_root: Path) -> tuple[dict, dict, dict]:
    sources = {name: sha(ROOT / name) for name in freeze["sources"]}
    refs = {name: sha(refs_root / rel) for name, rel in freeze["reference_sources"].items()}
    inputs = {name: sha(inputs_dir / name) for name in freeze["inputs"]}
    return sources, refs, inputs


def main() -> int:
    out = Path(os.environ["OUT_DIR"])
    inputs_dir = Path(os.environ["INPUTS_DIR"])
    refs_root = Path(os.environ["REFERENCE_ROOT"])
    freeze_bytes = (ROOT / "FREEZE.json").read_bytes()
    freeze = json.loads(freeze_bytes)
    sources, refs, inputs = identity(freeze, inputs_dir, refs_root)
    env_image = os.environ.get("CONTAINER_IMAGE_ID")
    expected_image = freeze["container"]["image_id"]
    mismatches = []
    if sources != freeze["sources"]:
        mismatches.append("source_hashes")
    if refs != freeze["reference_sources_sha256"]:
        mismatches.append("reference_hashes")
    if inputs != freeze["inputs_sha256"]:
        mismatches.append("input_hashes")
    if env_image != expected_image:
        mismatches.append("image_id")
    if platform.machine() != "x86_64" or not sys.version.startswith("3.12.14 "):
        mismatches.append("platform_or_python")
    if mismatches:
        print("CANDIDATE_STATUS=STOP_IDENTITY_MISMATCH " + ",".join(mismatches), flush=True)
        return 2
    if out.exists() and any(out.iterdir()):
        print("CANDIDATE_STATUS=STOP_OUTPUT_NOT_EMPTY", flush=True)
        return 2
    out.mkdir(parents=True, exist_ok=True)

    sys.path.insert(0, str(refs_root / "needle_role_skill_lifecycle_4916_first_rung_v2"))
    from lifecycle_corrected import ROLES, build_all, build_role, expected_rows, load_artifact, predict

    skill = inputs_dir / "skill.json"
    expected_path = inputs_dir / "expected.json"
    expected = expected_rows(expected_path)
    schedule = []
    for i in range(REQUESTS):
        role = ROLES[i % len(ROLES)]
        index = (i * 37 + 11) % len(expected["roles"][role]["pred"])
        schedule.append({"role": role, "index": index,
                         "expected": expected["roles"][role]["pred"][index]})

    raw = {
        "schema": "needle-role-skill-lifecycle-wslc-t0-raw-v1",
        "allocation": ALLOCATION,
        "status": "RUNNING",
        "environment": {"image_id": env_image, "python": sys.version,
                        "machine": platform.machine(), "platform": platform.platform()},
        "freeze_sha256": hashlib.sha256(freeze_bytes).hexdigest(),
        "source_hashes": sources,
        "reference_hashes": refs,
        "input_hashes": inputs,
        "started_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "schedule": schedule,
        "blocks_expected": BLOCKS,
        "requests_per_arm_block": REQUESTS,
        "completed_blocks": 0,
        "blocks": [],
    }
    raw_path = out / "raw.json"
    atomic_json(raw_path, raw)
    started_all = time.perf_counter_ns()
    try:
        for bi in range(BLOCKS):
            order = (["RELOAD_EACH_REQUEST", "LOAD_ONCE_REUSE"] if bi % 2 == 0
                     else ["LOAD_ONCE_REUSE", "RELOAD_EACH_REQUEST"])
            arms = {}
            for arm_name in order:
                init_ns = 0
                if arm_name == "LOAD_ONCE_REUSE":
                    tick = time.perf_counter_ns()
                    artifact, _ = load_artifact(skill)
                    models = build_all(artifact)
                    init_ns = time.perf_counter_ns() - tick
                predictions, durations = [], []
                for row in schedule:
                    tick = time.perf_counter_ns()
                    if arm_name == "RELOAD_EACH_REQUEST":
                        artifact, _ = load_artifact(skill)
                        model = build_role(artifact, row["role"])
                    else:
                        model = models[row["role"]]
                    prediction = predict(model, expected["roles"][row["role"]]["inputs"][row["index"]])
                    durations.append(time.perf_counter_ns() - tick)
                    predictions.append(prediction)
                arms[arm_name] = {"initialization_ns": init_ns,
                                  "request_ns": durations,
                                  "predictions": predictions}
            raw["blocks"].append({"index": bi, "order": order, "arms": arms})
            raw["completed_blocks"] = bi + 1
            raw["elapsed_ns"] = time.perf_counter_ns() - started_all
            atomic_json(raw_path, raw)
            print(f"CANDIDATE_BLOCK={bi + 1}/{BLOCKS} STATUS=CHECKPOINTED", flush=True)
        raw["status"] = "RUN_COMPLETE"
        raw["skill_sha256_after"] = sha(skill)
        raw["expected_sha256_after"] = sha(expected_path)
        raw["elapsed_ns"] = time.perf_counter_ns() - started_all
        atomic_json(raw_path, raw)
        print(f"CANDIDATE_STATUS=RUN_COMPLETE ROWS={BLOCKS * REQUESTS * 2}", flush=True)
        return 0
    except BaseException as exc:
        raw["status"] = "STOP_RUNNER_EXCEPTION"
        raw["exception_type"] = type(exc).__name__
        raw["exception"] = str(exc)
        raw["elapsed_ns"] = time.perf_counter_ns() - started_all
        atomic_json(raw_path, raw)
        print(f"CANDIDATE_STATUS=STOP_EXCEPTION TYPE={type(exc).__name__}", flush=True)
        raise


if __name__ == "__main__":
    raise SystemExit(main())
