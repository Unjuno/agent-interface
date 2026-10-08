"""Execute the exact current-main V39 measurement dispatch seam offline."""
import argparse
import ast
import hashlib
import json
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
FREEZE = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))
MAIN = FREEZE["main_commit"]


def source(path):
    expected = FREEZE["sources"][path]
    blob = subprocess.check_output(["git", "-C", str(REPO), "rev-parse", f"{MAIN}:{path}"], text=True).strip()
    if blob != expected:
        raise AssertionError(f"source blob drift: {path}")
    return subprocess.check_output(["git", "-C", str(REPO), "show", f"{MAIN}:{path}"])


def module_nodes(tree):
    constants = {}
    for node in tree.body:
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            value = node.value
            names = [target.id for target in targets if isinstance(target, ast.Name)]
            if value is not None and any(name in {"NODE", "CLI", "DISABLED_FEATURES", "DISABLED_MCPS"} for name in names):
                constants.update({name: node for name in names})
    return constants


def controller_contract():
    path = "research/doom/map01_overlap_controller_v39.py"
    tree = ast.parse(source(path).decode("utf-8"))
    command = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "session_command")
    main = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "main")
    constants = module_nodes(tree)
    wanted = {"NODE", "CLI", "DISABLED_FEATURES", "DISABLED_MCPS"}
    if set(constants) != wanted:
        raise AssertionError("command constants missing")
    parser_call = None
    report_expr = None
    for node in ast.walk(main):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "add_argument":
            if node.args and isinstance(node.args[0], ast.Constant) and node.args[0].value == "--measurement-session":
                parser_call = node
        if isinstance(node, ast.Dict):
            for key, value in zip(node.keys, node.values):
                if isinstance(key, ast.Constant) and key.value == "measurement_session":
                    report_expr = value
    if parser_call is None or report_expr is None:
        raise AssertionError("measurement flag or report label expression missing")
    local = {"argparse": argparse}
    for name, node in constants.items():
        exec(compile(ast.fix_missing_locations(ast.Module(body=[node], type_ignores=[])), path, "exec"), local)
    local["HERE"] = REPO / "research/doom"
    local["Path"] = Path
    local["sys"] = __import__("sys")
    exec(compile(ast.fix_missing_locations(ast.Module(body=[command], type_ignores=[])), path, "exec"), local)
    parser = argparse.ArgumentParser()
    exec(compile(ast.fix_missing_locations(ast.Module(body=[ast.Expr(value=parser_call)], type_ignores=[])), path, "exec"), {"parser": parser})
    return local, parser, report_expr


def evidence_chain():
    session_path = "research/doom/session_map01_v15.py"
    session = ast.parse(source(session_path).decode("utf-8"))
    session_text = source(session_path).decode("utf-8")
    release = source("research/doom/doom_owner_thread_release_batch_backend_v1.py").decode("utf-8")
    backend = source("research/doom/doom_typed_release_backend_v2.py").decode("utf-8")
    transition = source("research/live_control/input_transition_owner_v4.py").decode("utf-8")
    owner = source("research/live_control/input_owner_v12.py").decode("utf-8")
    if "doom_owner_thread_release_batch_backend_v1" not in session_text:
        raise AssertionError("V15 session does not select release-batch telemetry backend")
    if "doom_typed_release_backend_v2" not in release or "input_transition_owner_v4" not in release:
        raise AssertionError("V15 release backend composition missing")
    if "input_owner_v12" not in transition:
        raise AssertionError("transition owner does not delegate to InputOwner V12")
    for field in ("key_release_attempts", "key_release_intervals_ns"):
        if field not in owner:
            raise AssertionError(f"per-key release field missing: {field}")
    if not any(isinstance(node, ast.FunctionDef) and node.name == "_merge_sources" for node in session.body):
        raise AssertionError("V15 source manifest merge absent")
    return {
        "session_path": session_path,
        "release_backend_path": "research/doom/doom_owner_thread_release_batch_backend_v1.py",
        "typed_backend_path": "research/doom/doom_typed_release_backend_v2.py",
        "transition_owner_path": "research/live_control/input_transition_owner_v4.py",
        "input_owner_path": "research/live_control/input_owner_v12.py",
        "per_key_fields": ["key_release_attempts", "key_release_intervals_ns"],
    }


def run_case():
    local, parser, report_expr = controller_contract()
    chain = evidence_chain()
    rows = []
    for mode, argv in (("default", []), ("measurement", ["--measurement-session"])):
        args = parser.parse_args(argv)
        args.seed = 990605
        args.load_fixture_manifest = REPO / "fixture-manifest.json"
        runtime = REPO / f"synthetic-{mode}"
        command = local["session_command"](args, runtime)
        expected_session = "session_map01_v15.py" if mode == "measurement" else "session_map01_v12.py"
        if Path(command[1]).name != expected_session:
            raise AssertionError(f"{mode} mode selected wrong session")
        if command[command.index("--seed") + 1] != "990605":
            raise AssertionError("seed was not preserved")
        if command[command.index("--timeout-seconds") + 1] != "600":
            raise AssertionError("timeout was not preserved")
        if command[command.index("--out") + 1] != str(runtime):
            raise AssertionError("runtime output path was not preserved")
        if command[command.index("--skill") + 1] != "1":
            raise AssertionError("session skill was not preserved")
        if command[command.index("--load-fixture-manifest") + 1] != str(args.load_fixture_manifest.resolve()):
            raise AssertionError("fixture manifest was not preserved")
        label = eval(compile(ast.Expression(report_expr), "v39-report-label", "eval"), {"args": args})
        expected_label = "v15_scorer_only_per_key_release" if mode == "measurement" else "v12_default"
        if label != expected_label:
            raise AssertionError(f"{mode} report label mismatch")
        rows.append({"mode": mode, "measurement_session": bool(args.measurement_session),
                     "session": expected_session, "report_label": label,
                     "command_arguments_preserved": True})
    return {"schema": "v39-measurement-dispatch-a01-result-v1", "main_commit": MAIN,
            "disposition": "PASS_FUTURE_DISPATCH_CONSTRUCTION_ONLY", "modes": rows,
            "instrumentation_chain": chain,
            "scope": "exact current-main session_command and parser/report expressions; pinned V15 source capability; no session/game/model/GUI/input execution"}


if __name__ == "__main__":
    print(json.dumps(run_case(), sort_keys=True))
