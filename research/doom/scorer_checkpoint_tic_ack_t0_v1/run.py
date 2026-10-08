"""Execute synthetic refresh outcomes through the exact retained helper."""
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import threading

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
HELPER_PATH = REPO / "research/doom/post_guard_controller_preparation_59_4d74_20261004/private_score_checkpoint.py"
spec = importlib.util.spec_from_file_location("checkpoint_under_test", HELPER_PATH)
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
    records = []
    for name, advance_by, read_drift, fail in CASES:
        game = Game(advance_by=advance_by, read_drift=read_drift, fail=fail)
        with tempfile.TemporaryDirectory() as tmp:
            result = helper.checkpoint(
                game, Executor(), Owner(), {"kills": "kills", "deaths": "deaths"},
                Path(tmp) / "private.jsonl", name)
            row = json.loads((Path(tmp) / "private.jsonl").read_text(encoding="utf-8"))
        # Public receipts must never include score values.
        public_keys = sorted(result)
        records.append({
            "case": name,
            "helper_status": row["status"],
            "controller_gate_accepts_receipt": result["status"] == "REFRESH_RETURNED_RUNTIME_QUALIFICATION_PENDING",
            "tic_before": row.get("tic_before"),
            "tic_after": row.get("tic_after"),
            "tic_after_read": row.get("tic_after_read"),
            "private_value_keys": sorted((row.get("values") or {}).keys()),
            "public_keys": public_keys,
            "public_has_values": "values" in result,
        })
    output = {
        "schema": "scorer-checkpoint-tic-ack-t0-raw-v1",
        "helper_sha256": __import__("hashlib").sha256(HELPER_PATH.read_bytes()).hexdigest(),
        "base_main": "b63b8ad7872f3d19407dce8ed0862ec0aa4a4925",
        "runtime": "synthetic fake game and owner; no ViZDoom or input",
        "rows": records,
    }
    (ROOT / "raw.json").write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"rows": len(records), "helper_sha256": output["helper_sha256"], "path": "raw.json"}, sort_keys=True))


if __name__ == "__main__":
    main()
