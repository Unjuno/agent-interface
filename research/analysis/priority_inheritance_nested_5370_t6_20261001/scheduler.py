"""Small deterministic counterexample model for Issue #5370, T6."""
import argparse
import json


HORIZON = 20


def run_case(case, policy="inheritance_only"):
    if case not in {"transitive", "cancelled"}:
        raise ValueError("unknown case")
    if policy not in {"no_inheritance", "inheritance_only", "inheritance_plus_aging"}:
        raise ValueError("unknown policy")

    a_left, b_left, m_left = 2, 2, 40
    a_done = b_done = 0
    r1_released = False
    r2_released = False
    h_cancelled = h_done = False
    h_done_at = h_cancelled_at = None
    first_background_service = None
    last_background_service = None
    max_background_wait = 0
    schedule = []

    for tick in range(HORIZON):
        if case == "cancelled" and tick == 2:
            h_cancelled = True
            h_cancelled_at = tick

        h_waits_r2 = tick >= 1 and not r2_released and not h_cancelled
        inherited = 3 if h_waits_r2 and policy != "no_inheritance" else 0
        a_priority = inherited if not r1_released else 1
        b_priority = inherited if not r2_released else 2
        b_ready = r1_released and not r2_released and b_left > 0
        h_ready = r2_released and not h_cancelled and not h_done
        h_priority = 3

        u_wait = tick if last_background_service is None else tick - last_background_service
        max_background_wait = max(max_background_wait, u_wait)
        u_priority = 1
        if policy == "inheritance_plus_aging":
            u_priority = min(3, 1 + u_wait // 3)

        ready = []
        if a_left > 0:
            ready.append((a_priority, 0, "A"))
        if b_ready:
            ready.append((b_priority, 1, "B"))
        if h_ready:
            ready.append((h_priority, 2, "H"))
        if m_left > 0:
            ready.append((2, 3, "M"))
        ready.append((u_priority, 4, "U"))
        # Equal effective priority uses a fixed order, except aging gives U
        # precedence over M at equality once U has waited at least 3 ticks.
        if policy == "inheritance_plus_aging" and u_priority == 2 and tick >= 3:
            ready = [(p, (2 if name == "U" else 3 if name == "M" else rank), name)
                     for p, rank, name in ready]
        priority, _, selected = max(ready, key=lambda row: (row[0], -row[1]))
        schedule.append({"tick": tick, "job": selected, "effective_priority": priority})

        if selected == "A":
            a_left -= 1
            a_done += 1
            if a_left == 0:
                r1_released = True
        elif selected == "B":
            b_left -= 1
            b_done += 1
            if b_left == 0:
                r2_released = True
        elif selected == "H":
            h_done = True
            h_done_at = tick + 1
        elif selected == "M":
            m_left -= 1
        elif selected == "U":
            if first_background_service is None:
                first_background_service = tick
            last_background_service = tick

    return {
        "case": case,
        "policy": policy,
        "schedule": schedule,
        "owners": {"A": a_done, "B": b_done},
        "verifier": ({"status": "completed", "at": h_done_at} if h_done else
                     {"status": "cancelled", "at": h_cancelled_at} if h_cancelled else
                     {"status": "deadline_missed", "at": None}),
        "first_background_service": first_background_service,
        "max_background_wait": max_background_wait,
        "horizon": HORIZON,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    rows = [
        run_case("transitive", "no_inheritance"),
        run_case("transitive", "inheritance_only"),
        run_case("transitive", "inheritance_plus_aging"),
        run_case("cancelled", "inheritance_only"),
    ]
    with open(args.output, "w", encoding="utf-8", newline="\n") as f:
        json.dump(rows, f, sort_keys=True, separators=(",", ":"))
        f.write("\n")
    print(json.dumps({"rows": len(rows), "output": args.output}, sort_keys=True))


if __name__ == "__main__":
    main()
