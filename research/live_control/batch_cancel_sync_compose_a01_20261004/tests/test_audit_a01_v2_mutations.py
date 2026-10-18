"""Negative controls for the read-only A01 audit repair."""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from audit_a01_v2 import audit


def main() -> None:
    manifest = json.loads((ROOT / "SOURCE_MANIFEST.json").read_text(encoding="utf-8"))
    raw = json.loads((ROOT / "raw/trace.json").read_text(encoding="utf-8"))
    assert audit(raw, manifest) == []

    bad_schema = copy.deepcopy(raw)
    bad_schema["schema"] = "wrong-schema"
    assert "candidate_disposition" in audit(bad_schema, manifest)

    bad_interval = copy.deepcopy(raw)
    batch = next(x for x in bad_interval["cases"] if x["case"] == "batch_cancel_during_sync")
    batch["receipt"]["key_release_intervals_ns"][0]["interval_ns"][1] = batch["receipt"]["verified_ns"] + 1
    assert "batch_interval:0" in audit(bad_interval, manifest)

    bad_cancel = copy.deepcopy(raw)
    explicit = next(x for x in bad_cancel["cases"] if x["case"] == "explicit_up_cancel_during_sync")
    explicit["receipt"]["cancel_requested_after_sync"] = False
    assert "explicit_up_cancellation_receipt" in audit(bad_cancel, manifest)
    print("3 mutation controls passed; valid frozen trace accepted")


if __name__ == "__main__":
    main()
