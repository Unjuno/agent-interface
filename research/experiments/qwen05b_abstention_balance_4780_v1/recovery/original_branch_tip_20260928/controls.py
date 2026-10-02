"""Independent evidence-mutation controls for audit_raw.py."""
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path

from audit_raw import audit


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True)
    parser.add_argument("--data", required=True)
    parser.add_argument("--results", required=True)
    parser.add_argument("--audit-out", required=True)
    args = parser.parse_args()
    source, results, audit_output = Path(args.source), Path(args.results), Path(args.audit_out)
    freeze = json.loads((source / "FREEZE.json").read_text(encoding="utf-8"))
    data_bytes = Path(args.data).read_bytes()
    orchestration = json.loads((results / "ORCHESTRATION.json").read_text(encoding="utf-8"))
    orchestration["out_dir"] = str(results)
    raw = {
        "base": json.loads((results / "base-raw.json").read_text(encoding="utf-8")),
        "imbalanced": json.loads((results / "imbalanced-raw.json").read_text(encoding="utf-8")),
        "balanced": json.loads((results / "balanced-raw.json").read_text(encoding="utf-8")),
    }
    controls = []
    mutations = []
    missing = copy.deepcopy(raw)
    missing["balanced"]["results"].pop()
    mutations.append(("remove_heldout_row", data_bytes, missing))
    wrong_id = copy.deepcopy(raw)
    wrong_id["imbalanced"]["results"][0]["case_id"] = "forged-case"
    mutations.append(("alter_case_identity", data_bytes, wrong_id))
    wrong_text = copy.deepcopy(raw)
    wrong_text["balanced"]["results"][0]["raw_text"] += " INVALID-CORRUPTION"
    mutations.append(("alter_raw_model_text", data_bytes, wrong_text))
    wrong_binding = copy.deepcopy(raw)
    wrong_binding["balanced"]["results"][0]["bound"] = {
        "status": "BOUND", "name": "CLICK",
        "arguments": {"scope_id": "forged-scope", "generation": -1, "target": "forged"},
    }
    mutations.append(("forge_trusted_binding", data_bytes, wrong_binding))
    wrong_effect = copy.deepcopy(raw)
    wrong_effect["balanced"]["results"][0]["effect"] = {"changed": True, "kind": "forged"}
    mutations.append(("alter_simulated_effect", data_bytes, wrong_effect))
    for name, payload, docs in mutations:
        report = audit(payload, docs, freeze, orchestration, source)
        rejected = bool(report["errors"]) and report["disposition"] == "STOP_RAW_AUDIT_OR_PROVENANCE"
        controls.append({"name": name, "rejected": rejected, "errors": report["errors"][:12]})
    result = {
        "schema": "qwen05b-abstention-balance-corruption-controls-v1",
        "passed": sum(c["rejected"] for c in controls),
        "total": len(controls),
        "pass": all(c["rejected"] for c in controls),
        "controls": controls,
    }
    (audit_output / "CONTROL_RESULTS.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    audit_path = audit_output / "AUDIT.json"
    if audit_path.exists():
        report = json.loads(audit_path.read_text(encoding="utf-8"))
        report["gates"]["corruption_controls"] = result["pass"] and result["passed"] == 5
        if not report["gates"]["corruption_controls"]:
            report["integrity_pass"] = False
            report["errors"].append("corruption_controls")
            report["disposition"] = "STOP_RAW_AUDIT_OR_PROVENANCE"
        audit_path.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
