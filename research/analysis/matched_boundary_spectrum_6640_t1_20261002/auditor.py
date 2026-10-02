"""Independent raw-only audit; does not import candidate implementation."""
import hashlib
import json
import math
import random
import sys
from collections import defaultdict
from pathlib import Path

LABELS = ["admission", "policy", "gateway", "cache", "instrumentation", "render"]
RULES = ["unstratified", "matched", "first_symptom", "random"]


def close(a, b):
    return a is None and b is None or isinstance(a, (int, float)) and isinstance(b, (int, float)) and math.isclose(a, b, rel_tol=0, abs_tol=1e-12)


def reconstruct(fixture, hidden):
    grouped = defaultdict(list)
    for r in fixture["rows"]:
        grouped[int(r["seed"])].append(r)
    result = {"schema": 1, "interpretation": "inspection_priority_not_causal_evidence",
              "total_rows": len(fixture["rows"]), "seed_results": []}
    truth = {}
    for seed in sorted(grouped):
        rows = grouped[seed]
        by_stratum = defaultdict(list)
        symptoms = {label: 0 for label in LABELS}
        for r in rows:
            by_stratum[r["stratum"]].append(r)
            if r["first_symptom"] in symptoms:
                symptoms[r["first_symptom"]] += 1
        rankings, scores, statuses = {}, {}, {}
        for rule in RULES:
            scores[rule], statuses[rule] = {}, {}
            for label in LABELS:
                vals = []
                for group in ([rows] if rule == "unstratified" else by_stratum.values() if rule == "matched" else []):
                    yes, no = [], []
                    for r in group:
                        v = r["exposure"].get(label)
                        if v is True:
                            yes.append(bool(r["failed"]))
                        elif v is False:
                            no.append(bool(r["failed"]))
                    if yes and no:
                        vals.append(sum(yes)/len(yes) - sum(no)/len(no))
                if rule == "first_symptom":
                    scores[rule][label] = float(symptoms[label]); statuses[rule][label] = "SYMPTOM_COUNT_ONLY"
                elif rule == "random":
                    scores[rule][label] = None; statuses[rule][label] = "RANDOM_BASELINE"
                else:
                    score = sum(vals)/len(vals) if vals else None
                    scores[rule][label] = score
                    statuses[rule][label] = "ELIGIBLE" if vals else "NO_OVERLAP"
            if rule == "random":
                order = LABELS[:]
                random.Random(91_000 + seed).shuffle(order)
            else:
                order = sorted(LABELS, key=lambda k: (scores[rule][k] is None,
                               -(scores[rule][k] if scores[rule][k] is not None else 0), k))
            rankings[rule] = order
        ids = "\n".join(sorted(r["attempt_id"] for r in rows)).encode()
        result["seed_results"].append({"seed": seed, "row_count": len(rows),
             "attempt_ids_sha256": hashlib.sha256(ids).hexdigest(), "ranking": rankings,
             "scores": scores, "status": statuses})
        truth[str(seed)] = hidden["seeds"][str(seed)]["active_faults"]
    return result, truth


def metrics(result, truth):
    out = {}
    for method in RULES:
        reciprocal, all_top2 = [], []
        for item in result["seed_results"]:
            active = truth[str(item["seed"])]
            ranking = item["ranking"][method]
            ranks = [ranking.index(x)+1 for x in active]
            reciprocal.append(1/min(ranks))
            all_top2.append(all(rank <= 2 for rank in ranks))
        out[method] = {"mean_first_fault_reciprocal_rank": sum(reciprocal)/len(reciprocal),
                       "all_faults_top2_fraction": sum(all_top2)/len(all_top2)}
    return out


def audit(raw, fixture, hidden):
    expected, truth = reconstruct(fixture, hidden)
    errors = []
    if raw != expected:
        errors.append("RAW_RECONSTRUCTION_MISMATCH")
    if raw.get("interpretation") != "inspection_priority_not_causal_evidence":
        errors.append("CAUSAL_OVERCLAIM_OR_UNKNOWN_SCOPE")
    if raw.get("total_rows") != len(fixture["rows"]):
        errors.append("DENOMINATOR_MISMATCH")
    result_metrics = metrics(expected, truth)
    matched = result_metrics["matched"]["mean_first_fault_reciprocal_rank"]
    baselines = [result_metrics[x]["mean_first_fault_reciprocal_rank"] for x in ("unstratified", "first_symptom", "random")]
    pass_gate = matched >= max(baselines) + 0.10 and result_metrics["matched"]["all_faults_top2_fraction"] >= 0.75
    for item in expected["seed_results"]:
        if item["status"]["matched"]["cache"] != "NO_OVERLAP":
            errors.append("NO_OVERLAP_NOT_FLAGGED")
            break
        if item["status"]["unstratified"]["instrumentation"] not in ("ELIGIBLE", "NO_OVERLAP"):
            errors.append("MISSING_EXPOSURE_COLLAPSED")
            break
    return {"schema": 1, "audit_status": "PASS" if not errors else "FAIL",
            "disposition": "METHOD_PASS_SCOPED" if pass_gate and not errors else "FAIL_METHOD",
            "rows": len(fixture["rows"]), "seeds": len(expected["seed_results"]),
            "metrics": result_metrics, "errors": sorted(set(errors))}


def main():
    root = Path(__file__).resolve().parent
    fixture = json.loads((root / "fixture.json").read_text(encoding="utf-8"))
    hidden = json.loads((root / "oracle.json").read_text(encoding="utf-8"))
    raw = json.loads(Path("/in/candidate.json").read_text(encoding="utf-8"))
    out = audit(raw, fixture, hidden)
    Path("/out/audit.json").write_text(json.dumps(out, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    print(json.dumps(out, sort_keys=True))
    sys.exit(0 if out["audit_status"] == "PASS" else 1)


if __name__ == "__main__":
    main()
