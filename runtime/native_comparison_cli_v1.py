"""Prepare, run once, and audit the guarded native comparison from WSL."""

import argparse
from contextlib import contextmanager
from importlib.metadata import version
import json
import os
from pathlib import Path
import secrets
import shutil
import stat
import subprocess
import sys
import time
import tomllib

from research.live_control.codex_app_server_client_v2 import wsl_codex_home_environment
from research.live_control.integrated_efficiency_app_server_model_v1 import windows_path
from research.live_control.native_comparison_arm_x11_v1 import CONTEXT_ENV
from runtime import native_comparison_audit_v1 as audit
from runtime import native_comparison_failure_v1 as failure_evidence


ROOT = Path(__file__).resolve().parents[1]
RUNTIME_SECONDS = 1800
STOP_SECONDS = 8
HOST_FILES = (
    "claim.json", "service-start.json", "service-result.json", "display-start.json",
    "display-end.json", "capture-worker-result.json", "audit-anchor.json", "service.stdout", "service.stderr",
)
SERVICE_POLICY = {"kill_mode": "control-group", "runtime_limit_seconds": RUNTIME_SECONDS,
                  "stop_timeout_seconds": STOP_SECONDS}
VARIABLES = {
    "chromium": "AGENT_INTERFACE_CHROMIUM",
    "windows_codex_exe": "AGENT_INTERFACE_WINDOWS_CODEX_EXE",
    "windows_python": "AGENT_INTERFACE_WINDOWS_PYTHON",
    "codex_home": "CODEX_HOME",
}
REMOVED = (
    "DISPLAY", "XAUTHORITY", "WAYLAND_DISPLAY", "WAYLAND_SOCKET", "PYTHONPATH", "PYTHONHOME",
    "OPENAI_API_KEY", "OPENAI_BASE_URL", "OPENAI_API_BASE", "CODEX_API_KEY", "CODEX_BASE_URL",
    "AGENT_INTERFACE_MODEL_RUNNER", "AGENT_INTERFACE_MODEL_BACKEND",
    CONTEXT_ENV,
)


def private_directory(path):
    path = Path(path).resolve(strict=True)
    info = path.stat()
    audit.require(stat.S_ISDIR(info.st_mode) and info.st_uid == os.getuid()
                  and stat.S_IMODE(info.st_mode) == 0o700,
                  "allocation requires a private owner-only directory")
    return path


def environment(settings):
    result = {name: value for name, value in os.environ.items() if name not in REMOVED}
    result.update({variable: settings[key] for key, variable in VARIABLES.items()})
    result["PYTHONDONTWRITEBYTECODE"] = "1"
    # Forward the selected CODEX_HOME through the one audited bridge.
    result["WSLENV"] = ""
    return result


