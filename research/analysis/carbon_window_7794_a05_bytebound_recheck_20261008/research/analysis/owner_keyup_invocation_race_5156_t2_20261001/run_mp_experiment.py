from __future__ import annotations

import argparse
import hashlib
import json
import multiprocessing as mp
import os
import platform
import sys
import time
from datetime import datetime, timezone
from pathlib import Path


TRIALS_PER_ARM = 20
WORKER_COUNT = 2
SCHEMA = "issue5156_multiprocess_exclusive_claim_t2_v1"


def _worker(mode: str, directory_text: str, barrier, output_queue) -> None:
    directory = Path(directory_text)
    claim = directory / "CLAIM"
    # Both independent processes must observe the same pre-claim state before
    # either is permitted to dispatch.
    precheck_clear = not claim.exists()
    barrier.wait(timeout=20)
    if not precheck_clear:
        output_queue.put({"status": 2, "candidate": False, "reason": "precheck_not_clear"})
        return
    if mode == "exclusive":
        try:
            fd = os.open(str(claim), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        except FileExistsError:
            output_queue.put({"status": 2, "candidate": False, "reason": "claim_contended"})
            return
        else:
            os.close(fd)
    elif mode != "baseline":
        output_queue.put({"status": 3, "candidate": False, "reason": "unknown_mode"})
        return
    receipt = directory / f"candidate-{os.getpid()}"
    with receipt.open("x", encoding="ascii", newline="\n") as stream:
        stream.write("INERT_CANDIDATE\n")
        stream.flush()
        os.fsync(stream.fileno())
    output_queue.put({"status": 0, "candidate": True, "receipt": receipt.name})


def _run_trial(root: Path, mode: str, trial_index: int) -> dict:
    root.mkdir(parents=True, exist_ok=True)
    trial = root / f"{mode}-{trial_index:02d}"
    trial.mkdir()
    ctx = mp.get_context("spawn")
    barrier = ctx.Barrier(WORKER_COUNT)
    queue = ctx.Queue()
    processes = [ctx.Process(target=_worker, args=(mode, str(trial), barrier, queue))
                 for _ in range(WORKER_COUNT)]
    for process in processes:
        process.start()
    deadline = time.monotonic() + 45
    for process in processes:
        process.join(max(0, deadline - time.monotonic()))
    alive = [process.pid for process in processes if process.is_alive()]
    for process in processes:
        if process.is_alive():
            process.terminate()
            process.join(5)
    if alive:
        raise TimeoutError(f"worker timeout: {alive}")
    outcomes = [queue.get(timeout=5) for _ in processes]
    statuses = sorted(row["status"] for row in outcomes)
    receipts = sorted(path.name for path in trial.glob("candidate-*"))
    return {
        "mode": mode,
        "trial": trial_index,
        "worker_exitcodes": [p.exitcode for p in processes],
        "statuses": statuses,
        "candidate_count": len(receipts),
        "candidate_receipts": receipts,
        "claim_exists": (trial / "CLAIM").is_file(),
        "outcomes": sorted(outcomes, key=lambda row: row["status"]),
    }


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit("refusing to overwrite raw output; no retry")
    root = args.output.parent / "trials"
    rows = []
    for mode in ("baseline", "exclusive"):
        for index in range(TRIALS_PER_ARM):
            rows.append(_run_trial(root, mode, index))
    here = Path(__file__).resolve().parent
    raw = {
        "schema": SCHEMA,
        "allocation": "ISSUE-5156-MULTIPROCESS-CLAIM-T2-20261001-01",
        "hypothesis": "O_CREAT|O_EXCL on a shared local NTFS allocation path admits one of two independent spawned processes after a synchronized clear precheck, where the unclaimed check admits both.",
        "executed_at_utc": datetime.now(timezone.utc).isoformat(),
        "environment": {
            "os": platform.platform(),
            "python": sys.version,
            "filesystem_claim": "local workspace volume; verify mount/filesystem separately",
            "process_start_method": "spawn",
        },
        "design": {"workers_per_trial": WORKER_COUNT, "trials_per_arm": TRIALS_PER_ARM,
                   "arms": ["baseline", "exclusive"], "candidate_effects": "inert unique receipt only"},
        "source_sha256": {
            name: _sha(here / name)
            for name in ("PLAN.md", "test_mp_race.py", "run_mp_experiment.py", "audit_mp_experiment.py")
        },
        "docker_invocations": 0,
        "x11_input_invocations": 0,
        "model_calls": 0,
        "rows": rows,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(raw, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"rows": len(rows), "raw": str(args.output)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
