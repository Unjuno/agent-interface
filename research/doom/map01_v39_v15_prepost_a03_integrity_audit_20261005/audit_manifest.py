"""Read-only integrity check for the retained #7935 A03 audit package."""
import hashlib
import json
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[3]
SOURCE_HEAD = "af4c9d63336e508dfc846c79403500674339c805"
PACKAGE_REL = Path("research/doom/map01_v39_v15_selected_path_prepost_a03_audit_20261005")
PACKAGE = ROOT / PACKAGE_REL
MANIFEST = PACKAGE / "SHA256SUMS.txt"
REPORT_REL = PACKAGE_REL / "REPORT.md"
REPORT_GIT_BLOB = "0f119f0344f1d4378b23a8e04c3f8a5720fba800"


def git(*args):
    return subprocess.run(["git", *args], cwd=ROOT, check=True,
                          capture_output=True, text=True).stdout.strip()


entries = []
for line_number, line in enumerate(MANIFEST.read_text(encoding="utf-8").splitlines(), 1):
    fields = line.split()
    if len(fields) != 2 or len(fields[0]) != 64:
        raise ValueError(f"malformed manifest line {line_number}")
    digest, relative = fields
    path = (PACKAGE / relative).resolve()
    if not path.is_relative_to(PACKAGE.resolve()) or not path.is_file():
        raise ValueError(f"unsafe or missing manifest path on line {line_number}: {relative}")
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    entries.append({"path": relative, "expected": digest, "actual": actual,
                    "matches": digest == actual})

report_blob = git("rev-parse", f"{SOURCE_HEAD}:{REPORT_REL.as_posix()}")
if report_blob != REPORT_GIT_BLOB:
    raise ValueError(f"source report blob mismatch: {report_blob}")
mismatches = [item for item in entries if not item["matches"]]
result = {
    "disposition": "PASS_PACKAGE_MANIFEST" if not mismatches else "STOP_PACKAGE_MANIFEST_MISMATCH",
    "source_head": SOURCE_HEAD,
    "report_git_blob": report_blob,
    "manifest_entries": len(entries),
    "matching_entries": len(entries) - len(mismatches),
    "mismatch_count": len(mismatches),
    "mismatches": mismatches,
}
print(json.dumps(result, indent=2, sort_keys=True))
raise SystemExit(0 if not mismatches else 1)
