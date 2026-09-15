"""Verify every retained byte after the separately versioned semantic audit."""
import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
OUT = HERE / "results/action-grounded-memory-ablation-live-01"


def read(path): return json.loads(Path(path).read_text(encoding="utf-8"))
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    receipt = read(OUT / "retention.json")
    assert receipt["decision"] == "RETAIN_FIRST_OUTCOME_CROP_ELIGIBLE_FOR_TRANSFER"
    assert receipt["file_count"] == len(receipt["manifest"])
    assert receipt["total_bytes"] == sum(row["bytes"] for row in receipt["manifest"])
    assert len({row["path"] for row in receipt["manifest"]}) == receipt["file_count"]
    for row in receipt["manifest"]:
        path = OUT / row["path"]
        assert path.is_file() and path.stat().st_size == row["bytes"] and sha(path) == row["sha256"]
    result = {"passed": True, "files": receipt["file_count"], "bytes": receipt["total_bytes"],
              "decision": receipt["decision"]}
    (OUT / "retained-audit.json").write_text(json.dumps(result, indent=2) + "\n",
                                              encoding="utf-8", newline="\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__": main()