def host_inputs(settings):
    audit.require(os.name == "posix" and sys.version_info >= (3, 12)
                  and Path("/proc/sys/kernel/osrelease").is_file()
                  and "microsoft" in Path("/proc/sys/kernel/osrelease").read_text().lower()
                  and os.environ.get("WSL_INTEROP"), "WSL with Python 3.12+ and Windows interop required")
    for executable in ("Xvfb", "openbox", "xauth", "wmctrl", "git", "systemd-run", "systemctl", "wslpath"):
        audit.require(shutil.which(executable) is not None, f"missing host dependency: {executable}")
    packages = {}
    for line in (ROOT / "runtime" / "requirements-golden.txt").read_text().splitlines():
        name, expected = line.split("==")
        packages[name] = version(name)
        audit.require(packages[name] == expected, f"incorrect pinned dependency: {name}")
    browser, cli, python, home = (Path(settings[key]) for key in VARIABLES)
    audit.require(browser.suffix.lower() != ".exe" and os.access(browser, os.X_OK)
                  and cli.suffix.lower() == python.suffix.lower() == ".exe"
                  and cli.is_file() and python.is_file() and home.is_dir(),
                  "configured Chromium, Windows Codex, Windows Python or Codex home unavailable")
    config_file = home / "config.toml"
    config = tomllib.loads(config_file.read_text(encoding="utf-8")) if config_file.is_file() else {}
    selected_profile = config.get("profiles", {}).get(config.get("profile"), {})
    audit.require(all(value in {None, "openai"} for value in (
                      config.get("model_provider"), selected_profile.get("model_provider")))
                  and not config.get("openai_base_url") and not selected_profile.get("openai_base_url"),
                  "ordinary OpenAI provider configuration required")
    env = environment(settings)
    win_env = wsl_codex_home_environment(env)

    def checked(command, selected_environment):
        return subprocess.run(command, env=selected_environment, check=True, capture_output=True,
                              text=True, timeout=15)

    native_version = checked([cli, "--version"], win_env).stdout.strip()
    audit.require(native_version.startswith("codex-cli "), "Windows Codex version probe failed")
    login = checked([cli, "login", "status"], win_env)
    audit.require("logged in using chatgpt" in (login.stdout + login.stderr).lower(),
                  "existing ChatGPT authentication is required")
    browser_version = checked([browser, "--version"], env).stdout.strip()
    windows_python_version = checked([python, "--version"], win_env).stdout.strip()
    audit.require(browser_version and windows_python_version.startswith("Python "),
                  "Chromium or Windows Python version probe failed")
    return {
        "native": {"windows_path": windows_path(cli), "version": native_version,
                   "executable_sha256": audit.digest(cli)},
        "chromium": {"version": browser_version, "launcher_sha256": audit.digest(browser)},
        "windows_python": {"version": windows_python_version, "sha256": audit.digest(python)},
        "linux_python": {"path": str(Path(sys.executable).absolute()), "version": sys.version},
        "packages": packages, "auth": "existing_chatgpt_session",
        "codex_config_sha256": audit.digest(config_file) if config_file.is_file() else None,
    }


def prepare(allocation, seed, settings):
    allocation = Path(allocation).resolve()
    audit.require(not allocation.is_relative_to(ROOT) and not allocation.exists(),
                  "fresh allocation outside the source checkout required")
    settings = {name: str(Path(settings[name]).resolve(strict=True)) for name in VARIABLES}
    host = host_inputs(settings)
    out = allocation / "raw"
    registration = audit.registration_values(ROOT, out, seed, native=host["native"],
                                             windows_repo=windows_path(ROOT), windows_out=windows_path(out))
    allocation.mkdir(mode=0o700)
    private_directory(allocation)
    record = allocation / "registration.json"
    audit.write_record(record, registration)
    plan = allocation / "launch-plan.json"
    audit.write_record(plan, {
        "schema": "native_comparison_launch_plan_v1", "allocation": str(allocation),
        "settings": settings, "host": host, "registration_sha256": audit.digest(record),
        "service": SERVICE_POLICY,
    })
    return {"status": "PREPARED", "launch_plan_sha256": audit.digest(plan),
            "registration_sha256": audit.digest(record), "provider_calls": 0}


def load_plan(allocation, expected_sha):
    allocation = private_directory(allocation)
    plan_file = allocation / "launch-plan.json"
    audit.require(audit.valid_hex(expected_sha, 64) and audit.digest(plan_file) == expected_sha,
                  "launch plan digest differs from the prepared allocation")
    plan = audit.read(plan_file)
    registration_file = allocation / "registration.json"
    audit.require(plan.get("schema") == "native_comparison_launch_plan_v1"
                  and plan["allocation"] == str(allocation)
                  and audit.same(plan.get("service"), SERVICE_POLICY)
                  and audit.digest(registration_file) == plan["registration_sha256"],
                  "registration or launch plan has changed")
    return allocation, plan, registration_file


