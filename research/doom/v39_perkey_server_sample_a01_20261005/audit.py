from __future__ import annotations
import json
import re
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
freeze = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))

def blob_sha(rel: str) -> str:
    result = subprocess.run(
        ["git", "hash-object", "--path", rel, str(ROOT / rel)],
        cwd=ROOT, check=True, capture_output=True, text=True,
    )
    return result.stdout.strip()

for rel, expected in freeze["candidate_blobs"].items():
    actual = blob_sha(rel)
    if actual != expected:
        raise SystemExit(f"FAIL source blob {rel}: expected {expected}, got {actual}")

v39 = (ROOT / "research/doom/map01_overlap_controller_v39.py").read_text(encoding="utf-8")
v15 = (ROOT / "research/doom/session_map01_v15.py").read_text(encoding="utf-8")
v12 = (ROOT / "research/live_control/input_owner_v12.py").read_text(encoding="utf-8")
v5 = (ROOT / "research/live_control/input_transition_owner_v5.py").read_text(encoding="utf-8")
if "session_map01_v15.py" not in v39 or "measurement_session" not in v39:
    raise SystemExit("FAIL V39 opt-in selector is absent")
if "from doom_owner_thread_release_batch_backend_v2 import Backend as TelemetryBackend" not in v15:
    raise SystemExit("FAIL V15 does not select backend V2")
if "sample_keymap_after_each_explicit_up=False" not in v12:
    raise SystemExit("FAIL V12 default-off sample option missing")
if 'owner_keymap_state_after_release") == "UP"' not in v5:
    raise SystemExit("FAIL V5 does not require sampled UP for ordinary release")

def trace(name):
    return json.loads((HERE / f"{name}.json").read_text(encoding="utf-8"))
base, candidate = trace("BASELINE_TRACE"), trace("CANDIDATE_TRACE")
down, query_error = trace("DOWN_TRACE"), trace("QUERY_FAILURE_TRACE")
def indexes(data, event):
    return [i for i, row in enumerate(data["trace"]) if row[0] == event]
base_releases, base_samples = indexes(base, "KeyRelease"), indexes(base, "query_keymap")
if len(base_releases) != 2 or len(base_samples) != 1 or base_samples[0] <= base_releases[-1]:
    raise SystemExit("FAIL baseline is not post-batch-only")
cand_releases, cand_samples = indexes(candidate, "KeyRelease"), indexes(candidate, "query_keymap")
if len(cand_releases) != 2 or len(cand_samples) < 2:
    raise SystemExit("FAIL candidate trace lacks two edges/samples")
if not (cand_releases[0] < cand_samples[0] < cand_releases[1] < cand_samples[1]):
    raise SystemExit("FAIL candidate per-edge sample order")
if candidate["trace"][cand_samples[0]][1] != [56] or candidate["trace"][cand_samples[1]][1] != []:
    raise SystemExit("FAIL controlled fake server key states")
rows = candidate["release_rows"]
if len(rows) != 2 or [r.get("owner_keymap_state_after_release") for r in rows] != ["UP", "UP"]:
    raise SystemExit("FAIL candidate receipt states")
if not all(r.get("owner_transition_verified") is True and r.get("physical_verification_authoritative") is False for r in rows):
    raise SystemExit("FAIL candidate batch or scope flags")
if any("owner_keymap_sample_available" in r for r in base["release_rows"]):
    raise SystemExit("FAIL baseline unexpectedly contains per-edge samples")
if down["release_rows"][0].get("owner_keymap_state_after_release") != "DOWN":
    raise SystemExit("FAIL down negative control")
if any(r.get("owner_transition_verified") is True for r in down["release_rows"]):
    raise SystemExit("FAIL DOWN passed owner transition gate")
if down.get("cleanup_error") != "RuntimeError":
    raise SystemExit("FAIL stuck key was not retained through cleanup")
failed = query_error["release_rows"][0]
if failed.get("owner_keymap_state_after_release") != "UNAVAILABLE" or failed.get("owner_keymap_sample_error_type") != "OSError" or any(r.get("owner_transition_verified") is True for r in query_error["release_rows"]):
    raise SystemExit("FAIL query-error negative control")

counts = []
for mode in ("normal", "optimized"):
    for suite, expected_count in (("v5_integration",4),("v15_selection",8),("owner_v12_cancel",1),("owner_v4_join",1),("batch_actual",12),("batch_construction",2)):
        output = (HERE / f"{mode}_{suite}.stdout.txt").read_text(encoding="utf-8")
        found = re.search(r"Ran (\d+) tests?", output)
        if not found or int(found.group(1)) != expected_count or "OK" not in output:
            raise SystemExit(f"FAIL test receipt for {mode}_{suite}")
        counts.append(expected_count)
if sum(counts[:6]) != 28 or sum(counts[6:]) != 28:
    raise SystemExit("FAIL aggregate test counts")
print("PASS: candidate blobs, V39/V15 selection, baseline/candidate/fault traces, and 28+28 test receipts")
