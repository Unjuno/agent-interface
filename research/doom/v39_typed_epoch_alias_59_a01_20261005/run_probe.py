#!/usr/bin/env python3
"""Run the exact-main typed observation epoch-alias construction probe once."""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "source"
sys.path.insert(0, str(SOURCE / "research" / "live_control"))
sys.path.insert(0, str(SOURCE / "research" / "doom"))
from PIL import Image
from action_validity_admission_v1 import CONTRACT_FORMAT
from doom_typed_observation_v1 import build_action_snapshot, extract_typed_observation

OUT = ROOT / "RESULT.json"

class Reader:
    def __init__(self, signal_id, value, sequence, capture_ns, binding):
        self.signal_id = signal_id
        self.value = value
        self.sequence = sequence
        self.capture_ns = capture_ns
        self.binding = binding

    def read_frame(self, observation, frame):
        return {
            "format": "observable-signal-v1", "status": "observed",
            "signal_id": self.signal_id, "value": self.value,
            "sequence": self.sequence, "capture_ns": self.capture_ns,
            "binding": self.binding, "wad_sha256": "a" * 64,
        }


def main():
    if OUT.exists():
        raise SystemExit("STOP_OUTPUT_EXISTS")
    fixture = json.loads((ROOT / "fixture.json").read_text(encoding="utf-8"))
    metadata = fixture["metadata"]
    binding = metadata["pointer_binding"]
    contract = {"format": CONTRACT_FORMAT,
                "source": {"signals": {"health": {}, "ammo": {}}}}
    rows = []
    for case in fixture["cases"]:
        readers = {}
        raw_signal_fields = {}
        for signal_id, value in fixture["source_values"].items():
            sequence = metadata["sequence"]
            capture_ns = metadata["capture_ns"]
            if case["signal"] == signal_id and case["field"] == "sequence":
                sequence = case["value"]
            if case["signal"] == signal_id and case["field"] == "capture_ns":
                capture_ns = case["value"]
            readers[signal_id] = Reader(signal_id, value, sequence, capture_ns, binding)
            raw_signal_fields[signal_id] = {"sequence": sequence, "capture_ns": capture_ns}
        event = extract_typed_observation(
            Image.new("RGB", (2, 2), (11, 22, 33)), metadata, readers,
            clock=iter((2, 3)).__next__)
        try:
            snapshot = build_action_snapshot(event, contract)
            accepted, stage, error = True, "snapshot", None
        except (TypeError, ValueError) as exc:
            snapshot = None
            accepted, stage, error = False, "rejected", f"{type(exc).__name__}: {exc}"
        rows.append({"name": case["name"], "raw_signal_fields": raw_signal_fields,
                     "accepted": accepted, "stage": stage, "error": error,
                     "snapshot": snapshot})
    aliases = [row for row in rows if row["name"] != "control_exact_integer_epoch"]
    accepted_aliases = sum(row["accepted"] for row in aliases)
    result = {
        "format": "issue59-v39-typed-epoch-alias-result-v1",
        "source_pipeline": "extract_typed_observation -> build_action_snapshot",
        "construction_only": True, "live_allocation_invocations": 0,
        "cases": rows, "case_count": len(rows),
        "control_accepted": rows[0]["accepted"],
        "malformed_aliases_accepted": accepted_aliases,
        "malformed_aliases_rejected": len(aliases) - accepted_aliases,
        "classification": ("FAIL_CLOSED_EPOCH_IDENTITY_GAP"
                           if rows[0]["accepted"] and accepted_aliases
                           else "PASS_EXACT_EPOCH_TYPE_GATE"),
    }
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"classification": result["classification"],
                      "control_accepted": result["control_accepted"],
                      "malformed_aliases_accepted": accepted_aliases,
                      "malformed_aliases_rejected": len(aliases) - accepted_aliases},
                     sort_keys=True))

if __name__ == "__main__":
    main()
