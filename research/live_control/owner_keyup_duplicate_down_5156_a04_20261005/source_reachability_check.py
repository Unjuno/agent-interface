"""Read-only source-bound check of the canonical MAP01 repeated-DOWN path."""
import ast
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
MAIN = "86a2694c6251c2d7df2f69dbea490ec037903ff7"
SOURCES = {
    "controller": "research/doom/map01_overlap_controller_v39.py",
    "executor": "research/live_control/executor_v3.py",
    "session_v4": "research/live_control/session_v4.py",
    "session_v5": "research/live_control/session_v5.py",
    "session_v6": "research/live_control/session_v6.py",
    "session_v7": "research/live_control/session_v7.py",
    "session_v8": "research/live_control/session_v8.py",
    "session_v9": "research/live_control/session_v9.py",
    "session_v10": "research/live_control/session_v10.py",
    "coast": "research/live_control/coast_backend_v1.py",
    "doom_typed_coast": "research/doom/doom_typed_coast_backend_v1.py",
    "doom_retained_input_v4": "research/doom/doom_retained_input_backend_v4.py",
}


def source(path):
    return subprocess.check_output(["git", "show", MAIN + ":" + path], cwd=ROOT)


def module_for(body):
    return ast.fix_missing_locations(ast.Module(body=body, type_ignores=[]))


def decode(blob):
    return blob.decode("utf-8")


sources = {key: source(path) for key, path in SOURCES.items()}
controller_tree = ast.parse(sources["controller"])
compile_fn = next(node for node in controller_tree.body
                  if isinstance(node, ast.FunctionDef) and node.name == "compile_commands")
compile_cover_fn = next(node for node in controller_tree.body
                         if isinstance(node, ast.FunctionDef) and node.name == "compile_cover")
ns = {}
exec(compile(module_for([compile_fn, compile_cover_fn]), SOURCES["controller"], "exec"), ns)
table_node = next(node.value for node in ast.walk(compile_fn)
                  if isinstance(node, ast.Assign)
                  and any(isinstance(t, ast.Name) and t.id == "table" for t in node.targets))
table = ast.literal_eval(table_node)
extents_node = next(node.value for node in ast.walk(compile_fn)
                    if isinstance(node, ast.Assign)
                    and any(isinstance(t, ast.Name) and t.id == "extents" for t in node.targets))
extents = ast.literal_eval(extents_node)
commands = [{"action": action, "extent": extent}
            for action in table for extent in extents]
compiled = [ns["compile_commands"]([command]) for command in commands]
all_unique = all(len(step["keys"]) == len(set(step["keys"]))
                 for program in compiled for step in program)
assert all_unique
assert all(len(program) == 1 and program[0]["op"] == "hold" for program in compiled)

# Extract the exact inherited whole-program validator without importing X11/PIL.
base_tree = ast.parse(sources["session_v4"])
backend = next(node for node in base_tree.body
               if isinstance(node, ast.ClassDef) and node.name == "Backend")
validate = next(node for node in backend.body
                if isinstance(node, ast.FunctionDef) and node.name == "validate")
needed = []
for node in base_tree.body:
    if isinstance(node, ast.FunctionDef) and node.name == "number":
        needed.append(node)
    if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id in ("TEXT", "KEYS")
            for target in node.targets):
        needed.append(node)
needed.append(ast.ClassDef(name="Backend", bases=[], keywords=[], body=[validate], decorator_list=[]))
base_ns = {"math": __import__("math")}
exec(compile(module_for(needed), SOURCES["session_v4"], "exec"), base_ns)
validator = base_ns["Backend"]()

pair_count = 0
cover_pair_count = 0
cover_repeat_same_command_cases = 0
for first in commands:
    for second in commands:
        sequence = [first, second]
        program = ns["compile_commands"](sequence)
        validator.validate(program)
        pair_count += 1
        covered = ns["compile_cover"](sequence)
        validator.validate([step if step["op"] != "coast" else {"op": "observe"}
                            for step in covered])
        holds = [step for step in covered if step["op"] == "hold"]
        assert all(len(step["keys"]) == len(set(step["keys"])) for step in holds)
        if first == second:
            cover_repeat_same_command_cases += 1
        cover_pair_count += 1
