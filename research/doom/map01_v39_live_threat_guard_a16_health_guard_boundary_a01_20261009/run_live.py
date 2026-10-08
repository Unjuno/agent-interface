"""One-shot host relay for the frozen Issue #59 A16 allocation."""
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import os
import queue
import re
import subprocess
import sys
import threading
import time
from runtime_source_closure import RUNTIME_SOURCE_CLOSURE

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
ALLOC = "map01-v39-live-threat-guard-a16-health-guard-boundary-20261009"
OUT = REPO / "results-local/doom" / ALLOC
VM = "issue59-live-v39-a01-20261009"
CLI = Path("/opt/homebrew/bin/codex")
HOST_MOUNT_ROOT = REPO.parents[2].resolve()
SOURCE_ROOT = "/mnt/source/" + REPO.relative_to(HOST_MOUNT_ROOT).as_posix()
GUEST_MOUNT_ROOT = Path("/mnt/source")
GUEST_OUTPUT = SOURCE_ROOT + "/results-local/doom/" + ALLOC
PROXY = SOURCE_ROOT + "/research/doom/actual_source_recovery_59_4d74_20261004/controller_file_stdio_proxy.py"
ENTRY = SOURCE_ROOT + "/research/doom/map01_v39_live_threat_guard_a16_health_guard_boundary_a01_20261009/portable_entry.py"
FIXTURE = SOURCE_ROOT + "/research/doom/fixtures/map01-threat-contact-v2/fixture.json"
WAD = "/tmp/vizdoom-venv/lib/python3.12/site-packages/vizdoom/freedoom2.wad"
EXPECTED_WAD_SHA = "a8772e088847032510d97ba2312406a6998f21cbab44d4ff10696faa9c0ecd4b"
XVFB_SERVER_ARGS = "-screen 0 1280x800x24 -nolisten tcp"
MODEL = "gpt-5.6-luna"
EFFORT = "low"
MAX_DECISIONS = 24
FIXTURE_SEED = 990626
GAME_TIMEOUT_SECONDS = 600
MIN_MEMORY_AVAILABLE_BYTES = 2 * 1024**3
MIN_TMP_AVAILABLE_BYTES = 2 * 1024**3


def should_delay_completion(method, turn_number, already_delayed=False):
    return False


def memory_available_bytes(output):
    rows = [line.split() for line in output.splitlines()
            if line.startswith("Mem:")]
    if len(rows) != 1 or len(rows[0]) < 7:
        raise ValueError("cannot parse guest available-memory report")
    return int(rows[0][-1])


def tmp_available_bytes(output):
    rows = [line.split() for line in output.splitlines()
            if line.split() and line.split()[-1] == "/tmp"]
    if len(rows) != 1 or len(rows[0]) < 4:
        raise ValueError("cannot parse guest /tmp disk report")
    return int(rows[0][3])


def guest_source_mapping(repo=REPO, host_mount_root=HOST_MOUNT_ROOT,
                         guest_mount_root=GUEST_MOUNT_ROOT):
    relative_repo = Path(repo).resolve().relative_to(Path(host_mount_root).resolve())
    guest_source_root = Path(guest_mount_root) / relative_repo
    return {"host_mount_root": str(Path(host_mount_root).resolve()),
            "guest_mount_root": str(Path(guest_mount_root)),
            "host_repo_root": str(Path(repo).resolve()),
            "guest_source_root": str(guest_source_root),
            "relative_repo": relative_repo.as_posix()}


def qualified_guest_runtime(info):
    return (info.get("python") == "3.12.3" and info.get("vizdoom") == "1.3.0" and
            info.get("pillow") == "12.3.0" and info.get("python_xlib") == "0.33" and
            info.get("openpyxl") == "3.1.5")


def active_lane_processes(ps_output):
    return [line for line in ps_output.splitlines()[1:]
            if re.search(r"/tmp/vizdoom|vizdoom-venv|map01_overlap_controller|"
                         r"Xvfb|xvfb-run|controller_file_stdio_proxy|portable_entry\.py",
                         line)]


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def image_receipts(message):
    if message.get("method") != "turn/start":
        return []
    verified = []
    for item in message.get("params", {}).get("input", []):
        if item.get("type") != "localImage":
            continue
        path = Path(item.get("path", "")).resolve(strict=True)
        rel = path.relative_to(OUT.resolve(strict=True)).as_posix()
        records = [json.loads(line) for line in (OUT / "image-path-receipts.jsonl").read_text().splitlines()
                   if line.strip()]
        candidates = [row for row in records if row.get("relative_path") == rel and
                      Path(row.get("host_path", "")).resolve() == path]
        if not candidates:
            raise ValueError(f"no guest custody receipt for {rel}")
        raw_hash = sha(path)
        size = path.stat().st_size
        receipt = candidates[-1]
        if raw_hash != receipt.get("sha256") or size != receipt.get("bytes"):
            raise ValueError(f"host bytes differ from guest receipt for {rel}")
        verified.append({"host_path": str(path), "relative_path": rel, "sha256": raw_hash,
                         "bytes": size, "scope": "host file bytes at forwarding; no provider decoded-byte receipt"})
    return verified


