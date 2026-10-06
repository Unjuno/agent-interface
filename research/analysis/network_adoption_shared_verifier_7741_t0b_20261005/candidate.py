"""Deterministic discrete-event candidate for Issue #7741 T0b."""
import hashlib
import json
import sys

TICKS, N, SERVICE = 160, 24, 3
SEEDS, IMITATIONS = (11, 29, 47, 83), (0.08, 0.2)
MODES = ("baseline_frozen_shared_1", "reduced_frozen_shared_1", "reduced_peer_shared_1",
         "reduced_exogenous_shared_1", "reduced_no_imitation_shared_1",
         "reduced_frozen_shared_24", "reduced_peer_shared_24",
         "reduced_frozen_per_principal", "reduced_peer_per_principal")


def draw(*parts):
    b = ":".join(map(str, parts)).encode()
    return int.from_bytes(hashlib.sha256(b).digest()[:8], "big") / 2**64


def neighbors(topology, i):
    return ((i - 1) % N, (i + 1) % N) if topology == "ring" else ((1,) if i == 0 else (0,))


def simulate(topology, seed, imitation, mode):
    adopters = [False] * N
    adopters[0] = True
    feedback = [False] * N
    partitioned = mode.endswith("per_principal")
    queues = [[] for _ in range(N)] if partitioned else [[]]
    busy = [[] for _ in range(N)] if partitioned else [[]]
    shared_servers = 24 if "shared_24" in mode else (1 if mode.endswith("shared_1") else None)
    rows, task_id = [], 0
    frozen = "frozen" in mode or "no_imitation" in mode
    for tick in range(TICKS):
        # Outcomes completed after the preceding tick's adoption phase inform this tick.
        next_feedback = [False] * N
        for i in range(N):
            before = adopters[i]
            inn = draw("innovation", topology, seed, imitation, tick, i)
            imd = draw("imitation", topology, seed, imitation, tick, i)
            peers = neighbors(topology, i)
            verified = sum(feedback[j] for j in peers)
            if not before and not frozen:
                if mode.startswith("reduced_exogenous"):
                    adopted = inn < min(1.0, 0.012 + imitation * 0.5)
                    cause = "exogenous" if adopted else None
                else:
                    innov = inn < 0.012
                    imitate = imd < imitation * verified / len(peers)
                    adopted = innov or imitate
                    cause = "innovation" if innov else ("peer_verified" if imitate else None)
                adopters[i] = adopted
            else:
                cause = None
            rows.append({"type":"adoption","tick":tick,"principal":i,"before":before,
                         "after":adopters[i],"cause":cause,"innovation_draw":inn,
                         "imitation_draw":imd,"verified_peers":verified,"peer_count":len(peers)})
        feedback = next_feedback
        for i in range(N):
            rows.append({"type":"opportunity","tick":tick,"principal":i,"adopted":adopters[i],
                         "route_draw":draw("route",topology,seed,tick,i),
                         "start_draw":draw("start",topology,seed,tick,i),
                         "offered":True})
            start_p = 0.12 if mode.startswith("baseline") else 0.22
            if adopters[i] and draw("start",topology,seed,tick,i) < start_p:
                job={"id":task_id,"principal":i,"arrival":tick,"cost":10 if start_p==0.12 else 6}
                task_id += 1
                q = i if mode.endswith("per_principal") else 0
                queues[q].append(job)
                rows.append({"type":"arrival",**job})
        # Finish jobs due now; their feedback is visible only next tick.
        for qidx, qbusy in enumerate(busy):
            remain=[]
            for job in qbusy:
                if job["finish"] == tick:
                    rows.append({"type":"completion","id":job["id"],"tick":tick,
                                 "latency":tick-job["arrival"]})
                    next_feedback[job["principal"]]=True
                else:
                    remain.append(job)
            busy[qidx]=remain
        # One server per principal for partitioned mode; otherwise shared FIFO servers.
        for qidx, q in enumerate(queues):
            if partitioned:
                while q and len(busy[qidx]) < 1:
                    job={**q.pop(0),"finish":tick+SERVICE}
                    busy[qidx].append(job)
                    rows.append({"type":"service_start","id":job["id"],"tick":tick,"queue":qidx})
            else:
                while q and len(busy[0]) < shared_servers:
                    job={**q.pop(0),"finish":tick+SERVICE}
                    busy[0].append(job)
                    rows.append({"type":"service_start","id":job["id"],"tick":tick,"queue":0})
        feedback = next_feedback
    for qidx,q in enumerate(queues):
        rows.extend({"type":"unfinished","id":j["id"],"state":"queued","queue":qidx} for j in q)
    for qidx,qbusy in enumerate(busy):
        rows.extend({"type":"unfinished","id":j["id"],"state":"in_service","queue":qidx,
                     "finish":j["finish"]} for j in qbusy)
    return rows


def main():
    all_rows=[]
    for top in ("ring","star"):
        for seed in SEEDS:
            for imi in IMITATIONS:
                for mode in MODES:
                    for row in simulate(top,seed,imi,mode):
                        all_rows.append({"topology":top,"seed":seed,"imitation":imi,"mode":mode,**row})
    json.dump({"schema":"7741-t0b-raw-v1","rows":all_rows},sys.stdout,
              sort_keys=True,separators=(",",":"))


if __name__ == "__main__":
    main()
