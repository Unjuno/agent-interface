import json
from pathlib import Path
FIXTURE=json.loads(Path(__file__).with_name("fixture.json").read_text(encoding="utf-8"))
