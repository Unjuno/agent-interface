#!/usr/bin/env python3
"""Independent raw-only audit for decision-value acquisition T0 A01."""
import hashlib
import json
import math
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent
CFG = json.loads((ROOT / "profiles.json").read_text(encoding="utf-8"))


def u(profile, seed, stream):
    payload = ("7934-T0-A01|%s|%s|%s" % (profile, seed, stream)).encode("ascii")
    return int(hashlib.sha256(payload).hexdigest()[:13], 16) / float(16**13)


def states(profile):
    return [(int(a), int(b), float(p)) for a, b, p in profile["state_prior"]]


def p_signal(check, state, signal):
    x, y, _ = state
    if check["id"] == "xcheck":
        return check["accuracy"] if x == signal else 1 - check["accuracy"]
    return 1.0 if y == signal else 0.0


def h(values):
    total = 0.0
    for v in values:
        if v > 0:
            total -= v * math.log2(v)
    return total


def best(states_, admitted):
    values = {r: sum(p for x, y, p in states_
                     if (r == "A" and x == 0) or (r == "B" and x == 1))
              for r in admitted}
    return min(admitted, key=lambda r: (-values[r], r)) if admitted else None


def quantities(profile, check, admitted):
    prior = states(profile)
    before_route = best(prior, admitted)
    before = sum(p for x, y, p in prior
                 if (before_route == "A" and x == 0) or (before_route == "B" and x == 1))
    state_entropy = h([p for _, _, p in prior])
    expected_after = 0.0
    expected_entropy_after = 0.0
    signal_mass = {}
    normalized = {}
    for z in (0, 1):
        weighted = [(s, s[2] * p_signal(check, s, z)) for s in prior]
        mass = sum(v for _, v in weighted)
        signal_mass[z] = mass
        normalized[z] = [(s, v / mass) for s, v in weighted if mass] 
        if not mass:
            continue
        post = [(s[0], s[1], v) for s, v in normalized[z]]
        route = best(post, admitted)
        expected_after += mass * sum(p for x, y, p in post
                                     if (route == "A" and x == 0) or (route == "B" and x == 1))
        expected_entropy_after += mass * h([v for _, v in normalized[z]])
    return state_entropy - expected_entropy_after, expected_after - before, signal_mass


def select(profile, policy, admitted=("A", "B")):
    if len(admitted) == 1:
        return None
    checks = profile["checks"]
    allowed = [c for c in checks if c["cost"] <= CFG["budget"]]
    if policy == "cost":
        return min(allowed, key=lambda c: (c["cost"], c["id"]))["id"]
    stats = [(c, quantities(profile, c, admitted)) for c in allowed]
    if policy == "entropy":
        c, (info, _, _) = min(stats, key=lambda z: (-z[1][0], z[0]["cost"], z[0]["id"]))
        return c["id"] if info >= CFG["entropy_threshold_bits"] else None
    if policy in ("decision_value", "oracle"):
        good = [(c, q) for c, q in stats if q[1] - c["cost"] > 1e-12]
        if not good:
            return None
        c, _ = min(good, key=lambda z: (-(z[1][1] - z[0]["cost"]),
                                        z[0]["cost"], z[0]["id"]))
        return c["id"]
    raise ValueError(policy)


def expected_draw(profile_name, seed, name):
    x = int(u(profile_name, seed, "x") >= 0.5)
    if profile_name == "agreement":
        y = int(u(profile_name, seed, "y") >= 0.99)
    elif profile_name == "disagreement":
        y = int(u(profile_name, seed, "y") >= 0.5)
    else:
        y = x if u(profile_name, seed, "y") < 0.7 else 1 - x
    x_signal = x if u(profile_name, seed, "xcheck") < 0.8 else 1 - x
    return x, y, x_signal if name == "xcheck" else y


def route_after(profile, check_id, signal, admitted):
    if check_id is None:
        return best(states(profile), admitted)
    check = next(c for c in profile["checks"] if c["id"] == check_id)
    posterior = []
    for s in states(profile):
        posterior.append((s, s[2] * p_signal(check, s, signal)))
    norm = sum(v for _, v in posterior)
    post = [(s[0], s[1], v / norm) for s, v in posterior if norm]
    return best(post, admitted)


