#!/usr/bin/env python3
"""Independent verification of analyze.py's retained-trace result."""
import hashlib
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[2]


def read_jsonl(path):
    with path.open(encoding="utf-8") as handle:
        return list(map(json.loads, filter(str.strip, handle)))


def main():
    result = json.loads((BASE / "RESULT.json").read_text(encoding="utf-8"))
    assert result["status"] == "PASS_SCOPED"
    assert len(result["v39_candidate_pairs"]) == 2
    all_ok = True
    for pair in result["v39_candidate_pairs"]:
        rows = pair["rows"]
        assert len(rows) == 2
        assert pair["distinct_frame_hashes"] is True
        assert rows[0]["frame_rgb_sha256"] != rows[1]["frame_rgb_sha256"]
        assert rows[0]["observation_exact_match"] and rows[1]["observation_exact_match"]
        assert rows[0]["capture_ns"] < rows[1]["capture_ns"]
        assert rows[0]["emit_ns"] < rows[1]["emit_ns"]
        for row in rows:
            assert row["emit_ns"] >= row["capture_ns"]
    for name, item in result["inputs"].items():
        source = ROOT / item["path"]
        assert hashlib.sha256(source.read_bytes()).hexdigest() == item["sha256"], name
    events = read_jsonl(ROOT / result["inputs"]["v39_events"]["path"])
    indexed = {(e.get("event"), e.get("sequence")): e for e in events if e.get("event") in ("typed_observation", "observation")}
    for pair in result["v39_candidate_pairs"]:
        for row in pair["rows"]:
            typed = indexed[("typed_observation", row["sequence"])]
            observed = indexed[("observation", row["sequence"])]
            assert typed["id"] == observed["id"] == row["id"]
            assert typed["capture_ns"] == observed["capture_ns"] == row["capture_ns"]
            assert typed["frame_rgb_sha256"] == observed["frame_rgb_sha256"] == row["frame_rgb_sha256"]
            assert typed["signals"]["health"]["value"] == row["health"]
    audit = {"status": "PASS_SCOPED", "independent_checks": ["source hashes", "monotonic capture and emission", "different frame hashes within each candidate pair", "typed/exact same-sequence capture identity", "health value and sequence preservation"], "semantic_independence_proven": False, "all_checks_passed": all_ok}
    (BASE / "AUDIT.json").write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
