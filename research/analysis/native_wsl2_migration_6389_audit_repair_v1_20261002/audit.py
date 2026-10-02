"""Corrected independent auditor for the frozen WSL migration contract."""

from collections import Counter
from statistics import median

RAW_SCHEMA = "native-wsl2-migration-6389-raw-v1"
FREEZE_SCHEMA = "native-wsl2-migration-6389-freeze-v1"


def _result(status, runs=None, **metrics):
    return {"status": status, "runs_audited": 0 if runs is None else len(runs), **metrics}


def _exact_int(value, *, minimum=None):
    return type(value) is int and (minimum is None or value >= minimum)


def audit(raw, freeze):
    """Validate the raw record against the immutable nested freeze."""
    if (not isinstance(raw, dict) or raw.get("schema") != RAW_SCHEMA
            or not isinstance(freeze, dict) or freeze.get("schema") != FREEZE_SCHEMA):
        return _result("HOLD_RAW_RECORD_INVALID")
    workload = freeze.get("workload")
    runs = raw.get("runs")
    schedule = freeze.get("expected_schedule")
    source = workload.get("source_sha256") if isinstance(workload, dict) else None
    expected_ids = workload.get("expected_test_ids") if isinstance(workload, dict) else None
    image = freeze.get("wslc_image")
    expected_python_version = freeze.get("expected_python_version")
    threshold = freeze.get("min_improvement_fraction")
    if (not isinstance(runs, list) or not isinstance(schedule, list) or len(runs) != len(schedule)
            or not isinstance(source, dict) or not source or not isinstance(image, str)
            or not isinstance(expected_python_version, str) or not expected_python_version
            or not isinstance(expected_ids, list) or not expected_ids
            or type(threshold) not in (int, float) or not 0 < threshold < 1):
        return _result("HOLD_RAW_RECORD_INVALID", runs if isinstance(runs, list) else None)

    if [r.get("arm") if isinstance(r, dict) else None for r in runs] != schedule:
        return _result("HOLD_SCHEDULE_INVALID", runs)
    if any(not isinstance(r, dict) or not _exact_int(r.get("index"), minimum=0) for r in runs):
        return _result("HOLD_SCHEDULE_INVALID", runs)
    if [r["index"] for r in runs] != list(range(len(runs))):
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
        exit_code = run.get("exit_code")
        if not _exact_int(exit_code):
            return _result("HOLD_RAW_RECORD_INVALID", runs)
        if exit_code != 0:
            return _result("FAIL_CANDIDATE_EXIT", runs)
        if (not isinstance(run.get("python_version"), str) or not run["python_version"]
                or not _exact_int(run.get("wall_ns"), minimum=1)
                or not _exact_int(run.get("max_tree_rss_kib"), minimum=1)):
            return _result("HOLD_RAW_RECORD_INVALID", runs)
        if run["python_version"] != expected_python_version:
            return _result("STOP_RUNTIME_VERSION_MISMATCH", runs)
        tests = run.get("tests")
        if (not isinstance(tests, list) or [x.get("id") for x in tests if isinstance(x, dict)] != expected_ids
                or any(not isinstance(x, dict) or x.get("status") != "passed" for x in tests)):
            return _result("FAIL_SEMANTIC_OUTPUT_DIVERGENCE", runs)
        before, after = run.get("host_psi_total_before"), run.get("host_psi_total_after")
        if (not isinstance(before, dict) or not isinstance(after, dict)
                or set(before) != {"some", "full"} or set(after) != {"some", "full"}
                or not all(_exact_int(v, minimum=0) for d in (before, after) for v in d.values())
                or any(after[k] < before[k] for k in ("some", "full"))):
            return _result("HOLD_RAW_RECORD_INVALID", runs)
        if any(after[k] != before[k] for k in ("some", "full")):
            return _result("HOLD_MEMORY_PRESSURE_CONFOUNDED", runs)

    if len({r["python_version"] for r in runs}) != 1:
        return _result("STOP_RUNTIME_VERSION_MISMATCH", runs)
    semantic = [[(t["id"], t["status"]) for t in r["tests"]] for r in runs]
    if any(value != semantic[0] for value in semantic[1:]):
        return _result("FAIL_SEMANTIC_OUTPUT_DIVERGENCE", runs)

    native = [r for r in runs if r["arm"] == "native"]
    wslc = [r for r in runs if r["arm"] == "wslc"]
    nw, ww = median(r["wall_ns"] for r in native), median(r["wall_ns"] for r in wslc)
    nr, wr = median(r["max_tree_rss_kib"] for r in native), median(r["max_tree_rss_kib"] for r in wslc)
    wall_ratio, rss_ratio = nw / ww, nr / wr
    metrics = {"native_median_wall_ns": nw, "wslc_median_wall_ns": ww,
               "native_median_peak_tree_rss_kib": nr, "wslc_median_peak_tree_rss_kib": wr,
               "native_to_wslc_wall_ratio": wall_ratio, "native_to_wslc_peak_rss_ratio": rss_ratio}
    if wall_ratio > 1 + threshold or rss_ratio > 1 + threshold:
        return _result("FAIL_NATIVE_REGRESSION", runs, **metrics)
    if wall_ratio <= 1 - threshold or rss_ratio <= 1 - threshold:
        return _result("PASS_NATIVE_MIGRATION_SCOPED", runs, **metrics)
    return _result("NO_PREREGISTERED_BENEFIT", runs, **metrics)