def run(raw_path, result_path, outdir):
    raw_bytes = pathlib.Path(raw_path).read_bytes()
    result = json.loads(pathlib.Path(result_path).read_text(encoding="utf-8"))
    records = [json.loads(line) for line in raw_bytes.decode("utf-8").splitlines() if line]
    errors = []
    if hashlib.sha256(raw_bytes).hexdigest() != result.get("raw_sha256"):
        errors.append("raw_digest_mismatch")
    expected_n = len(CFG["profiles"]) * CFG["seed_count"]
    if len(records) != expected_n or result.get("observations") != expected_n:
        errors.append("observation_count")
    lookup = {}
    for row in records:
        ident = (row.get("profile"), row.get("seed"))
        if ident in lookup:
            errors.append("duplicate_seed:%s:%s" % ident)
        lookup[ident] = row
        pname, seed = ident
        if pname not in CFG["profiles"]:
            errors.append("unknown_profile:%s" % pname)
            continue
        expected_seed = CFG["seed_start"] <= seed < CFG["seed_start"] + CFG["seed_count"]
        if not expected_seed:
            errors.append("seed_out_of_range:%s:%s" % ident)
            continue
        for ck in ("xcheck", "ycheck"):
            x, y, signal = expected_draw(pname, seed, ck)
            if (row.get("x"), row.get("y"), row.get("signals", {}).get(ck)) != (x, y, signal):
                errors.append("draw_mismatch:%s:%s:%s" % (pname, seed, ck))
    policies = ("cost", "entropy", "decision_value", "oracle")
    recomputed = {}
    for pname, prof in CFG["profiles"].items():
        recomputed[pname] = {}
        for policy in policies:
            check = select(prof, policy)
            summary = result.get("summaries", {}).get(pname, {}).get(policy, {})
            if summary.get("selected_check") != check:
                errors.append("selection:%s:%s" % (pname, policy))
            actual_regret, actual_cost, gates = 0, 0.0, 0
            computed_decisions = []
            for seed in range(CFG["seed_start"], CFG["seed_start"] + CFG["seed_count"]):
                row = lookup.get((pname, seed))
                if row is None:
                    errors.append("missing:%s:%s" % (pname, seed))
                    continue
                signal = row["signals"].get(check) if check else None
                route = route_after(prof, check, signal, ("A", "B"))
                regret = int((route == "A" and row["x"] == 1) or
                             (route == "B" and row["x"] == 0))
                actual_regret += regret
                actual_cost += next((c["cost"] for c in prof["checks"]
                                      if c["id"] == check), 0.0)
                gates += int(route not in ("A", "B"))
                computed_decisions.append({"seed": seed, "signal": signal, "route": route,
                                           "utility": 1 - regret, "regret": regret,
                                           "cost": next((c["cost"] for c in prof["checks"]
                                                         if c["id"] == check), 0.0),
                                           "gate_violation": route not in ("A", "B")})
            if summary.get("actual_decisions") != computed_decisions:
                errors.append("raw_decisions:%s:%s" % (pname, policy))
            mean_regret = actual_regret / CFG["seed_count"]
            mean_cost = actual_cost / CFG["seed_count"]
            if abs(mean_regret - summary.get("mean_realized_regret", -1)) > 1e-12:
                errors.append("regret:%s:%s" % (pname, policy))
            if abs(mean_cost - summary.get("mean_check_cost", -1)) > 1e-12:
                errors.append("cost:%s:%s" % (pname, policy))
            if gates != summary.get("hard_gate_violations"):
                errors.append("hard_gate:%s:%s" % (pname, policy))
            recomputed[pname][policy] = {"selected_check": check,
                                         "mean_realized_regret": mean_regret,
                                         "mean_check_cost": mean_cost,
                                         "hard_gate_violations": gates}
    controls = result.get("controls", {})
    for name in ("stale_source", "unknown_dependency", "unmodeled_mass_0_10"):
        ctl = controls.get(name, {})
        if ctl.get("status") != "UNKNOWN" or ctl.get("check") is not None or ctl.get("checks_performed") != 0:
            errors.append("control_not_unknown:%s" % name)
    denied = result.get("one_route_denied", {})
    for policy in policies:
        ctl = denied.get(policy, {})
        if ctl.get("route") != "A" or ctl.get("check") is not None or ctl.get("checks_performed") != 0:
            errors.append("denied_route_gate:%s" % policy)
    expected_choices = {
        "agreement": {"cost": "xcheck", "entropy": "xcheck", "decision_value": "xcheck", "oracle": "xcheck"},
        "disagreement": {"cost": "ycheck", "entropy": "ycheck", "decision_value": "xcheck", "oracle": "xcheck"},
        "correlated": {"cost": "ycheck", "entropy": "xcheck", "decision_value": "xcheck", "oracle": "xcheck"},
    }
    if result.get("decisions") != expected_choices:
        errors.append("profile_choice_matrix")
    dis = recomputed["disagreement"]
    if not (dis["cost"]["mean_realized_regret"] - dis["decision_value"]["mean_realized_regret"] >= 0.05):
        errors.append("decision_value_not_better_than_cost")
    if not (dis["entropy"]["mean_realized_regret"] - dis["decision_value"]["mean_realized_regret"] >= 0.05):
        errors.append("decision_value_not_better_than_entropy")
    ag = recomputed["agreement"]
    for policy in policies:
        if ag[policy]["selected_check"] != "xcheck":
            errors.append("agreement_control_choice:%s" % policy)
    if (ag["decision_value"]["mean_realized_regret"] != ag["oracle"]["mean_realized_regret"] or
            ag["decision_value"]["mean_check_cost"] != ag["oracle"]["mean_check_cost"]):
        errors.append("agreement_oracle_mismatch")
    for pname in recomputed:
        for policy, values in recomputed[pname].items():
            if values["hard_gate_violations"] != 0:
                errors.append("hard_gate_violation:%s:%s" % (pname, policy))
    report = {"status": "PASS_METHOD_SCOPED" if not errors else "FAIL_AUDIT",
              "independent_observations": len(records), "independent_errors": errors,
              "recomputed": recomputed, "frozen_threshold": 0.05}
    outdir = pathlib.Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / "independent_audit.json").write_text(
        json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "errors": len(errors),
                      "observations": len(records)}, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(run(sys.argv[1], sys.argv[2], sys.argv[3]))
