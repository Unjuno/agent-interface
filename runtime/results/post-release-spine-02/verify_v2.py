"""Strict retained-artifact verifier with refusal-inventory order canonicalization."""
import argparse
import hashlib
import json
import tarfile
import tempfile
from pathlib import Path, PurePosixPath

from analyze import load, require
from analyze_v2 import analyze


def canonical(value):
    """Copy JSON data, sorting only route refusal inventories by unique attempt."""
    value = json.loads(json.dumps(value))
    routes = value.get("routes")
    require(isinstance(routes, dict), "routes schema")
    for route in routes.values():
        refusals = route.get("refusals")
        require(isinstance(refusals, list), "refusals schema")
        attempts = []
        for refusal in refusals:
            require(isinstance(refusal, dict), "refusal schema")
            attempt = refusal.get("attempt")
            require(type(attempt) is int, "refusal attempt schema")
            attempts.append(attempt)
        require(len(attempts) == len(set(attempts)), "duplicate refusal attempt")
        route["refusals"] = sorted(refusals, key=lambda item: item["attempt"])
    return value


def verify(dest):
    manifest = load(dest / "manifest.json")
    data = (dest / "raw.tar.gz").read_bytes()
    require(len(data) == manifest["archive"]["bytes"], "archive byte count")
    require(hashlib.sha256(data).hexdigest() == manifest["archive"]["sha256"], "archive hash")
    expected = {row["path"]: row for row in manifest["files"]}
    require(len(expected) == len(manifest["files"]), "manifest duplicate")
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        seen = set()
        with tarfile.open(dest / "raw.tar.gz", "r:gz") as archive:
            for member in archive.getmembers():
                path = PurePosixPath(member.name)
                require(member.isfile() and not path.is_absolute() and ".." not in path.parts,
                        "unsafe archive path")
                require(member.name in expected and member.name not in seen,
                        "unexpected or duplicate archive path")
                seen.add(member.name)
                payload = archive.extractfile(member).read()
                row = expected[member.name]
                require(len(payload) == row["bytes"], "file byte count " + member.name)
                require(hashlib.sha256(payload).hexdigest() == row["sha256"],
                        "file hash " + member.name)
                output = root / member.name
                output.parent.mkdir(parents=True, exist_ok=True)
                output.write_bytes(payload)
        require(seen == set(expected), "missing archive member")
        package = root / "post-release-spine-02"
        actual = analyze(package)
        frozen = load(package / "analysis-v3.json")
        published = load(dest / "analysis.json")
        require(canonical(actual) == canonical(frozen) == canonical(published),
                "analysis mismatch beyond refusal ordering")

        stop = root / "post-release-spine-01" / "guarded-local"
        require(load(stop / "session/finish.json")["status"] == "STOP_CONSTRUCTION_NO_INPUT",
                "retained STOP")
        oracle = load(stop / "session/evaluation-at-close.json")
        require(oracle["success"] is False and oracle["record_count"] == 0
                and len(oracle["missing"]) == 6, "STOP six missing")
        require((stop / "host/host-events.jsonl").read_bytes() == b"", "STOP no requests")

        usage = load(package / "model-usage-projection.json")
        require(usage == load(dest / "model-usage-projection.json")
                and usage["dollars"] is None, "usage identity")
        require(all(call["local_context"]["model"] == "gpt-6.1-sol"
                    and call["local_context"]["effort"] == "medium"
                    for call in usage["calls"] if call["local_context"]), "model labels")
        return {
            "status": "PASS_RETAINED_MANUAL_GUARDED_DIRECT_SIX_PAIR_AUDIT_V2",
            "retained_analysis_status": actual["status"], "files": len(seen),
            "integration_gate": actual["integration_gate"],
            "scope": "Retained effect/history, neutral releases, exact image/review identity, source archive identity, all attempts and attributed timing. No autonomous recovery or independent perception/cost proof.",
        }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--directory", type=Path, default=Path(__file__).resolve().parent)
    args = parser.parse_args()
    print(json.dumps(verify(args.directory)))
