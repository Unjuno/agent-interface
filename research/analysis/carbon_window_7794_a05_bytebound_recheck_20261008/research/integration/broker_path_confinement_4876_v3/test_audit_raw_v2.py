"""Posthoc audit mutation controls on copies; never touches formal raw."""
from __future__ import annotations
import copy
import json
import sys
from pathlib import Path
from audit_raw_v2 import audit_payload

def main(raw_path: Path, out: Path) -> int:
    original = json.loads(raw_path.read_text(encoding="utf-8"))
    mutations = []
    def record(name, mutate):
        candidate = copy.deepcopy(original)
        mutate(candidate)
        mutations.append({"name": name, "rejected": bool(audit_payload(candidate))})
    record("missing_case", lambda r: r["cases"].pop())
    record("accepted_path_escape", lambda r: r["cases"][0].update(actual="/outside/schema.json"))
    record("rejected_case_target", lambda r: r["cases"][4].update(actual="/outside/secret"))
    record("extra_case", lambda r: r["cases"].append(copy.deepcopy(r["cases"][0])))
    record("duplicate_subprocess", lambda r: r.update(subprocess_calls=2))
    record("authority_flip", lambda r: r.update(authority_granted=True))
    result = {
        "schema": "broker-path-confinement-4876-audit-v2-corruption-controls",
        "controls": mutations,
        "rejected": sum(x["rejected"] for x in mutations),
        "total": len(mutations),
        "decision": "PASS_CORRUPTION_CONTROLS" if all(x["rejected"] for x in mutations) else "FAIL_CORRUPTION_CONTROLS",
    }
    out.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0 if result["rejected"] == result["total"] else 1

if __name__ == "__main__":
    raise SystemExit(main(Path(sys.argv[1]), Path(sys.argv[2])))

