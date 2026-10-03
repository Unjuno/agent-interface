from __future__ import annotations

import json
from pathlib import Path

from auditor import audit
from scorer import score_all

root = Path("/study")
out = Path("/out")
out.mkdir(parents=True, exist_ok=True)
stimuli = json.loads((root / "stimuli.json").read_text())
truth = json.loads((root / "truth.json").read_text())
material = json.loads((Path("/candidate") / "material.json").read_text())
truth_by_id = {}
for event in stimuli["events"]:
    item = {**truth["default"], **truth["overrides"].get(event["id"], {})}
    item.setdefault("onset_ms", event["time_ms"])
    item.setdefault("expiry_ms", event["time_ms"] + stimuli["response_window_ms"])
    truth_by_id[event["id"]] = item
scored = score_all(material["rows"], truth_by_id, truth["scoring_vectors"])
result = audit(stimuli, truth, material, scored)
(out / "scored.json").write_text(json.dumps(scored, sort_keys=True, indent=2) + "\n")
(out / "audit.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
print(json.dumps(result, sort_keys=True))
raise SystemExit(0 if result["status"] == "PASS_METHOD_SCOPED" else 1)
