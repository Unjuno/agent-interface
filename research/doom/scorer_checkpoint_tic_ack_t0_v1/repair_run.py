"""Run the minimal tic-acknowledgment repair against the frozen fake cases."""
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import threading

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "candidate_helper.py"
spec = importlib.util.spec_from_file_location("repaired_checkpoint", SOURCE)
helper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helper)


class Executor:
    def __init__(self):
        self.lock = threading.RLock()
        self.closed = False
        self.active = None


class Owner:
    def call(self, operation):
        assert operation == "input_state"
        return {"owned_keycodes": [], "owned_buttons": [], "active_lease_deadline_ns": None}


class Game:
    def __init__(self, advance_by=1, read_drift=0, fail=False):
        self.tic = 10
        self.advance_by = advance_by
        self.read_drift = read_drift
        self.fail = fail
        self.reads = 0

    def is_episode_finished(self):
        return False

    def get_episode_time(self):
        return self.tic

    def advance_action(self, count, update):
        assert count == 1 and update is True
        if self.fail:
            raise RuntimeError("synthetic refresh failure")
        self.tic += self.advance_by

    def get_game_variable(self, variable):
        self.reads += 1
        if self.reads == 1:
            self.tic += self.read_drift
        return {"kills": 3, "deaths": 0}[variable]


CASES = [
    ("one_tic_acknowledged", 1, 0, False),
    ("refresh_no_op", 0, 0, False),
    ("refresh_two_tics", 2, 0, False),
    ("tic_changes_during_score_read", 1, 1, False),
    ("refresh_raises", 1, 0, True),
]


def main():
    rows = []
    for name, advance_by, read_drift, fail in CASES:
        game = Game(advance_by, read_drift, fail)
        with tempfile.TemporaryDirectory() as tmp:
            receipt = helper.checkpoint(
                game, Executor(), Owner(), {"kills": "kills", "deaths": "deaths"},
                Path(tmp) / "private.jsonl", name)
            private = json.loads((Path(tmp) / "private.jsonl").read_text(encoding="utf-8"))
        rows.append({
            "case": name,
            "status": receipt["status"],
            "controller_gate_accepts": receipt["status"] == "REFRESH_RETURNED_RUNTIME_QUALIFICATION_PENDING",
            "tic_before": private.get("tic_before"),
            "tic_after": private.get("tic_after"),
            "tic_after_read": private.get("tic_after_read"),
            "private_value_keys": sorted((private.get("values") or {}).keys()),
            "public_has_values": "values" in receipt,
        })
    result = {
        "schema": "scorer-checkpoint-tic-ack-repair-raw-v1",
        "source_helper_sha256": json.loads((ROOT / "source-pins.json").read_text(encoding="utf-8"))["files"]["helper"]["sha256"],
        "candidate_helper_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        "runtime": "synthetic fake game, executor, and owner only",
        "rows": rows,
    }
    (ROOT / "repair-raw.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"rows": len(rows), "candidate_helper_sha256": result["candidate_helper_sha256"]}, sort_keys=True))


if __name__ == "__main__":
    main()