try:
    validator.validate([{"op": "hold", "keys": ["Up", "Up"], "duration_ms": 180}])
except ValueError:
    duplicate_hold_rejected = True
else:
    duplicate_hold_rejected = False
assert duplicate_hold_rejected

# Verify the actual inheritance route and the base hold's finally-up structure.
trees = {key: ast.parse(blob) for key, blob in sources.items()}
chain = {
    "session_v5": "import session_v4 as previous",
    "session_v6": "from session_v5 import Backend as Previous",
    "session_v7": "from session_v6 import Backend as Previous",
    "session_v8": "from session_v7 import Backend as Previous",
    "session_v9": "from session_v8 import Backend as Previous",
    "session_v10": "from session_v9 import Backend as Previous",
    "coast": "from session_v10 import Backend as Previous",
    "doom_typed_coast": "from coast_backend_v1 import Backend as Previous",
    "doom_retained_input_v4": "from doom_typed_coast_backend_v1 import Backend as Previous",
}
chain_verified = all(fragment in decode(sources[key]) for key, fragment in chain.items())
assert chain_verified
session4_backend = next(node for node in trees["session_v4"].body
                        if isinstance(node, ast.ClassDef) and node.name == "Backend")
execute = next(node for node in session4_backend.body
               if isinstance(node, ast.FunctionDef) and node.name == "execute")
hold_branches = [node for node in ast.walk(execute)
                 if isinstance(node, ast.If) and isinstance(node.test, ast.Compare)
                 and isinstance(node.test.left, ast.Name)
                 and node.test.left.id == "op"
                 and len(node.test.ops) == 1 and isinstance(node.test.ops[0], ast.Eq)
                 and len(node.test.comparators) == 1
                 and isinstance(node.test.comparators[0], ast.Constant)
                 and node.test.comparators[0].value == "hold"]
assert hold_branches
has_finally_release = False
for branch in hold_branches:
    for node in ast.walk(branch):
        if isinstance(node, ast.Try) and node.finalbody:
            for child in ast.walk(module_for(node.finalbody)):
                if (isinstance(child, ast.Call) and isinstance(child.func, ast.Attribute)
                        and child.func.attr == "raw" and len(child.args) >= 2
                        and isinstance(child.args[1], ast.Constant)
                        and child.args[1].value is False):
                    has_finally_release = True
assert has_finally_release
assert "self.owner.call('down' if down else 'up', self.lease, key)" in decode(sources["session_v5"])
assert 'record = self.owner.call("down", self.lease, key)' in decode(sources["doom_retained_input_v4"])
assert "self.backend.validate(steps)" in decode(sources["executor"])
assert "self.active is not None" in decode(sources["executor"])

result = {
    "schema": "map01-duplicate-down-source-reachability-v1",
    "main": MAIN,
    "source_sha256": {key: hashlib.sha256(blob).hexdigest() for key, blob in sources.items()},
    "controller_actions": len(table),
    "extents": len(extents),
    "single_command_programs": len(compiled),
    "ordered_two_command_programs": pair_count,
    "ordered_two_command_cover_programs": cover_pair_count,
    "same_command_repeated_cover_programs": cover_repeat_same_command_cases,
    "all_compiled_hold_key_lists_unique": all_unique,
    "duplicate_key_hold_rejected_before_dispatch": duplicate_hold_rejected,
    "hold_branch_has_finally_key_up": has_finally_release,
    "inheritance_chain_verified": chain_verified,
    "executor_validates_before_dispatch_and_refuses_busy_submit": True,
    "scope": "source-extracted canonical MAP01 path; no imports, X11, model, game, or input",
}
Path(__file__).with_name("SOURCE_REACHABILITY.json").write_text(
    json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps({key: result[key] for key in (
    "schema", "main", "controller_actions", "extents", "single_command_programs",
    "ordered_two_command_programs", "ordered_two_command_cover_programs",
    "same_command_repeated_cover_programs", "all_compiled_hold_key_lists_unique",
    "duplicate_key_hold_rejected_before_dispatch", "hold_branch_has_finally_key_up",
    "inheritance_chain_verified", "executor_validates_before_dispatch_and_refuses_busy_submit",
)}, sort_keys=True))
