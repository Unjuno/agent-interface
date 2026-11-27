from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parent
REPO = "Unjuno/agent-interface"
ISSUE_ROUTE = f"repos/{REPO}/issues?state=open&per_page=100"
PR_ROUTE = f"repos/{REPO}/pulls?state=open&per_page=100"
ISSUE_JQ = ".[] | select(has(\"pull_request\") | not) | .number"
PR_JQ = ".[] | .number"


def api_sha() -> str:
    return subprocess.run(
        ["gh", "api", f"repos/{REPO}/commits/main", "--jq", ".sha"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def ids(route: str, jq: str, raw_name: str) -> list[int]:
    result = subprocess.run(
        ["gh", "api", "--paginate", "--jq", jq, route],
        check=True,
        capture_output=True,
        text=True,
    )
    (ROOT / raw_name).write_text(result.stdout, encoding="utf-8", newline="")
    values = sorted({int(line) for line in result.stdout.splitlines() if line.strip()})
    return values


def compact_hash(values: list[int]) -> str:
    encoded = json.dumps(values, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


started = datetime.now(timezone.utc)
main_before = api_sha()
issue_ids = ids(ISSUE_ROUTE, ISSUE_JQ, "repository-inventory-recheck-20261123-r173.raw_issue_ids.txt")
pr_ids = ids(PR_ROUTE, PR_JQ, "repository-inventory-recheck-20261123-r173.raw_pr_ids.txt")
main_after = api_sha()
finished = datetime.now(timezone.utc)

prior = json.loads((ROOT / "repository-inventory-recheck-20261123-r172.json").read_text())
prior_issues = set(prior["open_issue_ids"])
prior_prs = set(prior["open_pull_request_ids"])
current_issues = set(issue_ids)
current_prs = set(pr_ids)

receipt = {
    "checkpoint": "r173",
    "captured_at_start_utc": started.isoformat().replace("+00:00", "Z"),
    "captured_at_end_utc": finished.isoformat().replace("+00:00", "Z"),
    "main_before": main_before,
    "main_after": main_after,
    "source": "Complete GitHub REST pagination with gh api --paginate; open issue endpoint excludes pull_request objects; open pull endpoint; per_page=100",
    "open_issue_count": len(issue_ids),
    "open_pull_request_count": len(pr_ids),
    "comparison_baseline": "r172",
    "issue_added": sorted(current_issues - prior_issues),
    "issue_removed": sorted(prior_issues - current_issues),
    "pull_request_added": sorted(current_prs - prior_prs),
    "pull_request_removed": sorted(prior_prs - current_prs),
    "current_sorted_ids_sha256": {
        "algorithm": "SHA-256 over UTF-8 compact JSON arrays of numerically sorted integer IDs",
        "open_issues": compact_hash(issue_ids),
        "open_pull_requests": compact_hash(pr_ids),
    },
    "open_issue_ids": issue_ids,
    "open_pull_request_ids": pr_ids,
}
(ROOT / "repository-inventory-recheck-20261123-r173.json").write_text(
    json.dumps(receipt, indent=2) + "\n", encoding="utf-8", newline=""
)

stable = main_before == main_after
body = [
    "# Whole-repository membership recheck r173 — 2026-11-23 UTC",
    "",
    f"Complete GitHub REST pagination returned {len(issue_ids)} open Issues and {len(pr_ids)} open PRs.",
    f"The main ref was `{main_before}` before and `{main_after}` after the paginated reads ({'stable' if stable else 'changed during reads'}).",
    "",
    f"Compared with r172, Issue additions: {receipt['issue_added'] or 'none'}; removals: {receipt['issue_removed'] or 'none'}.",
    f"PR additions: {receipt['pull_request_added'] or 'none'}; removals: {receipt['pull_request_removed'] or 'none'}.",
    "Exact sorted ID arrays, API-derived ID lines, and reproducible SHA-256 hashes are stored in the [r173 JSON](repository-inventory-recheck-20261123-r173.json).",
    "",
    "The predecessor r172 Markdown receipt contained literal `$mainBefore` / `$mainAfter` placeholders; its JSON records `b600070965c48cc9449a87ff31264a5b3604c2d8`, and this recheck confirms the current main ref independently.",
    "",
    "This is membership evidence only, not semantic triage, merge readiness, or repository cleanliness. Family-by-family disposition and worktree/output custody remain open; see the [project organization plan](../REPOSITORY_ORGANIZATION_PLAN.md).",
]
(ROOT / "repository-inventory-recheck-20261123-r173.md").write_text(
    "\n".join(body) + "\n", encoding="utf-8", newline=""
)

manifest_entries = []
for name in (
    "repository-inventory-recheck-20261123-r173.py",
    "repository-inventory-recheck-20261123-r173.md",
    "repository-inventory-recheck-20261123-r173.json",
    "repository-inventory-recheck-20261123-r173.raw_issue_ids.txt",
    "repository-inventory-recheck-20261123-r173.raw_pr_ids.txt",
):
    path = ROOT / name
    manifest_entries.append(f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {name}")
(ROOT / "repository-inventory-recheck-20261123-r173.SHA256SUMS.txt").write_text(
    "\n".join(manifest_entries) + "\n", encoding="ascii", newline=""
)
print(json.dumps({key: receipt[key] for key in (
    "captured_at_start_utc", "captured_at_end_utc", "main_before", "main_after",
    "open_issue_count", "open_pull_request_count", "issue_added", "issue_removed",
    "pull_request_added", "pull_request_removed", "current_sorted_ids_sha256"
)}, indent=2))
