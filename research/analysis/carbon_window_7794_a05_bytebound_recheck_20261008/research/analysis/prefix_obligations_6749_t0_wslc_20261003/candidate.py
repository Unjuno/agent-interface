"""Candidate enumerator. The independent auditor must not import this module."""
import json
import sys
from collections import Counter
from pathlib import Path

from contract import all_prefixes


def build_raw():
    rows = all_prefixes()
    counts = Counter(row["disposition"] for row in rows)
    early = Counter()
    for row in rows:
        if row["disposition"] in ("STABLE_FAIL", "PASS"):
            early[row["disposition"].lower() + "_prefixes"] += 1
    return {"schema": "prefix-obligations-6749-raw-v1", "rows": rows,
            "disposition_counts": dict(sorted(counts.items())),
            "early_finalization_metrics": dict(sorted(early.items()))}


def main():
    destination = Path(sys.argv[1])
    if destination.exists():
        raise SystemExit("refusing to overwrite candidate raw")
    destination.parent.mkdir(parents=True, exist_ok=True)
    raw = build_raw()
    destination.write_text(json.dumps(raw, sort_keys=True, separators=(",", ":")) + "\n",
                           encoding="utf-8")
    print(json.dumps({"rows": len(raw["rows"]), "output": str(destination)}, sort_keys=True))


if __name__ == "__main__":
    main()
