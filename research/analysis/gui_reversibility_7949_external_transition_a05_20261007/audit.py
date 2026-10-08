"""One-shot audit of frozen candidate bytes."""
import hashlib
import json
from pathlib import Path
from audit_core import verify

ROOT = Path(__file__).parent
model = json.loads((ROOT / "model.json").read_text(encoding="utf-8"))
raw_bytes = (ROOT / "results/candidate.raw.json").read_bytes()
raw = json.loads(raw_bytes)
errors = verify(model, raw)
assert not errors, errors
audit = {"run_id": raw["run_id"], "disposition": "PASS_EXTERNAL_TRANSITION_SCOPE",
         "case_count": len(raw["cases"]), "errors": errors,
         "candidate_sha256": hashlib.sha256(raw_bytes).hexdigest()}
(ROOT / "results/audit.json").write_text(json.dumps(audit, sort_keys=True, indent=2) + "\n", encoding="utf-8")
print(json.dumps(audit, sort_keys=True, indent=2))
