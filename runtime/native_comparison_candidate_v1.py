"""Native App Server transport for a prospective matched comparison."""

from contextlib import contextmanager
import inspect
import json
import os
from pathlib import Path
import threading
import time

from research.live_control.codex_app_server_client_v2 import CodexAppServerClient
from research.live_control.codex_app_server_command_v1 import direct_command
from research.live_control.integrated_efficiency_app_server_model_v1 import (
    CONTRACTS,
    GroundingCallError,
    PersistentGroundingModel,
    windows_path,
)
from research.live_control.integrated_efficiency_fixture_v1 import workload
from research.live_control.integrated_efficiency_protocol_v1 import ARMS, EXPECTED_MODEL_CALLS, TASKS, USAGE_FIELDS
from research.live_control.native_app_server_job_v1 import WindowsAppServerOwner
from research.live_control.native_comparison_arm_x11_v1 import CONTEXT_ENV
from research.live_control.native_codex_usage_v1 import normalize_usage
from research.live_control.schema_preflight_v1 import EFFORT, MODEL


_GOLDEN_BINDING = threading.Lock()


def write_record(path, record):
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(record, stream, indent=2)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())


def neutral_release(terminal):
    release = terminal.get("release", {})
    return (isinstance(release, dict) and release.get("verified") is True
            and release.get("keys_down") == [] and release.get("buttons_down") == [])


def scheduled_grounding_roots(out, arm):
    root = Path(out) / "model-calls" / arm
    return tuple(root / task / ("repair" if arm == "persistent" and index == 3 else "anchor")
                 for index, (task, count) in enumerate(zip(TASKS, EXPECTED_MODEL_CALLS[arm], strict=True))
                 if count)


def repair_window(events, task_source_sequence):
    missing = [(i, row) for i, row in enumerate(events)
               if row.get("event") == "target_handle_checked" and row.get("handle") == "persistent_a_field"
               and row.get("status") == "MISSING" and row.get("eligible") is False]
    if len(missing) != 1 or type(task_source_sequence) is not int:
        return None
    start, refusal = missing[0]
    start_ns, refused_sequence = refusal.get("checked_ns"), refusal.get("observation_sequence")
    if (type(start_ns) is not int or type(refused_sequence) is not int
            or refused_sequence < task_source_sequence):
        return None
    lower_index, lower_ns, lower_sequence = start, start_ns, refused_sequence
    first_mint_ns = None
    for alias in ("persistent_b_field", "persistent_b_submit"):
        matches = [(i, row) for i, row in enumerate(events)
                   if row.get("event") == "target_handle_minted_from_point" and row.get("handle") == alias
                   and row.get("status") == "VALID"]
        if len(matches) != 1:
            return None
        index, mint = matches[0]
        sequence, stamp = mint.get("fresh_sequence"), mint.get("minted_ns")
        if (index <= lower_index or type(sequence) is not int or sequence <= lower_sequence
                or type(stamp) is not int or stamp <= lower_ns or mint.get("created_sequence") != sequence
                or mint.get("source_sequence") != task_source_sequence or mint.get("fresh_patch_exact") is not True):
            return None
        lower_index, lower_ns, lower_sequence = index, stamp, sequence
        if first_mint_ns is None:
            first_mint_ns = stamp
    checked = next(((i, row) for i, row in enumerate(events)
                    if i > lower_index and row.get("event") == "target_handle_checked"
                    and row.get("handle") == "persistent_b_field" and row.get("eligible") is True
                    and row.get("status") == "VALID"), None)
    if checked is None:
        return None
    end, verified = checked
    end_ns, final_sequence = verified.get("checked_ns"), verified.get("observation_sequence")
    if (type(end_ns) is not int or end_ns <= lower_ns
            or type(final_sequence) is not int or final_sequence <= lower_sequence):
        return None
    accepted = {row["id"]: row.get("accepted_ns") for row in events if row.get("event") == "accepted"}
    terminal = {row["id"]: row.get("terminal_ns") for row in events if row.get("event") == "terminal"}
    pointers = []
    for i, row in enumerate(events):
        if row.get("event") != "pointer_admission" or row.get("operation") != "button_down":
            continue
        admitted = row.get("admitted_ns")
        if type(admitted) is not int:
            return None
        if start < i < end or start_ns <= admitted <= end_ns:
            program = row.get("id")
            began, ended = accepted.get(program), terminal.get(program)
            if type(began) is not int or type(ended) is not int or not began <= admitted <= ended:
                return None
            pointers.append((program, admitted))
    return {"refusal_id": refusal["id"], "revalidation_id": verified["id"],
            "begin_ns": start_ns, "first_fresh_mint_ns": first_mint_ns, "end_ns": end_ns,
            "pointer_admissions": pointers}


