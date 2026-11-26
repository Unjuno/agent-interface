"""Read-only accounting and decision for a sealed native three-arm capture."""

from collections import defaultdict
import hashlib
import json
from pathlib import Path, PurePosixPath, PureWindowsPath
import subprocess
from urllib.parse import urlsplit

from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError

from research.live_control.integrated_efficiency_app_server_model_v1 import per_turn_usage
from research.live_control.integrated_efficiency_fixture_v1 import workload
from research.live_control.integrated_efficiency_protocol_v1 import (
    ARMS, EXPECTED_MODEL_CALLS, TASKS, USAGE_FIELDS, validate_task,
)
from research.live_control.native_app_server_job_v1 import (
    APP_SERVER_JOB_RECEIPT, APP_SERVER_JOB_START, retired_app_server,
)
from research.live_control.native_codex_usage_v1 import accounting, normalize_usage, preflight_terminal
from research.live_control.native_preflight_job_v1 import RECEIPT, START_RECORD, completed_receipt, valid_hex
from research.live_control.schema_preflight_v1 import EFFORT, MODEL
from runtime.native_comparison_candidate_v1 import (
    audit_local_effects, bind_golden_runner, capture_block, capture_plan_values,
    scheduled_grounding_roots, write_record,
)


RESEARCH = PurePosixPath("research/live_control")
SCHEMAS = {
    "plain": RESEARCH / "plain_form_points_schema_v1.json",
    "compiled": RESEARCH / "compiled_form_grounding_schema_v1.json",
}
RESPONDERS = {
    "plain": RESEARCH / "plain_form_points_responder_v1.txt",
    "compiled": RESEARCH / "compiled_form_grounding_responder_v1.txt",
}
EXEC_RUNNER = RESEARCH / "target_handle_model_runner_v2.py"
PREFLIGHT_RESPONDER = RESEARCH / "schema_preflight_responder_v1.txt"
EXEC_OWNER = RESEARCH / "native_preflight_job_v1.py"
APP_OWNER = RESEARCH / "native_app_server_job_v1.py"
REQUIRED_ASSETS = (*SCHEMAS.values(), *RESPONDERS.values(), EXEC_RUNNER,
                   PREFLIGHT_RESPONDER, EXEC_OWNER, APP_OWNER,
                   RESEARCH / "run_integrated_efficiency_live_v1.py",
                   PurePosixPath("runtime/native_comparison_candidate_v1.py"),
                   PurePosixPath("runtime/native_comparison_audit_v1.py"))
PREFLIGHT_PROMPT = "Schema compatibility probe. Produce any object accepted by the supplied schema."
GROUNDING_PROMPT = "Locate the editable token field and the control that submits this visible form. "
SCOPED_SOURCE = (
    "runtime", "research/live_control", "research/observation_gating",
    "research/real_apps_v1", "research/observation_tiles",
)


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def same(left, right):
    return canonical(left) == canonical(right)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_bytes())


def records(path):
    data = path.read_bytes()
    require(not data or data.endswith(b"\n"), "capture stream ends in a partial record")
    return [json.loads(line) for line in data.splitlines()]


def absolute_windows(value):
    path = PureWindowsPath(value)
    require(path.is_absolute() and ".." not in path.parts, "unverified Windows path")
    return path


def scoped_path(root, relative):
    path = PurePosixPath(relative)
    require(not path.is_absolute() and ".." not in path.parts, "unscoped capture path")
    local = root.joinpath(*path.parts)
    require(local.resolve() == local, "symlinked capture path")
    return local


def source_snapshot(repo):
    """Pin a clean Git checkout and the files in its runtime/source closure."""
    repo = Path(repo).resolve(strict=True)

    def git(*args):
        return subprocess.check_output(["git", "-C", str(repo), *args], timeout=20)

    require(Path(git("rev-parse", "--show-toplevel").decode().strip()).resolve() == repo,
            "comparison source must be a Git checkout root")
    require(not git("status", "--porcelain", "--untracked-files=all", "--", *SCOPED_SOURCE),
            "comparison runtime source has modifications or untracked entries")
    revision = git("rev-parse", "HEAD").decode().strip()
    names = git("ls-files", "-z", "--", *SCOPED_SOURCE).decode().split("\0")
    selected = []
    for name in filter(None, names):
        parts = PurePosixPath(name).parts
        if parts[0] == "runtime":
            if parts[1] != "results" and PurePosixPath(name).suffix in {".py", ".json", ".txt", ".sh"}:
                selected.append(name)
        elif len(parts) == 3 and PurePosixPath(name).suffix in {".py", ".json", ".txt"}:
            selected.append(name)
    result = {name: digest(scoped_path(repo, name)) for name in selected}
    require(all(str(path) in result for path in REQUIRED_ASSETS), "comparison source closure is incomplete")
    return {"revision": revision, "files": result}


def registration_values(repo, out, seed, *, native, windows_repo, windows_out):
    """Describe conditions before any call. Independent audit uses this exact record."""
    repo = Path(repo).resolve(strict=True)
    out = Path(out).resolve()
    require(type(seed) is int and seed >= 0 and not out.exists() and not out.is_relative_to(repo),
            "fresh out-of-checkout block and nonnegative seed required")
    exe = absolute_windows(native["windows_path"])
    require(exe.suffix.lower() == ".exe" and valid_hex(native["executable_sha256"], 64)
            and native["version"].startswith("codex-cli "), "native provider identity is incomplete")
    return {
        "schema": "native_comparison_registration_v1", "seed": seed,
        "arms": list(ARMS), "tasks": workload(seed), "model": MODEL, "effort": EFFORT,
        "retry": False, "source": source_snapshot(repo),
        "run_root": out.as_posix(), "windows_run_root": str(absolute_windows(windows_out)),
        "windows_source_root": str(absolute_windows(windows_repo)),
        "native": {key: native[key] for key in ("windows_path", "executable_sha256", "version")},
        "preflight_count": 3,
        "grounding_count": sum(sum(EXPECTED_MODEL_CALLS[arm]) for arm in ARMS),
        "session": "one_owned_app_server_per_arm_fresh_ephemeral_thread_per_grounding",
    }


