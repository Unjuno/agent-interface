#!/usr/bin/env python3
"""In-memory construction check; does not invoke the one-shot CLI or write raw."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import audit
import candidate

fixture = json.loads((HERE / "fixture.json").read_text(encoding="utf-8"))
digest = hashlib.sha256((HERE / "fixture.json").read_bytes()).hexdigest()
raw = candidate.build_raw(fixture, digest)
result = audit.audit(raw, fixture, digest)
controls = audit.mutations(raw, fixture, digest)
if not result["valid"] or controls["rejected"] != controls["total"]:
    print(json.dumps({"audit_errors": result["errors"], "mutation_controls": controls}, sort_keys=True))
    raise SystemExit(1)
print(json.dumps({"construction_only": True, "candidate_cli_invocations": 0,
                  "auditor_cli_invocations": 0, "rows_reconstructed": result["rows_reconstructed"],
                  "competing_fingerprint_rows": result["competing_fingerprint_rows"],
                  "pooled_false_assurance_cases": result["pooled_false_assurance_cases"],
                  "mutation_controls_rejected": controls["rejected"],
                  "mutation_controls_total": controls["total"]}, sort_keys=True))
