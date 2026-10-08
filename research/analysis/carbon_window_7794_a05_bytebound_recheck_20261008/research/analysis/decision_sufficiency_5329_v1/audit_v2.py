"""Post-hoc raw-only audit successor fixing v1's no-op mutation target."""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import independent_audit as v1  # independent of candidate analyze.py; retains the v1 oracle verbatim

ROOT = Path(__file__).resolve().parent


def run(raw_path: Path) -> dict:
    traces = json.loads((ROOT / "traces.json").read_text(encoding="utf-8"))["traces"]
    raw = json.loads(raw_path.read_text(encoding="utf-8"))
    errors = v1.check(raw, traces)
    controls = []
    mutations = [
        ("drop_row", lambda x: x["rows"].pop()),
        ("force_release_pass", lambda x: next(r for r in x["rows"] if r["consumer"] == "RELEASE_GATE" and r["decision"] != "PASS").update(decision="PASS")),
        ("corrupt_bytes", lambda x: x["rows"][0].update(bytes=-1)),
        ("erase_required_field", lambda x: x["rows"][20].update(fields=[])),
    ]
    for name, mutate in mutations:
        changed = copy.deepcopy(raw)
        mutate(changed)
        controls.append({"name": name, "rejected": bool(v1.check(changed, traces))})
    stats = raw.get("summary", {})
    gate = (
        stats.get("DECISION_SUFFICIENT", {}).get("decision_mismatches") == 0
        and stats.get("DECISION_SUFFICIENT", {}).get("bytes", 10**9) < stats.get("RAW_TRACE", {}).get("bytes", 0)
        and stats.get("LABEL_ONLY", {}).get("unsafe_passes", 0) > 0
        and stats.get("ADVERSARIAL_COMPRESSION", {}).get("decision_mismatches", 0) > 0
        and not errors and all(c["rejected"] for c in controls)
    )
    return {"audit": "issue_5329_v2_raw_only_mutation_target_correction", "raw_sha256_expected": "ABBFD07E541DAE643EAC7FE42DD630B1A55CCDA75A52C66444A35CC1CC4AD705",
            "row_count": len(raw.get("rows", [])), "errors": errors, "controls": controls,
            "all_controls_rejected": all(c["rejected"] for c in controls),
            "disposition": "PASS_FINITE_CONTRACT_ONLY" if gate else "FAIL_OR_UNCERTAIN", "summary": stats}


if __name__ == "__main__":
    print(json.dumps(run(Path(sys.argv[1])), sort_keys=True, indent=2))