def artifact_hashes(out):
    files = {}
    for path in sorted(out.rglob("*")):
        relative = path.relative_to(out).as_posix()
        require(not path.is_symlink(), "unsealed symlink in capture")
        if path.is_dir() or relative == "capture-seal.json":
            continue
        require(path.is_file(), "non-regular artifact in capture")
        files[relative] = digest(path)
    return files


def verify_all_provider_paths(out):
    """Ensure no additional App Server session, Exec stream or Job is in the capture."""
    paths = defaultdict(set)
    for arm in ARMS:
        contract = "plain" if arm == "plain" else "compiled"
        exec_home = out / "preflight" / arm / "gate" / (contract + "-form-grounding")
        raw = exec_home / "model-call"
        session = out / "native-app-server" / arm
        for path in (session / "protocol.jsonl", session / APP_SERVER_JOB_START, session / APP_SERVER_JOB_RECEIPT,
                     exec_home / START_RECORD, exec_home / RECEIPT, raw / "events.jsonl",
                     raw / "arrivals.jsonl", raw / "plan.json", raw / "process.json",
                     out / "arms" / arm / "runtime" / "events.jsonl"):
            paths[path.name].add(path)
        model_files = {slot / name for slot in scheduled_grounding_roots(out, arm)
                       for name in ("request.json", "prompt.txt", "result.json")}
        require({path for path in (out / "model-calls" / arm).rglob("*") if path.is_file()}
                == model_files, "unexpected or missing grounding artifacts")
        require({path.name for path in (out / "capture-arms" / arm).iterdir()} == {
            "preflight-start.json", "preflight-result.json", "task-results.json",
            "effect-release-audit.json", "arm-timing.json",
        }, "unexpected or missing arm evidence")
    require(not any(path.name.casefold() in {
        "failure.json", "terminal-publication-failure.json", "refused-groundings",
    } for path in out.rglob("*")), "capture has additional failure evidence")
    for name, expected in paths.items():
        require(set(out.rglob(name)) == expected, "provider artifacts differ from the allocated paths")
    for directory in ("native-app-server", "preflight", "model-calls", "capture-arms", "arms", "workspaces"):
        entries = list((out / directory).iterdir())
        require({path.name for path in entries} == set(ARMS) and all(path.is_dir() for path in entries),
                "unallocated or missing arm directory in " + directory)
    require({path.name for path in out.iterdir()} == {
        "capture-plan.json", "capture.json", "capture-seal.json", "capture-arms",
        "preflight", "native-app-server", "arms", "model-calls", "workspaces",
    }, "unallocated top-level capture artifact")


def seal_capture(out):
    """Publish a digest for retention outside the capture before auditing it."""
    out = Path(out).resolve(strict=True)
    seal = out / "capture-seal.json"
    write_record(seal, {"schema": "native_comparison_seal_v1", "files": artifact_hashes(out)})
    return digest(seal)


def capture_registered(repo, out, registration_file, *, registration_sha256):
    """Use the normal checked arm with a separately retained, exact preregistration."""
    from runtime.golden_desktop_demo import windows_arg

    repo, out, registration_file = (Path(path).resolve() for path in (repo, out, registration_file))
    require(repo == Path(__file__).resolve().parents[1], "running comparison source differs from registration")
    require(not registration_file.is_relative_to(out), "registration needs independent custody")
    require(digest(registration_file) == registration_sha256, "registration digest has changed")
    plan = read(registration_file)
    require(same(plan, registration_values(repo, out, plan["seed"], native=plan["native"],
                windows_repo=windows_arg(repo), windows_out=windows_arg(out))),
            "comparison registration differs from the clean checkout or runtime paths")
    with bind_golden_runner(out) as (doctor, bindings):
        require(same(doctor.get("native_codex"), plan["native"]), "native doctor differs from registration")
        result = capture_block(out, plan["seed"], registration=plan,
                               registration_sha256=registration_sha256, **bindings)
    return {"capture": result, "seal_sha256": seal_capture(out)}


