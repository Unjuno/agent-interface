from pathlib import Path
import hashlib
import sys


def table(root):
    return {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in Path(root).iterdir() if p.is_file()}


same = table(sys.argv[1]) == table(sys.argv[2])
print({"deterministic": same, "files": len(table(sys.argv[1]))})
raise SystemExit(0 if same else 1)
