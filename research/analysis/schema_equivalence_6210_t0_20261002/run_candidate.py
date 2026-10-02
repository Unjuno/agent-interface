#!/usr/bin/env python3
"""One-shot finite schema-surface candidate; writes only a fresh result path."""
import hashlib
import json
from pathlib import Path

from candidate import SURFACES, boundary_profile, certify_surfaces, execute_case, expand_calls, load_fixture

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "results" / "t0-01" / "raw.json"


def main():
    if OUTPUT.exists():
        raise SystemExit("STOP_OUTPUT_EXISTS")
    fixture_bytes = (ROOT / "fixture.json").read_bytes()
    fixture = json.loads(fixture_bytes)
    candidate_bytes = (ROOT / "candidate.py").read_bytes()
    decisions = certify_surfaces(fixture)
    rows = []
    for surface_id, surface in SURFACES.items():
        for case in fixture["cases"]:
            rows.append({
                "surface_id": surface_id,
                "case_id": case["id"],
                "input": {
                    surface["target_field"]: case["target_id"],
                    surface["epoch_field"]: case["evidence_epoch"],
                    "cancel_after_type": case["cancel_after_type"],
                },
                "tool_calls": surface["calls"],
                "boundary_profile": boundary_profile(surface),
                "expanded_primitives": expand_calls(surface),
                **execute_case(case, surface, fixture["context"]),
                "certified_equivalent": decisions[surface_id],
                "authority_granted": False,
            })
    raw = {
        "schema": "schema-equivalence-raw-v1",
        "allocation": fixture["allocation"],
        "source_main": fixture["source_main"],
        "fixture_sha256": hashlib.sha256(fixture_bytes).hexdigest(),
        "candidate_sha256": hashlib.sha256(candidate_bytes).hexdigest(),
        "surface_decisions": decisions,
        "rows": rows,
        "assertion_scope": "finite synthetic transition semantics and checkpoints; no model or runtime",
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=False)
    data = json.dumps(raw, sort_keys=True, separators=(",", ":")) + "\n"
    OUTPUT.write_text(data, encoding="utf-8")
    print(json.dumps({
        "status": "CANDIDATE_COMPLETE",
        "rows": len(rows),
        "certified_equivalent": [name for name, accepted in decisions.items() if accepted],
        "rejected": [name for name, accepted in decisions.items() if not accepted],
        "raw_sha256": hashlib.sha256(OUTPUT.read_bytes()).hexdigest(),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
