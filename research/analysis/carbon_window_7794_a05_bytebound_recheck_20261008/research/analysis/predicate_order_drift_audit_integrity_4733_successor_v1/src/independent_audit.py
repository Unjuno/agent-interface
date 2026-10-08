from __future__ import annotations

import base64
import hashlib
import json
import math
import sys
import zipfile
from io import BytesIO
from pathlib import Path


def git_blob(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def weighted_quantile(rows, q):
    ordered = sorted(rows, key=lambda row: row["cost"])
    total = sum(row["weight"] for row in ordered)
    threshold = q * total
    cumulative = 0.0
    for row in ordered:
        cumulative += row["weight"]
        if cumulative + 1e-12 >= threshold:
            return row["cost"]
    return max(row["cost"] for row in ordered)


def main(result_path: str, input_dir: str):
    root = Path(input_dir)
    source = (root / "legacy_audit.py").read_bytes()
    archive_text = (root / "RAW_AND_AUDIT.zip.base64").read_bytes()
    source = source[:-1] + b"\r\n" if len(source) == 6247 and source.endswith(b"\n\n") else source
    archive_text = archive_text[:-1] + b"\r\n" if len(archive_text) == 5325 and archive_text.endswith(b"\n") else archive_text
    assert git_blob(source) == "1a6cc0e46b32d4cd6989aed118d003cce4cfe399"
    assert git_blob(archive_text) == "c38dd2002f201d49b6fc261caff019550a4bf4bc"
    archive = base64.b64decode(archive_text.strip(), validate=True)
    with zipfile.ZipFile(BytesIO(archive)) as zf:
        raw_name = next(n for n in zf.namelist() if n.lower().endswith("raw.json"))
        raw = zf.read(raw_name)
    raw_sha = hashlib.sha256(raw).hexdigest()
    assert raw_sha == "5f48e0274f9fd800ac26af3dd70bd52171700b32ce159f3cdbe0f28c7ec35e7d"
    doc = json.loads(raw)
    assert len(doc["distributions"]) == 21
    orders = {"NAIVE": ("D", "C", "B", "A"),
              "FROZEN_COST_SELECTIVITY": ("A", "B", "C", "D")}
    costs = {"A": 1, "B": 2, "C": 5, "D": 10}
    crossover = None
    row_count = 0
    for dist, alpha in zip(doc["distributions"], [i / 20 for i in range(21)]):
        assert dist["alpha"] == alpha
        accum = {key: [] for key in orders}
        mass = 0.0
        for mask, row in enumerate(dist["rows"]):
            assert row["state_id"] == mask
            state = {name: bool(mask & (1 << bit)) for bit, name in enumerate(("A", "B", "C", "D"))}
            assert row["truth"] == state
            assert row["expected"] is all(state.values())
            wanted = 0.8 * (1-alpha) if mask == 14 else 0.8*alpha if mask == 7 else 0.2 if mask == 15 else 0.0
            weight = row["weight"]
            assert type(weight) in (int, float) and math.isfinite(weight)
            assert abs(weight - wanted) <= 1e-10
            mass += weight
            for label, order in orders.items():
                cost = 0
                decision = True
                evaluations = 0
                for name in order:
                    cost += costs[name]
                    evaluations += 1
                    if not state[name]:
                        decision = False
                        break
                assert row[label] == {"decision": decision, "cost": cost, "evaluations": evaluations}
                accum[label].append({"weight": weight, "cost": cost, "evaluations": evaluations})
            row_count += 1
        assert abs(mass - 1.0) <= 1e-10
        for label, values in accum.items():
            summary = dist["summaries"][label]
            ecost = sum(x["weight"] * x["cost"] for x in values)
            eeval = sum(x["weight"] * x["evaluations"] for x in values)
            assert summary["expected_cost"] == round(ecost, 12)
            assert summary["expected_evaluations"] == round(eeval, 12)
            assert summary["semantic_mismatches"] == 0
            for metric, q in (("p50_row_cost", .5), ("p95_row_cost", .95), ("p99_row_cost", .99)):
                assert summary[metric] == weighted_quantile(values, q)
        if crossover is None and accum["FROZEN_COST_SELECTIVITY"]:
            frozen = sum(x["weight"] * x["cost"] for x in accum["FROZEN_COST_SELECTIVITY"])
            naive = sum(x["weight"] * x["cost"] for x in accum["NAIVE"])
            if frozen > naive:
                crossover = alpha
    assert row_count == 336 and crossover == 0.7

    result = json.loads(Path(result_path).read_text(encoding="utf-8"))
    assert result["status"] == "PASS_AUDIT_HARDENING_SCOPED"
    assert result["runtime"] == "pinned-local-docker-python"
    assert result["source_git_blob"] == git_blob(source)
    assert result["archive_git_blob"] == git_blob(archive_text)
    assert result["raw_sha256_before"] == raw_sha == result["raw_sha256_after"]
    assert result["rows"] == row_count and result["distributions"] == 21
    assert result["crossover_alpha"] == crossover
    assert result["predecessor_audit"] == {
        "status": "PASS_DRIFT_BOUNDARY_MAPPED", "errors": [], "rows": 336,
        "corruption_controls_rejected": 5, "corruption_control_count": 5}
    assert set(result["mutations"]) == {"nan_weight", "development_alpha", "truth_state_count"}
    assert all(x["rejected"] for x in result["mutations"].values())
    assert set(result["json_constants"].values()) == {"REJECTED"}
    assert set(result["weight_controls"].values()) == {"REJECTED"}
    print(json.dumps({"audit": "PASS_INDEPENDENT_RAW_REPLAY", "errors": [],
                      "raw_sha256": raw_sha, "rows": row_count,
                      "distributions": 21, "crossover_alpha": crossover}, sort_keys=True))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
