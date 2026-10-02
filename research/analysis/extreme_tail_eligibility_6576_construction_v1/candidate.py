"""Run one deterministic gate-construction candidate over frozen cases."""

import hashlib
import json
import sys
from pathlib import Path

from research.analysis.extreme_tail_eligibility_6576_construction_v1.gate import decide


def main() -> int:
    source = Path(sys.argv[1])
    target = Path(sys.argv[2])
    raw = source.read_bytes()
    cases = json.loads(raw)
    output = {
        "input_sha256": hashlib.sha256(raw).hexdigest(),
        "rows": [
            {"case_id": case["case_id"], "decision": decide(case)}
            for case in cases
        ],
    }
    target.write_text(json.dumps(output, sort_keys=True, separators=(",", ":")) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
