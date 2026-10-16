"""AST/custody construction checks only: never import or execute a client/producer."""
import argparse
import ast
import copy
import hashlib
import json
from pathlib import Path


SOURCE_FILES = (
    "main_client.py", "send_proposal.py", "close_proposal.py",
    "composed_client.py", "bounded_journal_client.py", "echo_peer.py", "producer.py",
)
CELL_IDS = tuple(f"{variant}__{condition}" for variant in
                 ("main", "composed", "bounded_journal") for condition in
                 ("healthy", "held_journal"))
VARIANT_SOURCES = {"main": "main_client.py", "composed": "composed_client.py",
                   "bounded_journal": "bounded_journal_client.py"}
ORIGINS = {"main_client.py": ("66822a57", "6e34f7c17300072e6739ded5e3f977974c2673be"),
           "send_proposal.py": ("fbd804e549b589e7e7e692ab4f89183d21451ca7", "5f408d10850f69db3bd1279c5018044120d9a2df"),
           "close_proposal.py": ("31f10e660d2e7e13d8fe05c9a56d3f3c5e71f324", "b1d4762ae4d3ccef8c4dd73198c01b247a2c07e7")}
CONSTANTS = {
    "request_timeout_ns": 50_000_000,
    "checkpoint_offset_ns": 250_000_000,
    "holder_release_offset_ns": 400_000_000,
    "cell_watchdog_ns": 6_000_000_000,
    "peer_readiness_timeout_ns": 2_000_000_000,
    "setup_rendezvous_timeout_ns": 1_000_000_000,
    "cleanup_join_timeout_ns": 350_000_000,
    "client_close_timeout_ns": 200_000_000,
}


def dump(node):
    return ast.dump(node, include_attributes=False)


def client(module):
    matches = [n for n in module.body if isinstance(n, ast.ClassDef)
               and n.name == "CodexAppServerClient"]
    if len(matches) != 1:
        raise ValueError("expected exactly one CodexAppServerClient")
    return matches[0]


def method(module, name):
    matches = [n for n in client(module).body if isinstance(n, ast.FunctionDef)
               and n.name == name]
    if len(matches) != 1:
        raise ValueError(f"expected exactly one method {name}")
    return matches[0]


def replace_method(module, name, replacement):
    cls = client(module)
    old = method(module, name)
    cls.body[cls.body.index(old)] = copy.deepcopy(replacement)


def closed_branch(function):
    matches = [n for n in ast.walk(function) if isinstance(n, ast.If)
               and dump(n.test) == dump(ast.parse("self._closed", mode="eval").body)]
    if len(matches) != 1:
        raise ValueError("expected one EOF branch")
    return matches[0]


def expected_composed(main, send, close):
    expected = copy.deepcopy(send)
    request = method(expected, "request")
    closed_branch(request).body = copy.deepcopy(closed_branch(method(main, "request")).body)
    for name in ("_read", "wait_notification"):
        replace_method(expected, name, method(main, name))
    replace_method(expected, "close", method(close, "close"))
    return expected


def expected_bounded(composed):
    expected = copy.deepcopy(composed)
    record = method(expected, "_record")
    if len(record.body) != 3 or not isinstance(record.body[2], ast.With):
        raise ValueError("unexpected original journal body")
    journal_body = copy.deepcopy(record.body[2].body)
    record.args.kwonlyargs.append(ast.arg(arg="deadline"))
    record.args.kw_defaults.append(ast.Constant(value=None))
    default_branch = ast.parse(
        "if deadline is None:\n    with self._journal_lock:\n        pass\n    return\n"
    ).body[0]
    default_branch.body[0].body = copy.deepcopy(journal_body)
    timed_branch = ast.parse(
        "if not self._journal_lock.acquire(timeout=max(0, deadline - time.monotonic())):\n"
        "    raise TimeoutError('app-server sent journal lock timed out; no send attempted')\n"
    ).body[0]
    guarded_body = ast.parse(
        "try:\n    pass\nfinally:\n    self._journal_lock.release()\n"
    ).body[0]
    guarded_body.body = journal_body
    record.body = record.body[:2] + [default_branch, timed_branch, guarded_body]
    write = method(expected, "_write")
    calls = [n for n in ast.walk(write) if isinstance(n, ast.Call)
             and dump(n.func) == dump(ast.parse("self._record", mode="eval").body)]
    if len(calls) != 1 or calls[0].keywords:
        raise ValueError("unexpected sent-journal call")
    calls[0].keywords.append(ast.keyword(arg="deadline", value=ast.Name(id="deadline", ctx=ast.Load())))
    return expected


