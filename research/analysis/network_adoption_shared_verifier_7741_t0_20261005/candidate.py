"""Finite synthetic adoption/verification queue experiment for Issue #7741."""
import json
import random
import sys

TICKS = 160
N = 24
SERVICE = 3
SEEDS = (11, 29, 47, 83)
IMITATIONS = (0.0, 0.08, 0.2)
CAPACITIES = (1, 3, 24)


def neighbors(topology, i):
    if topology == "ring":
        return ((i - 1) % N, (i + 1) % N)
    if i == 0:
        return tuple(range(1, N))
    return (0,)


def simulate(topology, seed, imitation, capacity, mode):
    salt = sum(map(ord, topology + mode)) + round(imitation * 1000) + capacity * 17
    rng = random.Random(seed * 100003 + salt)
    adopted = [False] * N
    adopted[0] = True
    pending_feedback = [False] * N
    queue = []
    busy = []
    rows = []
    rid = 0
    task_p = 0.12 if mode == "baseline_frozen" else 0.22
    task_cost = 10 if mode == "baseline_frozen" else 6
    if mode in ("reduced_frozen", "baseline_frozen"):
        adoption_mode = "frozen"
    elif mode == "reduced_exogenous":
        adoption_mode = "exogenous"
    else:
        adoption_mode = "peer"
    effective_imitation = 0.0 if mode == "reduced_no_imitation" else imitation
    servers = 24 if mode == "reduced_nonbinding" else (3 if mode == "reduced_partitioned" else capacity)
    for tick in range(TICKS):
        if adoption_mode != "frozen":
            for i in range(N):
                if adopted[i]:
                    continue
                innovates = rng.random() < 0.012
                if adoption_mode == "exogenous":
                    influenced = rng.random() < min(1.0, 0.012 + effective_imitation * 0.5)
                else:
                    peers = neighbors(topology, i)
                    verified_share = sum(pending_feedback[j] for j in peers) / len(peers)
                    influenced = rng.random() < effective_imitation * verified_share
                if innovates or influenced:
                    adopted[i] = True
                    rows.append({"type": "adoption", "tick": tick, "principal": i,
                                 "cause": "innovation" if innovates else ("peer_verified" if adoption_mode == "peer" else "exogenous")})
        pending_feedback = [False] * N
        for principal in range(N):
            offered = rng.random() < 0.12
            started = offered and adopted[principal] and rng.random() < task_p / 0.12
            rows.append({"type": "opportunity", "tick": tick, "principal": principal,
                         "offered": offered, "adopted": adopted[principal], "started": started})
            if started:
                job = {"id": rid, "principal": principal, "arrival": tick, "cost": task_cost}
                rid += 1
                queue.append(job)
                rows.append({"type": "arrival", **job})
        # Complete jobs whose fixed service interval has elapsed; otherwise start FIFO work.
        still_busy = []
        for job in busy:
            if job["finish"] <= tick:
                latency = tick - job["arrival"]
                pending_feedback[job["principal"]] = True
                rows.append({"type": "completion", "id": job["id"], "tick": tick, "latency": latency})
            else:
                still_busy.append(job)
        busy = still_busy
        while queue and len(busy) < servers:
            job = queue.pop(0)
            job = {**job, "finish": tick + SERVICE}
            busy.append(job)
            rows.append({"type": "service_start", "id": job["id"], "tick": tick})
    for job in queue:
        rows.append({"type": "unfinished", "id": job["id"], "state": "queued"})
    for job in busy:
        rows.append({"type": "unfinished", "id": job["id"], "state": "in_service"})
    return rows


def run():
    out = []
    for topology in ("ring", "star"):
        for seed in SEEDS:
            for imitation in IMITATIONS:
                for capacity in CAPACITIES:
                    for mode in ("baseline_frozen", "reduced_frozen", "reduced_peer", "reduced_exogenous", "reduced_no_imitation", "reduced_partitioned", "reduced_nonbinding"):
                        # irrelevant dimensions are retained so every matched cell is explicit
                        out.extend({"topology": topology, "seed": seed, "imitation": imitation,
                                    "capacity": capacity, "mode": mode, **r}
                                   for r in simulate(topology, seed, imitation, capacity, mode))
    json.dump({"schema": "7741-t0-raw-v1", "rows": out}, sys.stdout, sort_keys=True, separators=(",", ":"))


if __name__ == "__main__":
    run()