def verify_protocol(protocol, owner, attempts):
    """Bind each fresh thread and turn to the exact sent request and received usage."""
    require(protocol and protocol[0].get("direction") == "windows_job_owner"
            and same(protocol[0].get("message"), owner)
            and sum(row.get("direction") == "windows_job_owner" for row in protocol) == 1,
            "App Server stream lacks a unique first Job marker")
    timestamps = [row.get("observed_ns") for row in protocol]
    require(all(type(value) is int and value >= 0 for value in timestamps)
            and timestamps == sorted(timestamps), "App Server journal clock is unverified")
    prepared, sent, replies = {}, [], defaultdict(list)
    notices = defaultdict(list)
    methods = ["initialize", "initialized"] + ["thread/start", "turn/start"] * len(attempts)
    for index, row in enumerate(protocol[1:], start=1):
        direction, message = row["direction"], row["message"]
        method = message.get("method")
        require(direction in {"send_prepared", "sent", "received"}, "uncertain App Server stream")
        if direction == "received":
            require(not ("id" in message and method is not None), "unexpected App Server request")
            if type(message.get("id")) is int and method is None:
                replies[message["id"]].append((index, message))
            if method in {"thread/tokenUsage/updated", "turn/started", "turn/completed",
                          "item/started", "item/completed", "error", "turn/failed"}:
                notices[method].append((index, message["params"]))
            continue
        key = message.get("id")
        if method == "initialized" and "id" not in message:
            key = "initialized"
        require(type(key) is int or key == "initialized", "invalid outbound App Server request ID")
        if direction == "send_prepared":
            require(key not in prepared, "duplicate App Server send preparation")
            prepared[key] = (index, message)
        else:
            sent.append((key, index, message))
    ids = [key for key, _index, _message in sent]
    require([m.get("method") for _key, _i, m in sent] == methods and len(set(ids)) == len(ids)
            and set(ids) == set(prepared), "App Server sends differ from the registered attempt count")
    require(set(replies) == {key for key in ids if type(key) is int}
            and not notices["error"] and not notices["turn/failed"],
            "App Server response or failure invalidates the comparison")

    def acknowledgement(send, predecessor):
        key, sent_index, message = send
        prep_index, prep_message = prepared[key]
        require(predecessor < prep_index < sent_index and same(prep_message, message),
                "App Server send does not match its ordered preparation")
        if key == "initialized":
            return sent_index, {}
        require(len(replies[key]) == 1, "App Server request lacks a unique acknowledgement")
        index, response = replies[key][0]
        require(index > sent_index and "error" not in response and type(response.get("result")) is dict,
                "App Server acknowledgement is unverified")
        return index, response["result"]

    init_index, init = acknowledgement(sent[0], 0)
    require(init.get("platformFamily") == "windows", "App Server did not acknowledge the Windows platform")
    previous_end, _ = acknowledgement(sent[1], init_index)
    usage_by_turn, start_by_turn, completion_by_turn, items_by_turn = (
        defaultdict(list) for _ in range(4))
    for index, params in notices["thread/tokenUsage/updated"]:
        usage_by_turn[(params["threadId"], params["turnId"])].append((index, params["tokenUsage"]))
    for index, params in notices["turn/completed"]:
        completion_by_turn[(params["threadId"], params["turn"]["id"])].append((index, params))
    for index, params in notices["turn/started"]:
        start_by_turn[(params["threadId"], params["turn"]["id"])].append((index, params))
    permitted_item_types = {"userMessage", "reasoning", "agentMessage"}
    for index, params in [*notices["item/started"], *notices["item/completed"]]:
        require(params["item"]["type"] in permitted_item_types, "unexpected App Server tool or output item")
        items_by_turn[params["threadId"], params["turnId"]].append(index)
    keys = {(attempt["thread_id"], attempt["call_id"]) for attempt in attempts}
    require(len(keys) == len(attempts)
            and len({thread for thread, _turn in keys}) == len(attempts)
            and len({turn for _thread, turn in keys}) == len(attempts)
            and set(usage_by_turn) == set(start_by_turn) == set(completion_by_turn) == keys
            and set(items_by_turn) <= keys,
            "App Server usage or completion has an unexpected identity")

    for i, attempt in enumerate(attempts):
        thread, turn = sent[2 + i * 2:4 + i * 2]
        thread_index, thread_ack = acknowledgement(thread, previous_end)
        thread_id, turn_id = attempt["thread_id"], attempt["call_id"]
        thread_request = attempt["thread_request"]
        require(same(thread[2]["params"], attempt["thread_request"])
                and attempt["started_ns"] <= timestamps[prepared[thread[0]][0]]
                and thread_ack["thread"]["id"] == thread_id
                and thread_ack["model"] == MODEL and thread_ack["reasoningEffort"] == EFFORT
                and absolute_windows(thread_ack["cwd"]) == absolute_windows(thread_request["cwd"])
                and absolute_windows(thread_ack["thread"]["cwd"]) == absolute_windows(thread_request["cwd"])
                and thread_ack["approvalPolicy"] == "never"
                and same(thread_ack["sandbox"], {"type": "readOnly", "networkAccess": False}),
                "App Server thread differs from the registered fresh context")
        turn_index, turn_ack = acknowledgement(turn, thread_index)
        require(same(turn[2]["params"], attempt["turn_request"]) and turn_ack["turn"]["id"] == turn_id,
                "App Server turn request or acknowledgement differs from the registered task")
        observations = usage_by_turn[thread_id, turn_id]
        beginnings = start_by_turn[thread_id, turn_id]
        completions = completion_by_turn[thread_id, turn_id]
        require(len(beginnings) == len(completions) == 1,
                "App Server does not have exactly one start and completion for the turn")
        started_index, started = beginnings[0]
        require(started_index > turn[1] and started["turn"]["status"] == "inProgress"
                and started["turn"].get("error") is None and observations[0][0] > started_index
                and all(i > started_index for i in items_by_turn[thread_id, turn_id]),
                "App Server usage or completion order is unverified")
        completed_index, completed = completions[0]
        terminal = completed["turn"]
        messages = [item for item in terminal["items"] if item.get("type") == "agentMessage"]
        require(completed_index > started_index and timestamps[completed_index] <= attempt["returned_ns"]
                and terminal.get("status") == "completed"
                and terminal.get("error") is None and completed.get("error") is None
                and all(item.get("type") in permitted_item_types for item in terminal["items"])
                and len(messages) == 1 and same(json.loads(messages[0]["text"]), attempt["answer"]),
                "App Server completion differs from the saved answer")
        observed = [(timestamps[index], per_turn_usage(value, allow_missing_cache_write=True))
                    for index, value in observations]
        acquired = [use for stamp, use in observed if stamp <= attempt["returned_ns"]]
        late = [use for stamp, use in observed if stamp > attempt["returned_ns"]]
        require(acquired and same(acquired[-1], attempt["usage"])
                and all(same(use, attempt["usage"]) for use in late),
                "App Server usage was unavailable at return or later changed")
        previous_end = max(completed_index, turn_index)


