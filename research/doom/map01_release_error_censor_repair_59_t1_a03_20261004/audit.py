from __future__ import annotations

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def main():
    for line in (HERE / "FILES.sha256").read_text(encoding="utf-8").splitlines():
        expected, name = line.split("  ", 1)
        assert hashlib.sha256((HERE / name).read_bytes()).hexdigest() == expected, name
    freeze = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))
    for path, expected in freeze["sources"].items():
        assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == expected, path
    oracle = json.loads((HERE / "ORACLE_TEST.json").read_text(encoding="utf-8"))
    owner = json.loads((HERE / "OWNER_BACKEND_TEST.json").read_text(encoding="utf-8-sig"))
    integration = json.loads((HERE / "INTEGRATION_RESULT.json").read_text(encoding="utf-8"))
    assert oracle["status"] == "PASS" and oracle["tests"] == 15
    assert oracle["failures"] == oracle["errors"] == 0
    assert "test_retry_after_unreceipted_release_error_uses_cleanup_censor" in oracle["output"]
    assert owner["status"] == "PASS" and owner["tests"] == 12
    assert owner["failures"] == owner["errors"] == 0
    assert integration["status"] == "PASS_SCOPED"
    assert integration["state_after_unreceipted_failure"]["fake_server_key_down"] is False
    assert integration["state_after_retry"]["release_requests"] == 2
    assert len(integration["reconciled"]) == 1
    row = integration["reconciled"][0]
    assert row["release_transition_interval_ns"] is None
    assert row["occupancy_lower_ns"] is None and row["censored"] is True
    return {"schema": "map01-release-error-censor-repair-audit-v1",
            "status": "PASS_SCOPED",
            "checks": ["artifact SHA256 inventory", "frozen source hashes",
                       "15 oracle cases including uncertain retry censoring",
                       "12 FakeDisplay owner/backend contracts",
                       "actual V10/V11-to-typed-backend-to-oracle failure/retry composition",
                       "synthetic scope only"]}


if __name__ == "__main__":
    print(json.dumps(main(), indent=2, sort_keys=True))
