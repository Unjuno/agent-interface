"""One-shot WSLc construction gate: enforce memory.max, then run tests."""
from pathlib import Path
import sys
import unittest


EXPECTED_MEMORY_MAX = 1073741824


def memory_limit_is_enforced(raw_value):
    try:
        return int(raw_value.strip()) == EXPECTED_MEMORY_MAX
    except (AttributeError, TypeError, ValueError):
        return False


def main():
    memory_path = Path("/sys/fs/cgroup/memory.max")
    raw_value = memory_path.read_text(encoding="ascii").strip() if memory_path.is_file() else "MISSING"
    print(f"memory.max={raw_value}")
    if not memory_limit_is_enforced(raw_value):
        print("CONSTRUCTION_STOP: requested 1 GiB cgroup memory ceiling is not enforced")
        return 2
    suite = unittest.defaultTestLoader.discover(
        start_dir=str(Path(__file__).resolve().parent), pattern="test_protocol.py")
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
