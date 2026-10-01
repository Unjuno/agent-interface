"""Independent raw-only auditor for Issue #5890 synthetic portfolio ledger."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path

SEED = 58901002
SCALE = 1_000_000
KINDS = ["STAT_NULL", "STAT_ALT", "METHOD_PASS", "STAT_NULL",
         "STAT_INVALID_CORRELATED", "STAT_ALT", "METHOD_FAIL", "DESCRIPTIVE",
         "HOLD", "HARD_SAFETY_FAIL", "STOP", "STAT_NULL", "STAT_ALT"]


def audit_draw(token: str) -> int:
    return int.from_bytes(hashlib.sha256(token.encode("ascii")).digest(), "big")


def audit_p(kind: str, family: int, slot: int) -> int | None:
    if kind == "STAT_NULL":
        n = audit_draw(f"{SEED}|{family}|{slot}|null")
        return n * SCALE // (1 << 256) + 1
    if kind == "STAT_ALT":
        n = audit_draw(f"{SEED}|{family}|{slot}|alternative")
        return n**5 * (SCALE - 1) // (1 << 1280) + 1
    return None


def should_reject(p_micro: int, i: int) -> bool:
    return p_micro * 100 * i * (i + 1) <= 5 * SCALE


def validate(raw: dict) -> tuple[list[str], dict]:
    errors = []
    rows = raw.get("rows")
    if raw.get("schema") != "portfolio-multiplicity-5890-raw-v2" or raw.get("allocation") != "PORTFOLIO-MULTIPLICITY-5890-T0-20261001-02" or raw.get("base_main") != "3d6ffc76d535309cf3820ed33cb9327354f03648" or raw.get("seed") != SEED:
        errors.append("identity")
    if not isinstance(rows, list) or len(rows) != 416:
        return errors + ["row-count"], {}
    seen = set()
    korder = 0
    first_null = {}
    counts = {k: 0 for k in set(KINDS)}
    naive_false = naive_true = online_false = online_true = 0
    safety_online = 0
    for n, row in enumerate(rows):
        family, slot = divmod(n, len(KINDS))
        kind = KINDS[slot]
        claim = f"F{family:02d}-C{slot+1:02d}"
        if row.get("claim_id") != claim or row.get("family_id") != f"F{family:02d}" or row.get("portfolio_id") != "portfolio-5890-r2" or row.get("registered_order") != n+1:
            errors.append(f"schedule:{n}")
        if row.get("completion_order") != family*len(KINDS)+((slot*5)%len(KINDS))+1:
            errors.append(f"completion-order:{n}")
        if row.get("candidate_id") != "interface-candidate-r2" or row.get("baseline_id") != "interface-baseline-v1" or row.get("endpoint") != "synthetic-discovery-claim" or row.get("claim_type") != kind:
            errors.append(f"claim-metadata:{n}")
        if claim in seen:
            errors.append(f"duplicate:{n}")
        seen.add(claim)
        counts[kind] += 1
        expected_p = audit_p(kind, family, slot)
        expected_truth = True if kind == "STAT_NULL" else False if kind == "STAT_ALT" else None
        expected_dep = f"independent-{family}-{slot}" if expected_truth is not None else None
        expected_safety = kind == "HARD_SAFETY_FAIL"
        expected_method = "PASS" if kind == "METHOD_PASS" else "FAIL" if kind == "METHOD_FAIL" else None
        expected_desc = "directional-only" if kind == "DESCRIPTIVE" else None
        if kind == "STAT_NULL":
            first_null[family] = expected_p
        if kind == "STAT_INVALID_CORRELATED":
            expected_p, expected_truth, expected_dep = first_null.get(family), True, f"shared-null-{family}"
        if kind == "HARD_SAFETY_FAIL":
            expected_p, expected_dep = 1, f"safety-{family}"
        eligible = kind in {"STAT_NULL", "STAT_ALT"}
        if eligible:
            korder += 1
            expected_alpha_num, expected_alpha_den = 5, 100*korder*(korder+1)
            expected_naive = expected_p*20 < SCALE
            expected_online = should_reject(expected_p, korder)
            if expected_truth and expected_naive:
                naive_false += 1
            elif expected_truth is False and expected_naive:
                naive_true += 1
            if expected_truth and expected_online:
                online_false += 1
            elif expected_truth is False and expected_online:
                online_true += 1
        else:
            expected_alpha_num = expected_alpha_den = None
            expected_naive = expected_online = False
            if expected_safety and expected_online:
                safety_online += 1
        expected_fields = {"p_micro": expected_p, "true_null": expected_truth,
                           "dependence_group": expected_dep, "hard_safety_failure": expected_safety,
                           "method_result": expected_method, "descriptive_summary": expected_desc,
                           "eligible_order": korder if eligible else None,
                           "alpha_num": expected_alpha_num, "alpha_den": expected_alpha_den,
                           "naive_promoted": expected_naive, "online_promoted": expected_online}
        for key, value in expected_fields.items():
            if row.get(key) != value:
                errors.append(f"field:{n}:{key}")
    metric = {"rows": len(rows), "eligible": korder, "null_tests": counts["STAT_NULL"],
              "alternative_tests": counts["STAT_ALT"], "invalid_correlated": counts["STAT_INVALID_CORRELATED"],
              "hard_safety_failures": counts["HARD_SAFETY_FAIL"], "safety_promotions": safety_online,
              "unadjusted_false": naive_false, "unadjusted_true": naive_true,
              "online_false": online_false, "online_true": online_true,
              "naive_fdp": naive_false/(naive_false+naive_true) if naive_false+naive_true else 0.0,
              "online_fdp": online_false/(online_false+online_true) if online_false+online_true else 0.0}
    return errors, metric


def run(path: Path) -> dict:
    raw_bytes = path.read_bytes()
    raw = json.loads(raw_bytes.decode("utf-8"))
    errors, metric = validate(raw)
    controls = {}
    mutations = {}
    omit = copy.deepcopy(raw); omit["rows"].pop(6)
    mutations["omitted_failure"] = omit
    duplicate = copy.deepcopy(raw); duplicate["rows"].append(copy.deepcopy(raw["rows"][0]))
    mutations["duplicate"] = duplicate
    reorder = copy.deepcopy(raw); reorder["rows"][0]["registered_order"], reorder["rows"][1]["registered_order"] = 2, 1
    mutations["reordered_start"] = reorder
    cohort = copy.deepcopy(raw); cohort["rows"][1]["dependence_group"] = cohort["rows"][0]["dependence_group"]
    mutations["shared_cohort"] = cohort
    family = copy.deepcopy(raw); family["rows"][0]["portfolio_id"] = "portfolio-5890-posthoc"
    mutations["posthoc_family"] = family
    methodp = copy.deepcopy(raw); methodp["rows"][2]["p_micro"] = 1
    mutations["invented_method_p"] = methodp
    safety = copy.deepcopy(raw); safety["rows"][9]["hard_safety_failure"] = False
    mutations["forged_safety"] = safety
    for name, altered in mutations.items():
        e, _ = validate(altered)
        controls[name] = bool(e)
    decision = "PASS_METHOD_SCOPED" if (not errors and metric["eligible"] == 192 and
        metric["null_tests"] == 96 and metric["alternative_tests"] == 96 and
        metric["invalid_correlated"] == 32 and metric["online_false"] == 0 and
        metric["naive_fdp"] > metric["online_fdp"] and metric["safety_promotions"] == 0 and
        len(controls) == 7 and all(controls.values())) else "FAIL_OR_HOLD"
    return {"decision": decision, "errors": errors, "raw_sha256": hashlib.sha256(raw_bytes).hexdigest(),
            **metric, "corruption_controls": controls, "corruptions_rejected": sum(controls.values())}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        raise SystemExit("refuse to overwrite audit output")
    result = run(args.raw)
    args.out.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(result["decision"])
    raise SystemExit(0 if result["decision"] == "PASS_METHOD_SCOPED" else 1)


if __name__ == "__main__":
    main()

