"""Compose exact current-main release publication with the frozen T5 adapter."""
import ast
import copy
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
FREEZE = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))
MAIN = FREEZE["current_main_commit"]
BACKEND = REPO / FREEZE["current_backend_path"]
sys.path.insert(0, str(HERE / "candidate"))
from adapter import adapt_session_records


def extract_backend():
    tree = ast.parse(BACKEND.read_text(encoding="utf-8"))
    backend = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "Backend")
    wanted = {"_delivery_ledger", "_set_delivery_state", "_publish_release_batch"}
    methods = [node for node in backend.body if isinstance(node, ast.FunctionDef) and node.name in wanted]
    if {node.name for node in methods} != wanted:
        raise AssertionError("could not extract exact release methods")
    wrapper = ast.ClassDef(name="Harness", bases=[], keywords=[], body=methods, decorator_list=[])
    scope = {}
    exec(compile(ast.fix_missing_locations(ast.Module(body=[wrapper], type_ignores=[])), str(BACKEND), "exec"), scope)
    return scope["Harness"]


class Owner:
    def __init__(self, owner_id, keycode_samples):
        self.owner_id = owner_id
        self.records = []
        self.keycode_samples = iter(keycode_samples)
    def call(self, method, *_args):
        if method != "input_state":
            raise AssertionError(f"unexpected owner method: {method}")
        started, finished = next(self.keycode_samples)
        return {"owner_id": self.owner_id, "owned_keycodes": [],
                "sample_started_ns": started, "sample_finished_ns": finished}


def release_row(key, sync_ns, caller_start, caller_end, receipt_count):
    owner_id, token, identifier, step = "owner-1", "intent-1", "plan-1", 0
    receipt = {"event": "owner_explicit_keyup", "operation": "up", "key": key,
               "owner_id": owner_id, "intent_token": token,
               "owner_keyrelease_started_ns": sync_ns - 10,
               "owner_sync_returned_ns": sync_ns,
               "server_sync_completed": True, "physical_verification_authoritative": False}
    row = {"event": "input_release_transition", "operation": "up", "key": key,
           "id": identifier, "step": step, "owner_id": owner_id, "intent_token": token,
           "release_call_started_ns": caller_start, "release_call_returned_ns": caller_end,
           "owner_thread_keyup_receipt": receipt,
           "owner_thread_keyup_verified": True,
           "owner_cleanup_record_count_before_release": receipt_count,
           "backend_owned_before_release": True, "ordinary_release_candidate": True,
           "release_batch_identifier": identifier, "release_batch_step": step}
    return row, receipt


def exact_published_rows():
    Harness = extract_backend()
    owner = Owner("owner-1", [(400, 410), (500, 510)])
    emitted = []
    class Lease:
        intent_token = "intent-1"
    backend = Harness()
    backend.owner, backend.lease, backend.emit = owner, Lease(), emitted.append
    backend._last_release_batch_delivery = None
    context = {"rows": [], "identifier": "plan-1", "step": 0}
    for key, sync_ns, start, end in (("space", 320, 305, 330), ("Up", 350, 335, 360)):
        row, receipt = release_row(key, sync_ns, start, end, len(owner.records))
        owner.records.append(receipt)
        context["rows"].append(row)
        backend._publish_release_batch(context)
    positions = [row.get("release_batch_delivery_position") for row in emitted]
    states = [position.get("state") for position in context["delivery_ledger"]["positions"]]
    if positions != [0, 1] or states != ["confirmed", "confirmed"]:
        raise AssertionError("exact backend delivery ledger did not advance monotonically")
    if any(row.get("owner_transition_verified") is not True or
           row.get("physical_verification_authoritative") is not False for row in emitted):
        raise AssertionError("exact backend emitted unexpected release verification flags")
    return emitted


def sample(ns, kills):
    return {"scheduled_ns": ns, "sample_started_ns": ns, "sample_finished_ns": ns,
            "start_lateness_ns": 0, "missed_periods_before": 0,
            "payload": {"schema": "independent-progress-sample-v2", "sample_ns": ns,
                        "kill_count": kills, "death_count": 0, "episode_finished": False,
                        "player_dead": False, "map_exit": False},
            "controller_visible": False}


