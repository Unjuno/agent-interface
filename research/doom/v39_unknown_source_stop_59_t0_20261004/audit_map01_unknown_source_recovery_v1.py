import ast
import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / "map01_overlap_controller_v40.py"
source_bytes = SOURCE.read_bytes()
source = source_bytes.decode("utf-8")
tree = ast.parse(source)
checks = {}

loop = next(node for node in ast.walk(tree)
            if isinstance(node, ast.For) and isinstance(node.target, ast.Name)
            and node.target.id == "index" and isinstance(node.iter, ast.Call)
            and isinstance(node.iter.func, ast.Name)
            and node.iter.func.id == "range")
calls = []
for node in ast.walk(loop):
    if isinstance(node, ast.Call):
        name = node.func.id if isinstance(node.func, ast.Name) else None
        if name in {"source_signal_rejection", "submit_cover", "begin_model_turn"}:
            calls.append((node.lineno, name))
positions = {name: sorted(line for line, called in calls if called == name)
             for name in {"source_signal_rejection", "submit_cover", "begin_model_turn"}}
checks["source_preflight_before_any_cover"] = (
    bool(positions["source_signal_rejection"]) and
    bool(positions["submit_cover"]) and
    positions["source_signal_rejection"][0] < positions["submit_cover"][0])
checks["post_accept_source_gate_before_planner"] = (
    len(positions["source_signal_rejection"]) >= 2 and
    bool(positions["begin_model_turn"]) and
    positions["submit_cover"][0] < positions["source_signal_rejection"][1] <
    positions["begin_model_turn"][0])
checks["unknown_stop_is_recorded_without_action_authority"] = all(
    token in source for token in (
        '"decision_status": "STOP_SOURCE_SIGNAL_UNKNOWN"',
        '"input_authority_granted": False',
        '"planner_call_started": False',
    ))
checks["cover_release_requires_verified_empty_state"] = all(
    token in source for token in (
        'release.get("verified") is True',
        'release.get("keys_down") == []',
        'release.get("buttons_down") == []',
    ))
checks["exception_exit_registers_session_custody"] = (
    "atexit.register(custody_exit_hook)" in source and
    'self.process.stdin.write(\'{"op":"finish"}' in source and
    '"controller-events.jsonl"' in source and
    '"controller-cleanup.json"' in source)

result = {
    "schema": "map01-unknown-source-recovery-audit-v1",
    "candidate_sha256": hashlib.sha256(source_bytes).hexdigest(),
    "checks": checks,
    "failed_checks": [name for name, passed in checks.items() if not passed],
    "decision": "PASS_CONSTRUCTION_STRUCTURE" if all(checks.values()) else "FAIL",
    "scope": "source-only independent audit; no WAD, model, game, GUI, OS input, or session runtime",
}
(HERE / "audit.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                                 encoding="utf-8")
print(json.dumps(result, sort_keys=True))
if result["failed_checks"]:
    raise SystemExit(1)
