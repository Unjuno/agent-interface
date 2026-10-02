"""Verify successor source/dependency identities only; does not run an experiment."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CAPSULE_SHA256 = "317068daacc2abafacc44b85e18c0b1ad468fa8eb185361fd9cdf3b247475e9e"
EXPERIMENT_SOURCE_SHA256 = {
    "audit.py": "d462b4cea332ed1e7dc658857de2ff6978f501f2445b142d9f525dc63d18242a",
    "construction.py": "1640b52852de5cf5764980234336693aad6c861c9f582268c8921f165b9b9a8e",
    "formal_runner.py": "86e92050d2e52bfaffd255e56f02e85366069004a4a7c0f728598a3e88fcfb11",
    "map01_v12_transition_owner.py": "3626281eb6066fa71e500160c671a3946c11fd7abb3a624d4f05d5cbed2f0db1",
    "run_case.py": "38bcced828837651732e126f8035f7685aaee380fd4f6b067e28be830974340a",
    "session_entry.py": "4489f83991311e17d9c6859f7d03f09943bc054854f90d92e72b24a880e155f9",
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit() -> dict:
    freeze = json.loads((ROOT / "FREEZE.json").read_text())
    preflight = json.loads((ROOT / "PREFLIGHT_RESULT.json").read_text())
    unit_tests = json.loads((ROOT / "UNIT_TEST_RESULT.json").read_text())
    v12_root = ROOT / "dependencies/v12"
    v12_manifest = json.loads((v12_root / "SOURCE_MANIFEST.json").read_text())
    checks = {
        "capsule_b64_hash_matches_freeze": sha(ROOT / "SOURCE.tar.xz.b64")
        == "23f0c36a1df8b5f882a53019920a2fd23015145207b9f74e12c377e3d473b0d1",
        "capsule_archive_hash_matches_freeze": sha(ROOT / "SOURCE.tar.xz") == CAPSULE_SHA256
        == freeze.get("source_capsule_sha256"),
        "experiment_source_hashes_match": all(
            (ROOT / "source" / name).is_file() and sha(ROOT / "source" / name) == digest
            for name, digest in EXPERIMENT_SOURCE_SHA256.items()
        ),
        "v12_source_manifest_matches": all(
            (v12_root / name).is_file() and sha(v12_root / name) == digest
            for name, digest in v12_manifest.get("files", {}).items()
        ),
        "v12_owner_adapter_match_issue_freeze": (
            sha(v12_root / "input_owner_v12.py") == freeze.get("v12_input_owner_sha256")
            and sha(v12_root / "adapter_contract.py") == freeze.get("v12_adapter_contract_sha256")
        ),
        "recipe_includes_exact_missing_wheel": (
            "python-xlib==0.33" in (ROOT / "Dockerfile.formal").read_text()
            and "six==1.17.0" in (ROOT / "Dockerfile.formal").read_text()
            and "PIP_NO_INDEX=1" in (ROOT / "Dockerfile.formal").read_text()
        ),
        "dockerfile_hash_matches_freeze": sha(ROOT / "Dockerfile.formal")
        == freeze.get("dockerfile_sha256"),
        "preflight_source_hash_matches_freeze": sha(ROOT / "import_preflight.py")
        == freeze.get("import_preflight_sha256"),
        "preflight_result_binds_frozen_image": (
            preflight.get("decision") == "IMPORT_ONLY_READY"
            and preflight.get("image_id") == freeze.get("runtime_image_id")
            and preflight.get("science_sessions") == 0
            and preflight.get("physical_inputs") == 0
        ),
        "local_unit_tests_passed_on_frozen_image": (
            unit_tests.get("decision") == "PASS"
            and unit_tests.get("image_id") == freeze.get("runtime_image_id")
            and unit_tests.get("tests_run") == 10
            and unit_tests.get("tests_passed") == 10
            and unit_tests.get("tests_failed") == 0
            and unit_tests.get("tests_errored") == 0
            and unit_tests.get("formal_invocations") == 0
        ),
        "formal_budget_still_unused": freeze.get("formal_invocations") == 0
        and freeze.get("reruns") == 0
        and freeze.get("replacements") == 0
        and freeze.get("tuning_after_freeze") == 0
        and not any((ROOT / "formal").iterdir()),
        "formal_budget_unused_and_not_authorized": freeze.get("formal_authorized") is False
        and freeze.get("container_preflight") == "IMPORT_ONLY_READY"
        and freeze.get("formal_invocations") == 0
        and preflight.get("formal_or_scientific_claim") is False,
    }
    return {
        "schema": "map01-attack-onset-allocation-02-input-audit-v1",
        "decision": "PASS_PREREGISTERED_INPUTS_ONLY" if all(checks.values()) else "FAIL_INPUT_IDENTITY",
        "checks": checks,
        "formal_or_scientific_claim": False,
        "formal_invocations": 0,
    }


if __name__ == "__main__":
    result = audit()
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["decision"] == "PASS_PREREGISTERED_INPUTS_ONLY" else 1)
