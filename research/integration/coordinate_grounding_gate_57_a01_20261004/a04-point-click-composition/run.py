from __future__ import annotations

import json
from pathlib import Path

from candidate import run_composition


HERE = Path(__file__).resolve().parent
result = run_composition()
(HERE / "RESULT.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps({"status": "A04_POINT_CLICK_COMPOSITION_RETAINED",
                  "accepted": sum(row["accepted"] for row in result["cases"]),
                  "proposals": len(result["cases"]),
                  "inert_refusals": sum(not row["accepted"] for row in result["negative_cases"].values()) +
                                      sum(not row["accepted"] for row in result["ineligible_cases"].values()),
                  "input_dispatch_count": result["input_dispatch_count"]}, sort_keys=True))
