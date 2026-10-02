"""Independent source-closure verifier; does not import the candidate runner."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path


SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def show(root: Path, commit: str, path: str) -> bytes | None:
    proc = subprocess.run(
        ["git", "-C", str(root), "show", f"{commit}:{path}"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    return proc.stdout if proc.returncode == 0 else None


def expected_inventory(prereg: dict) -> dict[str, set[str]]:
    result: dict[str, set[str]] = {}
    for key in ("source_sha256", "canonical_upstream_sha256"):
        values = prereg.get(key)
        if not isinstance(values, dict) or not values:
            raise ValueError(f"missing preregistration inventory: {key}")
        for path, digest in values.items():
            if not isinstance(path, str) or not path or not isinstance(digest, str) or not SHA256_RE.fullmatch(digest):
                raise ValueError(f"malformed pinned identity: {key}:{path}")
            result.setdefault(path, set()).add(digest)
    return result


def audit(root: Path, fixture: dict, candidate: dict) -> dict:
    errors: list[str] = []
    commit = fixture["source_commit"]
    prereg_raw = show(root, commit, fixture["prereg_path"])
    if prereg_raw is None:
        return {
            "schema": "map01-current-main-source-closure-audit-v1",
            "disposition": "FAIL_AUDIT_INTEGRITY",
            "errors": ["frozen-preregistration-blob-missing"],
        }
    try:
        prereg = json.loads(prereg_raw)
        expected = expected_inventory(prereg)
    except (json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        return {
            "schema": "map01-current-main-source-closure-audit-v1",
            "disposition": "FAIL_AUDIT_INTEGRITY",
            "errors": [f"invalid-frozen-preregistration:{type(exc).__name__}"],
        }

    observed_rows = candidate.get("rows") if isinstance(candidate, dict) else None
    if not isinstance(observed_rows, list):
        observed_rows = []
        errors.append("candidate-rows-not-list")
    observed_paths = [row.get("path") if isinstance(row, dict) else None for row in observed_rows]
    if observed_paths != sorted(expected) or len(observed_paths) != len(set(observed_paths)):
        errors.append("candidate-inventory-not-exact-union")
    if candidate.get("source_commit") != commit or candidate.get("prereg_path") != fixture["prereg_path"]:
        errors.append("candidate-source-identity-mismatch")

    drift_paths = []
    independently_verified = []
    for path in sorted(expected):
        source = show(root, commit, path)
        digest = hashlib.sha256(source).hexdigest() if source is not None else None
        pins = sorted(expected[path])
        observed = next((r for r in observed_rows if isinstance(r, dict) and r.get("path") == path), None)
        if source is None or len(pins) != 1 or digest != pins[0]:
            drift_paths.append(path)
        if observed is None or observed.get("actual_sha256") != digest or observed.get("expected_sha256") != pins or observed.get("present") is not (source is not None):
            errors.append(f"candidate-raw-row-mismatch:{path}")
        independently_verified.append({"path": path, "sha256": digest, "matches_pin": source is not None and len(pins) == 1 and digest == pins[0]})

    if candidate.get("expected_source_path_count") != len(expected):
        errors.append("candidate-declared-count-mismatch")
    if errors:
        disposition = "FAIL_AUDIT_INTEGRITY"
    elif drift_paths:
        disposition = "FAIL_PINNED_SOURCE_DRIFT"
    else:
        disposition = "PASS_SOURCE_CLOSURE_ONLY"
    return {
        "schema": "map01-current-main-source-closure-audit-v1",
        "source_commit": commit,
        "prereg_path": fixture["prereg_path"],
        "expected_source_path_count": len(expected),
        "independently_verified_path_count": len(independently_verified),
        "drift_paths": drift_paths,
        "errors": errors,
        "error_count": len(errors),
        "historical_allocation_id": fixture["historical_allocation_id"],
        "live_validation_authorized": False,
        "disposition": disposition,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--fixture", type=Path, default=Path(__file__).with_name("fixture.json"))
    parser.add_argument("--candidate", type=Path, default=Path(__file__).with_name("candidate_output.json"))
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    fixture = json.loads(args.fixture.read_text(encoding="utf-8"))
    candidate = json.loads(args.candidate.read_text(encoding="utf-8"))
    result = audit(args.repo_root, fixture, candidate)
    serialized = json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n"
    args.out.write_text(serialized, encoding="utf-8", newline="\n")
    print(serialized, end="")
    raise SystemExit(0 if result["error_count"] == 0 and result["disposition"] == "PASS_SOURCE_CLOSURE_ONLY" else 1)


if __name__ == "__main__":
    main()
