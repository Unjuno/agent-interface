import json
import sys


payload = {
    "schema": "gpu-diagnostic-raw-v1",
    "complete": True,
    "rows": [{"case": "synthetic-publication-control", "value": 7}],
}
sys.stdout.write(json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n")

