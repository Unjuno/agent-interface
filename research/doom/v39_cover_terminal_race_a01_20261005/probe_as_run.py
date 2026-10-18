import ast
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FREEZE = json.loads((ROOT / "FREEZE.json").read_text(encoding="utf-8"))
SOURCE_PATH = "research/doom/map01_overlap_controller_v39.py"
repo = ROOT.parent.parent / "work" / "verify-pr-7849-head"
commit = subprocess.run(["git", "rev-parse", "origin/main"], cwd=repo,
                       check=True, capture_output=True, text=True).stdout.strip()
if commit != FREEZE["source_commit"]:
    raise SystemExit("FROZEN_REF_MOVED")
source = subprocess.run(["git", "show", f"origin/main:{SOURCE_PATH}"], cwd=repo,
                        check=True, capture_output=True).stdout
if hashlib.sha256(source).hexdigest() != FREEZE["source_sha256"]:
    raise SystemExit("FROZEN_SOURCE_HASH_MISMATCH")
tree = ast.parse(source)
function = next(node for node in tree.body if isinstance(node, ast.FunctionDef)
                and node.name == "cancel_invalidated_cover")
source_function = ast.get_source_segment(source.decode("utf-8"), function)
assert source_function.count('terminal.get("status") != "cancelled"') == 1
candidate_function = source_function.replace(
    'terminal.get("status") != "cancelled"',
    'terminal.get("status") not in ("cancelled", "completed")',
)

def compile_function(text, filename):
    module = ast.parse(text)
    namespace = {"json": json}
    exec(compile(module, filename, "exec"), namespace)
    return namespace["cancel_invalidated_cover"]

baseline = compile_function(source_function, f"{SOURCE_PATH}@{commit}")
candidate = compile_function(candidate_function, f"candidate:{SOURCE_PATH}@{commit}")

class Stdin:
    def __init__(self, log): self.log = log
    def write(self, value): self.log.append(("write", value))
    def flush(self): self.log.append(("flush", None))
class Process:
    def __init__(self, log): self.stdin = Stdin(log)
class Planner:
    def __init__(self, log): self.log = log
    def interrupt(self, handle):
        self.log.append(("interrupt", handle))
        return {"status": "interrupted"}

def exercise(helper, status, release):
    operations = []
    terminal = {"event": "terminal", "id": "cover-race", "status": status,
                "release": release}
    def wait(predicate):
        operations.append(("wait", terminal["status"]))
        if not predicate(terminal):
            raise AssertionError("terminal waiter predicate rejected fixture row")
        return terminal
    try:
        interrupt, result = helper(Planner(operations), "planner-turn", Process(operations),
                                   wait, "cover-race")
        disposition = {"outcome": "accepted", "planner_interrupt": interrupt,
                       "terminal_status": result["status"]}
    except Exception as exc:
        disposition = {"outcome": "raised", "error_type": type(exc).__name__,
                       "error": str(exc)}
    return {"terminal": terminal, "result": disposition,
            "operations": [{"event": e, "value": str(v)} for e, v in operations]}

rows = []
scenarios = [
    ("cancelled_neutral", "cancelled", {"verified": True, "keys_down": [], "buttons_down": []}),
    ("completed_neutral", "completed", {"verified": True, "keys_down": [], "buttons_down": []}),
    ("completed_nonempty", "completed", {"verified": True, "keys_down": ["space"], "buttons_down": []}),
    ("failed_neutral", "failed", {"verified": True, "keys_down": [], "buttons_down": []}),
]
for name, status, release in scenarios:
    rows.append({"case": name, "baseline": exercise(baseline, status, release),
                 "candidate": exercise(candidate, status, release)})
result = {
    "schema": "v39-cover-terminal-race-probe-a01-v1",
    "source_commit": commit,
    "source_path": SOURCE_PATH,
    "source_sha256": FREEZE["source_sha256"],
    "probe_sha256": FREEZE["probe_sha256"],
    "cases": rows,
    "scope": "exact helper function body from frozen current-main blob, with planner/process/test-terminal doubles only",
}
(ROOT / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps({"schema": result["schema"], "source_commit": commit,
                  "cases": [{"case": row["case"],
                             "baseline": row["baseline"]["result"]["outcome"],
                             "candidate": row["candidate"]["result"]["outcome"]}
                            for row in rows]}, indent=2))