def preflight_argv(plan, arm, contract):
    workspace = absolute_windows(plan["windows_run_root"]) / "workspaces" / arm
    source = absolute_windows(plan["windows_source_root"])
    schema = source.joinpath(*SCHEMAS[contract].parts)
    instructions = source.joinpath(*PREFLIGHT_RESPONDER.parts)
    return [plan["native"]["windows_path"], "exec", "--ignore-user-config", "--ignore-rules",
            "--ephemeral", "--sandbox", "read-only", "--skip-git-repo-check",
            "--json", "--model", MODEL, "-c", f'model_reasoning_effort="{EFFORT}"',
            "-c", "model_instructions_file=" + json.dumps(instructions.as_posix()),
            "-c", "project_doc_max_bytes=0", "--output-schema", str(schema),
            "--disable", "plugins", "--disable", "remote_plugin", "--disable", "shell_snapshot",
            "--disable", "shell_tool", "--disable", "fast_mode", "-C", str(workspace), "-"]


def read_applicable_schema(repo, contract):
    schema = read(scoped_path(repo, SCHEMAS[contract]))
    Draft202012Validator.check_schema(schema)
    return schema


def verify_task_sources(events, details, seed):
    """Join each source frame to its own settled navigation and observe program."""
    ready = [row for row in events if row.get("event") == "ready"]
    require(len(ready) == 1, "runtime lacks a unique ready task allocation")
    tasks = ready[0]["goal"]["tasks"]
    planned = workload(seed)
    require(len(tasks) == len(planned) == len(details)
            and all(same({key: task[key] for key in expected}, expected)
                    for task, expected in zip(tasks, planned, strict=True)),
            "runtime task allocation differs from preregistration")
    step_programs = [(i, row["command"]) for i, row in enumerate(events)
                     if row.get("event") == "command" and row["command"].get("op") == "submit"]
    accepted, completed, observed = defaultdict(list), defaultdict(list), defaultdict(list)
    for i, row in enumerate(events):
        kind = row.get("event")
        if kind == "accepted":
            accepted[row["id"]].append((i, row))
        elif kind == "terminal":
            completed[row["id"]].append((i, row))
        elif kind == "observation":
            observed[row["id"]].append((i, row))

    def program(selector):
        index, command = selector
        program_id = command["id"]
        require(len(accepted[program_id]) == len(completed[program_id]) == 1,
                "task navigation or observation program lacks closure")
        (accept_at, accept), (finish_at, finish) = accepted[program_id][0], completed[program_id][0]
        require(index < accept_at < finish_at and finish["status"] == "completed"
                and type(accept["accepted_ns"]) is int and type(finish["terminal_ns"]) is int
                and accept["accepted_ns"] <= finish["terminal_ns"],
                "task navigation or observation program did not settle")
        return accept_at, accept, finish_at, finish

    previous = -1
    previous_sequence = -1
    port = None
    observations = []
    for task, detail in zip(tasks, details, strict=True):
        capture = detail["source"]
        target = urlsplit(task["url"])
        require(target.scheme == "http" and target.netloc == f"127.0.0.1:{target.port}"
                and target.port is not None and target.path == "/task/" + task["task_id"].removeprefix("task-")
                and not target.query and not target.fragment and (port is None or port == target.port),
                "runtime navigation differs from the isolated task URL")
        port = target.port
        steps = [{"op": "chord", "modifier": "Control_L", "key": "l"},
                 {"op": "text", "text": task["url"]}, {"op": "key", "key": "Return"},
                 {"op": "settle", "quiet_ms": 80, "timeout_ms": 500}]
        indices = [i for i, (_index, cmd) in enumerate(step_programs) if cmd.get("id") == capture["id"]]
        require(len(indices) == 1 and indices[0] > 0, "task source has no unique observation command")
        observe_at = indices[0]
        navigation, observation = step_programs[observe_at - 1:observe_at + 1]
        require(navigation[0] > previous and same(navigation[1]["steps"], steps)
                and same(observation[1]["steps"], [{"op": "observe"}]),
                "task source is detached from its navigation")
        _nav_i, _nav_accept, nav_end, nav_done = program(navigation)
        obs_start, obs_accept, obs_end, obs_done = program(observation)
        matches = [pair for pair in observed[capture["id"]] if
                   all(pair[1].get(key) == capture[key] for key in ("id", "sequence", "capture_ns", "image"))]
        require(len(matches) == 1, "task source has no unique observed frame")
        frame_at, frame = matches[0]
        require(nav_end < observation[0] < obs_start < frame_at < obs_end
                and type(frame["sequence"]) is int and frame["sequence"] > previous_sequence
                and type(frame["capture_ns"]) is int
                and nav_done["terminal_ns"] <= obs_accept["accepted_ns"] <= frame["capture_ns"] <= obs_done["terminal_ns"],
                "task source observation falls outside its accepted program")
        observations.append((capture["id"], frame["sequence"], frame["capture_ns"], obs_done["terminal_ns"]))
        previous, previous_sequence = obs_end, frame["sequence"]
    return observations


