"""Read-only verifier for the V39 context/release A01 saved result."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import subprocess


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
FREEZE = json.loads((ROOT / "FREEZE.json").read_text(encoding="utf-8"))
EXPECTED_REFS = {
    "base_main": FREEZE["base_main"],
    "pr_7602": FREEZE["components"]["pr_7602"],
    "pr_7750": FREEZE["components"]["pr_7750"],
    "pr_7769": FREEZE["components"]["pr_7769"],
}
REFS = {
    "base_main": "origin/main",
    "pr_7602": "refs/remotes/pr/7602",
    "pr_7750": "refs/remotes/pr/7750",
    "pr_7769": "refs/remotes/pr/7769",
}
LOGS = {
    "v39_typed_state": ("V39_TEST_OUTPUT.txt", 35),
    "owner_admission": ("OWNER_ADMISSION_TEST_OUTPUT.txt", 3),
    "cleanup_bridge": ("CLEANUP_BRIDGE_TEST_OUTPUT.txt", 3),
}


def git(*args: str) -> str:
    return subprocess.check_output(
        ["git", "-C", str(REPO), *args], text=True, encoding="utf-8"
    ).strip()


def main() -> int:
    checks: list[dict[str, object]] = []
    for key, ref in REFS.items():
        actual = git("rev-parse", ref)
        checks.append({"check": f"{key}_ref", "pass": actual == EXPECTED_REFS[key], "actual": actual})

    actual_tree = git("show", "-s", "--format=%T", FREEZE["synthetic_composition_commit"])
    checks.append({
        "check": "synthetic_tree",
        "pass": actual_tree == FREEZE["synthetic_composition_tree"],
        "actual": actual_tree,
    })

    composition = json.loads((ROOT / "COMPOSITION.json").read_text(encoding="utf-8"))
    for index, merge in enumerate(composition["merges"], start=1):
        actual_merge_tree = git("merge-tree", "--write-tree", *merge["parents"]).splitlines()[0]
        actual_commit_tree = git("show", "-s", "--format=%T", merge["commit"])
        checks.append({
            "check": f"merge_{index}_tree",
            "pass": actual_merge_tree == merge["tree"] == actual_commit_tree,
            "actual": actual_merge_tree,
        })

    source_hashes = json.loads((ROOT / "SOURCE_HASHES.json").read_text(encoding="utf-8"))
    for path, entry in source_hashes["files"].items():
        actual_blob = git("rev-parse", f"{FREEZE['synthetic_composition_tree']}:{path}")
        checks.append({
            "check": f"source_blob:{path}",
            "pass": actual_blob == entry["tree_blob"] == entry["exported_sha1"],
            "actual": actual_blob,
        })

    logs: dict[str, dict[str, object]] = {}
    for name, (filename, expected_count) in LOGS.items():
        path = ROOT / filename
        raw = path.read_bytes()
        output = raw.decode("utf-8-sig")
        match = re.search(r"Ran (\d+) tests? in [^\r\n]+", output)
        passed = bool(
            match
            and int(match.group(1)) == expected_count
            and re.search(r"(?m)^OK\s*$", output)
            and not re.search(r"(?m)^FAILED\b", output)
        )
        logs[name] = {
            "file": filename,
            "sha256": hashlib.sha256(raw).hexdigest(),
            "expected_tests": expected_count,
            "reported_tests": int(match.group(1)) if match else None,
            "pass": passed,
        }
        checks.append({"check": f"{name}_output", "pass": passed})

    result = json.loads((ROOT / "RESULT.json").read_text(encoding="utf-8"))
    checks.append({
        "check": "result_scope_and_count",
        "pass": (
            result.get("disposition") == "PASS_COMPOSITION_SCOPED"
            and result.get("total_focused_tests") == 41
            and len(result.get("focused_suites", [])) == 3
            and result.get("merge_conflicts") == 0
        ),
    })
    report = {
        "schema": "v39-context-release-composition-audit-v1",
        "disposition": "PASS_AUDIT" if all(item["pass"] for item in checks) else "FAIL_AUDIT",
        "checks": checks,
        "raw_outputs": logs,
    }
    (ROOT / "AUDIT.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if report["disposition"] == "PASS_AUDIT" else 1


if __name__ == "__main__":
    raise SystemExit(main())
