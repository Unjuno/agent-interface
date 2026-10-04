"""Seal the first passing shared-caller live integration."""
import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
OUT = HERE / "results/adaptive-semantic-repair-live-02"


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    excluded = {"retention.json", "retained-audit.json"}
    files = sorted(path for path in OUT.rglob("*") if path.is_file()
                   and path.name not in excluded)
    manifest = [{"path": str(path.relative_to(OUT)).replace("\\", "/"),
                 "sha256": sha(path), "bytes": path.stat().st_size} for path in files]
    receipt = {"schema": "adaptive-semantic-repair-live-retention-v2",
               "decision": "RETAIN_PASSED_FIRST_OUTCOME_NO_RETRY",
               "file_count": len(manifest),
               "total_bytes": sum(row["bytes"] for row in manifest),
               "manifest": manifest,
               "scope": "two unequal mutations; integration evidence, not a matched efficiency comparison"}
    (OUT / "retention.json").write_text(json.dumps(receipt, indent=2) + "\n",
                                         encoding="utf-8", newline="\n")
    print(json.dumps({"files": receipt["file_count"],
                      "bytes": receipt["total_bytes"]}, indent=2))


if __name__ == "__main__": main()
