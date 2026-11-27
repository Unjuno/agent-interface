"""Read-only source identity check for the retained v38/v39 tempo analysis."""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess


HERE = Path(__file__).resolve().parent
ANALYZER = HERE / "analyze_map01_v38_v39_control_tempo_posthoc_v1.py"
spec = importlib.util.spec_from_file_location("tempo_analyzer", ANALYZER)
analyzer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(analyzer)


def sha(path):
    return analyzer.sha(path)


def git_blob(path):
    relative = path.relative_to(HERE.parents[1]).as_posix()
    return subprocess.check_output(["git", "show", f"HEAD:{relative}"],
                                   cwd=HERE.parents[1])


def main():
    recorded = analyzer.read(analyzer.OUT / "analysis.json")
    rows = []
    for expected in recorded["runs"]:
        name = expected["run"]
        root = analyzer.ROOT / name
        current = {}
        expected_hashes = expected["source_sha256"]
        for key, expected_hash in expected_hashes.items():
            path = root / key
            worktree_bytes = path.read_bytes()
            normalized = worktree_bytes.replace(b"\r\n", b"\n")
            blob = git_blob(path)
            current[key] = {
                "worktree_sha256": hashlib.sha256(worktree_bytes).hexdigest(),
                "normalized_sha256": hashlib.sha256(normalized).hexdigest(),
                "git_blob_sha256": hashlib.sha256(blob).hexdigest(),
                "crlf_sequences": worktree_bytes.count(b"\r\n"),
                "blob_matches_expected": hashlib.sha256(blob).hexdigest() == expected_hash,
                "normalized_matches_blob": normalized == blob,
            }
        rows.append({
            "run": name,
            "current": current,
            "expected": expected_hashes,
        })
    rebuilt = [analyzer.analyze_run(row["run"]) for row in recorded["runs"]]
    rebuild_matches = all(
        {key: value for key, value in actual.items() if key != "source_sha256"}
        == {key: value for key, value in stored.items() if key != "source_sha256"}
        for actual, stored in zip(rebuilt, recorded["runs"])
    )
    identity_matches = all(
        item["blob_matches_expected"] and item["normalized_matches_blob"]
        for row in rows for item in row["current"].values()
    )
    result = {
        "schema": "map01-v38-v39-source-identity-audit-v2",
        "classification": "PASS_GIT_BLOB_AND_REBUILD" if identity_matches and rebuild_matches
        else "FAIL_SOURCE_IDENTITY_OR_REBUILD",
        "analysis_sha256": sha(analyzer.OUT / "analysis.json"),
        "analysis_rebuild_matches_except_transport_dependent_hashes": rebuild_matches,
        "runs": rows,
        "scope": "Git blob and CRLF-normalized checkout comparison plus retained analysis reconstruction; no live game, model, input, container, or source mutation",
    }
    out = HERE / "results" / "map01-v38-v39-source-identity-20261104-v2"
    out.mkdir(parents=True, exist_ok=True)
    (out / "audit.json").write_text(json.dumps(result, indent=2) + "\n",
                                     encoding="utf-8", newline="\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
