import hashlib
import json
from pathlib import Path
import sys

root = Path(__file__).resolve().parents[4]
c01 = root / "research/doom/results/map01-v39-cancel-release-cause-c01-20261004"
c02 = Path(__file__).resolve().parent
freeze = json.loads((c02 / "FREEZE.json").read_text(encoding="utf-8"))
raw = (c02 / "CANDIDATE-01.stdout.txt").read_text(encoding="utf-8")
exit_code = int((c02 / "CANDIDATE-01.exit.txt").read_text(encoding="utf-8"))
v10 = (root / "research/live_control/input_owner_v10.py").read_bytes()
v12 = (root / "research/live_control/input_owner_v12.py").read_bytes()
old = b"                        result = release(op)"
new = (b"                        reason = ('cancelled' if op == 'release' and active is lease and lease is not None and lease.cancel.is_set() else op)\r\n"
       b"                        result = release(reason)")
transition3 = (root / "research/live_control/input_transition_owner_v3.py").read_bytes()
transition4 = (root / "research/live_control/input_transition_owner_v4.py").read_bytes()
backend4 = (root / "research/doom/doom_retained_input_backend_v4.py").read_bytes()
backend5 = (root / "research/doom/doom_retained_input_backend_v5.py").read_bytes()
session13 = (root / "research/doom/session_map01_v13.py").read_bytes()
session14 = (root / "research/doom/session_map01_v14.py").read_bytes()
normalize_transition = (transition4.replace(b"over InputOwner v12.", b"over InputOwner v10.")
                        .replace(b"unchanged v12", b"unchanged v10")
                        .replace(b"from input_owner_v12 import InputOwner as Previous",
                                 b"from input_owner_v10 import InputOwner as Previous"))
normalize_backend = (backend5.replace(b"telemetry v5", b"telemetry v4")
                     .replace(b"from input_transition_owner_v4 import InputOwner",
                              b"from input_transition_owner_v3 import InputOwner"))
normalize_session = (session14.replace(b"MAP01 v14: cancellation-aware release cause on the v13 measurement path.",
                                       b"MAP01 v13: measurement-only composition around unchanged session v12.")
                     .replace(b"Selects retained release telemetry v5", b"Selects retained release telemetry v3")
                     .replace(b"session_map01_v14.py", b"session_map01_v13.py")
                     .replace(b"doom_retained_input_backend_v5.py", b"doom_retained_input_backend_v3.py")
                     .replace(b"from doom_retained_input_backend_v5 import Backend as TelemetryBackend",
                              b"from doom_retained_input_backend_v3 import Backend as TelemetryBackend")
                     .replace(b"input_transition_owner_v4.py',RESEARCH/'live_control/input_owner_v12.py'",
                              b"input_transition_owner_v3.py'"))
checks = {
    "c01_independent_audit_pass": json.loads((c01 / "AUDIT-01.json").read_text(encoding="utf-8"))["pass"] is True,
    "frozen_candidate_source_hash_matches": hashlib.sha256(v12).hexdigest() == freeze["source_sha256"],
    "frozen_test_hash_matches": hashlib.sha256((root / freeze["test"]).read_bytes()).hexdigest() == freeze["test_sha256"],
    "v10_parent_hash_matches_c01_freeze": hashlib.sha256(v10).hexdigest() == json.loads((c01 / "FREEZE.json").read_text(encoding="utf-8"))["source_sha256"],
    "candidate_delta_is_only_cause_selection": v12.count(new) == 1 and v12.replace(new, old, 1) == v10,
    "cancel_case_passes": "test_cancel_arriving_after_dequeue_is_preserved_as_release_cause (__main__.CancellationReleaseCauseTests.test_cancel_arriving_after_dequeue_is_preserved_as_release_cause) ... ok" in raw,
    "ordinary_control_passes": "test_ordinary_release_remains_ordinary (__main__.CancellationReleaseCauseTests.test_ordinary_release_remains_ordinary) ... ok" in raw,
    "candidate_exit_zero": exit_code == 0 and "Ran 2 tests" in raw and raw.rstrip().endswith("OK"),
    "transition_v4_differs_only_by_v12_base": normalize_transition == transition3,
    "backend_v5_preserves_v4_except_owner_base": normalize_backend == backend4,
    "session_v14_differs_only_by_versioned_owner_chain": normalize_session == session13,
    "session_manifest_hashes_all_new_sources": all(item in session14.decode("utf-8") for item in ("session_map01_v14.py", "doom_retained_input_backend_v5.py", "input_transition_owner_v4.py", "input_owner_v12.py")),
}
result = {"schema": "map01-v39-cancel-release-cause-c02-audit-v2", "checks": checks,
          "pass": all(checks.values()), "scope": "frozen candidate raw + post-run exact-delta source-chain audit"}
(c02 / "AUDIT-01.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps(result, indent=2, sort_keys=True))
sys.exit(0 if result["pass"] else 1)
