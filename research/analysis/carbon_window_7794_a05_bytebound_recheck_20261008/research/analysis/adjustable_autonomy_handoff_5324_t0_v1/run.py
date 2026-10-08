from __future__ import annotations

import json
import sys
from pathlib import Path

from .model import classify, run_matrix


def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit("usage: python -m research.analysis.adjustable_autonomy_handoff_5324_t0_v1.run OUTPUT_DIR")
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=False)
    rows = run_matrix()
    summary = {
        "main_sha": "e05cefde72a418e8574efddeae082de3490e5cd8",
        "rows": len(rows),
        "disposition": classify(rows),
        "metrics": [
            {k: row[k] for k in ("policy", "scenario", "authority_gap_ticks", "duplicate_owner_ticks", "lost_work", "false_success_claims")}
            for row in rows
        ],
    }
    (out / "raw.json").write_text(json.dumps({"summary": summary, "traces": rows}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
