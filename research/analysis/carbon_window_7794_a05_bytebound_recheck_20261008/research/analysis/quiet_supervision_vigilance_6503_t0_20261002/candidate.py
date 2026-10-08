"""Deterministic construction of a finite, no-participant opportunity ledger."""
from __future__ import annotations

import hashlib
import json


def build(fixture: dict) -> list[dict]:
    rows = []
    for block in fixture["blocks"]:
        for index, stimulus in enumerate(fixture["opportunities_per_block"]):
            token = hashlib.sha256(f"{fixture['allocation']}:{block}:{index}".encode()).hexdigest()[:12]
            for display in fixture["displays"]:
                rows.append({
                    "opportunity_token": token,
                    "block": block,
                    "display": display,
                    "stimulus": stimulus["stimulus"],
                    "display_visibility": stimulus["display_visibility"],
                    "available_evidence": stimulus["available_evidence"],
                    "checkpoint": display == "MATCHED_CHECKPOINT",
                    "machine_hard_stop": dict(fixture["hard_stop"]),
                    "human_response": None,
                })
    return rows


def main() -> None:
    from pathlib import Path
    root = Path(__file__).parent
    fixture = json.loads((root / "fixture.json").read_text())
    rows = build(fixture)
    out = root / "results" / "t0-01"
    out.mkdir(parents=True, exist_ok=True)
    (out / "RAW.json").write_text(json.dumps(rows, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": "CONSTRUCTED", "rows": len(rows), "allocation": fixture["allocation"]}, sort_keys=True))


if __name__ == "__main__":
    main()
