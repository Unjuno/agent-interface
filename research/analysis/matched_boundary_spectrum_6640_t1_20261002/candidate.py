"""Candidate ranking; deliberately has no access to the hidden injection oracle."""
import hashlib
import json
import random
from collections import defaultdict
from pathlib import Path

BOUNDARIES = ("admission", "policy", "gateway", "cache", "instrumentation", "render")
METHODS = ("unstratified", "matched", "first_symptom", "random")


def digest_ids(rows):
    raw = "\n".join(sorted(row["attempt_id"] for row in rows)).encode()
    return hashlib.sha256(raw).hexdigest()


def diff(rows, key):
    valid = [r for r in rows if r["exposure"].get(key) is not None]
    yes = [r["failed"] for r in valid if r["exposure"].get(key) is True]
    no = [r["failed"] for r in valid if r["exposure"].get(key) is False]
    if not yes or not no:
        return None, "NO_OVERLAP"
    return sum(yes) / len(yes) - sum(no) / len(no), "ELIGIBLE"


def rank_one(rows, seed):
    ranking, scores, statuses = {}, {}, {}
    strata = defaultdict(list)
    for row in rows:
        strata[row["stratum"]].append(row)
    symptoms = defaultdict(int)
    for row in rows:
        if row["first_symptom"] is not None:
            symptoms[row["first_symptom"]] += 1
    for method in METHODS:
        method_scores, method_status = {}, {}
        for key in BOUNDARIES:
            if method == "unstratified":
                score, status = diff(rows, key)
            elif method == "matched":
                pieces = [diff(group, key)[0] for group in strata.values()
                          if diff(group, key)[1] == "ELIGIBLE"]
                score = sum(pieces) / len(pieces) if pieces else None
                status = "ELIGIBLE" if pieces else "NO_OVERLAP"
            elif method == "first_symptom":
                score = float(symptoms.get(key, 0))
                status = "SYMPTOM_COUNT_ONLY"
            else:
                score = None
                status = "RANDOM_BASELINE"
            method_scores[key] = score
            method_status[key] = status
        if method == "random":
            order = list(BOUNDARIES)
            random.Random(91_000 + seed).shuffle(order)
        else:
            order = sorted(BOUNDARIES, key=lambda k: (method_scores[k] is None,
                            -(method_scores[k] if method_scores[k] is not None else 0), k))
        ranking[method], scores[method], statuses[method] = order, method_scores, method_status
    return {"seed": seed, "row_count": len(rows), "attempt_ids_sha256": digest_ids(rows),
            "ranking": ranking, "scores": scores, "status": statuses}


def run(fixture):
    by_seed = defaultdict(list)
    for row in fixture["rows"]:
        by_seed[row["seed"]].append(row)
    return {"schema": 1, "interpretation": "inspection_priority_not_causal_evidence",
            "total_rows": len(fixture["rows"]),
            "seed_results": [rank_one(by_seed[s], s) for s in sorted(by_seed)]}


def main():
    root = Path(__file__).resolve().parent
    fixture = json.loads((root / "fixture.json").read_text(encoding="utf-8"))
    out = run(fixture)
    Path("/out/candidate.json").write_text(json.dumps(out, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    print(json.dumps({"rows": out["total_rows"], "seeds": len(out["seed_results"]), "status": "CANDIDATE_COMPLETE"}, sort_keys=True))


if __name__ == "__main__":
    main()
