"""Independent standard-library audit for Issue #4957 raw result."""
import hashlib
import json
import math
import statistics
import sys
from pathlib import Path

ALLOCATION = "gpu-exact-frame-gate-1564-20260928-01"
EXPECTED_CASES = {
    (64, 64, "UNCHANGED"): True,
    (64, 64, "ONE_CHANNEL_PIXEL_CHANGE"): False,
    (1920, 1080, "UNCHANGED"): True,
    (1920, 1080, "ONE_CHANNEL_PIXEL_CHANGE"): False,
    (3840, 2160, "UNCHANGED"): True,
    (3840, 2160, "ONE_CHANNEL_PIXEL_CHANGE"): False,
}
EXPECTED_REPEATS = 25

def p95(values):
    return sorted(values)[math.ceil(0.95 * len(values)) - 1]

def audit(path):
    result = json.loads(Path(path).read_text(encoding="utf-8"))
    errors = []
    if result.get("schema_version") != 1:
        errors.append("SCHEMA_VERSION")
    if result.get("allocation") != ALLOCATION:
        errors.append("ALLOCATION")
    cases = {}
    for row in result.get("exactness_cases", []):
        key = (row.get("width"), row.get("height"), row.get("outcome"))
        if key in cases:
            errors.append("DUPLICATE_EXACTNESS_CASE")
        cases[key] = row
        if key not in EXPECTED_CASES:
            errors.append("UNEXPECTED_EXACTNESS_CASE")
            continue
        expected = EXPECTED_CASES[key]
        if row.get("expected_equal") is not expected:
            errors.append("DECLARED_EXPECTATION")
        if row.get("cpu_equal") is not expected:
            errors.append("CPU_EXACTNESS")
        if row.get("cuda_equal") is not expected:
            errors.append("CUDA_EXACTNESS")
        digest = row.get("input_pair_sha256", "")
        if len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
            errors.append("INPUT_DIGEST_FORMAT")
    if set(cases) != set(EXPECTED_CASES):
        errors.append("EXACTNESS_CASE_COVERAGE")

    measurements = {}
    for row in result.get("measurements", []):
        key = (row.get("width"), row.get("height"), row.get("outcome"))
        if key in measurements:
            errors.append("DUPLICATE_MEASUREMENT")
        measurements[key] = row
        if key not in EXPECTED_CASES:
            errors.append("UNEXPECTED_MEASUREMENT")
            continue
        cpu = row.get("cpu_ns", [])
        cuda = row.get("cuda_end_to_end_ns", [])
        if len(cpu) != EXPECTED_REPEATS or len(cuda) != EXPECTED_REPEATS:
            errors.append("SAMPLE_COUNT")
            continue
        if any(type(x) is not int or x <= 0 for x in cpu + cuda):
            errors.append("SAMPLE_VALUE")
            continue
        checks = [
            ("cpu_median_ns", int(statistics.median(cpu))),
            ("cuda_end_to_end_median_ns", int(statistics.median(cuda))),
            ("cpu_p95_ns", int(p95(cpu))),
            ("cuda_end_to_end_p95_ns", int(p95(cuda))),
        ]
        for field, value in checks:
            if row.get(field) != value:
                errors.append("SUMMARY_" + field.upper())
    if set(measurements) != set(EXPECTED_CASES):
        errors.append("MEASUREMENT_COVERAGE")

    large_wins = True
    for width, height in ((1920, 1080), (3840, 2160)):
        row = measurements.get((width, height, "UNCHANGED"))
        if row is None:
            large_wins = False
            continue
        large_wins &= row.get("cuda_end_to_end_median_ns", 0) < row.get("cpu_median_ns", 0)
    if result.get("large_size_cuda_wins_on_unchanged") is not large_wins:
        errors.append("LARGE_WIN_FLAG")
    expected_decision = "PASS_GPU_EXACT_GATE_BREAK_EVEN_SCOPED" if large_wins else "REJECT_GPU_FOR_HOST_RESIDENT_EXACT_O1_SCOPED"
    if result.get("decision") != expected_decision:
        errors.append("DECISION")
    if result.get("host", {}).get("device_count", 0) < 1:
        errors.append("GPU_DEVICE_RECEIPT")
    if result.get("host", {}).get("torch_cuda_runtime") in (None, ""):
        errors.append("CUDA_RUNTIME_RECEIPT")
    return {
        "result": "PASS_RAW_RESULT_AUDIT" if not errors else "FAIL_RAW_RESULT_AUDIT",
        "errors": errors,
        "exactness_rows": len(cases),
        "measurement_rows": len(measurements),
        "samples_per_arm_per_row": EXPECTED_REPEATS,
        "recomputed_decision": expected_decision,
        "result_sha256": hashlib.sha256(Path(path).read_bytes()).hexdigest(),
    }

if __name__ == "__main__":
    outcome = audit(sys.argv[1] if len(sys.argv) > 1 else "result.json")
    print(json.dumps(outcome, sort_keys=True))
    raise SystemExit(0 if outcome["result"] == "PASS_RAW_RESULT_AUDIT" else 1)
