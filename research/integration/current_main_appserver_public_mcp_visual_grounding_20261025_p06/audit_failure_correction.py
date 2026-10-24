from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
RUN = ROOT / "run"


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    result = read_json(RUN / "RESULT.json")
    provider = read_json(RUN / "provider-call" / "result.json")
    reports = [read_json(p) for p in (RUN / "server").glob("*/report.json")]
    observed = next(r for r in reports if r.get("status") == "observed")
    correction = read_json(ROOT / "OUTCOME_CORRECTION.json")
    source = observed["source"]
    assert result["classification"] == "FAIL_BEFORE_TRIAL"  # preserve the historical raw label
    assert result["physical_input"] is False
    assert provider["turn_status"] == "completed" and provider["answer_eligible"] is True
    assert provider["raw"]["point"] == correction["model_point"] == [16, 8]
    assert provider["usage"] == correction["provider_usage"]
    assert source["sequence"] == 1
    assert source["pointer_binding"]["process_generation"] == correction["public_observation"]["process_generation"]
    assert "window_generation" not in source["pointer_binding"]
    assert observed["input_dispatched"] is False and observed["task_success"] is None
    assert correction["correct_classification"] == "FAIL_AFTER_PROVIDER_PRE_MINT"
    assert correction["mint_attempted"] is False and correction["retry_performed"] is False
    sums = (RUN / "SHA256SUMS").read_text(encoding="utf-8").splitlines()
    for line in sums:
        digest, relative = line.split("  ", 1)
        path = RUN / relative
        assert hashlib.sha256(path.read_bytes()).hexdigest() == digest, relative
    packet_manifest = read_json(ROOT / "PACKET_SHA256.json")
    for relative, digest in packet_manifest["files"].items():
        assert hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() == digest, relative
    print("PASS: correction matches completed provider receipt, public observation, no-mint/no-input evidence; raw checksums intact")


if __name__ == "__main__":
    main()
