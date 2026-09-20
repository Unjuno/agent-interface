"""Independent stdlib audit for a recorded MAP01 VIZ_Tic perf breakpoint."""
import hashlib
import json
import statistics
from pathlib import Path


root = Path(__file__).resolve().parent / "map01-hwbp-probe"
raw_path = root / "raw.json"
raw = json.loads(raw_path.read_text(encoding="utf-8"))
errors = []
records = raw.get("records", [])
samples = [row for row in records if row.get("type") == "sample"]
times = [row.get("time_ns") for row in samples]
target = raw.get("runtime_viz_tic_address")

if raw.get("formal_allocation") is not False:
    errors.append("raw_not_excluded_construction")
if raw.get("perf_event_open") != "PASS":
    errors.append("perf_event_open_not_pass")
if raw.get("event_count") != len(samples) or not samples:
    errors.append("event_count_sample_count_mismatch")
if raw.get("engine_executable_sha256") != raw.get("baseline_binary_sha256"):
    errors.append("runtime_binary_not_symbol_build_binary")
if int(target, 16) != int(raw.get("load_bias", "0"), 16) + int(raw.get("viz_tic_link_address", "0"), 16):
    errors.append("runtime_address_reconstruction_failed")
if not raw.get("executable_mapping", "").split()[1].startswith("r-x"):
    errors.append("target_mapping_not_executable")
if raw.get("api_tic_before_window") != raw.get("api_tic_after_window"):
    errors.append("passive_api_snapshot_changed")
if raw.get("ring_data_tail_before_read") != 0 or raw.get("ring_data_head", 0) < len(samples) * 32:
    errors.append("ring_buffer_shape_invalid")
if any(row.get("ip") != target for row in samples):
    errors.append("sample_ip_did_not_match_viz_tic_entry")
if any(row.get("pid") != raw.get("engine_pid") or row.get("tid") != raw.get("engine_pid") for row in samples):
    errors.append("sample_task_identity_mismatch")
if any(right <= left for left, right in zip(times, times[1:])):
    errors.append("sample_timestamps_not_strictly_increasing")
if any(not raw.get("perf_start_monotonic_ns", 0) <= stamp <= raw.get("perf_end_monotonic_ns", 0) for stamp in times):
    errors.append("sample_timestamp_outside_capture_window")
if any(row.get("type") != "sample" for row in records):
    errors.append("non_sample_or_loss_record_present")

start_clock_delta = raw.get("perf_start_monotonic_ns", 0) - raw.get("python_start_perf_counter_ns", 0)
end_clock_delta = raw.get("perf_end_monotonic_ns", 0) - raw.get("python_end_perf_counter_ns", 0)
if max(abs(start_clock_delta), abs(end_clock_delta)) > 10_000:
    errors.append("monotonic_clock_alignment_over_10us")

scorer_start, scorer_end = raw.get("scorer_start_ns", 0), raw.get("scorer_end_ns", 0)
sample_ns = raw.get("scorer_return", {}).get("sample_ns", -1)
if not scorer_start <= sample_ns <= scorer_end:
    errors.append("scorer_sample_timestamp_outside_call")
if any(scorer_start <= stamp <= scorer_end for stamp in times):
    errors.append("unexpected_viz_tic_edge_inside_outer_scorer_call")
before = max((stamp for stamp in times if stamp < scorer_start), default=None)
after = min((stamp for stamp in times if stamp > scorer_end), default=None)
if before is None or after is None:
    errors.append("scorer_not_bracketed_by_observed_tic_edges")

spacing = [right - left for left, right in zip(times, times[1:])]
summary = {
    "schema": "map01-viz-tic-hwbp-audit-v1",
    "formal_allocation": False,
    "decision": "PASS_BREAKPOINT_TIMESTAMP_CONSTRUCTION_ONLY" if not errors else "FAIL_AUDIT",
    "errors": errors,
    "sample_count": len(samples),
    "lost_or_non_sample_record_count": sum(row.get("type") != "sample" for row in records),
    "target_ip": target,
    "distinct_sample_ips": sorted({row.get("ip") for row in samples}),
    "sample_interval_ns_min_median_max": [min(spacing), int(statistics.median(spacing)), max(spacing)] if spacing else None,
    "observed_event_rate_hz": round((len(times) - 1) * 1e9 / (times[-1] - times[0]), 6) if len(times) > 1 else None,
    "scorer_outer_span_ns": scorer_end - scorer_start,
    "scorer_edge_bracket_before_ns": scorer_start - before if before is not None else None,
    "scorer_edge_bracket_after_ns": after - scorer_end if after is not None else None,
    "scorer_edge_bracket_width_ns": after - before if before is not None and after is not None else None,
    "perf_vs_python_clock_offset_ns_start_end": [start_clock_delta, end_clock_delta],
    "raw_sha256": hashlib.sha256(raw_path.read_bytes()).hexdigest(),
}
(root / "audit.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps(summary, indent=2, sort_keys=True))
raise SystemExit(bool(errors))
