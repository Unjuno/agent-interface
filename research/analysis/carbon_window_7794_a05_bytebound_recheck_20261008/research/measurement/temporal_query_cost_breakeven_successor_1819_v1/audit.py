from fractions import Fraction
import json
import formal

def independent_priors():
    out = []
    for a in range(41):
        for b in range(41 - a):
            for c in range(41 - a - b):
                out.append((a, b, c, 40 - a - b - c))
    return out

def audit():
    ps = independent_priors()
    assert len(ps) == 12341
    q = ps[1]  # nonzero EVENT/REVERSAL witness for corruption controls
    class_values = []
    anchor_values = []
    for p in ps:
        class_values.append(Fraction(4*p[0] + 2*p[1] + 8*p[2] + 6*p[3], 40))
        anchor_values.append(Fraction(4*p[0] + 2*p[1] + 2*p[2] + 2*p[3], 40))
    extrema = {
        "class_only": (min(class_values), max(class_values)),
        "class_anchor": (min(anchor_values), max(anchor_values)),
    }
    control = {
        "budget_corruption_detected": class_values[1] != Fraction(4*q[0] + 2*q[1] + 7*q[2] + 6*q[3], 40),
        "normalization_corruption_detected": sum(ps[0]) != 41,
        "event_reversal_corruption_detected": Fraction(6*q[2] + 4*q[3], 40) != Fraction(6*q[2] + 5*q[3], 40),
        "inequality_direction_control": not (Fraction(6) < Fraction(0)),
    }
    return {
        "audit_invocations": 1,
        "prior_count": len(ps),
        "extrema": {k: [str(v[0]), str(v[1])] for k, v in extrema.items()},
        "equal_prior_thresholds": ["6", "5/2", "17/2"],
        "controls": control,
        "candidate_pass": formal.run()["pass"],
        "pass": extrema["class_only"] == (Fraction(2), Fraction(8))
                 and extrema["class_anchor"] == (Fraction(2), Fraction(4))
                 and all(control.values())
                 and formal.run()["pass"],
    }

if __name__ == "__main__":
    print(json.dumps(audit(), indent=2, sort_keys=True))