def producer_protocol_errors(module):
    """Check fixture constants at their consumers without importing the producer."""
    errors = []

    def expression(text):
        return dump(ast.parse(text, mode="eval").body)

    def assigned_values(name):
        return [n.value for n in ast.walk(module) if isinstance(n, ast.Assign)
                and any(isinstance(t, ast.Name) and t.id == name for t in n.targets)]

    def timeout(call):
        return [dump(k.value) for k in call.keywords if k.arg == "timeout"]

    ready = assigned_values("ready_deadline_ns")
    if len(ready) != 1 or dump(ready[0]) != expression("time.monotonic_ns() + constants['peer_readiness_timeout_ns']"):
        errors.append("producer_readiness_constant_not_consumed")
    waits = [n for n in ast.walk(module) if isinstance(n, ast.Call)
             and isinstance(n.func, ast.Attribute) and n.func.attr == "wait"
             and isinstance(n.func.value, ast.Name)
             and n.func.value.id in ("caller_started", "holder_acquired")]
    expected_wait = expression("constants['setup_rendezvous_timeout_ns'] / 1_000_000_000")
    if len(waits) != 3 or sum(n.func.value.id == "caller_started" for n in waits) != 2 or sum(n.func.value.id == "holder_acquired" for n in waits) != 1 or any(n.args or timeout(n) != [expected_wait] for n in waits):
        errors.append("producer_setup_rendezvous_constants_not_consumed")
    communication = sorted([n for n in ast.walk(module) if isinstance(n, ast.Call)
                            and dump(n.func) == expression("worker.communicate")],
                           key=lambda n: n.lineno)
    expected_watchdog = expression("fixture['constants']['cell_watchdog_ns'] / 1_000_000_000")
    if len(communication) != 3 or timeout(communication[0]) != [expected_watchdog] or any(timeout(n) != [expression("0.50")] for n in communication[1:]):
        errors.append("producer_supervisor_watchdog_constant_not_consumed")
    watchdog_messages = []
    for node in ast.walk(module):
        if isinstance(node, ast.Dict):
            entries = {key.value: value for key, value in zip(node.keys, node.values)
                       if isinstance(key, ast.Constant) and isinstance(key.value, str)}
            kind = entries.get("exception_type")
            if isinstance(kind, ast.Constant) and kind.value == "ExternalCellWatchdog":
                watchdog_messages.append(entries.get("message"))
    expected_message = expression(
        "f\"{fixture['constants']['cell_watchdog_ns'] / 1_000_000_000:g} s containment boundary; no retry\""
    )
    if len(watchdog_messages) != 1 or watchdog_messages[0] is None or dump(watchdog_messages[0]) != expected_message:
        errors.append("producer_watchdog_error_duration_not_derived_from_fixture")
    # Setup allowances must not replace the hypothesis-bearing timing values.
    requests = [n for n in ast.walk(module) if isinstance(n, ast.Call)
                and dump(n.func) == expression("client.request")]
    if len(requests) != 1 or timeout(requests[0]) != [expression("constants['request_timeout_ns'] / 1_000_000_000")]:
        errors.append("producer_scientific_request_timeout_changed")
    checkpoint = assigned_values("checkpoint_target_ns")
    checkpoint_expression = expression("row['timestamps']['caller_started_ns'] + constants['checkpoint_offset_ns']")
    if len(checkpoint) != 1 or dump(checkpoint[0]) != checkpoint_expression:
        errors.append("producer_scientific_checkpoint_changed")
    releases = assigned_values("release_target")
    release_expression = expression("row['timestamps']['caller_started_ns'] + constants['holder_release_offset_ns']")
    if len(releases) != 2 or any(dump(n) != release_expression for n in releases):
        errors.append("producer_scientific_holder_release_changed")
    return errors


