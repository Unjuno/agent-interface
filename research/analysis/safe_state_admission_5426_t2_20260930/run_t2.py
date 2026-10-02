"""One-shot deterministic candidate runner for Issue #5426 T2."""
import json
from pathlib import Path
from scenarios import SCENARIOS
from simulator import run_suite

ROOT = Path(__file__).parent
OUT = ROOT / "results" / "t2-01" / "raw.json"


def main():
    if OUT.exists():
        raise SystemExit(f"output already exists: {OUT}")
    OUT.parent.mkdir(parents=True, exist_ok=False)
    raw = run_suite(SCENARIOS)
    OUT.write_text(json.dumps(raw, sort_keys=True, separators=(",", ":")) + "\n",
                   encoding="utf-8")
    print(json.dumps({"status": "EXECUTED", "rows": len(raw["rows"]),
                      "scenarios": len(SCENARIOS), "policies": len(raw["policies"]),
                      "raw_path": str(OUT.relative_to(ROOT))}, sort_keys=True))


if __name__ == "__main__":
    main()
