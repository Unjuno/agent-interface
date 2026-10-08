"""Select and wait for one typed OpenTTD persisted finish outcome."""
import json
import time
from pathlib import Path


NAMES = ("result.json", "failure-evaluation.json")


def select(root, expected_finish_kind=None):
    root = Path(root)
    existing = [root / name for name in NAMES if (root / name).exists()]
    if not existing:
        raise FileNotFoundError("no persisted outcome")
    if len(existing) != 1:
        raise ValueError("exactly one persisted outcome required")
    path = existing[0]
    value = json.loads(path.read_text(encoding="utf-8"))
    if type(value.get("success")) is not bool:
        raise ValueError("persisted outcome requires boolean success")
    if path.name == "result.json" and value["success"] is not True:
        raise ValueError("result.json must retain independent success")
    if path.name == "failure-evaluation.json" and value["success"] is not False:
        raise ValueError("failure-evaluation.json must retain independent failure")
    if expected_finish_kind is not None and value.get("finish_kind") != expected_finish_kind:
        raise ValueError("persisted outcome finish kind mismatch")
    return path, value


def wait(root, process, seconds, expected_finish_kind=None, poll_seconds=0.025):
    deadline = time.monotonic() + seconds
    while True:
        try:
            return select(root, expected_finish_kind)
        except FileNotFoundError:
            pass
        if process.poll() is not None:
            try:
                return select(root, expected_finish_kind)
            except FileNotFoundError as error:
                raise RuntimeError("driver exited before a persisted outcome") from error
        if time.monotonic() > deadline:
            raise TimeoutError("persisted outcome")
        time.sleep(poll_seconds)
