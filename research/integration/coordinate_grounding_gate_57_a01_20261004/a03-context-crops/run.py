from __future__ import annotations
import json
from pathlib import Path
from candidate import run_experiment

HERE=Path(__file__).resolve().parent
result=run_experiment()
(HERE/"RESULT.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
print(json.dumps({"status":"A03_CONTEXT_CROP_REPLAY_RETAINED",**result["summary"]},sort_keys=True))
