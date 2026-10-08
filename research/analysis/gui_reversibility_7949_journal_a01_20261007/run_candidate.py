import json
from pathlib import Path

import candidate

ROOT = Path(__file__).parent
CASES = [
    ("baseline", "none"), ("disjoint_write", "disjoint_y"),
    ("same_field_write", "same_x"), ("missing_journal", "missing_row"),
    ("sequence_gap", "sequence_gap"), ("journal_state_mismatch", "tampered_value"),
]

def main():
    out = ROOT / "results"
    db = out / "db"
    db.mkdir(parents=True, exist_ok=True)
    rows = [candidate.run_case({"id": cid, "external_write": mode}, db) for cid, mode in CASES]
    (out / "candidate.raw.json").write_text(json.dumps({"cases": rows}, sort_keys=True, indent=2) + "\n")

if __name__ == "__main__":
    main()
