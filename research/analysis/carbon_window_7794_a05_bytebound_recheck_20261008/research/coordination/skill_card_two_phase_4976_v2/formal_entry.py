"""Single-invocation local container entrypoint for Issue #4998."""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path

SRC = Path("/src")
OUT = Path("/out")


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    raw = OUT / "raw.json"
    run = subprocess.run(
        [sys.executable, "-B", str(SRC / "runner.py"), str(raw)],
        cwd=SRC, env={"PATH": "/usr/local/bin:/usr/bin:/bin", "PYTHONDONTWRITEBYTECODE": "1"},
        capture_output=True, text=True, check=False,
    )
    (OUT / "runner.stdout").write_text(run.stdout, encoding="utf-8")
    (OUT / "runner.stderr").write_text(run.stderr, encoding="utf-8")
    (OUT / "runner.exit").write_text(f"{run.returncode}\n", encoding="ascii")

    spec = importlib.util.spec_from_file_location("independent_audit", SRC / "audit.py")
    audit_module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(audit_module)
    audit = audit_module.audit(raw, SRC) if run.returncode == 0 else {
        "schema": "issue-4998-independent-audit-v1", "pass": False,
        "errors": [f"runner_exit:{run.returncode}"]}
    mutations = {
        "remove_row": lambda p: p["rows"].pop(),
        "wrong_selected_key": lambda p: p["rows"][0].__setitem__("selected_key", "forged"),
        "preselection_detail_leak": lambda p: p["rows"][0].__setitem__("preselection_detail_loads", ["pointer_track_v2"]),
        "hint_event_reorder": lambda p: p["rows"][3]["events"].__setitem__(slice(1, 3), p["rows"][3]["events"][2:0:-1]),
        "receipt_provenance_tamper": lambda p: p["rows"][3]["revalidation_receipt"].__setitem__("source_provenance", "forged"),
        "negative_control_bypass": lambda p: p["negative_controls"][0].__setitem__("refused", False),
        "authority_side_effect": lambda p: p.__setitem__("authority_grants", 1),
        "source_hash_tamper": lambda p: p["source_hashes"].__setitem__("candidate.py", "0" * 64),
    }
    mutation_results = {}
    if run.returncode == 0 and raw.exists():
        pristine = json.loads(raw.read_text(encoding="utf-8"))
        for name, mutate in mutations.items():
            with tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                (root / "src").mkdir()
                for source in SRC.iterdir():
                    if source.is_file():
                        (root / "src" / source.name).write_bytes(source.read_bytes())
                mutated = json.loads(json.dumps(pristine))
                mutate(mutated)
                candidate_raw = root / "raw.json"
                candidate_raw.write_text(json.dumps(mutated), encoding="utf-8")
                result = audit_module.audit(candidate_raw, root / "src")
                mutation_results[name] = {"rejected": result["pass"] is False,
                                          "errors": result["errors"]}
    report = {
        "schema": "issue-4998-formal-result-v1", "runner_exit": run.returncode,
        "audit": audit, "mutation_controls": mutation_results,
        "mutations_rejected": sum(item["rejected"] for item in mutation_results.values()),
        "mutations_total": len(mutations),
        "decision": "PASS_TWO_PHASE_SKILL_SELECTION_CONSTRUCTION_SCOPED"
        if run.returncode == 0 and audit.get("pass") and all(x["rejected"] for x in mutation_results.values())
        else "FAIL_OR_STOP_AUDIT",
        "scope": "synthetic eight-case caller-boundary construction only; no model, GUI, action, or authority",
    }
    (OUT / "audit.json").write_text(json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"decision": report["decision"], "runner_exit": run.returncode,
                      "audit_pass": audit.get("pass"), "mutations_rejected": report["mutations_rejected"],
                      "mutations_total": report["mutations_total"]}, sort_keys=True))
    return 0 if report["decision"].startswith("PASS_") else 1


if __name__ == "__main__":
    raise SystemExit(main())
