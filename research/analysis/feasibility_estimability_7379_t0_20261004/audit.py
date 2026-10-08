#!/usr/bin/env python3
"""Independent exact-oracle verifier for Issue #7379 T0 raw certificates."""
from fractions import Fraction
from itertools import combinations
from functools import lru_cache
from pathlib import Path
import copy, hashlib, json, sys

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def columns_for(profile):
    return {"main_plus_pair": ["1", "A", "B", "C", "AB", "AC", "BC"],
            "saturated": ["1", "A", "B", "C", "AB", "AC", "BC", "ABC"]}[profile]

def design_row(code, columns):
    a, b, c = [1 if code & (1 << j) else -1 for j in range(3)]
    values = {"1": 1, "A": a, "B": b, "C": c,
              "AB": a*b, "AC": a*c, "BC": b*c, "ABC": a*b*c}
    return [values[name] for name in columns]

def det_bareiss(matrix):
    a = [list(map(int, row)) for row in matrix]
    n = len(a)
    if n == 0:
        return 1
    sign, previous = 1, 1
    for k in range(n - 1):
        pivot = next((i for i in range(k, n) if a[i][k]), None)
        if pivot is None:
            return 0
        if pivot != k:
            a[k], a[pivot] = a[pivot], a[k]
            sign *= -1
        value = a[k][k]
        for i in range(k + 1, n):
            for j in range(k + 1, n):
                numerator = a[i][j] * value - a[i][k] * a[k][j]
                if numerator % previous:
                    raise AssertionError("Bareiss division was not exact")
                a[i][j] = numerator // previous
        for i in range(k + 1, n):
            a[i][k] = 0
        previous = value
    return sign * a[n - 1][n - 1]

@lru_cache(maxsize=None)
def exact_rank(rows, width):
    if not rows:
        return 0
    for size in range(min(len(rows), width), 0, -1):
        for ri in combinations(range(len(rows)), size):
            for ci in combinations(range(width), size):
                if det_bareiss([[rows[i][j] for j in ci] for i in ri]):
                    return size
    return 0

def to_q(text):
    return Fraction(text)

def oracle_status(support, feasible, columns, contrast):
    x = tuple(tuple(design_row(code, columns)) for code in support)
    return ("ESTIMABLE" if exact_rank(x, len(columns)) ==
            exact_rank(x + (tuple(contrast),), len(columns)) else "NOT_ESTIMABLE")

def verify_witness(record, profile, result, contrast):
    columns = columns_for(profile)
    x = [design_row(code, columns) for code in record["support"]]
    if result["status"] == "ESTIMABLE":
        if set(result) != {"status", "witness", "minimum_safe_addition"}:
            raise ValueError("estimable result has wrong fields")
        alpha = [to_q(v) for v in result["witness"].get("row_coefficients", [])]
        if len(alpha) != len(x):
            raise ValueError("row-space witness length mismatch")
        reconstructed = [sum(alpha[i] * x[i][j] for i in range(len(x)))
                         for j in range(len(columns))]
        if reconstructed != list(map(Fraction, contrast)):
            raise ValueError("invalid row-space witness")
        if result["minimum_safe_addition"] is not None:
            raise ValueError("estimable contrast reports a repair")
    else:
        if set(result) != {"status", "witness", "minimum_safe_addition"}:
            raise ValueError("non-estimable result has wrong fields")
        v = [to_q(z) for z in result["witness"].get("null_vector", [])]
        if len(v) != len(columns):
            raise ValueError("null witness length mismatch")
        if any(sum(Fraction(row[j]) * v[j] for j in range(len(columns))) for row in x):
            raise ValueError("null witness is not in null space")
        if sum(Fraction(contrast[j]) * v[j] for j in range(len(columns))) == 0:
            raise ValueError("null witness does not separate target contrast")
    expected_status = oracle_status(record["support"], record["feasible"], columns, contrast)
    if result["status"] != expected_status:
        raise ValueError("certificate status disagrees with exact minor oracle")
    repair = result["minimum_safe_addition"]
    if result["status"] == "NOT_ESTIMABLE":
        available = sorted(set(record["feasible"]) - set(record["support"]))
        expected = None
        for size in range(len(available) + 1):
            expected = next((list(add) for add in combinations(available, size)
                             if oracle_status(record["support"] + list(add), record["feasible"],
                                              columns, contrast) == "ESTIMABLE"), None)
            if expected is not None:
                break
        if repair != expected:
            raise ValueError("repair is unsafe, nonminimal, or has wrong tie-break")
    return expected_status

