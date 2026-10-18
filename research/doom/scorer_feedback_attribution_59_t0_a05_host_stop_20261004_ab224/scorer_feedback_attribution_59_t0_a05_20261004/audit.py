"""Independent read-only audit of the captured A05 construction result."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
result = json.loads((ROOT / "RESULT.json").read_text(encoding="utf-8"))


def digest(name):
    return hashlib.sha256((ROOT / name).read_bytes()).hexdigest()


checks = {
    "schema": result["schema"] == "scorer-feedback-attribution-a05-result-v1",
    "base_commit": result["base_commit"] == "8ddf0925539d03733d803b469586fb74a5b444e0",
    "main_commit": result["current_main_commit"] == "af6d0f9842a2377fba736d2d65643b02690f99d9",
    "producer_hash": result["producer_contract"]["sha256"] == "3d906a7043f0d674bac3bd137952adeac11c77c9339bc38ef6ca37b05e0d1613",
    "producer_positive_vocab": result["producer_contract"]["positive_useful_kinds"] == ["KILL_COUNT_INCREASE", "MAP_EXIT"],
    "a04_red": result["red_baseline"]["exit_code"] == 1 and "SINGLE_POSSIBLE_INTENT_ENVELOPE" in result["red_baseline"]["stderr"],
    "a05_suite_green": result["green_a05_suite"]["exit_code"] == 0 and "Ran 2 tests" in result["green_a05_suite"]["stderr"] and "OK" in result["green_a05_suite"]["stderr"],
    "a04_suite_green": result["green_a04_suite"]["exit_code"] == 0 and "Ran 15 tests" in result["green_a04_suite"]["stderr"] and "OK" in result["green_a04_suite"]["stderr"],
    "compile_green": result["py_compile"]["exit_code"] == 0,
    "docker_stop_preserved": result["docker"]["status"] == "STOP_NOT_RUN",
    "v3_source_hash": digest("scorer_feedback_attribution_v3.py") == result["source_sha256"]["scorer_feedback_attribution_v3.py"],
    "v4_source_hash": digest("scorer_feedback_attribution_v4.py") == result["source_sha256"]["scorer_feedback_attribution_v4.py"],
    "a05_test_hash": digest("test_unknown_kind.py") == result["source_sha256"]["test_unknown_kind.py"],
    "red_probe_hash": digest("initial-red/test_unknown_kind_probe.py") == result["source_sha256"]["initial-red/test_unknown_kind_probe.py"],
    "freeze_hash": digest("FREEZE.json") == result["source_sha256"]["FREEZE.json"],
    "runner_hash": digest("run.py") == result["source_sha256"]["run.py"],
    "report_hash": digest("README.md") == result["source_sha256"]["README.md"],
    "initial_probe_frozen": result["source_sha256"]["initial-red/test_unknown_kind_probe.py"] == "f0976a92f1dac1839fbb8bea5205ea0eff1acd3ab8ea175f73cf04ec23b2a6f4",
    "disposition": result["disposition"] == "PASS_HOST_CONSTRUCTION_STOP_CONTAINER",
}
print(json.dumps({"status": "PASS_A05_SAVED_RESULT_AUDIT" if all(checks.values()) else "FAIL_A05_SAVED_RESULT_AUDIT", "checks": checks}, sort_keys=True))
raise SystemExit(0 if all(checks.values()) else 1)
