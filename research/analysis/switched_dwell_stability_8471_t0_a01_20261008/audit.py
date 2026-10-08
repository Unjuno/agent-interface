"""Independent exact reconstruction; intentionally imports neither protocol nor candidate."""
import copy
import itertools
import json
from fractions import Fraction as Q

N = 12
X0 = (Q(1), Q(1, 2))
BOUND = Q(4)
A = ((Q(1, 2), Q(1)), (Q(0), Q(1, 2)))
B = ((Q(1, 2), Q(0)), (Q(1), Q(1, 2)))
PA = ((Q(4, 3), Q(8, 9)), (Q(8, 9), Q(116, 27)))
PB = ((Q(116, 27), Q(8, 9)), (Q(8, 9), Q(4, 3)))
I = ((Q(1), Q(0)), (Q(0), Q(1)))


def sub(m, n):
    return tuple(tuple(m[i][j] - n[i][j] for j in range(2)) for i in range(2))


def psd(m):
    return m[0][0] >= 0 and m[1][1] >= 0 and m[0][0] * m[1][1] - m[0][1] * m[1][0] >= 0


def mv(m, x):
    return tuple(sum((m[i][j] * x[j] for j in range(2)), Q(0)) for i in range(2))


def mm(m, n):
    return tuple(tuple(sum((m[i][k] * n[k][j] for k in range(2)), Q(0))
                       for j in range(2)) for i in range(2))


def energy(p, x):
    return sum((x[i] * p[i][j] * x[j] for i in range(2) for j in range(2)), Q(0))


def stable(m):
    tr, det = m[0][0] + m[1][1], m[0][0] * m[1][1] - m[0][1] * m[1][0]
    return 1-tr+det > 0 and 1+tr+det > 0 and 1-det > 0


def enc(x):
    return [f"{z.numerator}/{z.denominator}" for z in x]


def reconstruct(word, matrices, initial=X0, reset=I, disturbance=False):
    state, states, sw, count, product = initial, [initial], [0], 0, I
    for i, mode in enumerate(word):
        if i and mode != word[i-1]:
            count += 1
            state = mv(reset, state)
        product = mm(matrices[mode], product)
        state = mv(matrices[mode], state)
        if disturbance:
            delta = (Q(1, 100), Q((-1)**i, 100))
            state = tuple(state[k] + delta[k] for k in range(2))
        states.append(state)
        sw.append(count)
    return states, sw, product


def expected():
    out = []
    for number in range(1 << N):
        word = tuple("B" if number & (1 << i) else "A" for i in range(N))
        states, switches, product = reconstruct(word, {"A": A, "B": B})
        s, bounds = 0, [Q(1)]
        for i, m in enumerate(word):
            if i and m != word[i-1]:
                s += 1
            bounds.append(Q(5, 6)**(i+1) * Q(5)**s)
        out.append({"id": number, "word": "".join(word), "states": [enc(x) for x in states],
            "switch_prefixes": switches, "product": [[f"{z.numerator}/{z.denominator}" for z in r] for r in product],
            "schur_stable": stable(product),
            "lyapunov_bounds": [f"{z.numerator}/{z.denominator}" for z in bounds],
            "lyapunov_certified": all(z < 1 for z in bounds[1:]),
            "envelope_crossed": any(max(map(abs, x)) > BOUND for x in states)})
    return out


