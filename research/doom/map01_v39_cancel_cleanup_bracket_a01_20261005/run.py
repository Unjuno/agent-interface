"""Run the one-shot fake-display cleanup bracket construction candidate."""
import hashlib
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
FREEZE_PATH = HERE / "FREEZE-A02.json"
OUT = HERE / "results" / "a02"
sys.path.insert(0, str(ROOT))

from research.doom.map01_v39_perkey_bridge_a01.test_bridge import (  # noqa: E402
    load_v12_test_harness,
)


def main():
    if OUT.exists():
        raise SystemExit("STOP: candidate output already exists")
    freeze = json.loads(FREEZE_PATH.read_text(encoding="utf-8"))
    source_raw = (HERE / "input_owner_v13.py").read_bytes()
    for name, expected in freeze["sources"].items():
        if hashlib.sha256((HERE / name).read_bytes()).hexdigest() != expected["sha256"]:
            raise SystemExit(f"STOP: {name} differs from FREEZE-A02.json")
    OUT.mkdir(parents=True)

    harness_module = load_v12_test_harness()
    owner_module = harness_module.load("input_owner_v13_candidate",
                                       HERE / "input_owner_v13.py")
    harness = harness_module.Harness(owner_module)
    keysym = owner_module.XK
    original_string_to_keysym = keysym.string_to_keysym
    keysym.string_to_keysym = lambda key: {"a": 11, "space": 12}.get(key, 0)
    harness.d.keysym_to_keycode = lambda sym: {11: 74, 12: 65}.get(sym, 0)
    lease = harness_module.Lease(intent="intent-cleanup-v13-a02")
    rows = []
    try:
        for key in ("a", "space"):
            rows.append(harness.owner.call("down", lease, key))
        started_ns = time.perf_counter_ns()
        lease.cancel.set()
        cleanup = None
        for _ in range(1000):
            cleanup = next((row for row in harness.owner.records
                            if row.get("event") == "owner_release"
                            and row.get("reason") == "cancelled"), None)
            if cleanup is not None:
                break
            time.sleep(0.001)
        finished_ns = time.perf_counter_ns()
        if cleanup is None:
            raise RuntimeError("cancellation cleanup did not arrive")
        rows.append(cleanup)
        fake_state = sorted(harness.d.physical)
        candidate = {
            "run_id": freeze["run_id"],
            "status": "PASS_CLEANUP_PER_KEY_BRACKETS_SCOPED",
            "started_ns": started_ns,
            "finished_ns": finished_ns,
            "admission_count": 2,
            "cleanup_verified": cleanup["verified"],
            "fake_physical_keys_after_cleanup": fake_state,
            "measurement_keys": sorted(
                row["key"] for row in cleanup["per_key_release_measurements"]
            ),
            "source_sha256": freeze["sources"]["input_owner_v13.py"]["sha256"],
            "authority_granted": False,
            "application_consumption_observed": False,
            "scope": "fake-display sample bracket around owner batch cleanup",
        }
        raw = "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows).encode("utf-8")
        (OUT / "candidate-events.jsonl").write_bytes(raw)
        candidate["raw_sha256"] = hashlib.sha256(raw).hexdigest()
        (OUT / "RESULT.json").write_text(
            json.dumps(candidate, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps(candidate, sort_keys=True))
    finally:
        harness.close()
        keysym.string_to_keysym = original_string_to_keysym


if __name__ == "__main__":
    main()
