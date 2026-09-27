#!/usr/bin/env python3
"""Protocol smoke controller. It intentionally does nothing except advance one tick."""
import json, sys
for line in sys.stdin:
    obs = json.loads(line)
    if obs.get("done"):
        print(json.dumps({"commands": []}), flush=True)
        break
    print(json.dumps({"commands": ["STEP 1"]}), flush=True)
