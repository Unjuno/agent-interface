"""One-shot host relay for the dedicated OrbStack VM V39 allocation."""
from pathlib import Path
import hashlib
import json
import os
import queue
import subprocess
import sys
import threading
import time

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
ALLOC = "map01-v39-live-threat-guard-a02-20261009"
OUT = REPO / "results-local/doom" / ALLOC
VM = "issue59-live-v39-a01-20261009"
CLI = Path("/opt/homebrew/bin/codex")
PROXY = "/mnt/source/research/doom/actual_source_recovery_59_4d74_20261004/controller_file_stdio_proxy.py"
ENTRY = "/mnt/source/research/doom/map01_v39_live_threat_guard_a02_20261009/portable_entry.py"
FIXTURE = "/mnt/source/research/doom/fixtures/map01-threat-contact-v2/fixture.json"
WAD = "/tmp/vizdoom-venv/lib/python3.12/site-packages/vizdoom/freedoom2.wad"


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
    OUT.mkdir(parents=True, exist_ok=False)
    (OUT / "host-cwd").mkdir()
    if not CLI.is_file():
        raise FileNotFoundError(CLI)
    source_names = json.loads((REPO / "research/doom/map01_v39_coast_liveness_live_v1_prereg.json").read_text())["source_sha256"]
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
    host_command = [str(CLI), "app-server", "--stdio", "--disable", "plugins",
                    "--disable", "remote_plugin", "--disable", "shell_tool",
                    "--disable", "shell_snapshot", "-c", "project_doc_max_bytes=0"]
    guest_env = {
        "HOME": "/tmp/issue59-live-v39-home", "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONPATH": "/mnt/source:/mnt/source/research/doom:/mnt/source/research/live_control:/mnt/source/research/observation_gating:/mnt/source/research/observation_tiles:/mnt/source/research/real_apps_v1",
        "GUEST_OUTPUT_ROOT": "/mnt/source/results-local/doom/" + ALLOC,
        "HOST_OUTPUT_ROOT": str(OUT.resolve()), "HOST_EMPTY_CWD": str((OUT / "host-cwd").resolve()),
        "RELAY_COMMAND_JSON": json.dumps(["/tmp/vizdoom-venv/bin/python", PROXY,
                                             "/mnt/source/results-local/doom/" + ALLOC]),
        "RELAY_MAX_SECONDS": "1800", "QUALIFIED_WAD_PATH": WAD,
    }
    guest_command = ["orb", "-m", VM, "/usr/bin/env"]
    guest_command.extend(f"{key}={value}" for key, value in guest_env.items())
    guest_command.extend([
        "/tmp/vizdoom-venv/bin/python", ENTRY,
        "--out", "/mnt/source/results-local/doom/" + ALLOC + "/episode",
        "--iterations", "6", "--seed", "990619", "--session-span", "6",
        "--model", "gpt-5.6-luna", "--effort", "low",
        "--measurement-session",
        "--load-fixture-manifest", FIXTURE,
    ])
    (OUT / "FREEZE.json").write_text(json.dumps({
        "allocation_id": ALLOC, "source_commit": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=REPO, text=True).strip(),
        "source_hashes": source_hashes,
        "preregistration_sha256": sha(HERE / "PREREGISTRATION.md"),
        "portable_entry_sha256": sha(HERE / "portable_entry.py"),
        "host_runner_sha256": sha(__file__),
        "fixture_manifest_sha256": sha(REPO / "research/doom/fixtures/map01-threat-contact-v2/fixture.json"),
        "fixture_save_sha256": sha(REPO / "research/doom/fixtures/map01-threat-contact-v2/save.png"),
        "wad_sha256": subprocess.check_output(["orb", "-m", VM, "sha256sum", WAD], text=True).split()[0], "codex_cli_sha256": sha(CLI),
        "codex_cli_version": subprocess.check_output([str(CLI), "--version"], text=True).strip(),
        "host_command": host_command, "guest_command": guest_command,
        "runtime": {"vm": VM, "container": False, "arch": "arm64", "model": "gpt-5.6-luna",
                    "effort": "low", "iterations": 6, "retry_limit": 0},
    }, indent=2) + "\n")

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
    request_n = response_n = 0
    error = None
    start = time.monotonic()
    try:
        guest = subprocess.Popen(guest_command, cwd=REPO, stdout=guest_out, stderr=guest_err)
        while guest.poll() is None:
            if time.monotonic() - start > 1800:
                raise TimeoutError("frozen allocation host relay reached 1800-second bound")
            if server.poll() is not None:
                raise RuntimeError("Codex app-server exited before guest")
            request = OUT / f"request-{request_n:06d}.jsonl"
            if request.is_file():
                payload = request.read_bytes()
                if len(payload) > 1_048_576 or not payload.endswith(b"\n"):
                    raise ValueError("guest request is not bounded complete JSONL")
                message = json.loads(payload)
                verified = image_receipts(message)
                if verified:
                    with (OUT / "host-image-receipts.jsonl").open("a", encoding="utf-8") as stream:
                        stream.write(json.dumps({"request_index": request_n, "images": verified}) + "\n")
                server.stdin.write(payload); server.stdin.flush()
                request_n += 1
            try:
                payload = response_queue.get(timeout=0.01)
                json.loads(payload)
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
                   "responses_forwarded": response_n, "error": error,
                   "elapsed_seconds": time.monotonic() - start, "reader_alive": reader.is_alive()}
        (OUT / "HOST.json").write_text(json.dumps(summary, indent=2) + "\n")
        print(json.dumps(summary), flush=True)
    if error or guest is None or guest.returncode != 0:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
