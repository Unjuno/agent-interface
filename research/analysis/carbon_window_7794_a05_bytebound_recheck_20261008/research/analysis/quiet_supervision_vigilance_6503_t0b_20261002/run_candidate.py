from __future__ import annotations

import json
from pathlib import Path

from candidate import build

root = Path(__file__).resolve().parent
out = Path("/out")
out.mkdir(parents=True, exist_ok=True)
stimuli = json.loads((root / "stimuli.json").read_text())
material = build(stimuli)
(out / "material.json").write_text(json.dumps(material, sort_keys=True, indent=2) + "\n")
print(json.dumps({"status":"MATERIAL_BUILT","rows":len(material["rows"]),"allocation":material["allocation"]}, sort_keys=True))