def verify_spec(spec):
    if spec.get("schema") != "feasibility-estimability-spec-v1":
        raise ValueError("unknown spec schema")
    if spec.get("model_profiles") != {
        "main_plus_pair": columns_for("main_plus_pair"),
        "saturated": columns_for("saturated")}:
        raise ValueError("model basis changed")
    expected = {
        "all_feasible": list(range(8)),
        "forbid_111": list(range(7)),
        "factor_A_fixed_low": [0, 2, 4, 6],
        "six_arm_restricted": [0, 1, 2, 4, 5, 6],
    }
    if spec.get("feasibility_cases") != expected:
        raise ValueError("feasibility predicate changed")
    if spec.get("contrasts") != {"main_A": {"A": 1}, "main_B": {"B": 1},
                                  "interaction_AB": {"AB": 1}}:
        raise ValueError("target contrasts changed")

def verify_record(record, spec):
    if set(record) != {"case", "feasible", "support", "contrast", "models", "disposition"}:
        raise ValueError("raw certificate has unexpected fields")
    if set(record["models"]) != set(spec["model_profiles"]):
        raise ValueError("raw profile roster mismatch")
    case = record["case"]
    if case not in spec["feasibility_cases"] or record["feasible"] != spec["feasibility_cases"][case]:
        raise ValueError("support uses wrong feasibility set")
    if record["support"] != sorted(set(record["support"])) or not set(record["support"]) <= set(record["feasible"]):
        raise ValueError("observed support contains infeasible or duplicate arm")
    terms = spec["contrasts"].get(record["contrast"])
    if terms is None:
        raise ValueError("unknown target contrast")
    statuses=[]
    for profile in spec["model_profiles"]:
        columns=columns_for(profile)
        contrast=[terms.get(name,0) for name in columns]
        statuses.append(verify_witness(record,profile,record["models"][profile],contrast))
    expected = statuses[0] if len(set(statuses)) == 1 else "UNRESOLVED_MODEL"
    if record["disposition"] != expected:
        raise ValueError("model-scope disposition mismatch")

def reject_mutation(fn, label):
    try:
        fn()
    except (AssertionError, KeyError, TypeError, ValueError, IndexError):
        return label
    raise AssertionError("mutation was accepted: " + label)

def run_mutation_controls(raw, spec):
    rows=raw["rows"]
    # An otherwise valid augmentation may never add a forbidden row.
    bad=copy.deepcopy(next(r for r in rows if r["case"]=="forbid_111"
        and r["models"]["main_plus_pair"]["minimum_safe_addition"] is not None))
    bad["models"]["main_plus_pair"]["minimum_safe_addition"].append(7)
    controls=[]
    controls.append(reject_mutation(lambda: verify_record(bad,spec),"forbidden_arm"))
    # Basis edits fail the pinned specification contract.
    altered=copy.deepcopy(spec); altered["model_profiles"]["main_plus_pair"][1]="ABC"
    controls.append(reject_mutation(lambda: verify_spec(altered),"model_basis_change"))
    # Alter a nonempty-support null witness so at least one exact equation fails.
    source=next(r for r in rows if r["case"]=="all_feasible" and r["support"]
                and r["models"]["main_plus_pair"]["status"]=="NOT_ESTIMABLE")
    bad=copy.deepcopy(source); v=bad["models"]["main_plus_pair"]["witness"]["null_vector"]
    v[0]=str(to_q(v[0])+1)
    controls.append(reject_mutation(lambda: verify_record(bad,spec),"invalid_null_witness"))
    # Claiming a non-estimable target is estimable cannot pass oracle/witness checks.
    bad=copy.deepcopy(source); bad["models"]["main_plus_pair"]["status"]="ESTIMABLE"
    controls.append(reject_mutation(lambda: verify_record(bad,spec),"false_estimable"))
    # A safe but larger repair is still rejected by minimum-cardinality comparison.
    source=next(r for r in rows if r["case"]=="all_feasible"
                and r["models"]["main_plus_pair"]["minimum_safe_addition"]
                and len(r["models"]["main_plus_pair"]["minimum_safe_addition"])==1
                and len(set(r["feasible"])-set(r["support"])-set(r["models"]["main_plus_pair"]["minimum_safe_addition"]))>0)
    bad=copy.deepcopy(source); repair=bad["models"]["main_plus_pair"]["minimum_safe_addition"]
    extra=min(set(bad["feasible"])-set(bad["support"])-set(repair)); repair.append(extra); repair.sort()
    controls.append(reject_mutation(lambda: verify_record(bad,spec),"nonminimal_safe_repair"))
    return controls