def audit_local_effects(out, seed, arm):
    """Recompute exact submissions and checked release from local runtime streams."""
    if arm not in ARMS or type(seed) is not int or seed < 0:
        raise ValueError("invalid comparison workload")
    runtime = Path(out) / "arms" / arm / "runtime"
    history, events, delivered = (
        [json.loads(line) for line in (runtime / name).read_bytes().splitlines()]
        for name in ("submission-history.jsonl", "events.jsonl", "delivered.jsonl"))
    details = json.loads((runtime.parent / "task-details.json").read_bytes())
    tasks = workload(seed)
    expected = {task["task_id"]: task for task in tasks}
    exact = []
    wrong = []
    for row in history:
        task = expected.get(row.get("task_id"))
        if (task is not None and row.get("schema") == "integrated_efficiency_submission_v1"
                and row.get("layout") == task["layout"]
                and row.get("expected_token") == task["token"]
                and row.get("submitted_values") == [task["token"]] and row.get("exact") is True):
            exact.append(task["task_id"])
        elif (task is not None and row.get("schema") == "integrated_efficiency_submission_v1"
                and row.get("layout") == task["layout"] and row.get("expected_token") == task["token"]
                and row.get("exact") is False and type(row.get("submitted_values")) is list
                and all(type(value) is str for value in row["submitted_values"])
                and row["submitted_values"] != [task["token"]]):
            wrong.append(task["task_id"])
    admissions = [row["id"] for row in events if row.get("event") == "accepted"]
    terminal = [row for row in events if row.get("event") == "terminal"]
    release_verified = [row["id"] for row in terminal if neutral_release(row)]
    delivered_admissions = [row["id"] for row in delivered if row.get("event") == "accepted"]
    delivered_terminal = [(row["id"], row.get("release"))
                          for row in delivered if row.get("event") == "terminal"]
    counts = [row.get("program_count") for row in details]
    recorded_tasks = [row.get("trace", {}).get("task_id") for row in details]
    released_all = (
        recorded_tasks == list(expected) and all(type(count) is int and count > 0 for count in counts)
        and sum(counts) == len(admissions) == len(set(admissions))
        and admissions == delivered_admissions == [row["id"] for row in terminal] == release_verified
        and delivered_terminal == [(row["id"], row.get("release")) for row in terminal])
    missing_checks = [row["id"] for row in events if row.get("event") == "target_handle_checked"
                      and row.get("handle") == "persistent_a_field"
                      and row.get("status") == "MISSING" and row.get("eligible") is False]
    old_target_admissions = sum(row.get("event") == "pointer_admission"
                                and row.get("operation") == "button_down"
                                and row.get("id") in missing_checks for row in events)
    source_sequence = (details[3].get("source", {}).get("sequence")
                       if arm == "persistent" and len(details) >= 4 else None)
    window = repair_window(events, source_sequence) if arm == "persistent" else None
    consistent = window is not None and window == repair_window(delivered, source_sequence)
    return {
        "exact_tasks": len(set(exact)), "submission_count": len(history),
        "exact_once_in_allocation_order": len(history) == len(tasks) and exact == list(expected),
        "accepted_programs": len(admissions), "verified_terminal_releases": len(release_verified),
        "all_accepted_programs_released": released_all, "old_layout_missing_checks": len(missing_checks),
        "old_check_program_button_down_admissions": old_target_admissions,
        "repair_window_verified": consistent,
        "repair_missing_ns": window["begin_ns"] if consistent else None,
        "repair_first_fresh_mint_ns": window["first_fresh_mint_ns"] if consistent else None,
        "pre_repair_button_down_admissions": len(window["pointer_admissions"]) if consistent else None,
        "confirmed_wrong_submissions": len(wrong),
        "confirmed_duplicate_exact_submissions": len(exact) - len(set(exact)),
    }


def comparison_arm_order(arms):
    """Validate the physical order independently of the fixed arm membership."""
    if not isinstance(arms, (list, tuple)) or tuple(arms) not in (ARMS, ARMS[::-1]):
        raise ValueError("comparison arm order must be forward or reverse")
    return tuple(arms)


