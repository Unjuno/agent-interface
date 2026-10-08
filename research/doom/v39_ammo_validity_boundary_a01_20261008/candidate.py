"""One-shot synthetic probe of the frozen V39 paired ammo validity boundary."""
import ast
import hashlib
import json
import subprocess
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
FREEZE = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))


def frozen_source(spec):
    data = subprocess.check_output(["git", "show", f"{FREEZE['main_commit']}:{spec['path']}"])
    blob = subprocess.check_output(["git", "rev-parse", f"{FREEZE['main_commit']}:{spec['path']}"], text=True).strip()
    if hashlib.sha256(data).hexdigest() != spec["sha256"] or blob != spec["git_blob"]:
        raise ValueError(f"source identity mismatch: {spec['path']}")
    return data


namespace = {"json": json, "time": time}
guard_spec = FREEZE["sources"]["guard"]
exec(compile(frozen_source(guard_spec), guard_spec["path"], "exec"), namespace)
controller = FREEZE["sources"]["controller"]
tree = ast.parse(frozen_source(controller), filename=controller["path"])
needed = {"MAX_AUTHORED_HEALTH_LOSS", "guard_spec", "ammo_guard_spec",
          "_typed_json_equal", "_signal_pair_matches", "_signal_pair_content_matches",
          "DoomCoverSignalPairMonitor", "build_cover_monitor"}
selected = [node for node in tree.body
            if ((isinstance(node, ast.Assign) and any(
                    isinstance(target, ast.Name) and target.id in needed for target in node.targets)) or
                (isinstance(node, (ast.FunctionDef, ast.ClassDef)) and node.name in needed))]
found = {next((target.id for target in node.targets if isinstance(target, ast.Name)), "")
         if isinstance(node, ast.Assign) else node.name for node in selected}
if found != needed:
    raise ValueError(f"missing frozen helper(s): {sorted(needed - found)}")
exec(compile(ast.Module(body=selected, type_ignores=[]), controller["path"], "exec"), namespace)


class Reader:
    def __init__(self, name):
        self.name = name

    def read(self, observation):
        return observation["signals"][self.name]


def observation(sequence, health, ammo):
    capture_ns = sequence * 1_000_000
    binding = {"surface_id": "synthetic-v39-ammo-boundary"}
    signals = {name: {"status": "observed", "signal_id": name, "value": value,
                      "sequence": sequence, "capture_ns": capture_ns, "binding": binding}
               for name, value in (("health", health), ("ammo", ammo))}
    return {"event": "typed_observation", "sequence": sequence,
            "capture_ns": capture_ns, "pointer_binding": binding,
            "signals": signals, "frame_rgb_sha256": "c" * 64}


def run():
    monitor, admission = namespace["build_cover_monitor"](
        Reader("health"), observation(1, 100, 50),
        {"signal_id": "health", "critical_health_minimum": 80,
         "maximum_health_loss": 12, "max_source_age_ms": 30_000},
        1, ammo_reader=Reader("ammo"), requires_ammo=True)
    rows = []
    for sequence, ammo in enumerate((39, 1, 0), start=2):
        invalidation = monitor.observe(observation(sequence, 100, ammo))
        soft = monitor.latest_soft_event
        rows.append({"sequence": sequence, "health": 100, "ammo": ammo,
                     "health_hard_minimum": admission["effective"]["hard_minimum"],
                     "ammo_hard_minimum": monitor.guards["ammo"].spec["hard_minimum"],
                     "disposition": "hard_invalidation" if invalidation is not None else
                         "soft_change" if soft is not None and soft["signal"]["value"] == ammo else
                         "preserved_unchanged",
                     "invalidation_reason": None if invalidation is None else invalidation["reason"],
                     "soft_event_count": monitor.soft_event_count,
                     "latest_soft_event": None if soft is None else {
                         "signal_id": soft["signal"]["signal_id"],
                         "value": soft["signal"]["value"],
                         "status": soft["outcome"]["status"],
                         "reason": soft["outcome"]["reason"]},
                     "requires_new_decision": False if invalidation is None else
                         invalidation["requires_new_decision"],
                     "grants_input_authority": False if invalidation is None else
                         invalidation["grants_input_authority"]})
    return {"schema": "issue59-v39-ammo-validity-boundary-result-v1",
            "status": "CONSTRUCTION_OBSERVATION", "main_commit": FREEZE["main_commit"],
            "source_ammo": 50, "source_health": 100, "critical_health_minimum": 80,
            "maximum_health_loss": 12, "rows": rows,
            "scope": "Synthetic paired typed-HUD monitor behavior only; no live or tactical efficacy claim."}


if __name__ == "__main__":
    output = HERE / "RESULT.json"
    if output.exists():
        raise SystemExit(f"refusing to overwrite {output}")
    result = run()
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(result, separators=(",", ":")))
