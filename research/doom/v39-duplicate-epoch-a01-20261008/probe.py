import ast
import json
import sys
import time
from pathlib import Path

source_path = Path(sys.argv[1])
source = source_path.read_text(encoding="utf-8")
tree = ast.parse(source)
wanted = {"_typed_json_equal", "_signal_pair_matches", "_signal_pair_content_matches",
          "DoomCoverSignalPairMonitor"}
selected = [node for node in tree.body
            if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and node.name in wanted]
if {node.name for node in selected} != wanted:
    raise RuntimeError("source AST does not contain exact monitor units")
namespace = {"time": time}
exec(compile(ast.Module(body=selected, type_ignores=[]), str(source_path), "exec"), namespace)
Monitor = namespace["DoomCoverSignalPairMonitor"]

class Guard:
    def __init__(self, value, sequence, capture_ns):
        self.spec = {"source_value": value, "source_sequence": sequence}
        self.source_capture_ns = capture_ns

    def evaluate(self, signal):
        return {"status": "UNCHANGED", "reason": "unchanged",
                "requires_new_decision": False,
                "keep_existing_policy": True, "signal_id": signal["signal_id"]}

def row(event, sequence, capture_ns, binding, frame_hash):
    signals = {
        "health": {"status": "observed", "signal_id": "health", "value": 100,
                   "sequence": sequence, "capture_ns": capture_ns, "binding": binding},
        "ammo": {"status": "observed", "signal_id": "ammo", "value": 50,
                 "sequence": sequence, "capture_ns": capture_ns, "binding": binding},
    }
    return {"event": event, "sequence": sequence, "capture_ns": capture_ns,
            "pointer_binding": binding, "frame_rgb_sha256": frame_hash, "signals": signals}

def monitor():
    return Monitor({"health": Guard(100, 9, 90), "ammo": Guard(50, 9, 90)},
                   None, None)

binding = {"device": "synthetic-pointer-1", "generation": 4}
cases = {}
m = monitor()
first = row("typed_observation", 10, 100, binding, "a" * 64)
advanced = row("typed_observation", 11, 200, binding, "b" * 64)
out_first = m.observe(first)
out_advanced = m.observe(advanced)
cases["advancing_epoch_hash_change"] = {
    "events": [first, advanced],
    "outcomes": [out_first, out_advanced],
}

m = monitor()
typed = row("typed_observation", 10, 100, binding, "c" * 64)
same_transport = row("observation", 10, 100, binding, "c" * 64)
out_typed = m.observe(typed)
out_same = m.observe(same_transport)
cases["same_epoch_same_hash_cross_transport"] = {
    "events": [typed, same_transport],
    "outcomes": [out_typed, out_same],
}

m = monitor()
typed = row("typed_observation", 10, 100, binding, "d" * 64)
mismatch = row("observation", 10, 100, binding, "e" * 64)
out_typed = m.observe(typed)
out_mismatch = m.observe(mismatch)
cases["same_epoch_different_hash_cross_transport"] = {
    "events": [typed, mismatch],
    "outcomes": [out_typed, out_mismatch],
}

def label(outcome):
    if outcome is None:
        return "PRESERVE"
    return outcome.get("reason", outcome.get("event", "INVALIDATED"))

labels = {name: [label(outcome) for outcome in item["outcomes"]]
          for name, item in cases.items()}
checks = {
    "newer_epoch_hash_change_preserves": labels["advancing_epoch_hash_change"] == ["PRESERVE", "PRESERVE"],
    "same_epoch_same_hash_cross_transport_preserves": labels["same_epoch_same_hash_cross_transport"] == ["PRESERVE", "PRESERVE"],
    "same_epoch_hash_mismatch_invalidates": labels["same_epoch_different_hash_cross_transport"] == ["PRESERVE", "signal_pair_duplicate_epoch_mismatch"],
    "invalidation_grants_no_input_authority": (
        cases["same_epoch_different_hash_cross_transport"]["outcomes"][1] is not None and
        cases["same_epoch_different_hash_cross_transport"]["outcomes"][1].get("grants_input_authority") is False
    ),
}
result = {
    "experiment": "issue59-duplicate-epoch-frame-coherence-a01-20261008",
    "status": "PASS_SYNTHETIC_BOUNDARY" if all(checks.values()) else "FAIL_SYNTHETIC_BOUNDARY",
    "checks": checks,
    "observed_labels": labels,
    "cases": cases,
    "scope": "Synthetic source-level monitor probe only; no game, model, GUI, OS input, physical release, semantic threat, policy quality, or task effect measured."
}
print(json.dumps(result, indent=2, sort_keys=True))
if not all(checks.values()):
    raise SystemExit(1)
