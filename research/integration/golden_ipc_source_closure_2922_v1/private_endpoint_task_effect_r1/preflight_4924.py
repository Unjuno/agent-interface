"""Reproducible, construction-only preflight for the frozen #4924 runner."""
import ast
import hashlib
import json
import pathlib
import platform
import shutil
import sys

sys.dont_write_bytecode = True
ROOT = pathlib.Path("/repo")
EXPECTED = {
    "research/live_control/executor_v3.py": "ea3fa8c9751a6a41b4814ad6e0d03bec85166765b0a41d2488a51750d17b3a4a",
    "research/live_control/lease.py": "e71f9850d3999a31fcb86c00f9ef7a8ba19bae8d3a8bdc11bf7bd620817a535f",
    "research/live_control/session_v4.py": "04f06d7b787baa77cae20d0c51b563ccc4985dc19b47308d7c24318c5a9e7fee",
    "research/observation_gating/exact_gate.py": "6780624513a95039657734e76c0420447a3f9ab49f98e1f3137a19a91bc31944",
    "research/observation_gating/gui_suite.py": "953a078a06d55b9278bd7b31e176404912340a4f13407e1db343b7776645e97f",
    "research/observation_tiles/image_artifact.py": "7bf6b71d811aaefa75e87f5d9d20fd9275fc928104e910deaca9e3f00c55363e",
    "research/observation_tiles/tile_transport.py": "f74caf4f2bea59fe3a73b3f04975384d8520bb06c296765566c4dd2542ef12b0",
    "research/real_apps_v1/real_app_suite_v1.py": "22b4cc86af68a0ae866fe24735faaeefa40c0e1722238ab8c04723e1a564db24",
}
RESEARCH = "research/integration/golden_ipc_source_closure_2922_v1/private_endpoint_task_effect_r1/"
EXPECTED_ARTIFACTS = {
    RESEARCH + "session_cli_chromium_task_effect_probe.py": "258ba79c9530187ec3b6eb4bc752b0891d40d7e432bf6eaf84d9a5c41a89e3cd",
    RESEARCH + "audit_task_effect.py": "9704ea7fad000eb1d7212f4f0eef6c2d2a2583ceba31564af5425c371fd914f3",
    RESEARCH + "test_audit_task_effect.py": "ccd90a881e91bc5bdec0e905462a177a5cbfc4791fc11ad90a8bd1c6ba6cee2b",
}

def main():
    expected = EXPECTED | EXPECTED_ARTIFACTS
    actual = {path: hashlib.sha256((ROOT / path).read_bytes()).hexdigest() for path in expected}
    assert actual == expected, {"expected": expected, "actual": actual}
    for path in expected:
        ast.parse((ROOT / path).read_text())
    sys.path[:0] = [
        str(ROOT / "research/live_control"),
        str(ROOT / "research/observation_tiles"),
        str(ROOT / "research/observation_gating"),
        str(ROOT / RESEARCH),
    ]
    import session_v4, executor_v3, lease, tile_transport, image_artifact, gui_suite, audit_task_effect
    binaries = {name: shutil.which(name) for name in ("Xvfb", "openbox", "wmctrl")}
    assert all(binaries.values()), binaries
    chromium = pathlib.Path("/home/taka/.cache/ms-playwright/chromium-1208/chrome-linux64/chrome")
    assert chromium.is_file(), str(chromium)
    print(json.dumps({
        "verdict": "PASS_FROZEN_PREFORMAL_PREFLIGHT",
        "source_and_harness_hashes": actual,
        "ast_parse_files": len(expected),
        "imports": "PASS",
        "binaries": binaries,
        "chromium": str(chromium),
        "python": sys.version.split()[0],
        "platform": platform.machine(),
        "formal_sessions": 0,
        "formal_seed_used": False,
    }, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
