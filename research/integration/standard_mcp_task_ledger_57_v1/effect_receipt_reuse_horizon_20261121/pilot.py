import os
import sys
import tempfile
from pathlib import Path
import copy

evidence_dir = Path(__file__).resolve().parent
package_dir = evidence_dir.parent
worktree_root = package_dir.parents[2]
sys.path.insert(0, str(package_dir))
temp_root = tempfile.TemporaryDirectory(prefix="issue57-pilot-", dir=worktree_root)
os.environ.update(TEMP=temp_root.name, TMP=temp_root.name, TMPDIR=temp_root.name)
from test_effect_receipt_handoff_v1 import EffectReceiptHandoffTests
from test_comparison_measurement_v1 import ComparisonMeasurementTests
from comparison_measurement_v1 import validate_reuse_horizon

t = EffectReceiptHandoffTests()
t.setUp()
t.measured["task_ledger"]["task"]["task_id"] = "task-01"
t.receipt["task_id"] = "task-01"
t.receipt["effect_interval_ns"] = {"lower_ns": 144, "upper_ns": 145}
t.write_receipt()
adapted = t.adapt()["measured_run"]
horizon = ComparisonMeasurementTests.horizon()
c_run = horizon["blocks"][0]["runs"][2]
c_run.update(copy.deepcopy(adapted))
ledger = c_run["task_ledger"]
ledger["comparison"] = {"arm":"C","block":1,"order":3,"task_seed":"seed-01"}
ledger["task"] = {"task_id":"task-01","fixture_sha256":"a"*64,"scorer_sha256":"b"*64}
ledger["source"] = {"commit":"c"*40,"route_sha256":"f"*64}
ledger["environment_sha256"] = "9"*64
ledger["model"] = {"id":"model-x","effort":"low","request_config_sha256":"8"*64}
ledger["run_id"] = "run-C"
for event in ledger["events"]:
    if event.get("attempt_id") == "attempt-1": event["attempt_id"] = "model-C-1"
    if event.get("model_attempt_id") == "attempt-1": event["model_attempt_id"] = "model-C-1"
for image in c_run["measurement"]["model_delivered_images"]:
    if image["attempt_id"] == "attempt-1": image["attempt_id"] = "model-C-1"
horizon["c_plan_trace"][0]["plan_generation_attempt_ids"] = ["model-C-1"]
horizon["c_plan_trace"][0]["attempt_dispositions"][0]["attempt_id"] = "model-C-1"
print(validate_reuse_horizon(horizon)["correctness_qualified_token_break_even_task_index"])
t.tearDown()
temp_root.cleanup()
