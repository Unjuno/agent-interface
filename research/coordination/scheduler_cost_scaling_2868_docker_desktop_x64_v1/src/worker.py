"""One fresh subprocess worker for a single queue policy and block."""
import heapq
import json
import sys
import time


def keys(candidates):
    return [(-c["priority"], c["deadline"], c["enqueue_seq"], c["op_id"])
            for c in candidates]


def select(policy, candidates):
    items = keys(candidates)
    if policy == "STABLE_LIST_SCAN":
        trace = []
        while items:
            chosen = min(items)
            trace.append(chosen[3])
            items.remove(chosen)
        return trace
    if policy == "STABLE_SORTED_LIST":
        items.sort()
        count = len(items)
        return [items.pop(0)[3] for _ in range(count)]
    if policy == "ELIGIBLE_HEAP":
        heapq.heapify(items)
        count = len(items)
        return [heapq.heappop(items)[3] for _ in range(count)]
    raise ValueError("unknown policy: " + policy)


def timed_select(policy, candidates):
    cpu_start = time.process_time_ns()
    wall_start = time.perf_counter_ns()
    trace = select(policy, candidates)
    wall_ns = time.perf_counter_ns() - wall_start
    cpu_ns = time.process_time_ns() - cpu_start
    return {"policy": policy, "cpu_ns": cpu_ns, "wall_ns": wall_ns, "trace": trace}


if __name__ == "__main__":
    policy = sys.argv[1]
    payload = json.load(sys.stdin)
    result = timed_select(policy, payload["candidates"])
    json.dump(result, sys.stdout, sort_keys=True, separators=(",", ":"))
    sys.stdout.write("\n")
