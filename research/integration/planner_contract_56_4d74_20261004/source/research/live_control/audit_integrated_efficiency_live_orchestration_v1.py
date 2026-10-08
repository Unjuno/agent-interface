"""Audit the retained composed-runner failure and corrected zero-model probe."""

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results"


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def main():
    failed = read(RESULTS / "integrated-efficiency-live-orchestration-probe-01/report.json")
    passed = read(RESULTS / "integrated-efficiency-live-orchestration-probe-02/report.json")
    assert failed["passed"] is False and failed["model_calls"] == 0
    assert failed["classification"] == "benchmark_setup_accounting_defect"
    assert passed["passed"] is True and passed["model_calls"] == 0
    assert passed["synthetic_grounding_invocations"] == 14
    assert passed["protocol_disposition_with_synthetic_usage"] == "RETAIN"
    assert all(passed["independent_success"].values())
    for arm in ("plain", "ephemeral", "persistent"):
        details = read(RESULTS / "integrated-efficiency-live-orchestration-probe-02" /
                       "arms" / arm / "task-details.json")
        assert len(details) == 6
        assert all(row["trace"]["submission_count"] == 1
                   and row["trace"]["exact_submission"] is True for row in details)
        assert all(len(row["trace"]["input_feedback_ns"]) == 2 for row in details)
    print(json.dumps({"passed": True, "retained_failure": True,
                      "corrected_three_arm_sequences": 3,
                      "formal_model_calls": 0}, indent=2))


if __name__ == "__main__":
    main()
