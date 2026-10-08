"""One-shot synthetic probe through frozen V39 authored-health monitor code."""
import ast
import hashlib
import json
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
FREEZE = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))


def frozen_source(spec):
    data = subprocess.check_output(["git", "show", f"{FREEZE['main_commit']}:{spec['path']}"])
    blob = subprocess.check_output(
        ["git", "rev-parse", f"{FREEZE['main_commit']}:{spec['path']}"], text=True).strip()
    if hashlib.sha256(data).hexdigest() != spec["sha256"] or blob != spec["git_blob"]:
        raise ValueError(f"frozen source identity mismatch: {spec['path']}")
    return data


namespace = {"json": json}
guard_bytes = frozen_source(FREEZE["guard"])
exec(compile(guard_bytes, FREEZE["guard"]["path"], "exec"), namespace)
controller_bytes = frozen_source(FREEZE["controller"])
tree = ast.parse(controller_bytes, filename=FREEZE["controller"]["path"])
needed = {"MAX_AUTHORED_HEALTH_LOSS", "guard_spec", "ammo_guard_spec",
          "_typed_json_equal", "_signal_pair_matches", "_signal_pair_content_matches",
          "DoomCoverSignalPairMonitor", "build_cover_monitor"}
selected = [node for node in tree.body
            if ((isinstance(node, ast.Assign) and
                 any(isinstance(target, ast.Name) and target.id in needed
                     for target in node.targets)) or
                (isinstance(node, (ast.FunctionDef, ast.ClassDef)) and node.name in needed))]
found = {next((target.id for target in node.targets
               if isinstance(target, ast.Name)), "")
         if isinstance(node, ast.Assign) else node.name for node in selected}
if found != needed:
    raise ValueError(f"could not isolate exact frozen source helpers: {sorted(needed - found)}")
exec(compile(ast.Module(body=selected, type_ignores=[]),
             FREEZE["controller"]["path"], "exec"), namespace)


class Reader:
    def __init__(self, signal_id):
        self.signal_id = signal_id

    def read(self, observation):
        return observation["signals"][self.signal_id]


def observation(sequence, health, capture_ns):
    binding = {"surface_id": "synthetic-v39-health-boundary"}
    signals = {
        name: {"status": "observed", "signal_id": name, "value": value,
               "sequence": sequence, "capture_ns": capture_ns, "binding": binding}
        for name, value in (("health", health), ("ammo", 50))
    }
    return {"event": "typed_observation", "sequence": sequence,
            "capture_ns": capture_ns, "pointer_binding": binding,
            "signals": signals, "frame_rgb_sha256": "a" * 64}


def probe(maximum_health_loss, health_value):
    source = observation(1, 100, 1_000_000)
    validity = {"signal_id": "health", "critical_health_minimum": 80,
                "maximum_health_loss": maximum_health_loss,
                "max_source_age_ms": 30_000}
    monitor, admission = namespace["build_cover_monitor"](
        Reader("health"), source, validity, 1,
        ammo_reader=Reader("ammo"), requires_ammo=True)
    event = monitor.observe(observation(2, health_value, 2_000_000))
    if event is not None:
        status = "HARD_INVALIDATED"
        reason = event["outcome"]["reason"]
        requires_new_decision = event["requires_new_decision"]
        grants_input_authority = event["grants_input_authority"]
    elif monitor.latest_soft_event is not None:
        status = "SOFT_CHANGED"
        reason = monitor.latest_soft_event["outcome"]["reason"]
        requires_new_decision = False
        grants_input_authority = False
    else:
        status, reason = "UNCHANGED", "signal_unchanged"
        requires_new_decision = False
        grants_input_authority = False
    return {"health": health_value, "status": status, "reason": reason,
            "requires_new_decision": requires_new_decision,
            "grants_input_authority": grants_input_authority,
            "hard_minimum": admission["effective"]["hard_minimum"]}


def run():
    rows = []
    for loss in range(21):
        floor = max(80, 100 - loss)
        rows.append({"maximum_health_loss": loss, "hard_minimum": floor,
                     "triage_value_84": probe(loss, 84),
                     "exact_floor": probe(loss, floor),
                     "one_below_floor": probe(loss, floor - 1)})
    return {"schema": "issue59-authored-health-loss-boundary-result-v1",
            "status": "CONSTRUCTION_OBSERVATION",
            "main_commit": FREEZE["main_commit"],
            "controller_sha256": FREEZE["controller"]["sha256"],
            "guard_sha256": FREEZE["guard"]["sha256"],
            "motivating_triage_sha256": FREEZE["motivating_evidence"]["sha256"],
            "pending_model": True,
            "synthetic_typed_health_source": 100,
            "critical_health_minimum": 80,
            "maximum_health_loss_values": [0, 20],
            "rows": rows,
            "scope": "Current-source construction boundary only; no live threat, timing, input, recovery, or task-effect evidence."}


if __name__ == "__main__":
    output = HERE / "RESULT.json"
    if output.exists():
        raise SystemExit(f"refusing to overwrite {output}")
    result = run()
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(result, separators=(",", ":")))