def capture_plan_values(seed, registration, registration_sha256):
    arms = ARMS if registration is None else comparison_arm_order(registration["arms"])
    return {
        "schema": "native_comparison_capture_plan_v1", "seed": seed,
        "arms": list(arms), "tasks": workload(seed), "requested_model": MODEL,
        "requested_effort": EFFORT, "automatic_retry": False,
        "expected_grounding_turns": {arm: sum(EXPECTED_MODEL_CALLS[arm]) for arm in ARMS},
        "schema_preflight_calls_per_arm": 1,
        "provider_context": "one_arm_owned_app_server_with_one_fresh_thread_per_grounding",
        "registration": registration, "registration_sha256": registration_sha256,
    }


def capture_block(out, seed, *, preflight, run_arm, open_grounding,
                  registration=None, registration_sha256=None):
    """Retain a fresh, ordered block pending independent raw verification."""
    if type(seed) is not int or seed < 0:
        raise ValueError("nonnegative integer comparison seed required")
    out = Path(out).resolve()
    if out.is_relative_to(Path(__file__).resolve().parents[1]):
        raise ValueError("comparison output must be outside the source checkout")
    plan = capture_plan_values(seed, registration, registration_sha256)
    out.mkdir(parents=True, exist_ok=False)
    write_record(out / "capture-plan.json", plan)
    statuses = dict.fromkeys(plan["arms"], "not_run")
    disposition = {"schema": "native_comparison_capture_v1", "disposition": "HOLD",
                   "reason": "independent_raw_audit_required", "arms": statuses}
    try:
        for arm in plan["arms"]:
            contract = "plain" if arm == "plain" else "compiled"
            workspace = out / "workspaces" / arm
            arm_receipts = out / "capture-arms" / arm
            arm_receipts.mkdir(parents=True)
            stage = "preflight"
            preflight_started = time.monotonic_ns()
            write_record(arm_receipts / "preflight-start.json", {"contract": contract,
                "started_monotonic_ns": preflight_started})
            try:
                preflight_row = preflight(arm, contract, workspace)
                preflight_finished = time.monotonic_ns()
                usage = normalize_usage(preflight_row["usage"])
                write_record(arm_receipts / "preflight-result.json", preflight_row)
                if set(usage) != set(USAGE_FIELDS):
                    raise ValueError("unreported schema preflight usage field")
                stage = "arm"
                arm_started = time.monotonic_ns()
                with open_grounding(arm, contract, workspace) as call:
                    rows, independent = run_arm(arm, seed, workspace, model_call=call)
                    write_record(arm_receipts / "task-results.json",
                                 {"tasks": rows, "independent": independent})
                write_record(arm_receipts / "arm-timing.json", {
                    "preflight_started_ns": preflight_started, "preflight_finished_ns": preflight_finished,
                    "arm_started_ns": arm_started, "arm_finished_ns": time.monotonic_ns(),
                })
                stage = "effect_release_audit"
                effects = audit_local_effects(out, seed, arm)
                write_record(arm_receipts / "effect-release-audit.json", effects)
            except BaseException as error:
                statuses[arm] = "interrupted"
                disposition["reason"] = stage + "_interrupted"
                write_record(arm_receipts / "failure.json", {
                    "stage": stage, "error_type": type(error).__name__,
                    "provider_calls_observed": None,
                })
                if not isinstance(error, Exception):
                    raise
                break
            if (len(rows) != len(EXPECTED_MODEL_CALLS[arm])
                    or any(row.get("typed_outcome") != "completed"
                           or row.get("exact_submission") is not True
                           or type(row.get("submission_count")) is not int or row["submission_count"] != 1
                           or row.get("releases_verified") is not True for row in rows)
                    or independent.get("success") is not True
                    or not effects["exact_once_in_allocation_order"]
                    or not effects["all_accepted_programs_released"]
                    or (registration is not None and arm == "persistent" and (
                        effects["repair_window_verified"] is not True
                        or effects["pre_repair_button_down_admissions"] != 0))):
                statuses[arm] = "incomplete"
                disposition["reason"] = "task_or_independent_effect_incomplete"
                break
            statuses[arm] = "captured"
    finally:
        write_record(out / "capture.json", disposition)
    return disposition


