"""Run five declared post-formal mutations against a copy of raw evidence."""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

from .audit import verify


def main() -> int:
    source, destination = map(Path, sys.argv[1:3])
    raw = json.loads(source.read_text(encoding="utf-8"))
    cases = {
        "omitted_row": lambda x: x["rows"].pop(),
        "swapped_direction": lambda x: x["rows"].__setitem__(slice(1, 3), reversed(x["rows"][1:3])),
        "wrong_expected_bytes": lambda x: x["rows"][1].__setitem__("expected_effect_hex", "00"),
        "absent_actor_receipt": lambda x: x["rows"][1].__setitem__("actor_receipt", None),
        "changed_raw_output": lambda x: x["rows"][2].__setitem__("saved_effect_hex", "00"),
    }
    results = []
    for name, mutate in cases.items():
        candidate = copy.deepcopy(raw)
        mutate(candidate)
        try:
            decision = verify(candidate)
            rejected = decision not in {"NO_STALE_EFFECT_OBSERVED", "PASS_MIDPROGRAM_REMAP_FAIL_CLOSED"}
            reason = decision
        except Exception as exc:
            rejected, reason = True, repr(exc)
        results.append({"case": name, "rejected": rejected, "reason": reason})
    report = {"cases": results, "passed": sum(bool(r["rejected"]) for r in results), "total": len(results)}
    destination.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, sort_keys=True))
    return 0 if report["passed"] == report["total"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
