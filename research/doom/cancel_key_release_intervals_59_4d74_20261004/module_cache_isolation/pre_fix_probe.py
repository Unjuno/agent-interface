"""Reproduce the reviewed module-cache leak using the archived prior test."""
import importlib.util
import sys
import types
from pathlib import Path

repo = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(repo / "research" / "live_control"))
test_path = Path(__file__).with_name("pre-review-test.py")
spec = importlib.util.spec_from_file_location("pre_review_owner_interval_test", test_path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

previous = sys.modules.get("input_owner_v12")
sentinel = types.ModuleType("input_owner_v12")
sys.modules["input_owner_v12"] = sentinel
try:
    module.BatchReleaseIntervalTests(
        "test_cancelled_release_records_each_key_to_shared_sync_bound"
    ).run()
    if sys.modules.get("input_owner_v12") is not sentinel:
        raise AssertionError("pre-existing input_owner_v12 cache entry was discarded")
finally:
    if previous is None:
        sys.modules.pop("input_owner_v12", None)
    else:
        sys.modules["input_owner_v12"] = previous
