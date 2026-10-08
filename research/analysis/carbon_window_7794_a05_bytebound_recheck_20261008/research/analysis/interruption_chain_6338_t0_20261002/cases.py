"""Construction-only loader used by unit tests, not included in formal run."""
import json
from pathlib import Path
CASES = json.loads(Path(__file__).with_name("cases.json").read_text(encoding="utf-8"))