@contextmanager
def bind_golden_runner(out):
    """Bind the existing GUI arm and schema preflight to the native capture.

    The script-oriented Golden implementation uses module globals. Keep this
    binding within one block and restore the caller's configuration.
    """
    from runtime import golden_desktop_demo_v3 as golden
    import integrated_efficiency_model_v1 as legacy_model
    import run_integrated_efficiency_live_v1 as implementation
    import schema_preflight_v1 as schema_preflight

    with _GOLDEN_BINDING:
        repo = Path(__file__).resolve().parents[1]
        runtime_base = golden.previous.base
        research = repo / "research" / "live_control"
        runner_source = research / "run_integrated_efficiency_live_v1.py"
        loaded_sources = (
            (implementation.__file__, runner_source),
            (inspect.getsourcefile(implementation.run_arm), runner_source),
            (inspect.getsourcefile(implementation.preflight_call), runner_source),
            (schema_preflight.__file__, research / "schema_preflight_v1.py"),
            (legacy_model.__file__, research / "integrated_efficiency_model_v1.py"),
            (runtime_base.__file__, repo / "runtime" / "golden_desktop_demo.py"),
            (golden.__file__, repo / "runtime" / "golden_desktop_demo_v3.py"),
        )
        if any(actual is None or Path(actual).resolve() != expected for actual, expected in loaded_sources):
            raise ValueError("loaded comparison source is outside the registered checkout")
        config = runtime_base.configuration()
        executable = config.get("windows_codex_exe")
        windows_python, chromium = config.get("windows_python"), config.get("chromium")
        if executable is None or windows_python is None or chromium is None:
            raise ValueError("native executable, Windows Python and Linux Chromium required")
        health = golden.doctor()
        if health.get("passed") is not True or "native_codex" not in health:
            raise ValueError("native Golden doctor refused comparison configuration")
        saved = [
            (implementation, "OUT", implementation.OUT),
            (implementation, "RuntimeClient", implementation.RuntimeClient),
            (legacy_model, "WINDOWS_PYTHON", legacy_model.WINDOWS_PYTHON),
            (schema_preflight, "WINDOWS_PYTHON", schema_preflight.WINDOWS_PYTHON),
            (schema_preflight, "CLI_EXE_WSL", schema_preflight.CLI_EXE_WSL),
        ]
        try:
            configured, runtime_client = runtime_base.configure_research_modules(config, chromium)
            if configured is not implementation:
                raise RuntimeError("unexpected Golden arm implementation")
            class ReleaseCheckedRuntime(runtime_client):
                release_failed = False

                def submit(self, label, steps, timeout=10):
                    if self.release_failed:
                        raise RuntimeError("the previous input release is unverified")
                    program = super().submit(label, steps, timeout=timeout)
                    if not neutral_release(program["terminal"]):
                        self.release_failed = True
                        raise RuntimeError("input release is unverified")
                    return program

                def finish(self, request_id):
                    evaluation = super().finish(request_id)
                    if CONTEXT_ENV in os.environ:
                        receipt = self.runtime / "comparison-display-end.json"
                        deadline = time.monotonic() + 10
                        while not receipt.is_file() and time.monotonic() < deadline:
                            time.sleep(.05)
                        if not receipt.is_file():
                            raise RuntimeError("actual arm Xvfb exit receipt did not arrive")
                        observed = json.loads(receipt.read_bytes())
                        if observed.get("retired") is not True or observed.get("input_neutral_at_end") is not True:
                            raise RuntimeError("actual arm Xvfb retirement or input neutrality did not verify")
                    return evaluation

            implementation.OUT = Path(out).resolve()
            implementation.RuntimeClient = ReleaseCheckedRuntime

            def preflight(arm, contract, workspace):
                if workspace != implementation.OUT / "workspaces" / arm:
                    raise ValueError("preflight workspace differs from the allocated arm")
                return implementation.preflight_call(arm, contract)

            def open_grounding(arm, contract, workspace):
                return owned_grounding(
                    implementation.OUT / "native-app-server" / arm,
                    workspace, contract=contract, executable=executable, windows_python=windows_python,
                    allowed_groundings=scheduled_grounding_roots(implementation.OUT, arm))

            yield health, {
                "preflight": preflight,
                "run_arm": implementation.run_arm,
                "open_grounding": open_grounding,
            }
        finally:
            for module, name, value in saved:
                setattr(module, name, value)