def main(spec_path, raw_path, freeze_path):
    spec_bytes=Path(spec_path).read_bytes(); spec=json.loads(spec_bytes)
    freeze=json.loads(Path(freeze_path).read_text())
    if hashlib.sha256(spec_bytes).hexdigest()!=freeze["spec_sha256"]:
        raise ValueError("spec does not match frozen bytes")
    if sha(__file__)!=freeze["audit_sha256"]:
        raise ValueError("auditor does not match frozen bytes")
    verify_spec(spec)
    raw=json.loads(Path(raw_path).read_bytes())
    if raw.get("schema")!="feasibility-estimability-raw-v1": raise ValueError("bad raw schema")
    if raw.get("spec_sha256")!=hashlib.sha256(spec_bytes).hexdigest(): raise ValueError("raw is not bound to frozen spec")
    if raw.get("candidate_sha256")!=freeze["candidate_sha256"]: raise ValueError("candidate source differs from freeze")
    if raw.get("source_commit")!=freeze["main_sha"]: raise ValueError("source commit differs from freeze")
    expected_cases=sum(1 << len(v) for v in spec["feasibility_cases"].values()) * len(spec["contrasts"])
    if len(raw.get("rows",[]))!=expected_cases: raise ValueError("incomplete enumeration")
    expected_keys=set()
    for case, feasible in spec["feasibility_cases"].items():
        for mask in range(1 << len(feasible)):
            support=tuple(config for i,config in enumerate(feasible) if (mask >> i) & 1)
            for contrast in spec["contrasts"]: expected_keys.add((case,tuple(feasible),support,contrast))
    observed_keys=[]
    for record in raw["rows"]:
        verify_record(record,spec)
        observed_keys.append((record["case"],tuple(record["feasible"]),tuple(record["support"]),record["contrast"]))
    if len(observed_keys)!=len(set(observed_keys)) or set(observed_keys)!=expected_keys:
        raise ValueError("enumeration has duplicate or missing support cases")
    if not any(r["case"]=="all_feasible" and len(r["support"])==8
               and r["disposition"]=="ESTIMABLE" for r in raw["rows"]):
        raise ValueError("missing full-rank positive control")
    if not any(r["disposition"]=="UNRESOLVED_MODEL" for r in raw["rows"]):
        raise ValueError("missing hierarchy-sensitivity case")
    if not any(r["models"]["main_plus_pair"]["status"]=="NOT_ESTIMABLE"
               and r["models"]["main_plus_pair"]["minimum_safe_addition"] is None
               for r in raw["rows"]):
        raise ValueError("missing no-safe-repair case")
    if not any(r["models"]["main_plus_pair"]["minimum_safe_addition"] is not None
               and len(r["models"]["main_plus_pair"]["minimum_safe_addition"])==1
               for r in raw["rows"]):
        raise ValueError("missing one-safe-repair case")
    controls=run_mutation_controls(raw,spec)
    if len(controls)!=5: raise AssertionError("mutation control count")
    print(json.dumps({"disposition":"PASS_METHOD_SCOPED","records":len(raw["rows"]),
                      "independent_exact_oracle":"fraction_free_minor_determinants",
                      "mutation_controls_rejected":controls,"candidate_sha256":raw["candidate_sha256"],
                      "raw_sha256":sha(raw_path),"spec_sha256":sha(spec_path)},sort_keys=True))

if __name__ == "__main__":
    if len(sys.argv)!=4: raise SystemExit("usage: audit.py SPEC.json RAW.json FREEZE.json")
    main(sys.argv[1],sys.argv[2],sys.argv[3])