def check(source_dir, fixture_path):
    errors = []
    source_dir = Path(source_dir)
    fixture = json.loads(Path(fixture_path).read_text(encoding="utf-8"))
    if fixture.get("schema") != "issue59-request-journal-composition-fixture-v1":
        errors.append("fixture_schema")
    if fixture.get("fixture_id") != "59-REQUEST-JOURNAL-MUTEX-COMPOSITION-4D74-A02":
        errors.append("fixture_identity")
    if fixture.get("constants") != CONSTANTS:
        errors.append("fixture_constants")
    expected_cells = [{"cell_id": identifier, "variant": identifier.split("__")[0],
                       "condition": identifier.split("__")[1],
                       "source_file": VARIANT_SOURCES[identifier.split("__")[0]]}
                      for identifier in CELL_IDS]
    if fixture.get("cells") != expected_cells:
        errors.append("fixture_six_cell_order")
    expected_request = {"method": "echo", "id": 1, "params": {"payload": "journal-mutex-witness"}}
    if fixture.get("request") != expected_request or fixture.get("expected_result") != expected_request["params"]:
        errors.append("fixture_echo_contract")
    if fixture.get("request_wire") != json.dumps(expected_request, separators=(",", ":")) + "\n":
        errors.append("fixture_wire_contract")
    actual_hashes = {}
    trees = {}
    for name in SOURCE_FILES:
        content = (source_dir / name).read_bytes()
        actual_hashes[name] = hashlib.sha256(content).hexdigest()
        trees[name] = ast.parse(content.decode("utf-8"), filename=name)
        if name in ORIGINS:
            prefix, blob = ORIGINS[name]
            origin = fixture.get("source_origins", {}).get(name, {})
            ref = origin.get("ref_at_fetch", "")
            actual_blob = hashlib.sha1(b"blob " + str(len(content)).encode("ascii") + b"\0" + content).hexdigest()
            if origin.get("repository") != "Unjuno/agent-interface" or origin.get("git_blob") != blob or actual_blob != blob or len(ref) != 40 or not ref.startswith(prefix):
                errors.append(f"exact_source_origin:{name}")
    if fixture.get("source_sha256") != actual_hashes:
        errors.append("fixture_source_custody")
    for name in ("auditor.py", "construction_checks.py"):
        ast.parse((source_dir / name).read_text(encoding="utf-8"), filename=name)
    errors.extend(producer_protocol_errors(trees["producer.py"]))
    composed = expected_composed(trees["main_client.py"], trees["send_proposal.py"], trees["close_proposal.py"])
    if dump(trees["composed_client.py"]) != dump(composed):
        errors.append("composed_not_exact_donor_AST")
    changed_methods = {"__init__", "_write", "request", "notify", "close"}
    for node in client(trees["main_client.py"]).body:
        if isinstance(node, ast.FunctionDef) and node.name not in changed_methods:
            if dump(method(trees["composed_client.py"], node.name)) != dump(node):
                errors.append(f"untouched_main_method_changed:{node.name}")
    if dump(trees["bounded_journal_client.py"]) != dump(expected_bounded(composed)):
        errors.append("bounded_not_exact_journal_only_AST_change")
    for name in ("main_client.py", "composed_client.py", "bounded_journal_client.py"):
        # EOF branches must preserve main's explicit no-drain behavior.
        for fn in ("request", "wait_notification"):
            if dump(closed_branch(method(trees[name], fn)).body[0]) != dump(closed_branch(method(trees["main_client.py"], fn)).body[0]):
                errors.append(f"EOF_branch_changed:{name}:{fn}")
    return {"schema": "issue59-request-journal-construction-v1", "errors": errors,
            "source_sha256": actual_hashes,
            "result": "PASS_CONSTRUCTION" if not errors else "STOP"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", default=str(Path(__file__).parent))
    parser.add_argument("--fixture", required=True)
    args = parser.parse_args()
    try:
        result = check(args.source_dir, args.fixture)
    except (OSError, ValueError, TypeError, KeyError, SyntaxError, AttributeError) as exc:
        result = {"schema": "issue59-request-journal-construction-v1", "result": "STOP",
                  "errors": [f"construction_error:{type(exc).__name__}:{exc}"]}
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    raise SystemExit(0 if result["result"] == "PASS_CONSTRUCTION" else 1)


if __name__ == "__main__":
    main()