def task_effect_times(events, details, history, unplanned_repair_presses):
    start = [row for row in events if row["event"] == "accepted"]
    stop = {row["id"]: row for row in events if row["event"] == "terminal"}
    effects = defaultdict(list)
    previous_receipt = -1
    for row in history:
        stamp = row["received_ns"]
        require(type(stamp) is int and stamp > previous_receipt, "submission receipt clock is unverified")
        previous_receipt = stamp
        effects[row["task_id"]].append(stamp)
    require(list(effects) == [detail["trace"]["task_id"] for detail in details],
            "submission receipt order differs from the allocated tasks")
    require(len(start) == len(stop) == sum(detail["program_count"] for detail in details),
            "task effects lack a complete input program partition")
    timeline, cursor, previous_end = [], 0, -1
    for detail in details:
        task = detail["trace"]
        entries = start[cursor:cursor + detail["program_count"]]
        cursor += len(entries)
        ids = [row["id"] for row in entries]
        require(len(ids) >= 2 and ids[1] == detail["source"]["id"],
                "task source and input program partition differ")
        for opened in entries:
            begin = opened["accepted_ns"]
            end = stop[opened["id"]]["terminal_ns"]
            require(type(begin) is int and type(end) is int and previous_end < begin <= end,
                    "accepted task programs are not serial")
            previous_end = end
        downs = [row for row in events if row["event"] == "pointer_admission"
                 and row.get("operation") == "button_down" and row["id"] in ids]
        allowed_extra = unplanned_repair_presses if task["repair"]["required"] else 0
        require(task["pointer_admissions"] == 2 and len(downs) == 2 + allowed_extra,
                "task button-down admissions differ from its checked two-click sequence")
        field, submit = downs[-2:]
        source_ns = detail["source"]["capture_ns"]
        receipts = effects[task["task_id"]]
        submit_end = stop[submit["id"]]["terminal_ns"]
        stamps = [source_ns, field["admitted_ns"], field["input_ack_ns"],
                  submit["admitted_ns"], submit["input_ack_ns"], *receipts, submit_end]
        require(all(type(stamp) is int for stamp in stamps)
                and stamps == sorted(stamps) and len(set(stamps)) == len(stamps)
                and (len(receipts) != 1 or task["source_to_completion_ns"] == receipts[0] - source_ns),
                "task submission is not bound to the settled source and submit program")
        program_begins = {row["id"]: row["accepted_ns"] for row in entries}
        require(all(program_begins[row["id"]] <= row["admitted_ns"] < row["input_ack_ns"]
                    <= stop[row["id"]]["terminal_ns"] for row in (field, submit)),
                "task pointer input is outside its accepted program")
        timeline.append({
            "first_program_id": ids[0], "first_accepted_ns": entries[0]["accepted_ns"],
            "source_captured_ns": source_ns, "field_button_down_ns": field["admitted_ns"],
            "submit_button_down_ns": submit["admitted_ns"], "submission_receipts_ns": receipts,
            "last_program_terminal_ns": previous_end,
        })
    return timeline


def verify_arm_timing(out, arm, effects, prior_arm_end):
    receipt = out / "capture-arms" / arm
    timing = read(receipt / "arm-timing.json")
    first, checked, opened, closed = [timing[key] for key in (
        "preflight_started_ns", "preflight_finished_ns", "arm_started_ns", "arm_finished_ns")]
    start = read(receipt / "preflight-start.json")
    require(all(type(stamp) is int for stamp in (first, checked, opened, closed))
            and prior_arm_end < first < checked <= opened < closed
            and start.get("started_monotonic_ns") == first
            and start.get("contract") == ("plain" if arm == "plain" else "compiled"),
            "arm clocks overlap or its preflight ordering is unverified")
    arm_root = out / "arms" / arm
    runtime = arm_root / "runtime"
    detail = read(arm_root / "task-details.json")
    history = records(runtime / "submission-history.jsonl")
    extra = effects["pre_repair_button_down_admissions"] or 0
    events = records(runtime / "events.jsonl")
    delivered = records(runtime / "delivered.jsonl")
    scope = task_effect_times(events, detail, history, extra)
    require(scope == task_effect_times(delivered, detail, history, extra),
            "task effect ordering differs across the runtime streams")
    protocol = records(out / "native-app-server" / arm / "protocol.jsonl")
    ready = [row.get("emit_started_ns") for row in events if row.get("event") == "ready"]
    require(len(ready) == 1 and type(ready[0]) is int
            and opened <= protocol[0]["observed_ns"] <= ready[0] <= scope[0]["first_accepted_ns"]
            and max(scope[-1]["last_program_terminal_ns"], protocol[-1]["observed_ns"]) <= closed,
            "runtime or provider activity is outside the sealed arm interval")
    return closed, scope


