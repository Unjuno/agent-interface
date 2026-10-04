"""Recheck A09/A10/A11 identities in a current-main + PR-head checkout."""
import argparse
import ast
import copy
import hashlib
import json
import subprocess
from pathlib import Path

CONTROLLER = Path("research/doom/map01_overlap_controller_v39.py")
PACKAGE = Path("research/doom/v39_adapter_partial_identity_taint_59_a09_a10_20261005")
FIXTURE = Path("research/doom/map01_v39_perkey_bridge_a01/results/construction-a01/candidate-events.jsonl")

def digest(data):
    return hashlib.sha256(data).hexdigest()

def source_from_git(root, ref):
    return subprocess.run(
        ["git", "show", f"{ref}:{CONTROLLER.as_posix()}"],
        cwd=root,
        check=True,
        stdout=subprocess.PIPE,
    ).stdout

def extract_projector(source, filename):
    tree = ast.parse(source.decode("utf-8"))
    node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "input_edge_receipts")
    env = {"hashlib": hashlib}
    module = ast.Module(body=[node], type_ignores=[])
    exec(compile(ast.fix_missing_locations(module), filename, "exec"), env)
    return node, env["input_edge_receipts"]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--integration-root", default=".", help="repository checkout of the tested merge tree")
    parser.add_argument("--candidate-ref", required=True, help="PR head/ref containing the candidate source")
    parser.add_argument("--expected-candidate-source-sha256", required=True)
    parser.add_argument("--expected-composed-source-sha256", required=True)
    parser.add_argument("--expected-test-sha256", required=True)
    args = parser.parse_args()
    root = Path(args.integration_root).resolve()
    package = root / PACKAGE
    current_bytes = (root / CONTROLLER).read_bytes()
    candidate_bytes = source_from_git(root, args.candidate_ref)
    fixture_path = root / FIXTURE
    fixture_sha = "ad0b1c29da4b626e9be27e8716cdabfbb25ac49dcf0abd4bda4bd2f7a9f84e4e"
    current_node, current_fn = extract_projector(current_bytes, str(root / CONTROLLER))
    candidate_node, candidate_fn = extract_projector(candidate_bytes, args.candidate_ref)
    checks = 0
    errors = []

    def ck(value, message):
        nonlocal checks
        checks += 1
        if not value:
            errors.append(message)

    ck(ast.dump(candidate_node, include_attributes=False) == ast.dump(current_node, include_attributes=False), "target projector AST preserved across composition")
    ck(digest(candidate_bytes) == args.expected_candidate_source_sha256, "candidate branch source pin")
    ck(digest(current_bytes) == args.expected_composed_source_sha256, "composed source pin")
    test_bytes = (root / "research/doom/test_map01_v39_typed_state_feedback.py").read_bytes()
    ck(digest(test_bytes) == args.expected_test_sha256, "composed test pin")
    raw_fixture = fixture_path.read_bytes()
    ck(digest(raw_fixture) == fixture_sha, "retained raw fixture pin")

    fixture = [json.loads(line) for line in raw_fixture.decode("utf-8").splitlines() if line]
    down = next(row for row in fixture if row.get("event") == "input_admission")
    up = next(row for row in fixture if row.get("event") == "input_release_measurement")
    replay = json.loads((package / "REPLAY_RESULT.json").read_text(encoding="utf-8-sig"))
    mutations = []
    for suite in ("A09", "A10"):
        for case in replay[suite]["cases"]:
            event = copy.deepcopy(down)
            event[case["outer"][0]] = case["outer"][1]
            event["physical_key_measurement"]["adapter_edge"][case["nested"]] = case["value"]
            mutations.append((f"{suite}:{case['outer'][0]}:{case['nested']}:{case['value']!r}", [copy.deepcopy(down), event, copy.deepcopy(up)]))
    a11 = json.loads((package / "A11_RESULT.json").read_text(encoding="utf-8-sig"))
    for case in a11["cases"]:
        event = copy.deepcopy(down)
        event[case["outer_field"]] = case["value"]
        mutations.append((f"A11:{case['outer_field']}:{case['value']!r}", [copy.deepcopy(down), event, copy.deepcopy(up)]))

    for label, events in mutations:
        branch_output = candidate_fn(copy.deepcopy(events))
        composed_output = current_fn(copy.deepcopy(events))
        ck(branch_output == composed_output, "candidate/composed parity " + label)
        adapter_rows = [row for row in composed_output if row.get("status", "").startswith("adapter_edge_")]
        paired = [row for row in adapter_rows if row.get("status") == "adapter_edge_brackets_paired"]
        ck(not paired, "no paired timing " + label)
        ck(bool(adapter_rows) and all(
            row.get("status") == "adapter_edge_receipt_incomplete"
            and row.get("down_edge_interval_ns") is None
            and row.get("up_edge_interval_ns") is None
            for row in adapter_rows
        ), "fail-closed incomplete null intervals " + label)

    report = {
        "audit": "PASS" if not errors else "FAIL",
        "checks": checks,
        "errors": errors,
        "mutations": len(mutations),
        "candidate_source_sha256": digest(candidate_bytes),
        "composed_source_sha256": digest(current_bytes),
        "composed_test_sha256": digest(test_bytes),
        "fixture_sha256": digest(raw_fixture),
        "scope": "independent AST parity and raw replay for A09/A10/A11 against the supplied latest-main composition; synthetic projector only",
    }
    print(json.dumps(report, indent=2))
    raise SystemExit(bool(errors))

if __name__ == "__main__":
    main()