@contextmanager
def exclusive_launch(role="caller"):
    import fcntl

    root = private_directory(Path("/run/user") / str(os.getuid()))
    filename = root / ("agent-interface-native-comparison.service.lock" if role == "service"
                       else "agent-interface-native-comparison.lock")
    original = os.open(filename, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    try:
        info = os.fstat(original)
        audit.require(stat.S_ISREG(info.st_mode) and info.st_uid == os.getuid()
                      and stat.S_IMODE(info.st_mode) == 0o600, "invalid comparison launch lock")
        fcntl.flock(original, fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield
    finally:
        os.close(original)


def service_command(unit, payload):
    return ["systemd-run", "--user", "--wait", "--pipe", "--collect", "--setenv=WSL_INTEROP",
            f"--unit={unit}", f"--working-directory={ROOT}", "--property=KillMode=control-group",
            f"--property=RuntimeMaxSec={RUNTIME_SECONDS}s",
            f"--property=TimeoutStopSec={STOP_SECONDS}s",
            "--property=UnsetEnvironment=PYTHONPATH PYTHONHOME", *map(str, payload)]


def effective_service(unit):
    properties = ("KillMode", "RuntimeMaxUSec", "TimeoutStopUSec", "ControlGroup", "MainPID")
    output = subprocess.check_output(
        ["systemctl", "--user", "show", unit, *(f"--property={name}" for name in properties)],
        text=True, timeout=5, env={**os.environ, "LC_ALL": "C"})
    result = dict(line.split("=", 1) for line in output.splitlines() if "=" in line)
    group = Path("/proc/self/cgroup").read_text().strip()
    audit.require(result.get("KillMode") == "control-group"
                  and result.get("RuntimeMaxUSec") == f"{RUNTIME_SECONDS // 60}min"
                  and result.get("TimeoutStopUSec") == f"{STOP_SECONDS}s"
                  and result.get("MainPID") == str(os.getpid())
                  and group == "0::" + result.get("ControlGroup", "")
                  and result["ControlGroup"].endswith("/" + unit),
                  "transient service cgroup or effective ownership limits did not verify")
    return result


def cgroup_retired(group, unit):
    root = Path("/sys/fs/cgroup")
    relative = Path(group)
    audit.require(relative.is_absolute() and relative.name == unit and ".." not in relative.parts,
                  "invalid comparison service cgroup")
    events = root.joinpath(*relative.parts[1:]) / "cgroup.events"
    try:
        return "populated 0" in events.read_text().splitlines()
    except FileNotFoundError:
        return True


def host_seal_values(allocation, expected_sha):
    return {"schema": "native_comparison_host_seal_v1", "launch_plan_sha256": expected_sha,
            "files": {name: audit.digest(audit.scoped_path(allocation, name)) for name in HOST_FILES}}


def failed_service_retired(allocation, unit):
    """Observe retirement before reading files a failed worker could still change."""
    fields = ("ActiveState", "MainPID", "ControlGroup")
    try:
        stopped = subprocess.run(
            ["systemctl", "--user", "show", unit, *(f"--property={name}" for name in fields)],
            capture_output=True, text=True, timeout=5, check=False)
        values = dict(line.split("=", 1) for line in stopped.stdout.splitlines() if "=" in line)
        if values.get("ActiveState") not in {"inactive", "failed"} or values.get("MainPID") != "0":
            return False
        uid = os.getuid()
        default_group = f"/user.slice/user-{uid}.slice/user@{uid}.service/app.slice/{unit}"
        groups = {values.get("ControlGroup") or default_group}
        proof = allocation / "service-start.json"
        if proof.is_file():
            record = audit.read(proof)
            if record.get("unit") != unit or type(record.get("ControlGroup")) is not str:
                return False
            groups.add(record["ControlGroup"])
        return all(cgroup_retired(group, unit) for group in groups)
    except (OSError, TypeError, ValueError, subprocess.SubprocessError):
        return False


def retain_failed_capture(allocation, expected_sha, unit, reason):
    settled = failed_service_retired(allocation, unit)
    return failure_evidence.retain(allocation, expected_sha, HOST_FILES, settled=settled, reason=reason)


def seal_host(allocation, expected_sha):
    target = allocation / "host-seal.json"
    audit.write_record(target, host_seal_values(allocation, expected_sha))
    return audit.digest(target)


def verify_display_receipt(start, end, service, scope):
    pid, manager = start["pids"]
    number = start["number"]
    auth = Path(start["xauthority"])
    audit.require(type(pid) is int and type(manager) is int and min(pid, manager) > 1
                  and len({pid, manager, int(service["MainPID"])}) == 3
                  and type(number) is int and 120 <= number < 190
                  and start["display"] == f":{number}" and start["lock"] == f"/tmp/.X{number}-lock"
                  and type(start.get("lock_pid")) is int and start["lock_pid"] == pid
                  and start.get("xauthority_mode") == "0600"
                  and type(start.get("xauthority_uid")) is int and start["xauthority_uid"] == os.getuid()
                  and auth.is_absolute() and auth.is_relative_to("/tmp") and auth.name == "Xauthority"
                  and ".." not in auth.parts and start["service_unit"] == service["unit"]
                  and start["claim_token"] == service["claim_token"]
                  and start["service_group"] == service["ControlGroup"] and start["scope"] == scope
                  and start["input_neutral"] is True and start["xtest"] is True
                  and start["wayland_present"] is False,
                  "Xvfb ownership or private authority receipt is unverified")
    exits = end.get("owned_returncodes")
    retirement = {**start, "retired": True, "lock_absent": True, "owned_returncodes": exits}
    if scope == "actual_comparison_arm_display":
        retirement.update(input_neutral_at_end=True, finished_monotonic_ns=end.get("finished_monotonic_ns"))
    audit.require(type(exits) is list and len(exits) == 2 and all(type(code) is int for code in exits)
                  and audit.same(end, retirement), "claimed private Xvfb did not retire")


def verify_host_receipts(allocation, expected_sha):
    claim = audit.read(allocation / "claim.json")
    service = audit.read(allocation / "service-start.json")
    result = audit.read(allocation / "service-result.json")
    display = audit.read(allocation / "display-start.json")
    retired = audit.read(allocation / "display-end.json")
    token, unit = claim["token"], claim["unit"]
    group = service["ControlGroup"]
    uid = os.getuid()
    audit.require(audit.valid_hex(token, 32) and claim["launch_plan_sha256"] == expected_sha
                  and claim.get("automatic_retry") is False
                  and unit == f"agent-interface-native-comparison-{token}.service"
                  and service.get("unit") == unit and service.get("claim_token") == token
                  and service.get("launch_plan_sha256") == expected_sha
                  and service.get("KillMode") == "control-group"
                  and service.get("RuntimeMaxUSec") == f"{RUNTIME_SECONDS // 60}min"
                  and service.get("TimeoutStopUSec") == f"{STOP_SECONDS}s"
                  and type(service.get("MainPID")) is str and service["MainPID"].isascii()
                  and service["MainPID"].isdigit() and int(service["MainPID"]) > 1
                  and type(group) is str and group.startswith(f"/user.slice/user-{uid}.slice/user@{uid}.service/")
                  and Path(group).name == unit and ".." not in Path(group).parts,
                  "service receipt does not match the effective limits and claimed systemd unit")
    verify_display_receipt(display, retired, service, "supervisor_doctor_display")
    audit.require(type(result["returncode"]) is int and result["returncode"] == 0
                  and result.get("unit") == unit and result.get("claim_token") == token
                  and cgroup_retired(group, unit),
                  "claimed host service or its owned supervisor display did not retire")
    return service


def verify_actual_arm_displays(allocation, service):
    out = allocation / "raw"
    outer = audit.read(allocation / "display-start.json")
    previous_end = -1
    pids = set(outer["pids"])
    for arm in audit.ARMS:
        runtime = out / "arms" / arm / "runtime"
        started = audit.read(runtime / "comparison-display-start.json")
        settled = audit.read(runtime / "comparison-display-end.json")
        verify_display_receipt(started, settled, service, "actual_comparison_arm_display")
        timing = audit.read(out / "capture-arms" / arm / "arm-timing.json")
        events = audit.records(runtime / "events.jsonl")
        ready = [row["emit_started_ns"] for row in events if row["event"] == "ready"]
        terminals = [row["terminal_ns"] for row in events if row["event"] == "terminal"]
        started_ns, settled_ns = started.get("started_monotonic_ns"), settled.get("finished_monotonic_ns")
        audit.require(started.get("arm") == arm and started["display"] != outer["display"]
                      and set(started["pids"]).isdisjoint(pids)
                      and type(started_ns) is int and type(settled_ns) is int
                      and len(ready) == 1 and bool(terminals)
                      and previous_end < timing["arm_started_ns"] <= started_ns <= ready[0]
                      <= max(terminals) <= settled_ns <= timing["arm_finished_ns"],
                      "actual arm Xvfb scope or lifecycle could not be verified")
        previous_end = settled_ns
        pids.update(started["pids"])


@contextmanager
def owned_display(allocation, service):
    sys.path.insert(0, str(ROOT / "research" / "observation_gating"))
    try:
        from gui_suite import Session
    finally:
        sys.path.pop(0)
    session = Session()
    proof = None
    try:
        pids = [session.xvfb.pid, session.openbox.pid]
        lock = Path(f"/tmp/.X{session.display_num}-lock")
        auth = session.auth.resolve(strict=True)
        group = service["ControlGroup"]
        audit.require(120 <= session.display_num < 190 and int(lock.read_text()) == pids[0]
                      and all(Path(f"/proc/{pid}/cgroup").read_text().strip() == "0::" + group for pid in pids)
                      and auth.is_relative_to(session.tmp) and auth.stat().st_uid == os.getuid()
                      and stat.S_IMODE(auth.stat().st_mode) == 0o600
                      and session.d.has_extension("XTEST") and not any(session.d.query_keymap())
                      and not session.d.screen().root.query_pointer().mask
                      and "WAYLAND_DISPLAY" not in os.environ and "WAYLAND_SOCKET" not in os.environ,
                      "private neutral Xvfb ownership did not verify")
        proof = {"display": session.name, "number": session.display_num, "pids": pids, "lock": str(lock),
                 "lock_pid": pids[0], "xauthority": str(auth), "xauthority_mode": "0600",
                 "xauthority_uid": auth.stat().st_uid, "service_unit": service["unit"],
                 "service_group": group, "claim_token": service["claim_token"],
                 "scope": "supervisor_doctor_display", "input_neutral": True, "xtest": True,
                 "wayland_present": False}
        audit.write_record(allocation / "display-start.json", proof)
        yield
    finally:
        session.close()
        if proof is not None:
            lock_absent = not lock.exists()
            exits = [process.poll() for process in (session.xvfb, session.openbox)]
            audit.write_record(allocation / "display-end.json", {
                **proof, "retired": lock_absent and all(type(code) is int for code in exits),
                "lock_absent": lock_absent, "owned_returncodes": exits,
            })


def run_service(allocation, expected_sha, token):
    allocation, plan, registration = load_plan(allocation, expected_sha)
    claim = audit.read(allocation / "claim.json")
    audit.require(audit.valid_hex(token, 32) and claim["token"] == token
                  and not (allocation / "service-result.json").exists() and not (allocation / "raw").exists()
                  and claim["launch_plan_sha256"] == expected_sha
                  and claim["unit"] == f"agent-interface-native-comparison-{token}.service",
                  "transient service does not match the one-shot claim")
    properties = {**effective_service(claim["unit"]), "unit": claim["unit"],
                  "claim_token": token, "launch_plan_sha256": expected_sha}
    audit.write_record(allocation / "service-start.json", properties)
    clean = environment(plan["settings"])
    os.environ.clear()
    os.environ.update(clean)
    audit.require(audit.same(host_inputs(plan["settings"]), plan["host"]),
                  "host inputs changed after preparation")
    with exclusive_launch("service"):
        with owned_display(allocation, properties):
            display = audit.read(allocation / "display-start.json")
            os.environ[CONTEXT_ENV] = json.dumps({
                "raw": str(allocation / "raw"), "group": properties["ControlGroup"],
                "unit": claim["unit"], "token": token, "outer_display": display["display"],
            })
            result = audit.capture_registered(ROOT, allocation / "raw", registration,
                                              registration_sha256=plan["registration_sha256"])
            audit.write_record(allocation / "capture-worker-result.json",
                               {"unit": claim["unit"], "claim_token": token, "capture": result["capture"]})
    return 0 if capture_adjudicable(result["capture"]) else 2


def capture_adjudicable(result):
    """Report whether the worker reached a terminal state the auditor can assess."""
    expected = {
        "schema": "native_comparison_capture_v1", "disposition": "HOLD",
        "reason": "independent_raw_audit_required", "arms": dict.fromkeys(audit.ARMS, "captured"),
    }
    if audit.same(result, expected):
        return True
    # A semantic stop in the last arm can have independently verified failure evidence.
    # The caller must still prove retirement and the auditor decides the outcome.
    expected["reason"] = "task_or_independent_effect_incomplete"
    expected["arms"]["persistent"] = "incomplete"
    return audit.same(result, expected)


def verify_worker_capture(allocation, unit, token):
    worker = audit.read(allocation / "capture-worker-result.json")
    result = audit.read(allocation / "raw" / "capture.json")
    audit.require(audit.same(worker, {"unit": unit, "claim_token": token, "capture": result})
                  and capture_adjudicable(result), "comparison capture cannot be independently adjudicated")


def seal_settled_capture(allocation, expected_sha, unit, token):
    verify_worker_capture(allocation, unit, token)
    audit.require(failed_service_retired(allocation, unit), "comparison service retirement is unverified")
    raw = allocation / "raw"
    audit.require(failure_evidence.native_writers_retired(raw, require_all=True),
                  "all allocated native Windows writers must have settled before full sealing")
    service = verify_host_receipts(allocation, expected_sha)
    verify_actual_arm_displays(allocation, service)
    raw_digest = audit.seal_capture(raw)
    audit.write_record(allocation / "audit-anchor.json", {"seal_sha256": raw_digest})
    return raw_digest, seal_host(allocation, expected_sha)


def adjudicate(allocation, expected_sha, *, expected_seal=None, expected_host_seal=None):
    allocation, plan, registration = load_plan(allocation, expected_sha)
    try:
        if any((allocation / name).exists() for name in (failure_evidence.HOST_SEAL, failure_evidence.RAW_SEAL)):
            return failure_evidence.verify(allocation, expected_sha, HOST_FILES,
                                           raw_digest=expected_seal, host_digest=expected_host_seal)
        host_seal = allocation / "host-seal.json"
        host_digest = audit.digest(host_seal)
        audit.require(audit.valid_hex(expected_host_seal, 64) and host_digest == expected_host_seal
                      and audit.same(audit.read(host_seal), host_seal_values(allocation, expected_sha)),
                      "host ownership evidence differs from the retained host seal")
        service = verify_host_receipts(allocation, expected_sha)
        verify_worker_capture(allocation, service["unit"], service["claim_token"])
        anchor = audit.read(allocation / "audit-anchor.json")
        seal = anchor["seal_sha256"]
        audit.require(audit.valid_hex(seal, 64) and seal == expected_seal,
                      "post-capture seal differs from the retained anchor")
        verify_actual_arm_displays(allocation, service)
        outcome = audit.audit_comparison(ROOT, allocation / "raw", registration,
                                         registration_sha256=plan["registration_sha256"], seal_sha256=seal)
        return {**outcome, "seal_sha256": seal, "host_seal_sha256": host_digest}
    except (OSError, ValueError, TypeError, KeyError) as error:
        return {"disposition": "HOLD", "reason": str(error), "accounting_verified": False}


def run_once(allocation, expected_sha, *, confirm_live):
    audit.require(confirm_live is True, "explicit --confirm-live required")
    allocation, plan, registration = load_plan(allocation, expected_sha)
    with exclusive_launch():
        audit.require(not (allocation / "claim.json").exists() and not (allocation / "raw").exists(),
                      "comparison allocation has already been claimed")
        audit.require(audit.same(audit.source_snapshot(ROOT), audit.read(registration)["source"])
                      and audit.same(host_inputs(plan["settings"]), plan["host"]),
                      "registered source or host inputs changed")
        with exclusive_launch("service"):
            pass
        token = secrets.token_hex(16)
        unit = f"agent-interface-native-comparison-{token}.service"
        audit.write_record(allocation / "claim.json", {
            "token": token, "unit": unit, "launch_plan_sha256": expected_sha,
            "claimed_ns": time.time_ns(), "automatic_retry": False,
        })
        payload = [plan["host"]["linux_python"]["path"], "-B", "-m", "runtime.native_comparison_cli_v1",
                   "_service", str(allocation), expected_sha, token]
        try:
            with (allocation / "service.stdout").open("xb") as stdout, (allocation / "service.stderr").open("xb") as stderr:
                completed = subprocess.run(service_command(unit, payload), stdout=stdout, stderr=stderr,
                                           timeout=RUNTIME_SECONDS + STOP_SECONDS + 20)
            audit.write_record(allocation / "service-result.json", {
                "returncode": completed.returncode, "unit": unit, "claim_token": token,
            })
        except BaseException as error:
            cleanup = None
            try:
                stop = subprocess.run(["systemctl", "--user", "stop", unit], check=False, capture_output=True,
                                      timeout=STOP_SECONDS + 5)
                cleanup = stop.returncode
            except (OSError, subprocess.SubprocessError) as close_error:
                error.add_note("Stopping the claimed unit raised " + type(close_error).__name__)
            try:
                audit.write_record(allocation / "service-result.json", {
                    "returncode": None, "unit": unit, "claim_token": token,
                    "error_type": type(error).__name__, "stop_returncode": cleanup,
                })
            except (OSError, ValueError) as receipt_error:
                error.add_note("Saving service result raised " + type(receipt_error).__name__)
            retained = retain_failed_capture(
                allocation, expected_sha, unit, "claimed comparison service interrupted: " + type(error).__name__)
            if isinstance(error, Exception):
                if getattr(error, "__notes__", None):
                    retained["diagnostics"] = error.__notes__
                return retained
            error.add_note(json.dumps(retained, sort_keys=True))
            raise
        if completed.returncode != 0:
            return retain_failed_capture(allocation, expected_sha, unit, "claimed comparison service exited nonzero")
        try:
            raw_digest, host_digest = seal_settled_capture(allocation, expected_sha, unit, token)
        except (OSError, ValueError, KeyError, TypeError, AttributeError) as error:
            result = retain_failed_capture(allocation, expected_sha, unit, "full capture custody unavailable")
            result["diagnostics"] = [str(error)]
            return result
        return adjudicate(allocation, expected_sha, expected_seal=raw_digest, expected_host_seal=host_digest)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    setup = commands.add_parser("prepare", help="freeze source, host dependencies and the allocation")
    setup.add_argument("allocation", type=Path)
    setup.add_argument("--seed", type=int, required=True)
    for name in VARIABLES:
        setup.add_argument("--" + name.replace("_", "-"), required=True)
    launch = commands.add_parser("run", help="explicitly execute the prepared block once")
    readout = commands.add_parser("audit", help="read the sealed allocation and host settlement")
    for command in (launch, readout):
        command.add_argument("allocation", type=Path)
        command.add_argument("launch_plan_sha256")
    launch.add_argument("--confirm-live", action="store_true")
    readout.add_argument("--seal-sha256")
    readout.add_argument("--host-seal-sha256", required=True)
    service = commands.add_parser("_service", help=argparse.SUPPRESS)
    service.add_argument("allocation", type=Path)
    service.add_argument("launch_plan_sha256")
    service.add_argument("token")
    args = parser.parse_args(argv)
    try:
        if args.command == "prepare":
            result = prepare(args.allocation, args.seed, {name: getattr(args, name) for name in VARIABLES})
        elif args.command == "run":
            result = run_once(args.allocation, args.launch_plan_sha256, confirm_live=args.confirm_live)
        elif args.command == "audit":
            result = adjudicate(args.allocation, args.launch_plan_sha256, expected_seal=args.seal_sha256,
                                expected_host_seal=args.host_seal_sha256)
        else:
            return run_service(args.allocation, args.launch_plan_sha256, args.token)
    except (OSError, ValueError, TypeError, KeyError, subprocess.SubprocessError) as error:
        result = {"disposition": "HOLD", "reason": str(error), "accounting_verified": False}
    print(json.dumps(result, indent=2))
    return {"RETAIN": 0, "REJECT": 1, "HOLD": 2}.get(result.get("disposition"), 0)


if __name__ == "__main__":
    raise SystemExit(main())
