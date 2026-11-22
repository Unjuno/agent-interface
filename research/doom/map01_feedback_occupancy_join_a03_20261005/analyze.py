import hashlib
import json
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".git").exists() and (p / "research/doom").exists())
PKG = Path(__file__).resolve().parent
SRC = ROOT / "research/doom/results/v39-control-telemetry-gap-audit-20261004"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    for line in (PKG / "SOURCE_SHA256SUMS.txt").read_text().splitlines():
        expected, rel = line.split("  ", 1)
        if sha(ROOT / rel) != expected:
            raise SystemExit(f"HOLD_SOURCE_HASH_MISMATCH {rel}")
    events = [json.loads(line) for line in (SRC / "events.jsonl").read_text().splitlines()]
    admissions = [e for e in events if e.get("event") == "input_admission"]
    holds = [e for e in events if e.get("event") == "keys_held"]

    matches = []
    for a in admissions:
        candidates = [
            h for h in holds
            if h.get("input_ack_ns", -1) >= a["input_ack_ns"] and a["key"] in h.get("keys", [])
        ]
        matches.append({
            "key": a["key"],
            "input_ack_ns": a["input_ack_ns"],
            "candidate_count": len(candidates),
            "candidate_ids_steps": [[h.get("id"), h.get("step")] for h in candidates],
        })

    # This tests set-level consistency only. It cannot bind individual
    # admission rows to an aggregate hold row without extra identity.
    by_step = {}
    for e in events:
        if e.get("event") in ("step_started", "input_admission", "keys_held", "step_completed") and "id" in e and "step" in e:
            by_step.setdefault((e["id"], e["step"]), {"admissions": [], "holds": [], "start": 0, "complete": 0})
            row = by_step[(e["id"], e["step"])]
            if e["event"] == "input_admission": row["admissions"].append(e["key"])
            if e["event"] == "keys_held": row["holds"].append(e.get("keys", []))
            if e["event"] == "step_started": row["start"] += 1
            if e["event"] == "step_completed": row["complete"] += 1
    set_checks = []
    for (ident, step), row in by_step.items():
        if row["holds"]:
            set_checks.append({
                "id": ident, "step": step,
                "admission_key_set": sorted(set(row["admissions"])),
                "aggregate_key_set": sorted(set().union(*(set(x) for x in row["holds"]))),
                "consistent": sorted(set(row["admissions"])) == sorted(set().union(*(set(x) for x in row["holds"]))),
                "admission_count": len(row["admissions"]),
                "hold_receipt_count": len(row["holds"]),
            })

    ambiguous_fixture = {
        "admission": {"event": "input_admission", "key": "space", "input_ack_ns": 10},
        "holds": [
            {"event": "keys_held", "id": "A", "step": 0, "keys": ["space"], "input_ack_ns": 20},
            {"event": "keys_held", "id": "B", "step": 0, "keys": ["space"], "input_ack_ns": 30},
        ],
        "admissible_identity_assignments": ["A", "B"],
    }

    ambiguity = {str(n): sum(m["candidate_count"] == n for m in matches) for n in sorted({m["candidate_count"] for m in matches})}
    result = {
        "schema": "map01-admission-hold-identity-ambiguity-a03-v1",
        "status": "PASS_AMBIGUITY_FALSIFIED_RECONSTRUCTION_SCOPED",
        "source_sha256": {p.name: sha(p) for p in [SRC / "events.jsonl", SRC / "owner-events.json", SRC / "sources.json"]},
        "counts": {"events": len(events), "admissions": len(admissions), "aggregate_holds": len(holds)},
        "candidate_count_histogram": ambiguity,
        "uniquely_joinable": sum(m["candidate_count"] == 1 for m in matches),
        "ambiguous": sum(m["candidate_count"] > 1 for m in matches),
        "unmatched": sum(m["candidate_count"] == 0 for m in matches),
        "all_step_key_sets_consistent": all(x["consistent"] for x in set_checks),
        "inconsistent_step_key_sets": sum(not x["consistent"] for x in set_checks),
        "checked_hold_steps": len(set_checks),
        "ambiguity_counterexample": ambiguous_fixture,
        "limits": ["Temporal/key-set candidates are not event identity.", "Set-level consistency does not establish row pairing.", "No undocumented serial-order invariant is assumed.", "No physical occupancy, task effect, causal attribution, or live result is inferred."],
        "admissions": matches,
        "step_set_checks": set_checks,
    }
    out = (json.dumps(result, indent=2, sort_keys=True) + "\n").encode()
    (PKG / "RESULT.json").write_bytes(out)
    print(json.dumps({k: result[k] for k in ["schema", "status", "counts", "candidate_count_histogram", "uniquely_joinable", "ambiguous", "unmatched", "all_step_key_sets_consistent", "inconsistent_step_key_sets", "checked_hold_steps", "ambiguity_counterexample"]}, indent=2))


if __name__ == "__main__":
    main()
