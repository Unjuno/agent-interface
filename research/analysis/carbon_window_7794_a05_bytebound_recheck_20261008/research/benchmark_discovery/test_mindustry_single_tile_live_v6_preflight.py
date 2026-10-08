"""Prove the v6 continuation cannot run after a cached schema refusal."""
import json
from pathlib import Path
import shutil
import tempfile

from run_mindustry_single_tile_live_v6 import CACHE, authorize_then_continue
from schema_preflight_gate_v1 import SchemaPreflightRefused


def main():
    negative = [{"name": "world-oneof",
        "schema": "benchmark_discovery/mindustry_world_target_contract_schema_v1.json"}]
    positive = [
        {"name": "candidate", "schema": "live_control/bounded_visual_target_contract_schema_v3.json"},
        {"name": "anchor", "schema": "live_control/anchor_evidence_contract_schema_v1.json"},
        {"name": "world", "schema": "benchmark_discovery/mindustry_world_target_contract_schema_v3.json"},
    ]
    calls = []
    with tempfile.TemporaryDirectory(prefix="schema-authority-") as temporary:
        root = Path(temporary)
        cache = root / "cache"
        shutil.copytree(CACHE, cache)
        try:
            authorize_then_continue(negative, cache, root / "negative", root / "workspace",
                                    lambda: calls.append("negative"))
            raise AssertionError("negative schema unexpectedly authorized continuation")
        except SchemaPreflightRefused as error:
            assert error.report["accepted"] is False
            assert calls == []
        report, returned = authorize_then_continue(positive, cache, root / "positive",
            root / "workspace", lambda: calls.append("positive") or "continued")
        assert report["accepted"] is True and report["model_calls"] == 0
        assert returned == "continued" and calls == ["positive"]
        summary = {
            "passed": True,
            "negative_continuation_calls": 0,
            "positive_continuation_calls": 1,
            "positive_endpoint_calls": report["model_calls"],
            "authority": "GUI continuation is downstream of accepted schema gate",
        }
        print(json.dumps(summary, indent=2))


if __name__ == "__main__": main()
