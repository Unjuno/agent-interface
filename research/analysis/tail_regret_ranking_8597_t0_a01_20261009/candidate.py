"""Candidate exports the finite visible action grid; it never reads oracle truth."""
import argparse
import json
from pathlib import Path


def run(visible):
    rows = []
    for opportunity in visible["assigned_opportunities"]:
        for tick in opportunity["ticks"]:
            rows.append({
                "opportunity_id": opportunity["opportunity_id"],
                "stratum": opportunity["stratum"],
                "cluster": opportunity["cluster"],
                **tick,
            })
    return {"schema": "tail-regret-8597-candidate-raw-v1", "rows": rows}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dir", type=Path, default=Path(__file__).parent)
    root = parser.parse_args().dir
    visible = json.loads((root / "visible.json").read_text())
    raw = run(visible)
    (root / "candidate_raw.json").write_text(json.dumps(raw, indent=2, sort_keys=True) + "\n")
    print(f"CANDIDATE_COMPLETE opportunities={len(visible['assigned_opportunities'])} rows={len(raw['rows'])}")


if __name__ == "__main__":
    main()
