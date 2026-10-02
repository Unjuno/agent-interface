"""Independent auditor for the bounded native-WSL2 / WSLc pilot."""

from collections import Counter
from statistics import median


RAW_SCHEMA = "native-wsl2-migration-6389-raw-v1"
FREEZE_SCHEMA = "native-wsl2-migration-6389-freeze-v1"


def _result(status, runs=None, **metrics):
    return {"status": status, "runs_audited": 0 if runs is None else len(runs), **metrics}


def audit(raw, freeze):
    """Validate raw executions against the freeze; never trust summary labels."""
    if (not isinstance(raw, dict) or raw.get("schema") != RAW_SCHEMA
            or not isinstance(freeze, dict) or freeze.get("schema") != FREEZE_SCHEMA):
        return _result("HOLD_RAW_RECORD_INVALID")
    runs = raw.get("runs")
    schedule = freeze.get("expected_schedule")
    source = freeze.get("source_sha256")
    image = freeze.get("wslc_image")
    expected_ids = freeze.get("expected_test_ids")
    threshold = freeze.get("min_improvement_fraction")
    if (not isinstance(runs, list) or not isinstance(schedule, list) or len(runs) != len(schedule)
            or not isinstance(source, dict) or not source or not isinstance(image, str)
            or not isinstance(expected_ids, list) or not expected_ids
            or not isinstance(threshold, (int, float)) or isinstance(threshold, bool)
            or not 0 < threshold < 1):
        return _result("HOLD_RAW_RECORD_INVALID", runs if isinstance(runs, list) else None)

    if [run.get("arm") if isinstance(run, dict) else None for run in runs] != schedule:
        return _result("HOLD_SCHEDULE_INVALID", runs)
    if [run.get("index") if isinstance(run, dict) else None for run in runs] != list(range(len(runs))):
        return _result("HOLD_SCHEDULE_INVALID", runs)
    arms = Counter(schedule)
    if set(arms) != {"native", "wslc"} or arms["native"] < 2 or arms["wslc"] < 2:
        return _result("HOLD_SCHEDULE_INVALID", runs)

    for run in runs:
        if run.get("source_sha256") != source:
            return _result("STOP_SOURCE_IDENTITY_MISMATCH", runs)
        wanted_runtime = image if run["arm"] == "wslc" else freeze.get("native_runtime_identity")
        if not wanted_runtime or run.get("runtime_identity") != wanted_runtime:
            return _result("STOP_RUNTIME_IDENTITY_MISMATCH", runs)
        if (not isinstance(run.get("python_version"), str) or not run["python_version"]
                or not isinstance(run.get("exit_code"), int) or run["exit_code"] != 0
                or not isinstance(run.get("wall_ns"), int) or run["wall_ns"] <= 0
                or not isinstance(run.get("max_tree_rss_kib"), int) or run["max_tree_rss_kib"] <= 0):
            return _result("FAIL_CANDIDATE_EXIT" if run.get("exit_code") != 0 else "HOLD_RAW_RECORD_INVALID", runs)
        tests = run.get("tests")
        if (not isinstance(tests, list) or [x.get("id") for x in tests if isinstance(x, dict)] != expected_ids
                or any(not isinstance(x, dict) or x.get("status") != "passed" for x in tests)):
            return _result("FAIL_SEMANTIC_OUTPUT_DIVERGENCE", runs)
        before, after = run.get("host_psi_total_before"), run.get("host_psi_total_after")
        if (not isinstance(before, dict) or not isinstance(after, dict)
                or not all(isinstance(v, int) and not isinstance(v, bool) and v >= 0
                           for d in (before, after) for v in d.values())
                or set(before) != {"some", "full"} or set(after) != {"some", "full"}
                or any(after[k] < before[k] for k in ("some", "full"))):
            return _result("HOLD_RAW_RECORD_INVALID", runs)
        if any(after[k] != before[k] for k in ("some", "full")):
            return _result("HOLD_MEMORY_PRESSURE_CONFOUNDED", runs)

    versions = {run["python_version"] for run in runs}
    if len(versions) != 1:
        return _result("STOP_RUNTIME_VERSION_MISMATCH", runs)
    semantic = [[(t["id"], t["status"]) for t in run["tests"]] for run in runs]
    if any(value != semantic[0] for value in semantic[1:]):
        return _result("FAIL_SEMANTIC_OUTPUT_DIVERGENCE", runs)

    native = [run for run in runs if run["arm"] == "native"]
    wslc = [run for run in runs if run["arm"] == "wslc"]
    native_wall, wslc_wall = median(r["wall_ns"] for r in native), median(r["wall_ns"] for r in wslc)
    native_rss, wslc_rss = median(r["max_tree_rss_kib"] for r in native), median(r["max_tree_rss_kib"] for r in wslc)
    wall_ratio, rss_ratio = native_wall / wslc_wall, native_rss / wslc_rss
    metrics = {"native_median_wall_ns": native_wall, "wslc_median_wall_ns": wslc_wall,
               "native_median_peak_tree_rss_kib": native_rss,
               "wslc_median_peak_tree_rss_kib": wslc_rss,
               "native_to_wslc_wall_ratio": wall_ratio,
               "native_to_wslc_peak_rss_ratio": rss_ratio}
    if wall_ratio > 1 + threshold or rss_ratio > 1 + threshold:
        return _result("FAIL_NATIVE_REGRESSION", runs, **metrics)
    if wall_ratio <= 1 - threshold or rss_ratio <= 1 - threshold:
        return _result("PASS_NATIVE_MIGRATION_SCOPED", runs, **metrics)
    return _result("NO_PREREGISTERED_BENEFIT", runs, **metrics)