def audit_exec(repo, out, plan, arm, contract):
    home = out / "preflight" / arm
    entry_name = contract + "-form-grounding"
    base = home / "gate" / entry_name
    raw = base / "model-call"
    gate = read(home / "gate" / "gate-report.json")
    retained = read(base / "preflight-result.json")
    require(gate.get("accepted") is True and type(gate.get("model_calls")) is int and gate["model_calls"] == 1
            and same(gate.get("results"), [{"name": entry_name, "result": retained}])
            and retained.get("model_call_performed") is True and retained.get("cache_hit") is False
            and retained.get("endpoint_status") == "ENDPOINT_COMPATIBLE",
            "schema preflight did not complete a fresh compatible call")
    identity = retained["identity"]
    files = plan["source"]["files"]
    native = plan["native"]
    expected = {
        "schema_sha256": files[str(SCHEMAS[contract])],
        "instructions_sha256": files[str(PREFLIGHT_RESPONDER)],
        "runner_sha256": files[str(EXEC_RUNNER)],
        "windows_owner_sha256": files[str(EXEC_OWNER)],
        "windows_app_server_owner_sha256": files[str(APP_OWNER)],
        "requested_model": MODEL, "requested_effort": EFFORT,
        "cli_executable_sha256": native["executable_sha256"], "cli_version": native["version"],
        "cli_windows_path": native["windows_path"], "cli_transport": "windows-native-codex-exe",
        "request_shape": f"{EXEC_RUNNER.name}:handle:no-image:output-schema",
        "usage_policy": "native-cache-write-optional-v1",
    }
    require(same(identity, expected), "preflight source or provider identity differs from registration")
    key = hashlib.sha256(canonical(identity).encode()).hexdigest()
    cache_files = list((home / "fresh-cache").iterdir())
    require(retained.get("compatibility_key") == key and cache_files == [home / "fresh-cache" / (key + ".json")],
            "preflight cache differs from the fresh arm allocation")
    cache = read(cache_files[0])
    require(type(cache.pop("observed_at_unix_ns", None)) is int and same(cache, retained),
            "preflight cache differs from the acquired result")
    owner = read(base / START_RECORD)
    receipt = read(base / RECEIPT)
    process = read(raw / "process.json")
    call_plan = read(raw / "plan.json")
    require(owner.get("owner_sha256") == expected["windows_owner_sha256"]
            and completed_receipt(receipt, 0, run_nonce=owner["run_nonce"], owner_sha256=owner["owner_sha256"])
            and same(receipt, retained["windows_job"])
            and type(process.get("exit_code")) is int and process["exit_code"] == 0,
            "preflight Windows Job or worker exit is unverified")
    require(same(call_plan.get("args"), preflight_argv(plan, arm, contract))
            and call_plan.get("mode") == process.get("mode") == "handle"
            and call_plan.get("image_sha256") is None
            and all(call_plan.get(field) == expected[field]
                    for field in ("requested_model", "requested_effort", "runner_sha256",
                                  "schema_sha256", "instructions_sha256"))
            and process.get("requested_model") == MODEL and process.get("requested_effort") == EFFORT
            and (raw / "prompt.txt").read_bytes() == PREFLIGHT_PROMPT.encode()
            and call_plan.get("prompt_sha256") == digest(raw / "prompt.txt"),
            "preflight actual argv or prompt differs from registration")
    stream = raw / "events.jsonl"
    events = records(stream)
    arrival = records(raw / "arrivals.jsonl")
    lines = stream.read_bytes().splitlines(keepends=True)
    require(len(arrival) == len(lines)
            and all(row["line"] == i and type(row["line"]) is int and row["bytes"] == len(line)
                    and row["sha256"] == hashlib.sha256(line).hexdigest()
                    for i, (row, line) in enumerate(zip(arrival, lines, strict=True))),
            "preflight raw Exec stream differs from its local arrival journal")
    lifecycle = {"thread.started", "turn.started", "turn.completed"}
    items = {"item.started", "item.updated", "item.completed"}
    require(all(row.get("type") in lifecycle or (
        row.get("type") in items and row.get("item", {}).get("type") in {"agent_message", "reasoning"})
                for row in events), "preflight stream has an unregistered item or a failed event")
    usage = normalize_usage(preflight_terminal(events).get("usage"))
    messages = [row["item"]["text"] for row in events if row.get("type") == "item.completed"
                and row.get("item", {}).get("type") == "agent_message"]
    require(len(messages) == 1 and Draft202012Validator(
        read_applicable_schema(repo, contract)).is_valid(json.loads(messages[0])),
        "preflight reply does not verify the registered schema")
    call_id = next(row["thread_id"] for row in events if row["type"] == "thread.started")
    row = read(out / "capture-arms" / arm / "preflight-result.json")
    require(same(usage, retained.get("usage")) and same(row, {
        "call_id": call_id, "stage": "schema_preflight", "requested_model": MODEL,
        "requested_effort": EFFORT, "usage": usage, "model_visible_images": 0,
    }), "preflight usage or identity differs from the actual raw event")
    return row, owner["run_nonce"]


