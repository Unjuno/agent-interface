#!/usr/bin/env python3
"""Compute omitted spectrum baselines from #6640's immutable archived rows."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
from collections import defaultdict
from pathlib import Path
from typing import Any

LABELS = ["admission", "policy", "gateway", "cache", "instrumentation", "render"]
OLD_METHODS = ["unstratified", "matched", "first_symptom", "random"]
NEW_METHODS = ["ochiai", "failed_exposure_count", "failed_exposure_rate"]
PREDECESSOR = Path("research/analysis/matched_boundary_spectrum_6640_t1_20261002")


def _rank(scores: dict[str, float | None]) -> list[str]:
    return sorted(LABELS, key=lambda k: (scores[k] is None, -(scores[k] or 0.0), k))


def _safe_mean(values: list[float]) -> float | None:
    return sum(values) / len(values) if values else None


def _risk_difference(rows: list[dict[str, Any]], label: str) -> tuple[float | None, str]:
    known = [r for r in rows if isinstance(r["exposure"].get(label), bool)]
    yes = [bool(r["failed"]) for r in known if r["exposure"].get(label) is True]
    no = [bool(r["failed"]) for r in known if r["exposure"].get(label) is False]
    if not yes or not no:
        return None, "NO_OVERLAP"
    return sum(yes) / len(yes) - sum(no) / len(no), "ELIGIBLE"


def reconstruct_old(rows: list[dict[str, Any]], seed: int) -> dict[str, Any]:
    by_stratum: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_stratum[row["stratum"]].append(row)
    out: dict[str, Any] = {"seed": seed, "row_count": len(rows), "methods": {}}
    for method in OLD_METHODS:
        scores: dict[str, float | None] = {}
        statuses: dict[str, str] = {}
        for label in LABELS:
            if method == "unstratified":
                scores[label], statuses[label] = _risk_difference(rows, label)
            elif method == "matched":
                parts = [score for group in by_stratum.values()
                         for score, status in [_risk_difference(group, label)]
                         if status == "ELIGIBLE" and score is not None]
                scores[label] = _safe_mean(parts)
                statuses[label] = "ELIGIBLE" if parts else "NO_OVERLAP"
            elif method == "first_symptom":
                scores[label] = float(sum(r["first_symptom"] == label for r in rows))
                statuses[label] = "SYMPTOM_COUNT_ONLY"
            else:
                scores[label] = None
                statuses[label] = "RANDOM_BASELINE"
        ranking = None
        if method == "random":
            ranking = LABELS[:]
            random.Random(91_000 + seed).shuffle(ranking)
        else:
            ranking = _rank(scores)
        out["methods"][method] = {"scores": scores, "status": statuses, "ranking": ranking}
    ids = "\n".join(sorted(r["attempt_id"] for r in rows)).encode()
    out["attempt_ids_sha256"] = hashlib.sha256(ids).hexdigest()
    return out


def compute_new(rows: list[dict[str, Any]]) -> dict[str, Any]:
    scores: dict[str, dict[str, float | None]] = {m: {} for m in NEW_METHODS}
    counts: dict[str, dict[str, int]] = {}
    for label in LABELS:
        ef = ep = nf = 0
        failed_exposed = failed_known = missing = 0
        for row in rows:
            exposed = row["exposure"].get(label)
            if exposed is None:
                missing += 1
                continue
            failed = bool(row["failed"])
            if failed:
                failed_known += 1
                if exposed is True:
                    ef += 1
                    failed_exposed += 1
                else:
                    nf += 1
            elif exposed is True:
                ep += 1
        denom = (ef + nf) * (ef + ep)
        scores["ochiai"][label] = ef / math.sqrt(denom) if denom else None
        scores["failed_exposure_count"][label] = float(failed_exposed)
        scores["failed_exposure_rate"][label] = failed_exposed / failed_known if failed_known else None
        counts[label] = {"failed_exposed": ef, "failed_unexposed": nf,
                         "passed_exposed": ep, "missing_exposure": missing,
                         "failed_known_exposure_rows": failed_known}
    return {"scores": scores, "rankings": {method: _rank(value) for method, value in scores.items()},
            "counts": counts}


def _metrics(rankings: dict[str, list[str]], active_faults: list[str]) -> dict[str, float]:
    ranks = [rankings.index(label) + 1 for label in active_faults]
    return {"first_fault_reciprocal_rank": 1.0 / min(ranks),
            "all_faults_top2": float(all(rank <= 2 for rank in ranks))}


def analyze(fixture: dict[str, Any], oracle: dict[str, Any], old_raw: dict[str, Any], old_audit: dict[str, Any]) -> dict[str, Any]:
    rows = fixture["rows"]
    grouped: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[int(row["seed"])].append(row)
    errors: list[str] = []
    expected_seeds = sorted(map(int, oracle["seeds"].keys()))
    if len(rows) != 8192 or len(grouped) != 32 or set(grouped) != set(expected_seeds):
        errors.append("FIXTURE_SEED_OR_DENOMINATOR_MISMATCH")
    if len({r["attempt_id"] for r in rows}) != len(rows):
        errors.append("DUPLICATE_ATTEMPT_ID")
    raw_seeds = {int(item["seed"]): item for item in old_raw["seed_results"]}
    if set(raw_seeds) != set(expected_seeds):
        errors.append("PREDECESSOR_RAW_SEED_SET_MISMATCH")

    seed_audits = []
    all_methods = OLD_METHODS + NEW_METHODS
    metric_acc: dict[str, list[dict[str, float]]] = {m: [] for m in all_methods}
    for seed in expected_seeds:
        seed_rows = grouped[seed]
        old = reconstruct_old(seed_rows, seed)
        predecessor_seed = raw_seeds.get(seed, {})
        if len(seed_rows) != 256:
            errors.append(f"ROW_COUNT_SEED_{seed}")
        if predecessor_seed.get("row_count") != old["row_count"] or predecessor_seed.get("attempt_ids_sha256") != old["attempt_ids_sha256"]:
            errors.append(f"PREDECESSOR_RAW_INVENTORY_MISMATCH_SEED_{seed}")
        for method in OLD_METHODS:
            p = predecessor_seed.get("ranking", {}).get(method)
            s = predecessor_seed.get("scores", {}).get(method, {})
            if p != old["methods"][method]["ranking"]:
                errors.append(f"PREDECESSOR_RANK_MISMATCH_{method}_SEED_{seed}")
            for label, expected in old["methods"][method]["scores"].items():
                got = s.get(label)
                if expected is None:
                    if got is not None:
                        errors.append(f"PREDECESSOR_SCORE_MISMATCH_{method}_{label}_SEED_{seed}")
                elif not isinstance(got, (int, float)) or not math.isclose(float(got), expected, rel_tol=0, abs_tol=1e-12):
                    errors.append(f"PREDECESSOR_SCORE_MISMATCH_{method}_{label}_SEED_{seed}")

        new = compute_new(seed_rows)
        per_seed = {m: old["methods"][m]["ranking"] for m in OLD_METHODS}
        per_seed.update(new["rankings"])
        active = oracle["seeds"][str(seed)]["active_faults"]
        for method in all_methods:
            metric_acc[method].append(_metrics(per_seed[method], active))
        seed_audits.append({"seed": seed, "row_count": len(seed_rows),
                            "predecessor_ranks_reconstructed": True,
                            "new_baselines": new,
                            "active_faults": active,
                            "rank_metrics": {m: _metrics(per_seed[m], active) for m in all_methods}})

    metrics = {}
    for method, values in metric_acc.items():
        metrics[method] = {
            "mean_first_fault_reciprocal_rank": sum(v["first_fault_reciprocal_rank"] for v in values) / len(values),
            "all_faults_top2_fraction": sum(v["all_faults_top2"] for v in values) / len(values),
        }
    previous_metrics = old_audit.get("metrics", {})
    for method in OLD_METHODS:
        for metric_name, got in metrics[method].items():
            expected = previous_metrics.get(method, {}).get(metric_name)
            if not isinstance(expected, (int, float)) or not math.isclose(got, float(expected), rel_tol=0, abs_tol=1e-12):
                errors.append(f"PREDECESSOR_AUDIT_METRIC_MISMATCH_{method}_{metric_name}")
    if old_audit.get("disposition") != "FAIL_METHOD" or old_audit.get("audit_status") != "PASS":
        errors.append("PREDECESSOR_DISPOSITION_IDENTITY_MISMATCH")

    return {
        "schema": "matched-boundary-spectrum-omitted-baselines-audit-v1",
        "successor_issue": 6668,
        "predecessor_issue": 6640,
        "interpretation": "descriptive post-hoc comparator sensitivity; not causal evidence; predecessor disposition unchanged",
        "integrity_status": "PASS_ARCHIVE_RECONSTRUCTION" if not errors else "HOLD_AUDIT_INTEGRITY",
        "errors": sorted(set(errors)),
        "rows": len(rows),
        "seeds": len(expected_seeds),
        "predecessor_disposition": old_audit.get("disposition"),
        "metrics": metrics,
        "seed_results": seed_audits,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[3]
    predecessor = root / PREDECESSOR
    fixture = json.loads((predecessor / "fixture.json").read_text(encoding="utf-8"))
    oracle = json.loads((predecessor / "oracle.json").read_text(encoding="utf-8"))
    raw = json.loads((predecessor / "results/allocation-01/candidate/candidate.json").read_text(encoding="utf-8"))
    audit = json.loads((predecessor / "results/allocation-01/audit/audit.json").read_text(encoding="utf-8"))
    result = analyze(fixture, oracle, raw, audit)
    target = Path(args.output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"integrity_status": result["integrity_status"], "errors": result["errors"], "rows": result["rows"], "seeds": result["seeds"], "metrics": result["metrics"]}, sort_keys=True))
    return 0 if result["integrity_status"] == "PASS_ARCHIVE_RECONSTRUCTION" else 2


if __name__ == "__main__":
    raise SystemExit(main())
