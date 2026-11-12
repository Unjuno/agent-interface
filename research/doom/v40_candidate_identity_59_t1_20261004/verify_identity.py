"""Read-only source identity gate for the retained V40 T0 audit."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import sys


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
CANDIDATE = REPO / "research/doom/map01_overlap_controller_v40.py"
PRIOR = REPO / "research/doom/v39_unknown_source_stop_59_t0_20261004"
AUDIT = PRIOR / "audit.json"
README = PRIOR / "README.md"
EXPECTED_RE = re.compile(r"Candidate: `research/doom/map01_overlap_controller_v40\.py`, SHA-256 `([0-9a-f]{64})`\.")


def evaluate(candidate_sha: str, audit_sha: str, readme_sha: str) -> dict:
    matches = {
        "audit_matches_candidate": audit_sha == candidate_sha,
        "readme_matches_candidate": readme_sha == candidate_sha,
        "audit_matches_readme": audit_sha == readme_sha,
    }
    return {
        "schema": "v40-candidate-source-identity-result-v1",
        "candidate_sha256": candidate_sha,
        "committed_audit_candidate_sha256": audit_sha,
        "committed_readme_candidate_sha256": readme_sha,
        "checks": matches,
        "decision": "PASS_SOURCE_IDENTITY" if all(matches.values()) else "FAIL_SOURCE_IDENTITY",
        "scope": "source identity only; no behavioral or runtime validation",
    }


def main() -> int:
    candidate_sha = hashlib.sha256(CANDIDATE.read_bytes()).hexdigest()
    audit_sha = json.loads(AUDIT.read_text(encoding="utf-8"))["candidate_sha256"]
    match = EXPECTED_RE.search(README.read_text(encoding="utf-8"))
    if match is None:
        raise ValueError("candidate SHA-256 claim not found in predecessor README")
    result = evaluate(candidate_sha, audit_sha, match.group(1))
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["decision"] == "PASS_SOURCE_IDENTITY" else 1


if __name__ == "__main__":
    sys.exit(main())
