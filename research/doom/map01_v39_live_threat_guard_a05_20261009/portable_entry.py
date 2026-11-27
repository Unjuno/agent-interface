"""POSIX OrbStack VM entry adapter for the frozen V39 controller."""
from pathlib import Path
import hashlib
import json
import os
import sys
import subprocess
import threading

SOURCE = Path(os.environ["A05_SOURCE_ROOT"]).resolve()
sys.path[:0] = [str(SOURCE), str(SOURCE / "research/doom"),
                str(SOURCE / "research/live_control"),
                str(SOURCE / "research/observation_gating"),
                str(SOURCE / "research/observation_tiles"),
                str(SOURCE / "research/real_apps_v1")]
import map01_overlap_controller_v39 as controller

GUEST_OUTPUT = Path(os.environ["GUEST_OUTPUT_ROOT"]).resolve()
HOST_OUTPUT = Path(os.environ["HOST_OUTPUT_ROOT"]).resolve()
HOST_CWD = Path(os.environ["HOST_EMPTY_CWD"]).resolve()


def host_path(path):
    supplied = Path(path)
    resolved = supplied.resolve() if supplied.is_absolute() else (Path.cwd() / supplied).resolve()
    if resolved == SOURCE:
        return str(HOST_CWD)
    relative_to_source = resolved.relative_to(SOURCE)
    if resolved.is_file():
        relative = resolved.relative_to(GUEST_OUTPUT)
        host = (HOST_OUTPUT / relative).resolve()
        receipt = {"guest_path": str(resolved), "relative_path": relative.as_posix(),
                   "host_path": str(host), "sha256": hashlib.sha256(resolved.read_bytes()).hexdigest(),
                   "bytes": resolved.stat().st_size,
                   "scope": "guest path custody; host independently verifies before forwarding"}
        with (GUEST_OUTPUT / "image-path-receipts.jsonl").open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(receipt, separators=(",", ":")) + "\n")
        return str(host)
    return str(HOST_CWD / relative_to_source)


def install():
    # Drain the frozen controller's session-child stderr from process start.
    # This writes only a diagnostic artifact and keeps the child pipe flowing.
    original_popen = subprocess.Popen
    def captured_popen(*args, **kwargs):
        command = args[0] if args else kwargs.get("args")
        if "session_map01_v15.py" not in str(command):
            return original_popen(*args, **kwargs)
        child = original_popen(*args, **kwargs)
        if child.stderr is None:
            raise RuntimeError("session stderr pipe missing")
        capture = GUEST_OUTPUT / "episode" / "session.stderr.txt"
        capture.parent.mkdir(parents=True, exist_ok=True)
        def drain():
            with capture.open("ab") as stream:
                for chunk in iter(lambda: child.stderr.read(4096), ""):
                    stream.write(chunk.encode("utf-8", errors="replace"))
                    stream.flush()
        reader = threading.Thread(target=drain, name="session-stderr-capture", daemon=True)
        reader.start()
        child._a05_stderr_reader = reader
        return child
    subprocess.Popen = captured_popen
    controller.win = host_path
    controller.WAD = Path(os.environ["QUALIFIED_WAD_PATH"]).resolve()
    expected = "a8772e088847032510d97ba2312406a6998f21cbab44d4ff10696faa9c0ecd4b"
    if hashlib.sha256(controller.WAD.read_bytes()).hexdigest() != expected:
        raise ValueError("qualified Freedoom WAD hash mismatch")
    relay = json.loads(os.environ["RELAY_COMMAND_JSON"])
    if not isinstance(relay, list) or not relay or not all(isinstance(item, str) for item in relay):
        raise ValueError("invalid JSONL relay command")
    controller.app_server_command = lambda: list(relay)
    return controller


if __name__ == "__main__":
    install().main()
