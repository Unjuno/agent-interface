"""Apply the in-memory source-instrumentation scope to the shared raw audit."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, "/")
import audit

raw_path = Path(sys.argv[1])
out_path = Path(sys.argv[2])
report = audit.audit(raw_path)
report["schema"] = "source-instrumented-viz-tic-entry-inmemory-audit-v1"
report["limitations"] = [
    "The direct CLOCK_MONOTONIC call is the first C statement in VIZ_Tic after compiler-generated function prologue; the true machine function-entry-to-clock-sample latency is not independently bounded.",
    "Each tic performs a clock read and in-memory record/index writes; records are flushed in one write sequence only when the engine process exits. This remains instrumented scheduling, not an unmodified engine distribution.",
    "CLOCK_MONOTONIC is shared across processes on this Linux fixture; no portability or hard-real-time claim follows.",
    "Three construction sessions do not fill the frozen 120-row schedule and do not authorize formal collection.",
]
out_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
print(json.dumps({"decision": report["decision"], "errors": report["errors"],
                  "formal_allocation": False, "rows": len(report["rows"])}, sort_keys=True))
raise SystemExit(bool(report["errors"]))
