"""Actual lineage->CLI API->Win32Session->core, with an explicitly inert backend."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "source"))
from runtime.cli_v1 import api
from runtime.cli_v1.lineage import dispatch_with_lineage
from runtime.backends.win32_v1.session import Win32RuntimeSession
from runtime.core_v1.contract import OFFICE_FLOOR, INPUT_POINTER, capability_manifest

def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()

def seal(p, r, s):
    r["digest"] = hashlib.sha256(encoded({k: r[k] for k in
        ("receipt_id", "role", "currentness", "point", "observation_seq", "binding_revision", "source_receipt_id")})).hexdigest()
    s["program_digest"] = hashlib.sha256(encoded(p)).hexdigest()
    s["evidence_receipt_digest"] = r["digest"]
    s["digest"] = hashlib.sha256(encoded({k: s[k] for k in
        ("program_digest", "evidence_receipt_digest", "role", "currentness", "point", "observation_seq", "binding_revision")})).hexdigest()

def fixture():
    p = {"schema": "agent-interface/program-v1", "program_id": "inert-lineage-review",
        "source": {"observation_seq": 7, "binding_revision": 3},
        "authority": {"lease_id": "inert-lease", "expires_at_ns": 10000},
        "terminal": {"release_all_required": True},
        "ops": [{"op": "focus", "target": "window-1"},
            {"op": "pointer_move", "frame": "window_client", "x": 10, "y": 20}, {"op": "release_all"}]}
    r = {"receipt_id": "review-r", "role": "ADMISSION_DEPENDENCY", "currentness": "CURRENT",
        "point": [10, 20], "observation_seq": 7, "binding_revision": 3, "source_receipt_id": "review-source"}
    s = {k: deepcopy(r[k]) for k in ("role", "currentness", "point", "observation_seq", "binding_revision")}
    return p, r, s

class InertBackend:
    emissions = 0
    def __init__(self, counters, supported): self.counters, self.supported = counters, supported
    def monotonic_ns(self): return 1000
    def manifest(self): return capability_manifest("inert-review", "windows", "inert", self.supported)
    def preflight(self, program): self.counters["preflight"] += 1
    def execute(self, program):
        self.counters["execute"] += 1
        return {"releases": [{"verified": True, "synthetic": True}], "synthetic": True}
    def close(self): self.counters["close"] += 1

SPEC = [
    ("valid", "delegated", None, "completed", None, 1, 1),
    ("reordered", "delegated", None, "completed", None, 1, 1),
    ("sidecar-float", "lineage_rejected", "SIDECAR_RECEIPT_MISMATCH", None, None, 0, 0),
    ("source-float", "lineage_rejected", "PROGRAM_SOURCE_MISMATCH", None, None, 0, 0),
    ("current-float", "lineage_rejected", "STALE_OBSERVATION", None, None, 0, 0),
    ("binding-float", "lineage_rejected", "STALE_BINDING", None, None, 0, 0),
    ("stale", "lineage_rejected", "STALE_OBSERVATION", None, None, 0, 0),
    ("bad-digest", "lineage_rejected", "EVIDENCE_RECEIPT_DIGEST_MISMATCH", None, None, 0, 0),
    ("matching-float", "delegated", None, "refused", "INVALID_PROGRAM", 1, 0),
    ("expired", "delegated", None, "refused", "LEASE_EXPIRED", 1, 0),
    ("unsupported", "delegated", None, "refused", "UNSUPPORTED_CAPABILITY", 1, 0),
    ("signed-zero", "lineage_rejected", "PROGRAM_POINT_MISMATCH", None, None, 0, 0),
]

def run():
    rows = []
    for label, status, error, terminal_status, terminal_error, openings, executions in SPEC:
        p, r, s = fixture()
        current = {"current_observation_seq": 7, "current_binding_revision": 3}
        supported = OFFICE_FLOOR
        if label == "reordered": p["source"] = dict(reversed(list(p["source"].items())))
        elif label == "sidecar-float": s["point"][0] = 10.0
        elif label == "source-float": p["source"]["observation_seq"] = 7.0
        elif label == "current-float": current["current_observation_seq"] = 7.0
        elif label == "binding-float": current["current_binding_revision"] = 3.0
        elif label == "stale": current["current_observation_seq"] = 8
        elif label == "matching-float":
            p["ops"][1]["x"] = 10.0; r["point"][0] = 10.0; s["point"][0] = 10.0
        elif label == "expired": p["authority"]["expires_at_ns"] = 999
        elif label == "unsupported": supported = OFFICE_FLOOR - {INPUT_POINTER}
        elif label == "signed-zero":
            p["ops"][1]["x"] = -0.0; r["point"][0] = 0.0; s["point"][0] = 0.0
        seal(p, r, s)
        if label == "bad-digest": r["digest"] = "0" * 64
        before = encoded([p, r, s, current])
        counts = {"open": 0, "preflight": 0, "execute": 0, "close": 0}
        def open_inert(*args, **kwargs):
            counts["open"] += 1
            return Win32RuntimeSession(InertBackend(counts, supported))
        with patch.object(api, "open_session", side_effect=open_inert):
            result = dispatch_with_lineage(p, {"window-1": 1}, r, s, **current)
        terminal = result.get("cli_result", {}).get("result", {})
        expected_counts = {"open": openings, "preflight": executions, "execute": executions, "close": openings}
        actual = {"status": result["status"], "error": result.get("error"),
            "terminal_status": terminal.get("status"), "terminal_error": terminal.get("error")}
        expected = {"status": status, "error": error, "terminal_status": terminal_status, "terminal_error": terminal_error}
        if actual != expected or counts != expected_counts or before != encoded([p, r, s, current]):
            raise ValueError({"case": label, "actual": actual, "expected": expected, "counts": counts, "wanted_counts": expected_counts})
        rows.append({"case": label, "actual": actual, "counts": counts, "input_unchanged": True,
            "input_sha256": hashlib.sha256(before).hexdigest()})
    mode = "optimized" if not __debug__ else "normal"
    (ROOT / ("default-path-v2-result-" + mode + ".json")).write_text(json.dumps({"rows": rows,
        "scope": "Actual current combined-source admission seam with synthetic backend/release only. No Win32Backend object, DLL method, native input, screenshot or real release."}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"cases": len(rows), "normal_or_optimized": "optimized" if not __debug__ else "normal", "all_matched": True}))

if __name__ == "__main__":
    run()
