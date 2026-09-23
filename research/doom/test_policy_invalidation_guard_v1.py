"""Boundary tests for one-way policy invalidation."""
import sys
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "live_control"))
from policy_invalidation_guard_v1 import PolicyInvalidationGuard


def spec(sequence=10, minimum=4):
    return {
        "op": "policy_invalidation_guard",
        "guard_id": "synthetic-region",
        "source_sequence": sequence,
        "box": [2, 2, 8, 8],
        "metric": "rgb_change",
        "rgb_threshold": 32,
        "minimum_changed_pixels": minimum,
        "max_source_age_ms": 10000,
        "on_change": "needs_decision",
        "on_unknown": "needs_decision",
    }


def main():
    source = Image.new("RGB", (10, 10), "black")
    guard = PolicyInvalidationGuard(spec(), source, 10, "surface-a", 1_000_000_000)
    same = guard.evaluate(source.copy(), 11, "surface-a", 1_100_000_000)
    assert same["status"] == "UNCHANGED" and same["keep_existing_policy"] is True
    changed = source.copy()
    for point in ((2, 2), (3, 2), (4, 2), (5, 2)):
        changed.putpixel(point, (255, 0, 0))
    hit = guard.evaluate(changed, 11, "surface-a", 1_100_000_000)
    assert hit["status"] == "INVALIDATED" and hit["changed_pixels"] == 4
    below = PolicyInvalidationGuard(spec(minimum=5), source, 10, "surface-a", 1_000_000_000)
    assert below.evaluate(changed, 11, "surface-a", 1_100_000_000)["status"] == "UNCHANGED"
    controls = {
        "binding": guard.evaluate(source, 11, "surface-b", 1_100_000_000),
        "sequence": guard.evaluate(source, 10, "surface-a", 1_100_000_000),
        "time": guard.evaluate(source, 11, "surface-a", 900_000_000),
        "expiry": guard.evaluate(source, 11, "surface-a", 12_000_000_000),
        "geometry": guard.evaluate(Image.new("RGB", (9, 10)), 11, "surface-a", 1_100_000_000),
    }
    assert all(row["status"] == "UNKNOWN" and row["requires_new_decision"]
               and not row["grants_input_authority"] for row in controls.values())
    malformed = []
    for update in (
            {"source_sequence": 9}, {"box": [0, 0, 20, 20]},
            {"rgb_threshold": 0}, {"minimum_changed_pixels": 37},
            {"max_source_age_ms": 99}, {"on_change": "continue"}):
        candidate = spec(); candidate.update(update)
        try:
            PolicyInvalidationGuard(candidate, source, 10, "surface-a", 1_000_000_000)
        except ValueError:
            malformed.append(True)
        else:
            malformed.append(False)
    assert all(malformed)
    print({"passed": True, "changed_boundary": 4,
           "unknown_controls": len(controls), "malformed_controls": len(malformed)})


if __name__ == "__main__":
    main()