def inputs_from_rows(releases):
    admissions = [
        {"event": "input_admission", "key": "space", "admitted_ns": 80,
         "input_ack_ns": 85, "valid_until_ns": 900, "id": "plan-1", "step": 0,
         "owner_id": "owner-1", "intent_token": "intent-1"},
        {"event": "input_admission", "key": "Up", "admitted_ns": 90,
         "input_ack_ns": 95, "valid_until_ns": 900, "id": "plan-1", "step": 0,
         "owner_id": "owner-1", "intent_token": "intent-1"},
    ]
    return [admissions[0], releases[0], admissions[1], *releases[1:]]


def adapt(releases):
    return adapt_session_records(
        [sample(100, 0), sample(300, 1)],
        [{"schema": "independent-progress-event-v2", "event_sequence": 1,
          "observed_ns": 300, "kind": "KILL_COUNT_INCREASE", "polarity": "positive",
          "useful": True, "controller_visible": False,
          "before": {"kill_count": 0}, "after": {"kill_count": 1, "delta": 1}}],
        inputs_from_rows(releases))


def run_case():
    expected = {"research/doom/doom_owner_thread_release_batch_backend_v1.py": FREEZE["current_backend_blob"]}
    for path, blob in expected.items():
        actual = subprocess.check_output(["git", "-C", str(REPO), "rev-parse", f"{MAIN}:{path}"], text=True).strip()
        if actual != blob: raise AssertionError(f"current producer source drift: {actual}")
    releases = exact_published_rows()
    baseline = adapt(releases)
    attribution = baseline["attributions"][0]
    if (baseline["trace_integrity"] != "SOURCE_ROWS_JOINED" or
            attribution["status"] != "TEMPORALLY_UNIQUE" or
            attribution["intent_token"] != "intent-1" or
            attribution["causal_attribution"] != "NOT_ESTABLISHED"):
        raise AssertionError("exact producer output failed T5 baseline attribution contract")

    controls = {}
    mixed = copy.deepcopy(releases); mixed[1].pop("release_batch_delivery_position")
    duplicate = copy.deepcopy(releases); duplicate[1]["release_batch_delivery_position"] = 0
    gap = copy.deepcopy(releases); gap[1]["release_batch_delivery_position"] = 2
    for name, rows in (("mixed_position_schema", mixed), ("duplicate_position", duplicate), ("delivery_gap", gap)):
        result = adapt(rows)
        if (result["trace_integrity"] != "HOLD_INCOMPLETE_RELEASE_BATCH" or
                result["attributions"][0]["status"] != "UNRESOLVED"):
            raise AssertionError(f"T5 failed closed control: {name}")
        controls[name] = "HOLD_INCOMPLETE_RELEASE_BATCH/UNRESOLVED"

    missing = adapt([releases[0]])
    if missing["attributions"][0]["status"] == "TEMPORALLY_UNIQUE":
        raise AssertionError("missing release row retained a unique temporal label")
    controls["missing_release_row"] = missing["attributions"][0]["status"]

    reordered = adapt(list(reversed(releases)))
    if (reordered["trace_integrity"] != baseline["trace_integrity"] or
            reordered["attributions"] != baseline["attributions"]):
        raise AssertionError("input row order changed adapter disposition")
    controls["row_reordering"] = "same_disposition"

    return {"schema": "v15-release-batch-current-producer-t6-result-v1",
            "main_commit": MAIN, "candidate_source_commit": FREEZE["candidate_source_commit"],
            "disposition": "PASS_CURRENT_PRODUCER_TO_FAIL_CLOSED_ADAPTER_COMPOSITION",
            "producer": {"release_rows": len(releases), "delivery_positions": [0, 1],
                         "delivery_states": ["confirmed", "confirmed"],
                         "owner_transition_verified": [row["owner_transition_verified"] for row in releases],
                         "physical_verification_authoritative": False},
            "baseline": {"trace_integrity": baseline["trace_integrity"],
                         "attribution": attribution["status"],
                         "causal_attribution": attribution["causal_attribution"]},
            "controls": controls,
            "scope": "exact release producer methods plus frozen T5 adapter; synthetic owner, admissions, and scorer event; no physical input or causal claim"}


if __name__ == "__main__":
    print(json.dumps(run_case(), sort_keys=True))
