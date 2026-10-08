#!/usr/bin/env python3
"""Image/proposer coverage diagnostics; no model calls or outcome selection."""
import json, hashlib
from pathlib import Path
from PIL import Image
from audit_model import selected_tile

ROOT=Path(__file__).resolve().parent
tasks=json.loads((ROOT/"candidate_inputs"/"task_prompts.json").read_text())
truth={x["case_id"]:x for x in json.loads((ROOT/"oracle"/"oracle_truth.json").read_text())}
rows=[]
for task in tasks:
    path=ROOT/"candidate_inputs"/"screens"/task["screen_file"]
    img=Image.open(path).convert("RGB"); tile=selected_tile(img); t=truth[task["case_id"]]
    b=t["target_box"]; missing=bool(b and tile!=t["target_panel"])
    rows.append({"case_id":task["case_id"],"sha256":hashlib.sha256(path.read_bytes()).hexdigest(),
                 "selected_tile":tile,"target_panel":t["target_panel"],"target_absent_from_crop":missing,
                 "source_size":list(img.size)})
assert len(rows)==8 and len({r["sha256"] for r in rows})==8
print(json.dumps({"rows":rows,"target_present_but_crop_missed":sum(r["target_absent_from_crop"] for r in rows)},sort_keys=True))