def main():
    if len(sys.argv) != 2 or sys.argv[1] != "--execute-frozen-allocation":
        raise SystemExit("explicit one-shot execution flag required")
    main_sha = os.environ.get("A16_MAIN_SHA", "")
    if len(main_sha) != 40:
        raise SystemExit("A16_MAIN_SHA must name the frozen current-main commit")
    if OUT.exists():
        raise SystemExit(f"allocation output already exists; refusing reuse: {OUT}")
    remote_main = subprocess.check_output(
        ["git", "ls-remote", "origin", "refs/heads/main"], cwd=REPO,
        text=True).split()[0]
    if remote_main != main_sha:
        raise SystemExit(f"main moved before freeze: expected {main_sha}, observed {remote_main}")
    if subprocess.check_output(["git", "merge-base", "HEAD", main_sha], cwd=REPO,
                               text=True).strip() != main_sha:
        raise SystemExit("frozen main is not an ancestor of this experiment tree")
    if subprocess.check_output(["git", "status", "--porcelain"], cwd=REPO,
                               text=True).strip():
        raise SystemExit("experiment tree must be committed and clean before launch")
    if not CLI.is_file():
        raise FileNotFoundError(CLI)
    source_names = set(json.loads(
        (REPO / "research/doom/map01_v39_coast_liveness_live_v1_prereg.json").read_text()
    )["source_sha256"])
    source_names.update(RUNTIME_SOURCE_CLOSURE)
    source_hashes = {name: sha(REPO / name) for name in sorted(source_names)}
    for name in (
        "research/doom/actual_source_recovery_59_4d74_20261004/controller_file_stdio_proxy.py",
        "research/doom/actual_source_recovery_59_4d74_20261004/host_image_custody.py",
        "research/doom/session_map01_v15.py",
        "research/doom/map01_scorer_stdio_adapter_v1.py",
        "research/doom/main_thread_scorer_polling_v1.py",
        "research/doom/independent_progress_clock_v2.py",
        "research/doom/doom_owner_thread_release_batch_backend_v1.py",
        "research/doom/doom_typed_release_backend_v2.py",
        "research/live_control/executor_v13.py",
        "research/live_control/executor_v12.py",
        "research/live_control/input_transition_owner_v4.py",
        "research/live_control/input_transition_owner_v3.py",
        "research/live_control/input_owner_v12.py",
        "research/live_control/input_owner_v11.py",
    ):
        source_hashes[name] = sha(REPO / name)
    # Compare every runtime dependency to the exact current-main tree, not just
    # to the experiment worktree that carries this runner and audit.
    for name, digest in source_hashes.items():
        committed = subprocess.check_output(
            ["git", "show", f"{main_sha}:{name}"], cwd=REPO)
        if hashlib.sha256(committed).hexdigest() != digest:
            raise RuntimeError(f"runtime dependency differs from frozen main: {name}")
    machine_info = json.loads(subprocess.check_output(
        ["orbctl", "info", VM, "--format", "json"], text=True))
    try:
        guest_source_mapping_record = guest_source_mapping()
    except ValueError as error:
        raise RuntimeError(f"repository is outside the VM source mount: {REPO}") from error
    expected_guest_source = guest_source_mapping_record["guest_source_root"]
    if expected_guest_source != SOURCE_ROOT:
        raise RuntimeError(f"guest source mapping mismatch: expected {expected_guest_source}, configured {SOURCE_ROOT}")
    mounts = machine_info.get("record", {}).get("config", {}).get("mounts", [])
    if not any(Path(row.get("source", "")).resolve() == HOST_MOUNT_ROOT and
               row.get("destination") == str(GUEST_MOUNT_ROOT) for row in mounts):
        raise RuntimeError("dedicated VM is not mounting the expected host source root at /mnt/source")
    guest_entry_sha = subprocess.check_output(
        ["orb", "-m", VM, "sha256sum", ENTRY], text=True).split()[0]
    if guest_entry_sha != sha(HERE / "portable_entry.py"):
        raise RuntimeError("guest entrypoint is missing or differs from the committed source")
    guest_fixture_sha = subprocess.check_output(
        ["orb", "-m", VM, "sha256sum", FIXTURE], text=True).split()[0]
    if guest_fixture_sha != sha(REPO / "research/doom/fixtures/map01-threat-contact-v2/fixture.json"):
        raise RuntimeError("guest fixture is missing or differs from the committed source")
    guest_processes = subprocess.check_output(
        ["orb", "-m", VM, "ps", "-eo", "pid,ppid,stat,args"], text=True)
    active_game_processes = active_lane_processes(guest_processes)
    if active_game_processes:
        raise RuntimeError("dedicated VM already has a game/display process: " +
                           " | ".join(active_game_processes))
    guest_memory = subprocess.check_output(["orb", "-m", VM, "free", "-b"], text=True)
    memory_available = memory_available_bytes(guest_memory)
    if memory_available < MIN_MEMORY_AVAILABLE_BYTES:
        raise RuntimeError(f"guest available memory below minimum: {memory_available}")
    guest_tmp_disk = subprocess.check_output(
        ["orb", "-m", VM, "df", "-B1", "-P", "/tmp"], text=True)
    tmp_available = tmp_available_bytes(guest_tmp_disk)
    if tmp_available < MIN_TMP_AVAILABLE_BYTES:
        raise RuntimeError(f"guest /tmp available disk below minimum: {tmp_available}")
    guest_python = subprocess.check_output([
        "orb", "-m", VM, "/tmp/vizdoom-venv/bin/python", "-c",
        "import importlib.metadata,json,platform,sys,vizdoom,Xlib,openpyxl; "
        "print(json.dumps({'python':platform.python_version(),'vizdoom':"
        "importlib.metadata.version('vizdoom'),'pillow':importlib.metadata.version('Pillow'),"
        "'python_xlib':importlib.metadata.version('python-xlib'),"
        "'openpyxl':importlib.metadata.version('openpyxl'),'module':vizdoom.__file__}))"],
        text=True)
    guest_python = json.loads(guest_python)
    if not qualified_guest_runtime(guest_python):
        raise RuntimeError(f"guest runtime version mismatch: {guest_python}")
    wad_sha = subprocess.check_output(
        ["orb", "-m", VM, "sha256sum", WAD], text=True).split()[0]
    if wad_sha != EXPECTED_WAD_SHA:
        raise RuntimeError(f"qualified WAD hash mismatch: {wad_sha}")
    xvfb_info = subprocess.check_output([
        "orb", "-m", VM, "xvfb-run", "-a", "-s", XVFB_SERVER_ARGS,
        "xdpyinfo"], text=True)
    dimensions = next((line.strip() for line in xvfb_info.splitlines()
                       if "dimensions:" in line), "")
    if not re.search(r"dimensions:\s+1280x800 pixels", dimensions):
        raise RuntimeError(f"Xvfb screen preflight mismatch: {dimensions}")
    guest_packages = subprocess.check_output(
        ["orb", "-m", VM, "/tmp/vizdoom-venv/bin/python", "-m", "pip", "freeze", "--all"],
        text=True).splitlines()
    guest_system = subprocess.check_output(
        ["orb", "-m", VM, "dpkg-query", "-W", "python3.12-venv", "xvfb", "xauth", "x11-utils"],
        text=True).splitlines()
    host_command = [str(CLI), "app-server", "--stdio", "--disable", "plugins",
                    "--disable", "remote_plugin", "--disable", "shell_tool",
                    "--disable", "shell_snapshot", "-c", "project_doc_max_bytes=0"]
    guest_env = {
        "HOME": "/tmp/issue59-live-v39-home", "PYTHONDONTWRITEBYTECODE": "1",
        "A16_SOURCE_ROOT": SOURCE_ROOT,
        "PYTHONPATH": SOURCE_ROOT + ":" + ":".join(
            SOURCE_ROOT + path for path in (
                "/research/doom", "/research/live_control",
                "/research/observation_gating", "/research/observation_tiles",
                "/research/real_apps_v1")),
        "GUEST_OUTPUT_ROOT": GUEST_OUTPUT,
        "HOST_OUTPUT_ROOT": str(OUT.resolve()), "HOST_EMPTY_CWD": str((OUT / "host-cwd").resolve()),
        "RELAY_COMMAND_JSON": json.dumps(["/tmp/vizdoom-venv/bin/python", PROXY,
                                             GUEST_OUTPUT]),
        "RELAY_MAX_SECONDS": "900", "QUALIFIED_WAD_PATH": WAD,
    }
    guest_command = ["orb", "-m", VM, "xvfb-run", "-a", "-s", XVFB_SERVER_ARGS,
                     "/usr/bin/env"]
    guest_command.extend(f"{key}={value}" for key, value in guest_env.items())
    guest_command.extend([
        "/tmp/vizdoom-venv/bin/python", ENTRY,
        "--out", GUEST_OUTPUT + "/episode",
        "--iterations", str(MAX_DECISIONS), "--seed", str(FIXTURE_SEED),
        "--session-span", str(MAX_DECISIONS),
        "--model", MODEL, "--effort", EFFORT,
        "--measurement-session",
        "--load-fixture-manifest", FIXTURE,
    ])
    freeze = {
        "schema": "map01-v39-live-threat-guard-a16-health-guard-boundary-freeze-v1",
        "allocation_id": ALLOC,
        "frozen_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_commit": main_sha,
        "experiment_tree_commit": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=REPO, text=True).strip(),
        "source_hashes": source_hashes,
        "runtime_source_closure": list(RUNTIME_SOURCE_CLOSURE),
        "runtime_source_closure_sha256": sha(HERE / "runtime_source_closure.py"),
        "preflight_test_sha256": sha(HERE / "test_preflight_contract.py"),
        "no_delay_test_sha256": sha(HERE / "test_delay_policy.py"),
        "recovery_auditor_sha256": sha(HERE / "audit_recovery_censoring.py"),
        "custody_auditor_sha256": sha(HERE / "audit_cancellation_custody_independent.py"),
        "custody_reconciliation_module_sha256": sha(HERE / "audit_cancellation_custody_v2.py"),
        "custody_reconciliation_sha256": sha(HERE / "audit_cancellation_custody_v3.py"),
        "custody_reconciliation_v2_1_sha256": sha(HERE / "audit_cancellation_custody_v2_1.py"),
        "custody_reconciliation_v2_1_test_sha256": sha(HERE / "test_cancellation_custody_v2_1.py"),
        "recovery_result_auditor_sha256": sha(HERE / "audit_a16_health_guard_result.py"),
        "result_audit_test_sha256": sha(HERE / "test_result_audit.py"),
        "recovery_test_sha256": sha(HERE / "test_audit_recovery_censoring.py"),
        "custody_test_sha256": sha(HERE / "test_audit_cancellation_custody_independent.py"),
        "custody_module_test_sha256": sha(HERE / "test_cancellation_custody_v2.py"),
        "custody_v3_test_sha256": sha(HERE / "test_audit_cancellation_custody_v3.py"),
        "preregistration_sha256": sha(HERE / "PREREGISTRATION.md"),
        "portable_entry_sha256": sha(HERE / "portable_entry.py"),
        "guest_entrypoint_sha256": guest_entry_sha,
        "guest_fixture_manifest_sha256": guest_fixture_sha,
        "host_runner_sha256": sha(__file__),
        "auditor_sha256": sha(HERE / "audit_live.py"),
        "environment_setup_sha256": sha(HERE / "ENVIRONMENT_SETUP.md"),
        "fixture_manifest_sha256": sha(REPO / "research/doom/fixtures/map01-threat-contact-v2/fixture.json"),
        "fixture_save_sha256": sha(REPO / "research/doom/fixtures/map01-threat-contact-v2/save.png"),
        "wad_sha256": wad_sha, "codex_cli_sha256": sha(CLI),
        "codex_cli_version": subprocess.check_output([str(CLI), "--version"], text=True).strip(),
        "host_command": host_command, "guest_command": guest_command,
        "guest_source_mapping": guest_source_mapping_record,
        "guest_environment": {"python": guest_python, "pip_freeze": guest_packages,
                              "system_packages": guest_system,
                              "machine_info": machine_info,
                              "free_memory_bytes": guest_memory,
                              "memory_available_bytes": memory_available,
                              "minimum_memory_available_bytes": MIN_MEMORY_AVAILABLE_BYTES,
                              "tmp_filesystem_bytes": guest_tmp_disk,
                              "tmp_available_bytes": tmp_available,
                              "minimum_tmp_available_bytes": MIN_TMP_AVAILABLE_BYTES,
                              "no_preexisting_game_processes": active_game_processes,
                              "xvfb_dimensions": dimensions,
                              "xvfb_server_args": XVFB_SERVER_ARGS},
        "runtime": {"vm": VM, "container": False, "arch": "arm64", "model": MODEL,
                    "effort": EFFORT, "iterations": MAX_DECISIONS,
                    "game_timeout_seconds": GAME_TIMEOUT_SECONDS,
                    "retry_limit": 0, "recovery_decision_cap": 2,
                    "host_relay_timeout_seconds": 900},
        "treatment": {"kind": "none", "model_request_reissued": False,
                      "reason": "A16 active-cover health-policy boundary observation; no relay delay injected",
                      "no_delay_test_sha256": sha(HERE / "test_delay_policy.py")},
        "stop_rule": [f"{MAX_DECISIONS} model decisions", "death", "MAP01 exit", "episode timeout",
                      "runtime or model failure", "600 second episode bound"],
        "fixture_seed": FIXTURE_SEED,
        "fresh_allocation_delta_from_a15": [
            "new preselected fixed seed 990626 and 24-decision cap; the longer bound allows two post-guard decisions while retaining the 600-second episode cap",
            "A15 active authored-cover health samples stayed above their effective floors; A16 uses the same current-main controller and injects no relay delay",
            "one descriptive episode, not a causal efficacy estimate",
            "separate allocation; no retry or reuse of any prior allocation output",
        ],
    }
    OUT.mkdir(parents=True, exist_ok=False)
    (OUT / "host-cwd").mkdir()
    (OUT / "FREEZE.json").write_text(json.dumps(freeze, indent=2) + "\n")

    server_out = (OUT / "app-server.stdout.jsonl").open("wb")
    server_err = (OUT / "app-server.stderr.txt").open("wb")
    guest_out = (OUT / "guest.stdout.jsonl").open("wb")
    guest_err = (OUT / "guest.stderr.txt").open("wb")
    server = subprocess.Popen(host_command, cwd=OUT / "host-cwd", stdin=subprocess.PIPE,
                              stdout=subprocess.PIPE, stderr=server_err, bufsize=0)
    response_queue = queue.Queue()

    def read_server():
        for line in server.stdout:
            server_out.write(line); server_out.flush()
            response_queue.put(line)

    reader = threading.Thread(target=read_server, daemon=True)
    reader.start()
    guest = None
    request_n = response_n = turn_n = 0
    error = None
    start = time.monotonic()
    try:
        guest = subprocess.Popen(guest_command, cwd=REPO, stdout=guest_out, stderr=guest_err)
        while guest.poll() is None:
            if time.monotonic() - start > 900:
                raise TimeoutError("frozen allocation host relay reached 900-second bound")
            if server.poll() is not None:
                raise RuntimeError("Codex app-server exited before guest")
            request = OUT / f"request-{request_n:06d}.jsonl"
            if request.is_file():
                payload = request.read_bytes()
                if len(payload) > 1_048_576 or not payload.endswith(b"\n"):
                    raise ValueError("guest request is not bounded complete JSONL")
                message = json.loads(payload)
                if message.get("method") == "turn/start":
                    turn_n += 1
                verified = image_receipts(message)
                if verified:
                    with (OUT / "host-image-receipts.jsonl").open("a", encoding="utf-8") as stream:
                        stream.write(json.dumps({"request_index": request_n, "images": verified}) + "\n")
                server.stdin.write(payload); server.stdin.flush()
                request_n += 1
            try:
                payload = response_queue.get(timeout=0.01)
                response_message = json.loads(payload)
                response = OUT / f"response-{response_n:06d}.jsonl"
                tmp = response.with_suffix(".tmp")
                tmp.write_bytes(payload); tmp.replace(response)
                response_n += 1
            except queue.Empty:
                pass
        guest.wait(timeout=10)
    except BaseException as exc:
        error = f"{type(exc).__name__}: {exc}"
        (OUT / "relay-error.txt").write_text(error + "\n")
        if guest is not None and guest.poll() is None:
            guest.terminate()
            try:
                guest.wait(timeout=10)
            except subprocess.TimeoutExpired:
                guest.kill(); guest.wait()
    finally:
        if server.stdin and not server.stdin.closed:
            server.stdin.close()
        try:
            server.wait(timeout=10)
        except subprocess.TimeoutExpired:
            server.terminate()
            try:
                server.wait(timeout=5)
            except subprocess.TimeoutExpired:
                server.kill(); server.wait()
        reader.join(timeout=5)
        for stream in (server_out, server_err, guest_out, guest_err):
            stream.close()
        summary = {"guest_exit": None if guest is None else guest.returncode,
                   "app_server_exit": server.returncode, "requests_forwarded": request_n,
                   "responses_forwarded": response_n, "model_turn_starts": turn_n,
                   "delay_injected": False, "retry_count": 0, "error": error,
                   "elapsed_seconds": time.monotonic() - start, "reader_alive": reader.is_alive()}
        (OUT / "HOST.json").write_text(json.dumps(summary, indent=2) + "\n")
        print(json.dumps(summary), flush=True)
    if error or guest is None or guest.returncode != 0:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