@contextmanager
def owned_grounding(session_root, workspace, *, contract, executable, windows_python,
                    allowed_groundings):
    """Give every arm one owned process and each grounding a fresh planner thread."""
    if contract not in CONTRACTS:
        raise ValueError("unknown comparison grounding contract")
    session_root = Path(session_root)
    workspace = Path(workspace).resolve(strict=True)
    slots = tuple(Path(path).resolve() for path in allowed_groundings)
    if not slots or len(set(slots)) != len(slots):
        raise ValueError("unique, scheduled grounding slots required")
    session_root.mkdir(parents=True, exist_ok=False)
    attempts = session_root / "attempts"
    attempts.mkdir()
    owner = WindowsAppServerOwner(windows_python, windows_path, session_root)
    client = CodexAppServerClient(
        direct_command(executable), cwd=workspace,
        journal_path=session_root / "protocol.jsonl", windows_owner=owner)
    generation = 0
    refused = 0
    blocked = False
    ready = False

    def call(root, prompt, image, selected_contract, selected_workspace):
        nonlocal generation, refused, blocked
        if not ready:
            raise RuntimeError("native comparison transport is outside its owned lifetime")
        if (blocked or selected_contract != contract or Path(selected_workspace).resolve() != workspace
                or generation >= len(slots) or Path(root).resolve() != slots[generation]):
            blocked = True
            refused += 1
            failures = session_root / "refused-groundings"
            failures.mkdir(exist_ok=True)
            write_record(failures / f"{refused:02d}.json", {
                "status": "refused_unscheduled_grounding", "result_root": str(root),
                "provider_turn_observed": False, "usage": None,
            })
            raise ValueError("grounding is outside the next scheduled allocation slot")
        generation += 1
        attempt = attempts / f"{generation:02d}"
        try:
            attempt.mkdir()
            write_record(attempt / "start.json", {
                "generation": generation, "contract": contract, "result_root": str(root),
                "source_image": str(image), "started_monotonic_ns": time.monotonic_ns(),
            })
        except BaseException:
            blocked = True
            raise
        started = time.monotonic_ns()
        try:
            model = PersistentGroundingModel(
                session_root / "threads" / attempt.name, workspace, contract=contract,
                model=MODEL, effort=EFFORT, allow_missing_cache_write=True, client=client)
            result = model.call(root, prompt, image, selected_contract, selected_workspace)
            returned = time.monotonic_ns()
            usage = normalize_usage(result["usage"])
        except BaseException as error:
            blocked = True
            observed_usage = getattr(error, "usage", None)
            try:
                usage = normalize_usage(observed_usage) if observed_usage is not None else None
            except ValueError:
                usage = None
            call_id = getattr(error, "call_id", None)
            try:
                write_record(attempt / "terminal.json", {
                    "status": "failed", "error_type": type(error).__name__,
                    "provider_turn_observed": True if call_id else None, "call_id": call_id,
                    "thread_id": getattr(error, "thread_id", None), "usage": usage,
                    "finished_monotonic_ns": time.monotonic_ns(),
                })
            except Exception as publication_error:
                error.add_note("Attempt terminal publication failed: " + type(publication_error).__name__)
            raise
        terminal = {
            "status": "completed", "provider_turn_observed": True, "call_id": result["call_id"],
            "thread_id": result["thread_id"], "usage": usage,
            "result_returned_monotonic_ns": returned,
            "finished_monotonic_ns": time.monotonic_ns(),
        }
        try:
            write_record(attempt / "terminal.json", terminal)
        except Exception as publication_error:
            blocked = True
            try:
                write_record(attempt / "terminal-publication-failure.json", {
                    **terminal, "status": "terminal_publication_failed",
                    "error_type": type(publication_error).__name__,
                })
            except Exception as secondary_error:
                publication_error.add_note("Secondary publication failed: " + type(secondary_error).__name__)
            raise GroundingCallError(
                publication_error, call_id=result["call_id"], thread_id=result["thread_id"],
                usage=usage, visible_images_submitted=1, wait_ns=time.monotonic_ns() - started,
                requested_model=MODEL, requested_effort=EFFORT,
                publication_error=publication_error) from publication_error
        if set(usage) != set(USAGE_FIELDS):
            blocked = True
            error = ValueError("unreported grounding usage field")
            raise GroundingCallError(
                error, call_id=result["call_id"], thread_id=result["thread_id"],
                usage=usage, visible_images_submitted=1, wait_ns=time.monotonic_ns() - started,
                requested_model=MODEL, requested_effort=EFFORT, usage_error=str(error)) from error
        return result

    try:
        client.initialize()
        ready = True
        yield call
    except BaseException as error:
        ready = False
        try:
            client.close()
        except BaseException as retirement_error:
            error.add_note("App Server retirement failed: " + type(retirement_error).__name__)
        raise
    else:
        ready = False
        client.close()
