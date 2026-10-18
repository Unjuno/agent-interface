import ast
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FREEZE = json.loads((ROOT / "FREEZE_A01.json").read_text(encoding="utf-8"))
SOURCE_PATH = "research/doom/map01_overlap_controller_v39.py"
repo = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=ROOT,
                     check=True, capture_output=True, text=True).stdout.strip()
source = subprocess.run(["git", "show", f"{FREEZE['source_commit']}:{SOURCE_PATH}"], cwd=repo,
                        check=True, capture_output=True).stdout
if hashlib.sha256(source).hexdigest() != FREEZE["source_sha256"]:
    raise SystemExit("FROZEN_SOURCE_HASH_MISMATCH")
tree = ast.parse(source)
function = next(node for node in tree.body if isinstance(node, ast.FunctionDef)
                and node.name == "cancel_invalidated_cover")
source_function = ast.get_source_segment(source.decode("utf-8"), function)
needle = 'terminal.get("status") != "cancelled"'
if source_function.count(needle) != 1:
    raise SystemExit("FROZEN_HELPER_SHAPE_MISMATCH")
candidate_function = source_function.replace(
    needle, 'terminal.get("status") not in ("cancelled", "completed")')

def load_function(function_source, filename):
    namespace = {"json": json}
    exec(compile(ast.parse(function_source), filename, "exec"), namespace)
    return namespace["cancel_invalidated_cover"]

baseline = load_function(source_function, f"{SOURCE_PATH}@{FREEZE['source_commit']}")
candidate = load_function(candidate_function, "candidate-completed-neutral")

class Stdin:
    def __init__(self, events): self.events = events
    def write(self, value): self.events.append(("write", value))
    def flush(self): self.events.append(("flush", None))
class Process:
    def __init__(self, events): self.stdin = Stdin(events)
class Planner:
    def __init__(self, events): self.events = events
    def interrupt(self, handle):
        self.events.append(("interrupt", handle))
        return {"status": "interrupted"}

def exercise(helper, status, release):
    events = []
    terminal = {"event": "terminal", "id": "cover-race", "status": status,
                "release": release}
    def wait(predicate):
        events.append(("wait", status))
        if not predicate(terminal):
            raise AssertionError("terminal predicate rejected fixture")
        return terminal
    try:
        interrupt, returned = helper(Planner(events), "planner-turn", Process(events),
                                     wait, "cover-race")
        outcome = {"outcome": "accepted", "terminal_status": returned["status"],
                   "planner_interrupt": interrupt}
    except Exception as exc:
        outcome = {"outcome": "raised", "error_type": type(exc).__name__,
                   "error": str(exc)}
    return {"terminal": terminal, "outcome": outcome,
            "operations": [{"event": event, "value": str(value)} for event, value in events]}

cases = []
for name, status, release in (
    ("cancelled_neutral", "cancelled", {"verified": True, "keys_down": [], "buttons_down": []}),
    ("completed_neutral", "completed", {"verified": True, "keys_down": [], "buttons_down": []}),
    ("completed_nonempty", "completed", {"verified": True, "keys_down": ["space"], "buttons_down": []}),
    ("failed_neutral", "failed", {"verified": True, "keys_down": [], "buttons_down": []}),
):
    cases.append({"case": name, "baseline": exercise(baseline, status, release),
                  "candidate": exercise(candidate, status, release)})
result = {
    "schema": "v39-cover-terminal-race-reproduction-a01-v1",
    "source_commit": FREEZE["source_commit"],
    "source_sha256": FREEZE["source_sha256"],
    "reproduction_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    "cases": cases,
    "scope": "portable replay of the frozen controller helper with planner/process/terminal doubles only",
}
(ROOT / "reproduction_a01.json").write_text(
    json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps({"schema": result["schema"], "cases": [
    {"case": case["case"], "baseline": case["baseline"]["outcome"]["outcome"],
     "candidate": case["candidate"]["outcome"]["outcome"]} for case in cases]}, indent=2))
