"""Effect-qualified policy runner. Emits candidate schedules only; oracle is separate."""
import json
import sys

HIGH, LOW, DWELL = 3, 1, 2
POLICIES = ("raw", "fixed_hysteresis", "minimum_dwell")


def policy_modes(symbols, policy):
    mode, remaining, result = 0, 0, []
    for symbol in symbols:
        if type(symbol) is not int or not 0 <= symbol < 20:
            raise ValueError("symbol must be integer 0..19")
        risk, stale, critical = symbol % 5, bool((symbol // 5) % 2), symbol >= 10
        if policy == "raw":
            mode = int(stale or critical or risk >= HIGH)
        elif stale:
            mode, remaining = 0, 0
            result.append(1)
            continue
        elif critical:
            mode = 1
            if policy == "minimum_dwell":
                remaining = DWELL
        elif policy == "fixed_hysteresis":
            if mode == 0 and risk >= HIGH:
                mode = 1
            elif mode == 1 and risk <= LOW:
                mode = 0
        elif policy == "minimum_dwell":
            if mode == 0 and risk >= HIGH:
                mode, remaining = 1, DWELL
            elif mode == 1:
                if remaining:
                    remaining -= 1
                elif risk < HIGH:
                    mode = 0
        else:
            raise ValueError("unknown policy")
        result.append(mode)
    return result


def run(fixture):
    rows = []
    for case in fixture["cases"]:
        schedules = {p: policy_modes(case["symbols"], p) for p in POLICIES}
        rows.append({"id":case["id"], "symbols":case["symbols"], "schedules":schedules})
    return {"schema":"planner-hysteresis-effect-candidate-v1", "rows":rows}


if __name__ == "__main__":
    fixture = json.load(open(sys.argv[1], encoding="utf-8"))
    json.dump(run(fixture), sys.stdout, sort_keys=True, separators=(",", ":"))
    sys.stdout.write("\n")