def audit(data):
    assert data["schema"] == "switched-dwell-stability-8471-t0-a01-v1"
    assert data["horizon"] == N
    for matrix, p in ((A, PA), (B, PB)):
        assert sub(p, mm(mm(tuple(zip(*matrix)), p), matrix)) == I
        assert p[0][0] > 0 and p[0][0] * p[1][1] - p[0][1] ** 2 > 0
    assert psd(sub(tuple(tuple(5 * PB[i][j] for j in range(2)) for i in range(2)), PA))
    assert psd(sub(tuple(tuple(5 * PA[i][j] for j in range(2)) for i in range(2)), PB))
    wanted = expected()
    assert data["rows"] == wanted
    assert len(wanted) == 4096
    assert sum(not r["schur_stable"] for r in wanted) == 1248
    assert sum(r["envelope_crossed"] for r in wanted) == 129
    assert sum(r["lyapunov_certified"] for r in wanted) == 10
    assert all(not r["lyapunov_certified"] or r["schur_stable"] for r in wanted)

    schedules = set()
    disturbed_max = Q(0)
    for number in range(1 << N):
        requests = tuple("B" if number & (1 << i) else "A" for i in range(N))
        actual, last, current = [], -10, "A"
        for t, req in enumerate(requests):
            if req != current and t-last >= 10:
                current, last = req, t
            actual.append(current)
        schedules.add("".join(actual))
        trace, _, _ = reconstruct(requests, {"A": A, "B": B}, disturbance=True)
        disturbed_max = max(disturbed_max, *(abs(v) for x in trace for v in x))
    dwell_rows = []
    for schedule_text in sorted(schedules):
        schedule = tuple(schedule_text)
        states, _, product = reconstruct(schedule, {"A": A, "B": B})
        dwell_rows.append({"word": schedule_text, "schur_stable": stable(product),
            "envelope_crossed": any(max(map(abs, x)) > BOUND for x in states)})
    assert data["minimum_dwell"] == {"count": len(schedules), "dwell": 10,
        "unique_schedules": sorted(schedules), "rows": dwell_rows}
    assert len(schedules) == 16
    assert all(r["schur_stable"] for r in dwell_rows)
    assert not any(r["envelope_crossed"] for r in dwell_rows)
    assert data["hysteresis"] == {"all_binary_words": True,
        "proof_witness": "A->B uses 1; B->A uses 0; each tick's extreme crosses threshold",
        "scheduled_words": 4096}
    assert data["disturbance"] == {"count": 4096,
        "max_abs_coordinate": f"{disturbed_max.numerator}/{disturbed_max.denominator}",
        "strictly_below_declared_observation_envelope": disturbed_max < 16,
        "robust_stability_claim": False}
    assert data["reset_control"]["identity"] == [["1/1", "0/1"], ["0/1", "1/1"]]
    assert data["reset_control"]["mode_change_applies_reset_before_next_mode"] is True
    assert data["emergency_override_control"] == {"minimum_dwell": 10,
        "emergency_request_applies_immediately": True}
    assert data["boundary_control"] == {"alpha": "1/2", "mu": "2/1", "switches": 1,
        "prefix_bound": "1/1", "strict_less_than_one_certifies": False}
    assert data["common_lyapunov_control"]["accepted"] == 4096
    assert data["common_lyapunov_control"]["all_stable"] is True
    assert len(data["common_lyapunov_control"]["rows"]) == 4096
    assert data["claims"] == {"finite_horizon_only": True, "iss_established": False,
        "hardware_or_actuator_tested": False, "safety_authority": False}
    return True


def mutation_suite(data):
    # Each corruption independently models one frozen integrity/safety gate.
    mutations = {
        "mode_matrix_or_product": lambda d: d["rows"][0]["product"][0].__setitem__(0, "9/1"),
        "state_transition": lambda d: d["rows"][0]["states"][1].__setitem__(0, "9/1"),
        "dwell_counter": lambda d: d["rows"][0]["switch_prefixes"].__setitem__(0, 1),
        "safety_envelope": lambda d: d["rows"][0].__setitem__("envelope_crossed", True),
        "reset_map": lambda d: d["reset_control"]["identity"][0].__setitem__(0, "2/1"),
        "emergency_override": lambda d: d["emergency_override_control"].__setitem__("emergency_request_applies_immediately", False),
        "strict_boundary": lambda d: d["boundary_control"].__setitem__("strict_less_than_one_certifies", True),
    }
    caught = []
    for name, mutate in mutations.items():
        bad = copy.deepcopy(data)
        mutate(bad)
        try:
            audit(bad)
        except (AssertionError, KeyError, TypeError, IndexError):
            caught.append(name)
    assert len(caught) == len(mutations), (caught, list(mutations))
    return caught


if __name__ == "__main__":
    with open("candidate.json", encoding="utf-8") as f:
        result = json.load(f)
    audit(result)
    print(json.dumps({"audit": "PASS", "rows": 4096, "mutations_rejected": mutation_suite(result)}))
