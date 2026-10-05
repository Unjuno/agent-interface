#!/usr/bin/env python3
"""Render immutable formal outputs into a concise report and checksum list."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    run_path = RESULTS / "RUN.json"
    run = json.loads(run_path.read_text())
    report = ["# Issue #8152 T0 formal result", "", f"Base commit: `{run['base_commit']}`",
              f"Container image: `{run['image']}`", ""]
    audit_path = RESULTS / "AUDIT.json"
    if not audit_path.exists() or audit_path.stat().st_size == 0:
        report.extend(["Disposition: `STOP_NO_AUDIT`", "", "The candidate container did not produce an auditable completed result. No retry was performed."])
    else:
        audit = json.loads(audit_path.read_text())
        disposition = "STOP_CANDIDATE_NONZERO" if run.get("candidate_exit_code", 0) != 0 else audit["disposition"]
        report.extend([f"Disposition: `{disposition}`",
                       f"Audited method disposition: `{audit['disposition']}`.", "",
                       f"Raw audit valid: `{audit['valid']}`; auditor errors: `{len(audit['errors'])}`.", "",
                       "## Method metrics", "",
                       "| Method | Search queries | Shorter instances | Held-out NI instances |", "|---|---:|---:|---:|"])
        for method, data in audit["method_decisions"].items():
            ni = sum(item["noninferiority"] for item in data["instances"])
            report.append(f"| {method} | {data['search_queries']} | {data['shorter_instances']} | {ni}/{len(data['instances'])} |")
        report.extend(["", "## Auditor disposition details", ""])
        if audit["errors"]:
            report.extend(["Auditor errors:", ""] + [f"- `{item}`" for item in audit["errors"]])
        else:
            report.append(f"Sequential query advantage over fixed-64: `{audit['sequential_query_advantage']}`.")
        report.extend(["", "## Scope", "",
                       "Synthetic stationary hash-oracle experiment only. No live failure, GUI, model, or user data was used. A method-scoped PASS is not evidence of production reliability, causal root cause, general minimality, or deployment safety."])
    (RESULTS / "REPORT.md").write_text("\n".join(report) + "\n")
    names = ["RUN.json", "candidate.raw.json", "candidate.log", "AUDIT.json", "audit.log", "REPORT.md"]
    lines = [f"{digest(RESULTS/name)}  {name}" for name in names if (RESULTS/name).is_file()]
    lines.append(f"{digest(ROOT/'FREEZE.json')}  ../FREEZE.json")
    (RESULTS / "SHA256SUMS").write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
