from __future__ import annotations

import json
import sys
from pathlib import Path

from posthoc_audit import review

result = review(Path(sys.argv[1]))
Path(sys.argv[2]).write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
print(json.dumps(result, sort_keys=True))