def audit_app_server(repo, out, plan, arm, contract, rows, task_times, effects):
    session = out / "native-app-server" / arm
    owner = read(session / APP_SERVER_JOB_START)
    receipt = read(session / APP_SERVER_JOB_RECEIPT)
    require(absolute_windows(owner["windows_executable"]) == absolute_windows(plan["native"]["windows_path"])
            and owner["owner_sha256"] == plan["source"]["files"][str(APP_OWNER)]
            and retired_app_server(receipt, owner["run_nonce"], owner["owner_sha256"]),
            "App Server terminal Job is unverified")
    require(not (session / "refused-groundings").exists(), "grounding dispatch was refused")
    slots = scheduled_grounding_roots(out, arm)
    attempt_root = session / "attempts"
    require(sorted(path.name for path in attempt_root.iterdir())
            == [f"{index:02d}" for index in range(1, len(slots) + 1)],
            "grounding attempt allocation differs from registration")
    details = read(out / "arms" / arm / "task-details.json")
    require(same([detail["trace"] for detail in details], rows), "task detail trace differs from arm result")
    schema = read_applicable_schema(repo, contract)
    instructions = scoped_path(repo, RESPONDERS[contract]).read_text(encoding="utf-8")
    runtime = out / "arms" / arm / "runtime"
    bindings = verify_task_sources(records(runtime / "events.jsonl"), details, plan["seed"])
    require(bindings == verify_task_sources(records(runtime / "delivered.jsonl"), details, plan["seed"]),
            "grounding task source differs across runtime streams")
    absolute_source = PurePosixPath(plan["run_root"])
    absolute_target = absolute_windows(plan["windows_run_root"])
    workspace = absolute_target / "workspaces" / arm
    threads, images, provider_calls = [], set(), []
    for index, slot in enumerate(slots, start=1):
        task_id = slot.parent.name
        task_index = TASKS.index(task_id)
        [call] = rows[task_index]["model_calls"]
        attempt = attempt_root / f"{index:02d}"
        require(sorted(path.name for path in attempt.iterdir()) == ["start.json", "terminal.json"]
                and not (slot / "failure.json").exists(), "grounding attempt ended with an incomplete record")
        start, terminal = read(attempt / "start.json"), read(attempt / "terminal.json")
        request, result = read(slot / "request.json"), read(slot / "result.json")
        observed = details[task_index]["source"]
        source = PurePosixPath(observed["image"])
        relative = source.relative_to(absolute_source)
        require(len(relative.parts) == 4 and relative.parts[:3] == ("arms", arm, "runtime")
                and source.suffix.lower() == ".png" and relative not in images
                and request["source_image"] == start["source_image"] == str(source)
                and request["provider_image"] == str(absolute_target.joinpath(*relative.parts))
                and request["image_sha256"] == digest(scoped_path(out, relative)),
                "grounding input image differs from the captured task")
        images.add(relative)
        source_slot = absolute_source.joinpath(*slot.relative_to(out).parts)
        require(type(start["generation"]) is int and start["generation"] == index
                and start["result_root"] == str(source_slot) and start["contract"] == contract
                and terminal["status"] == "completed" and terminal["provider_turn_observed"] is True
                and all(type(value) is int for value in (
                    start["started_monotonic_ns"], terminal["result_returned_monotonic_ns"],
                    terminal["finished_monotonic_ns"]))
                and terminal["finished_monotonic_ns"] >= terminal["result_returned_monotonic_ns"]
                >= start["started_monotonic_ns"] >= bindings[task_index][3],
                "grounding attempt ledger did not settle")
        require(terminal["finished_monotonic_ns"] < task_times[task_index]["field_button_down_ns"],
                "grounding result did not settle before its task field input")
        if slot.name == "repair":
            missing, mint = effects["repair_missing_ns"], effects["repair_first_fresh_mint_ns"]
            require(effects["repair_window_verified"] and type(missing) is int and type(mint) is int
                    and missing < start["started_monotonic_ns"]
                    and terminal["finished_monotonic_ns"] < mint,
                    "repair grounding is outside the old-target refusal and first fresh mint")
        usage = normalize_usage(result["usage"])
        require(same(usage, normalize_usage(terminal["usage"])) and same(usage, normalize_usage(call["usage"]))
                and same(usage, per_turn_usage(result["provider_usage"], allow_missing_cache_write=True))
                and result["turn_status"] == "completed" and result["answer_eligible"] is True
                and call["stage"] == ("anchor_model" if slot.name == "anchor" else "expanded_model")
                and call["requested_model"] == result["requested_model"] == MODEL
                and call["requested_effort"] == result["requested_effort"] == EFFORT
                and terminal["thread_id"] == result["thread_id"] and type(result["thread_id"]) is str
                and terminal["call_id"] == result["call_id"] == result["turn_id"] == call["call_id"]
                and Draft202012Validator(schema).is_valid(result["raw"]),
                "grounding attempt, result and usage do not agree")
        require((slot / "prompt.txt").read_bytes() == GROUNDING_PROMPT.encode(),
                "grounding prompt differs from the registered task")
        thread_request = {"model": MODEL, "cwd": str(workspace), "approvalPolicy": "never",
                          "sandbox": "read-only", "baseInstructions": instructions, "ephemeral": True,
                          "threadSource": "exec",
                          "config": {"project_doc_max_bytes": 0, "model_reasoning_effort": EFFORT}}
        turn_request = {"threadId": result["thread_id"], "model": MODEL, "effort": EFFORT,
                        "outputSchema": schema, "input": [
                            {"type": "text", "text": GROUNDING_PROMPT, "text_elements": []},
                            {"type": "localImage", "path": request["provider_image"]},
                        ]}
        threads.append({"thread_id": result["thread_id"], "call_id": result["call_id"],
                        "thread_request": thread_request, "turn_request": turn_request,
                        "answer": result["raw"], "usage": usage,
                        "started_ns": start["started_monotonic_ns"],
                        "returned_ns": terminal["result_returned_monotonic_ns"]})
        provider_calls.append(call)
    require(sorted(path.relative_to(out) for path in (out / "model-calls" / arm).rglob("result.json"))
            == sorted(slot.relative_to(out) / "result.json" for slot in slots),
            "unexpected grounding result outside the allocated slots")
    verify_protocol(records(session / "protocol.jsonl"), owner, threads)
    return provider_calls, [thread["thread_id"] for thread in threads], owner["run_nonce"]


