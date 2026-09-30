#!/usr/bin/env python3
"""Independent stdlib-only raw-result auditor for Issue #853 Rung 0."""
from __future__ import annotations

import csv
import hashlib
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MODEL = Path("/model/model.safetensors")
RESULT = Path("/out/RESULT.json")
ERRORS: list[str] = []


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def q(values: list[float], p: float) -> float:
    ordered = sorted(values)
    index = (len(ordered) - 1) * p
    low = math.floor(index)
    high = math.ceil(index)
    if low == high:
        return ordered[low]
    return ordered[low] + (ordered[high] - ordered[low]) * (index - low)


def check(condition: bool, name: str) -> None:
    if not condition:
        ERRORS.append(name)


def main() -> int:
    result = json.loads(RESULT.read_text(encoding="utf-8"))
    freeze = json.loads((ROOT / "FREEZE.json").read_text(encoding="utf-8"))
    classes = [f"C{i}" for i in range(6)]
    features = [f"f{i}" for i in range(8)]
    check(result.get("schema") == "issue-853-mitra-rung0-result-v1", "schema")
    check(result.get("allocation") == "mitra-cpu-rung0-853-local-20260927-01", "allocation")
    check(result.get("model_revision") == "edada0d20759c58ada8c8605c25f22f6e98ea5f0", "model_revision")
    check(result.get("model_sha256") == digest(MODEL), "model_sha256")
    check(result.get("model_bytes") == MODEL.stat().st_size == 302717904, "model_bytes")
    check(result.get("model_config") == {"dim": 512, "dim_output": 10, "n_layers": 12, "n_heads": 4, "task": "CLASSIFICATION"}, "model_config")
    check(result.get("freeze_file_sha256") == digest(ROOT / "FREEZE.json"), "freeze_file_sha256")
    check(result.get("source_sha256") == freeze.get("source_sha256"), "source_sha256_binding")
    for relative, expected in freeze.get("source_sha256", {}).items():
        check(digest(ROOT / relative) == expected, f"source_hash:{relative}")
    check(result.get("fine_tune") is False, "fine_tune")
    check(result.get("optimizer_step_calls") == 0, "optimizer_step_calls")
    check(result.get("device") == "cpu" and result.get("cuda_available") is False, "cpu_only")
    check(result.get("torch_threads") == 1, "thread_count")
    check(result.get("class_ids") == classes, "class_ids")
    check(result.get("feature_ids") == features, "feature_ids")
    check(result.get("support_rows") == 256 and result.get("query_rows") == 1024, "row_counts")
    check(result.get("network_expected") == "none", "network_expectation")
    with (ROOT / "support.csv").open(newline="", encoding="utf-8") as stream:
        support = list(csv.DictReader(stream))
    with (ROOT / "queries.csv").open(newline="", encoding="utf-8") as stream:
        queries = list(csv.DictReader(stream))
    check(len(support) == 256 and len(queries) == 1024, "fixture_rows")
    check(set(row["label"] for row in support) == set(classes), "support_class_coverage")
    check(result.get("support_csv_sha256") == digest(ROOT / "support.csv"), "support_hash")
    check(result.get("query_csv_sha256") == digest(ROOT / "queries.csv"), "query_hash")
    check(result.get("support_csv_sha256") == "bf4d64cf826ea2d727990bd799d7e6d0f813a97a64119751e05d22a819fdf785", "support_expected_hash")
    check(result.get("query_csv_sha256") == "dc68fe551034d6f961900e0300af8c41fea641e058380d21c904bc4146df7fd1", "query_expected_hash")
    probabilities = result.get("warm_probabilities", [])
    latencies = result.get("warm_single_query_latency_ms", [])
    check(len(probabilities) == len(latencies) == 1024, "warm_row_counts")
    check(all(len(row) == 6 and all(math.isfinite(v) for v in row) and abs(sum(row) - 1.0) <= 1e-4 for row in probabilities), "warm_probability_shape_finite_sum")
    check(all(math.isfinite(v) and v >= 0 for v in latencies), "latency_values")
    repeated = result.get("repeat_probabilities", [])
    repeated_ids = result.get("repeat_query_indices", [])
    check(repeated_ids == list(range(16)) and len(repeated) == 16, "repeat_rows")
    if len(repeated) == 16 and len(probabilities) >= 16:
        check(all(len(r) == 6 for r in repeated), "repeat_shape")
        check(all(abs(a - b) <= 1e-6 for i in range(16) for a, b in zip(probabilities[i], repeated[i])), "repeat_determinism")
    check(math.isfinite(result.get("fit_wall_s", float("nan"))) and result["fit_wall_s"] > 0, "fit_wall")
    check(math.isfinite(result.get("cold_model_load_s", float("nan"))) and result["cold_model_load_s"] > 0, "cold_load")
    check(math.isfinite(result.get("context_setup_excluding_load_s", float("nan"))) and result["context_setup_excluding_load_s"] >= 0, "context_setup")
    check(isinstance(result.get("peak_rss_bytes"), int) and result["peak_rss_bytes"] > 0, "peak_rss")
    p50 = q(latencies, 0.50) if len(latencies) == 1024 else None
    p95 = q(latencies, 0.95) if len(latencies) == 1024 else None
    p99 = q(latencies, 0.99) if len(latencies) == 1024 else None
    if p95 is not None:
        expected_decision = (
            "REJECT_CPU_HIGH_CADENCE_SHAPE"
            if p95 >= 500.0
            else "PASS_GENERAL_LOCAL_SYSTEM1_RUNTIME_SCOPED+REALTIME_10HZ_CANDIDATE"
            if p95 < 100.0
            else "PASS_GENERAL_LOCAL_SYSTEM1_RUNTIME_SCOPED+INTERACTIVE_2HZ"
        )
        check(result.get("decision") == expected_decision, "decision_gate")
        summary = result.get("latency_summary_ms", {})
        check(abs(summary.get("p50", float("inf")) - p50) < 1e-9, "p50_summary")
        check(abs(summary.get("p95", float("inf")) - p95) < 1e-9, "p95_summary")
        check(abs(summary.get("p99", float("inf")) - p99) < 1e-9, "p99_summary")
    audit = {
        "schema": "issue-853-mitra-rung0-audit-v1",
        "errors": ERRORS,
        "pass": not ERRORS,
        "audited_rows": len(probabilities),
        "p50_ms": p50,
        "p95_ms": p95,
        "p99_ms": p99,
        "decision": result.get("decision"),
    }
    Path("/out/AUDIT.json").write_text(json.dumps(audit, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(audit, sort_keys=True))
    return 0 if not ERRORS else 1


if __name__ == "__main__":
    sys.exit(main())
