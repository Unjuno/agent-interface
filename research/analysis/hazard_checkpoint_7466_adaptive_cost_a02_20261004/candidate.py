#!/usr/bin/env python3
"""One-shot candidate driver; hidden events remain inside the simulator harness."""
import json
import math
import os
import subprocess
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "formal_01" / "candidate.json"
STDOUT = ROOT / "formal_01" / "candidate.stdout.json"


def readj(name):
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


def digest(path):
    import hashlib
    return hashlib.sha256(path.read_bytes()).hexdigest()


def jwrite(path, value):
    path.write_text(json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")


def run_baseline(case, labels, cp_cost, replay_cost, kind, fixed_interval, event_interval):
    durable = progress = 0
    next_event = event_interval
    cp_count = lost = wall = 0
    for t, y in enumerate(labels):
        if progress >= case["task_units"]:
            break
        legal = bool(case["legal"][t])
        if kind == "fixed":
            take = legal and progress - durable >= fixed_interval
        else:
            take = legal and progress >= next_event
        if take:
            durable = progress
            cp_count += 1
            if kind == "event":
                next_event = ((progress // event_interval) + 1) * event_interval
        progress += 1
        wall = t + 1
        if y and progress < case["task_units"]:
            lost += (progress - durable) * replay_cost
            progress = durable
    if progress >= case["task_units"]:
        # Final independent verification makes the final state durable.
        durable = progress
    total = lost + cp_count * cp_cost
    return {"completed": progress >= case["task_units"], "final_effects": progress if progress >= case["task_units"] else durable,
            "expected_effects": case["task_units"], "checkpoint_count": cp_count, "checkpoint_cost": cp_count * cp_cost,
            "lost_work_cost": lost, "total_cost": total, "wall_ticks": wall}


def main():
    if OUT.exists() or STDOUT.exists():
        raise SystemExit("STOP_OUTPUT_EXISTS")
    train = readj("training.json")
    pub = readj("public.json")
    oracle = readj("oracle.json")
    fit = train["fit"]
    counts = Counter(x["symbol"] for x in fit)
    hits = Counter(x["symbol"] for x in fit if x["interrupted"])
    p = {s: hits[s] / counts[s] for s in sorted(counts)}
    base = sum(x["interrupted"] for x in fit) / len(fit)
    val = train["validation"]
    brier_model = sum((p[x["symbol"]] - x["interrupted"]) ** 2 for x in val) / len(val)
    brier_base = sum((base - x["interrupted"]) ** 2 for x in val) / len(val)
    class_counts = Counter(x["symbol"] for x in val)
    calibration_pass = all(class_counts[s] >= 100 for s in ("HIGH", "LOW")) and brier_model < brier_base
    env = os.environ.copy()
    worker = subprocess.Popen([sys.executable, str(ROOT / "policy.py")], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE, text=True, bufsize=1, env=env)

    def tx(obj):
        worker.stdin.write(json.dumps(obj, sort_keys=True, separators=(",", ":")) + "\n")
        worker.stdin.flush()
        line = worker.stdout.readline()
        if not line:
            raise RuntimeError(worker.stderr.read() or "policy exited without response")
        return json.loads(line)

    ready = tx({"type": "CALIBRATION", "p_by_signal": p, "base_rate": base, "calibration_pass": calibration_pass})
    transcript, episode_results = [], []
    hidden_by_id = {x["episode_id"]: x for x in oracle["episodes"]}
    for case in pub["episodes"]:
        hidden = hidden_by_id[case["episode_id"]]
        for cp_cost in pub["checkpoint_costs"]:
            for replay_cost in pub["replay_costs"]:
                cell = {"episode_id": case["episode_id"], "checkpoint_cost": cp_cost, "replay_cost": replay_cost}
                started = tx({"type": "START", **cell})
                if started.get("type") != "START_ACK":
                    raise RuntimeError("policy did not acknowledge episode start")
                durable = progress = cp_count = lost = 0
                next_event = pub["task_event_interval"]
                decisions, active_at = [], []
                used = 0
                for t, y in enumerate(hidden["interruptions"]):
                    if progress >= case["task_units"]:
                        break
                    tick = {"type": "TICK", "signal": case["signals"][t], "legal": bool(case["legal"][t]),
                            "progress": progress, "age": progress - durable,
                            "next_event": next_event,
                            "checkpoint_cost": cp_cost, "replay_cost": replay_cost}
                    d = tx(tick)
                    if d["checkpoint"]:
                        if not tick["legal"]:
                            raise RuntimeError("policy proposed illegal checkpoint")
                        durable = progress
                        cp_count += 1
                        if progress >= next_event:
                            next_event = ((progress // pub["task_event_interval"]) + 1) * pub["task_event_interval"]
                    progress += 1
                    lost_tick = 0
                    if y and progress < case["task_units"]:
                        lost_tick = (progress - durable) * replay_cost
                        lost += lost_tick
                        progress = durable
                    decisions.append(bool(d["checkpoint"]))
                    active_at.append(bool(d["adaptive_active"]))
                    observed = tx({"type": "FEEDBACK", "signal": tick["signal"], "interrupted": int(y)})
                    transcript.append({"episode_id": case["episode_id"], "checkpoint_cost": cp_cost, "replay_cost": replay_cost,
                                       "tick": t, "input": tick, "decision": d, "observed_interruption": int(y),
                                       "progress_after": progress, "durable_after": durable, "lost_work_cost_tick": lost_tick,
                                       "adaptive_active_after_feedback": observed["adaptive_active"],
                                       "llr_after_feedback": observed["llr"]})
                    used = t + 1
                end = tx({"type": "END"})
                completed = progress >= case["task_units"]
                if completed:
                    durable = progress
                result = {"episode_id": case["episode_id"], "checkpoint_cost": cp_cost, "replay_cost": replay_cost,
                          "completed": completed, "final_effects": progress if completed else durable,
                          "expected_effects": case["task_units"], "checkpoint_count": cp_count,
                          "checkpoint_cost_total": cp_count * cp_cost, "lost_work_cost": lost,
                          "total_cost": cp_count * cp_cost + lost, "wall_ticks": used,
                          "adaptive_active_at_end": end["active"], "observations": end["nobs"],
                          "disabled_by_tick": next((i for i, a in enumerate(active_at, 1) if i > 1 and active_at[i-2] and not a), None),
                          "decision_digest": __import__("hashlib").sha256(bytes(decisions)).hexdigest()}
                adaptive = result
                # Identical oracle realization is replayed by independent fixed/event baselines.
                fixed = run_baseline(case, hidden["interruptions"], cp_cost, replay_cost, "fixed", pub["fixed_interval"], pub["task_event_interval"])
                event = run_baseline(case, hidden["interruptions"], cp_cost, replay_cost, "event", pub["fixed_interval"], pub["task_event_interval"])
                episode_results.append({**adaptive, "cohort": hidden["cohort"], "fixed": fixed, "event": event})
    worker.stdin.write(json.dumps({"type": "QUIT"}, separators=(",", ":")) + "\n")
    worker.stdin.flush()
    worker.stdin.close()
    worker.wait(timeout=10)
    if worker.returncode != 0:
        raise SystemExit(f"policy worker exit {worker.returncode}")
    worker_stdout = worker.stdout.read()
    worker_stderr = worker.stderr.read()
    payload = {"format": "7466-a02-candidate-v1", "main_sha": "41df296f3ce4d03c801c998d38f6e537e64a83ab",
               "public_sha256": digest(ROOT / "public.json"), "training_sha256": digest(ROOT / "training.json"),
               "oracle_sha256": digest(ROOT / "oracle.json"), "policy_sha256": digest(ROOT / "policy.py"),
               "calibration": {"p_by_signal": p, "base_rate": base, "brier_model_validation": brier_model,
                               "brier_base_validation": brier_base, "calibration_pass": calibration_pass,
                               "validation_counts": dict(class_counts)},
               "ready": ready, "episodes": episode_results, "transcript": transcript,
               "worker_exit": worker.returncode, "worker_stdout_tail": worker_stdout[-4000:], "worker_stderr": worker_stderr}
    OUT.parent.mkdir(exist_ok=True)
    jwrite(OUT, payload)
    STDOUT.write_text(json.dumps({"candidate_exit": 0, "episodes": len(episode_results), "ticks": len(transcript),
                                  "calibration_pass": calibration_pass, "policy_worker_exit": worker.returncode,
                                  "candidate_sha256": digest(Path(__file__)), "policy_sha256": digest(ROOT / "policy.py")}, sort_keys=True) + "\n")
    print(f"candidate episodes={len(episode_results)} streamed_ticks={len(transcript)} calibration_pass={calibration_pass}")


if __name__ == "__main__":
    main()
