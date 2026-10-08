"""Single candidate invocation: fixture to hash-bound JSONL ledger."""
import hashlib
import json
import sys
from pathlib import Path
from candidate import run


def main():
    if len(sys.argv) != 3:
        raise SystemExit("usage: run_candidate.py FIXTURE OUTPUT_DIR")
    fixture_path, output = Path(sys.argv[1]), Path(sys.argv[2])
    raw_fixture = fixture_path.read_bytes()
    fixture = json.loads(raw_fixture)
    output.mkdir(parents=True, exist_ok=True)
    raw = b"".join((json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n").encode() for row in run(fixture))
    (output / "ledger.jsonl").write_bytes(raw)
    names = ("candidate.py", "run_candidate.py", "independent_audit.py")
    manifest = {"allocation": fixture["allocation"], "fixture_sha256": hashlib.sha256(raw_fixture).hexdigest(),
                "ledger_sha256": hashlib.sha256(raw).hexdigest(), "row_count": len(fixture["rows"]),
                "source_sha256": {name: hashlib.sha256((Path(__file__).parent / name).read_bytes()).hexdigest() for name in names}}
    (output / "candidate_manifest.json").write_text(json.dumps(manifest, sort_keys=True) + "\n")
    print(json.dumps({"status": "CANDIDATE_COMPLETE", **manifest}, sort_keys=True))


if __name__ == "__main__":
    main()
