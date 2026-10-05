#!/usr/bin/env python3
"""One-shot posthoc replay through the pinned current guard evaluator."""
import ast
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
FREEZE = json.loads((HERE / "FREEZE.json").read_text())
INPUT = HERE / "input/VISUAL_READOUT.json"
CONTROLLER = REPO / "research/doom/map01_overlap_controller_v39.py"
GUARD = REPO / "research/live_control/observable_signal_guard_v2.py"

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
if sha(INPUT) != "610b77f02302150f26c7de81e46bcba5e8a4fc646d6195442c86db93c6305724":
    raise SystemExit("STOP_INPUT_HASH")
if sha(CONTROLLER) != FREEZE["controller_source_sha256"]: raise SystemExit("STOP_CONTROLLER_SOURCE_HASH")
if sha(GUARD) != FREEZE["guard_source_sha256"]: raise SystemExit("STOP_GUARD_SOURCE_HASH")
# Import only the pinned production guard module; extract the exact production
# guard_spec function AST to avoid importing unrelated GUI/runtime dependencies.
spec = importlib.util.spec_from_file_location("pinned_observable_signal_guard_v2", GUARD)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
tree = ast.parse(CONTROLLER.read_text())
fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "guard_spec")
namespace = {}
exec(compile(ast.Module(body=[fn], type_ignores=[]), str(CONTROLLER), "exec"), namespace)
guard_spec = namespace["guard_spec"]
readout = json.loads(INPUT.read_text())
rows = readout["samples"]
binding = {"focus": "replay-only", "surface": "retained-video", "geometry": [0,0,640,560]}
source_ns = 1
source = {"status":"observed", "signal_id":"health", "value":100,
          "sequence":1, "capture_ns":source_ns, "binding":binding}
results = []
for max_loss in FREEZE["thresholds"]:
    validity = {"signal_id":"health", "critical_health_minimum":35,
                "maximum_health_loss":max_loss, "max_source_age_ms":30000}
    policy = guard_spec(validity, source, 4)
    guard = module.ObservableSignalGuard(policy, source, binding)
    observations = []
    for i, row in enumerate(rows):
        game_s = float(row["game_clock"].rstrip("s"))
        if game_s <= 44.6: continue
        signal = {"status":"observed", "signal_id":"health", "value":row["health"],
                  "sequence":i+2, "capture_ns":source_ns+int((game_s-44.6)*1e9),
                  "binding":binding}
        outcome = guard.evaluate(signal)
        observations.append({"game_time_s":game_s,"health":row["health"],
                             "phase":row["phase"],"status":outcome["status"],
                             "reason":outcome["reason"],"hard_minimum":outcome["hard_minimum"]})
        if outcome["requires_new_decision"]:
            break
    first = observations[-1] if observations and observations[-1]["status"] == "HARD_INVALIDATED" else None
    results.append({"maximum_health_loss":max_loss,"hard_minimum":policy["hard_minimum"],
                    "first_invalidation":first,"evaluated_samples":observations})
raw = {"schema":"astra-health-guard-replay-a01-v1","source_video_sha256":"201ab6aaa8ab5823285b44864ad1df899ebe5a19c97ec6e84b8cc5db063f6be4",
       "input_sha256":sha(INPUT),"controller_sha256":sha(CONTROLLER),"guard_sha256":sha(GUARD),
       "source_readout_sample_count":len(rows),"sweep":results,
       "sampling_limit":"only manually transcribed selected full-frame samples; no interpolation"}
(HERE/"raw.json").write_text(json.dumps(raw,indent=2)+"\n")
print(json.dumps({"results":[{"maximum_health_loss":r["maximum_health_loss"],"hard_minimum":r["hard_minimum"],"first_invalidation":r["first_invalidation"]} for r in results]},indent=2))