def measured_decision(arms):
    persistent = arms["persistent"]
    comparisons = [arms[arm] for arm in ("plain", "ephemeral")]
    break_even = next((index + 1 for index in range(len(TASKS))
                       if all(persistent["cumulative_input"][index] < row["cumulative_input"][index]
                              for row in comparisons)), None)
    retain = (break_even is not None and break_even <= 4
              and all(persistent["cumulative_input"][-1] < row["cumulative_input"][-1]
                      and persistent["provider_calls"] < row["provider_calls"] for row in comparisons))
    return {"disposition": "RETAIN" if retain else "REJECT",
            "reason": "matched_token_and_generation_gate" if retain else "matched_efficiency_gate_failed",
            "observed_break_even_task": break_even, "arms": arms}


def audit_comparison(repo, out, registration_file, *, registration_sha256, seal_sha256):
    """Bound the decision to separately anchored, fully observed native evidence."""
    try:
        repo, out, registration_file = (Path(path).resolve(strict=True)
                                         for path in (repo, out, registration_file))
        require(valid_hex(registration_sha256, 64) and valid_hex(seal_sha256, 64)
                and not registration_file.is_relative_to(out)
                and digest(registration_file) == registration_sha256, "unverified comparison registration")
        seal = out / "capture-seal.json"
        require(digest(seal) == seal_sha256 and same(read(seal),
            {"schema": "native_comparison_seal_v1", "files": artifact_hashes(out)}),
            "sealed comparison evidence has changed")
        plan = read(registration_file)
        stored = read(out / "capture-plan.json")
        require(plan["schema"] == "native_comparison_registration_v1"
                and type(plan["seed"]) is int and plan["seed"] >= 0
                and plan["arms"] == list(ARMS) and same(plan["tasks"], workload(plan["seed"]))
                and plan["model"] == MODEL and plan["effort"] == EFFORT and plan["retry"] is False
                and same(plan["source"], source_snapshot(repo))
                and same(stored, capture_plan_values(plan["seed"], plan, registration_sha256)),
                "capture differs from the frozen plan or source")
        statuses = read(out / "capture.json").get("arms")
        require(type(statuses) is dict and set(statuses) == set(ARMS)
                and all(statuses[arm] == "captured" for arm in ("plain", "ephemeral"))
                and statuses["persistent"] in {"captured", "incomplete", "interrupted"}
                and plan["preflight_count"] == 3 and plan["grounding_count"] == 14,
                "the retained block lacks the two reference arms or persistent attempt")
        verify_all_provider_paths(out)
        arms, call_ids, nonces = {}, [], []
        prior_arm_end = -1
        for arm in ARMS:
            contract = "plain" if arm == "plain" else "compiled"
            saved = read(out / "capture-arms" / arm / "task-results.json")
            rows = saved["tasks"]
            require(len(rows) == len(TASKS), "arm task schedule is incomplete")
            checked = [validate_task(row, arm, i) for i, row in enumerate(rows)]
            effects = audit_local_effects(out, plan["seed"], arm)
            prior_arm_end, task_times = verify_arm_timing(out, arm, effects, prior_arm_end)
            preflight, preflight_nonce = audit_exec(repo, out, plan, arm, contract)
            calls, threads, session_nonce = audit_app_server(repo, out, plan, arm, contract, rows, task_times, effects)
            nonces.extend((preflight_nonce, session_nonce))
            call_ids.extend([preflight["call_id"], *threads, *(call["call_id"] for call in calls)])
            summary = accounting([preflight, *calls])
            require(summary["usage_status"] == "complete", "required provider usage field is unreported")
            if arm == "persistent" and (effects["confirmed_wrong_submissions"]
                    or effects["confirmed_duplicate_exact_submissions"]
                    or (effects["repair_window_verified"] and effects["pre_repair_button_down_admissions"] > 0)):
                require(len(set(nonces)) == len(nonces) == 6 and len(set(call_ids)) == len(call_ids) == 31,
                        "provider or Windows Job identities are duplicated across the matched block")
                return {"disposition": "REJECT", "reason": "confirmed_persistent_safety_or_effect_failure",
                        "accounting_verified": True, "effects": effects}
            require(saved["independent"].get("success") is True
                    and effects["exact_once_in_allocation_order"] and effects["all_accepted_programs_released"]
                    and all(row["typed_outcome"] == "completed" and row["exact_submission"] is True
                            and row["releases_verified"] is True and row["submission_count"] == 1
                            and row["old_target_pointer_admissions"] == 0 for row in checked)
                    and effects["old_check_program_button_down_admissions"] == 0
                    and effects["old_layout_missing_checks"] == (1 if arm == "persistent" else 0)
                    and (arm != "persistent" or effects["repair_window_verified"]
                         and effects["pre_repair_button_down_admissions"] == 0)
                    and statuses[arm] == "captured",
                    "task effects or input settlement do not verify")
            if arm == "persistent":
                require(checked[3]["repair"]["succeeded"] is True,
                        "persistent repair did not complete")
            tokens, cumulative = preflight["usage"]["input_tokens"], []
            for row in rows:
                tokens += sum(call["usage"]["input_tokens"] for call in row["model_calls"])
                cumulative.append(tokens)
            arms[arm] = {**effects, **summary, "cumulative_input": cumulative,
                         "provider_calls": 1 + len(calls),
                         "task_elapsed_ns": sum(row["elapsed_ns"] for row in checked)}
        require(len(set(nonces)) == len(nonces) == 6
                and len(set(call_ids)) == len(call_ids) == 31
                and sum(arm["provider_calls"] for arm in arms.values()) == 17,
                "provider or Windows Job identities are duplicated across the matched block")
        return measured_decision(arms)
    except (OSError, ValueError, TypeError, KeyError, IndexError, AttributeError,
            subprocess.SubprocessError, SchemaError) as error:
        return {"disposition": "HOLD", "reason": str(error), "accounting_verified": False}
