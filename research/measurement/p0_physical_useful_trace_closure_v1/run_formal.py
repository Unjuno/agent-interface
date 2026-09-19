from __future__ import annotations
import json
from pathlib import Path
from common import load_fixture,evaluate
HERE=Path(__file__).resolve().parent
OUT=HERE/'RESULT.json'
if OUT.exists(): raise RuntimeError('RESULT exists; rerun forbidden')
r=evaluate(load_fixture()); OUT.write_text(json.dumps(r,indent=2,sort_keys=True)+'\n'); print(json.dumps(r,sort_keys=True))
