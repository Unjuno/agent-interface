"""Retain a synthetic A/B/C public owner-receipt adapter contract packet."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
TEST_DIR = REPO / "research/integration/standard_mcp_task_ledger_57_v1"
sys.path.insert(0, str(TEST_DIR))

from comparison_measurement_v1 import validate_matched_block  # noqa: E402
from test_recorded_comparison_adapter_v1 import (  # noqa: E402
    RecordedComparisonAdapterTests,
)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8")


def main() -> None:
    output = HERE / "runs"
    if output.exists() and any(output.iterdir()):
        raise SystemExit(f"refusing to overwrite nonempty evidence directory: {output}")
    output.mkdir(parents=True, exist_ok=True)
    runs = []
    for order, arm in enumerate(("A", "B", "C"), start=1):
        run_root = output / arm
        run = RecordedComparisonAdapterTests.make_run(run_root, arm, order)
        runs.append(run)
        write_json(run_root / "measured_run.json", run)
    summary = validate_matched_block(runs)
    write_json(HERE / "matched_summary.json", summary)

    source_paths = (
        REPO / "research/integration/standard_mcp_task_ledger_57_v1/recorded_comparison_adapter_v1.py",
        REPO / "research/integration/standard_mcp_task_ledger_57_v1/test_recorded_comparison_adapter_v1.py",
        REPO / "research/integration/standard_mcp_task_ledger_57_v1/comparison_measurement_v1.py",
        REPO / "research/integration/standard_mcp_task_ledger_57_v1/effect_attribution_v1.py",
        REPO / "runtime/cli_v1/owned_win32_session.py",
        REPO / "runtime/cli_v1/test_mcp_supervised_win32.py",
    )
    conditions = {
        "schema": "agent-interface/native-owner-receipt-join-conditions-v1",
        "base_commit": "37868105a6f08d42e5d7bffa0589038cf3665a17",
        "experiment": "synthetic contract test of public interface_results owner join",
        "arms": ["A", "B", "C"],
        "arm_design": "matched-schema validation only; arm labels do not encode different systems",
        "input": "deterministic synthetic provider/tool journal and synthetic public owner receipt",
        "provider_calls": 0,
        "gui_or_os_input": 0,
        "docker_or_wslc": 0,
        "effect_clock": "fixture-supplied timestamp; not an independently measured live effect",
        "native_scope": "separate current-main supervised Win32 projection unit test only; fake owner contract",
        "source_sha256": {
            path.relative_to(REPO).as_posix(): digest(path)
            for path in source_paths
        },
    }
    write_json(HERE / "conditions.json", conditions)

    print(json.dumps({
        "status": "PASS_SYNTHETIC_ADAPTER_CONTRACT_ONLY",
        "arms": list(summary["arms"]),
        "matched_summary": "matched_summary.json",
    }, sort_keys=True))


if __name__ == "__main__":
    main()
