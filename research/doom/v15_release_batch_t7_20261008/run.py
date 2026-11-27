"""Inject sink failures into exact current-main release publication methods."""
import ast
import copy
import hashlib
import importlib.util
import json
import subprocess
from pathlib import Path
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
FREEZE = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))
MAIN = FREEZE["current_main_commit"]
BACKEND_PATH = REPO / FREEZE["current_backend_path"]
T6_PATH = REPO / "research/doom/v15_release_batch_t6_20261008/run.py"
spec = importlib.util.spec_from_file_location("t6_release_adapter", T6_PATH)
t6 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(t6)


def exact_backend_harness():
    tree = ast.parse(BACKEND_PATH.read_text(encoding="utf-8"))
    backend = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "Backend")
    names = {"_delivery_ledger", "_set_delivery_state", "_copy_delivery_ledger",
             "_attach_delivery_ledger", "_publish_incomplete_release_batch",
             "_finish_incomplete_release_batch", "_publish_release_batch"}
    methods = [node for node in backend.body if isinstance(node, ast.FunctionDef) and node.name in names]
    if {node.name for node in methods} != names:
        raise AssertionError("exact current-main fault-boundary methods missing")
    wrapper = ast.ClassDef(name="Harness", bases=[], keywords=[], body=methods, decorator_list=[])
    scope = {}
    exec(compile(ast.fix_missing_locations(ast.Module(body=[wrapper], type_ignores=[])), str(BACKEND_PATH), "exec"), scope)
    return scope["Harness"]


class Lease:
    intent_token = "intent-1"


def publication_attempt(accept_then_raise):
    Harness = exact_backend_harness()
    owner = t6.Owner("owner-1", [(400, 410)])
    emitted = []
    def sink(row):
        if row["key"] == "Up":
            if accept_then_raise:
                emitted.append(copy.deepcopy(row))
            raise RuntimeError("injected sink failure after accept" if accept_then_raise
                               else "injected sink failure before accept")
        emitted.append(copy.deepcopy(row))
    backend = Harness()
    backend.owner, backend.lease, backend.emit = owner, Lease(), sink
    backend._last_release_batch_delivery = None
    first, receipt0 = t6.release_row("space", 320, 305, 330, 0)
    second, receipt1 = t6.release_row("Up", 350, 335, 360, 0)
    owner.records.extend([receipt0, receipt1])
    context = {"rows": [first, second], "identifier": "plan-1", "step": 0}
    backend._release_batch = SimpleNamespace(context=context)
    publication_error = None
    try:
        backend._publish_release_batch(context)
    except RuntimeError as error:
        publication_error = error
        backend._finish_incomplete_release_batch(context, error, "publication_exception")
    else:
        raise AssertionError("injected publication failure did not occur")
    ledger = publication_error.release_batch_publication
    if [row["state"] for row in ledger["positions"]] != ["confirmed", "unknown"]:
        raise AssertionError("exact backend did not retain confirmed/unknown delivery states")
    return emitted, ledger


def run_case():
    backend_blob = subprocess.check_output(
        ["git", "-C", str(REPO), "rev-parse", f"{MAIN}:{FREEZE['current_backend_path']}"], text=True).strip()
    if backend_blob != FREEZE["current_backend_blob"]:
        raise AssertionError("current-main backend blob drift")
    adapter = REPO / FREEZE["adapter_source_path"]
    if hashlib.sha256(adapter.read_bytes()).hexdigest() != FREEZE["adapter_source_sha256"]:
        raise AssertionError("frozen adapter source changed")

    missing_rows, missing_ledger = publication_attempt(False)
    missing = t6.adapt(missing_rows)
    if (len(missing_rows) != 1 or missing["trace_integrity"] != "HOLD_INCOMPLETE_RELEASE_BATCH" or
            missing["attributions"][0]["status"] != "UNRESOLVED"):
        raise AssertionError("pre-acceptance sink failure did not fail closed")

    accepted_rows, accepted_ledger = publication_attempt(True)
    accepted = t6.adapt(accepted_rows)
    if (len(accepted_rows) != 2 or
            [row["release_batch_delivery_position"] for row in accepted_rows] != [0, 1] or
            [row["release_batch_position"] for row in accepted_rows] != [0, 1] or
            accepted["trace_integrity"] != "SOURCE_ROWS_JOINED" or
            accepted["attributions"][0]["status"] != "TEMPORALLY_UNIQUE" or
            accepted["attributions"][0]["causal_attribution"] != "NOT_ESTABLISHED"):
        raise AssertionError("stored full batch after ambiguous acknowledgment did not remain row-evidence scoped")

    return {
        "schema": "v15-release-publication-failure-t7-result-v1",
        "main_commit": MAIN,
        "adapter_source_sha256": FREEZE["adapter_source_sha256"],
        "disposition": "PASS_FAIL_CLOSED_ON_MISSING_ROW_ROW_SCOPED_ON_ACCEPTED_BATCH",
        "before_accept_failure": {"producer_ledger_states": [row["state"] for row in missing_ledger["positions"]],
                                  "visible_release_rows": len(missing_rows),
                                  "trace_integrity": missing["trace_integrity"],
                                  "attribution": missing["attributions"][0]["status"]},
        "after_accept_failure": {"producer_ledger_states": [row["state"] for row in accepted_ledger["positions"]],
                                 "visible_release_rows": len(accepted_rows),
                                 "delivery_positions": [row["release_batch_delivery_position"] for row in accepted_rows],
                                 "trace_integrity": accepted["trace_integrity"],
                                 "attribution": accepted["attributions"][0]["status"],
                                 "causal_attribution": accepted["attributions"][0]["causal_attribution"],
                                 "interpretation": "all members are directly present in the adapter input; no producer acknowledgment or causal claim is inferred"},
        "scope": "exact current-main publication/failure methods plus bundled T5 adapter; synthetic sink, owner receipts, and scorer event; no physical input",
    }


if __name__ == "__main__":
    print(json.dumps(run_case(), sort_keys=True))
