import hashlib
import json
import subprocess
import tempfile
from pathlib import Path
from threading import Lock

ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".git").exists())
PKG = Path(__file__).resolve().parent
FREEZE = json.loads((PKG / "FREEZE.json").read_text(encoding="utf-8"))


class Executor:
    def __init__(self):
        self.lock, self.closed, self.active = Lock(), False, None


class Owner:
    def call(self, _):
        return {"owned_keycodes": [], "owned_buttons": [], "active_lease_deadline_ns": None}


class State:
    def __init__(self, tic):
        self.tic, self.game_variables = tic, (0, 1)


class Game:
    def __init__(self, before, after, readback):
        self.values = (before, after, readback)
        self.position = 0

    def is_episode_finished(self):
        return False

    def advance_action(self, *_):
        return None

    def get_episode_time(self):
        value = self.values[min(self.position, 2)]
        self.position += 1
        return value

    def get_state(self):
        return State(1 if self.values[1] == 1 else 11)


def main():
    frozen = FREEZE["source_path"]
    source = subprocess.check_output(["git", "show", f"{FREEZE['subject_pr_head']}:{frozen}"], cwd=ROOT)
    digest = hashlib.sha256(source).hexdigest()
    if digest != FREEZE["source_sha256"]:
        raise SystemExit("HOLD_SOURCE_HASH_MISMATCH")
    namespace = {"__name__": "frozen_candidate"}
    exec(compile(source, frozen, "exec"), namespace)
    cases = [
        ("integer_control", 10, 11, 11),
        ("float_alias", 10, 11, 11.0),
        ("bool_alias", 0, 1, True),
    ]
    outputs = []
    with tempfile.TemporaryDirectory() as td:
        for name, before, after, readback in cases:
            log = Path(td) / f"{name}.jsonl"
            receipt = namespace["checkpoint"](
                Game(before, after, readback), Executor(), Owner(),
                {"DEATHCOUNT": object(), "KILLCOUNT": object()}, log, name)
            row = json.loads(log.read_text(encoding="utf-8").splitlines()[0])
            outputs.append({
                "case": name,
                "before": {"value": before, "type": type(before).__name__},
                "after": {"value": after, "type": type(after).__name__},
                "readback": {"value": readback, "type": type(readback).__name__},
                "receipt_status": receipt["status"],
                "row_status": row["status"],
                "error": row.get("error"),
                "values_present": "values" in row,
            })
    result = {
        "schema": "scorer-endpoint-read-type-7685-a01-v1",
        "source_sha256": digest,
        "subject_pr_head": FREEZE["subject_pr_head"],
        "cases": outputs,
        "decision": "FAIL_OPEN_ENDPOINT_TYPE" if any(x["case"] != "integer_control" and x["receipt_status"] == "REFRESH_RETURNED_RUNTIME_QUALIFICATION_PENDING" for x in outputs) else "PASS_FAIL_CLOSED",
        "scope": "candidate construction behavior under stubs only",
    }
    (PKG / "RESULT.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
