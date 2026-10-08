"""Exclusive-create custody manifest for this additive publication batch."""
import hashlib
from pathlib import Path

PACKAGE = Path(__file__).resolve().parent
REPO = PACKAGE.parents[2]
PRIOR = REPO / "research/doom/results/issue59_v39_hud_ocr_posthoc_20261003_01"
destination = PACKAGE / "SHA256SUMS"
files = sorted(path for directory in (PACKAGE, PRIOR) for path in directory.rglob("*")
               if path.is_file() and path != destination)
if any(path.is_symlink() or "__pycache__" in path.parts for path in files):
    raise SystemExit("STOP_UNEXPECTED_MANIFEST_ENTRY")
with destination.open("x") as stream:
    for path in files:
        stream.write(hashlib.sha256(path.read_bytes()).hexdigest() + "  " + str(path.relative_to(REPO)) + "\n")
print(f"Manifested {len(files)} files")
