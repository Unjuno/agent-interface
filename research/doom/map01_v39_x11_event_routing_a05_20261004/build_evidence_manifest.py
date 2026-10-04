"""Create or verify the A05 package manifest without self-reference."""
import argparse
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
MANIFEST = HERE / "EVIDENCE_MANIFEST.json"
GENERATOR = Path(__file__).name


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def expected():
    paths = sorted(path for path in HERE.rglob("*") if path.is_file()
                   and path.relative_to(HERE).as_posix() not in {GENERATOR, MANIFEST.name}
                   and "__pycache__" not in path.parts)
    return {
        "schema": "v39-x11-event-routing-evidence-manifest-a05-v1",
        "generator": {"path": GENERATOR, "sha256": sha(HERE / GENERATOR)},
        "file_count": len(paths),
        "files": {path.relative_to(HERE).as_posix(): {
            "bytes": path.stat().st_size, "sha256": sha(path)} for path in paths},
    }


parser = argparse.ArgumentParser()
parser.add_argument("--verify", action="store_true")
args = parser.parse_args()
value = expected()
if args.verify:
    actual = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if actual != value:
        raise SystemExit("EVIDENCE_MANIFEST does not match current package")
    print(json.dumps({"status": "PASS_MANIFEST", "file_count": value["file_count"]}, sort_keys=True))
else:
    if MANIFEST.exists():
        raise FileExistsError(MANIFEST)
    MANIFEST.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": "WROTE_MANIFEST", "file_count": value["file_count"]}, sort_keys=True))
