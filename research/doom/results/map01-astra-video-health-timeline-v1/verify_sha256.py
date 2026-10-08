import hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4]
PKG=Path(__file__).resolve().parent
failures=[]
for line in (PKG/"SHA256SUMS.txt").read_text(encoding="utf-8").splitlines():
 digest,rel=line.split("  ",1); p=(PKG/rel).resolve()
 if PKG.resolve() not in p.parents or not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest()!=digest: failures.append(rel)
print("PASS_PACKAGE_SHA256" if not failures else "FAIL_PACKAGE_SHA256", failures)
raise SystemExit(bool(failures))
