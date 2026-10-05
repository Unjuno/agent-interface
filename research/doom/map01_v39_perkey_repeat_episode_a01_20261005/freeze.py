"""Freeze source/input identities for construction A01."""
import hashlib
import json
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BASELINE = HERE.parent / "map01_v39_perkey_measurement_consumer_a03_20261005" / "candidate.py"
FILES = ["BASE_PAIR.jsonl", "INPUT_EVENTS.jsonl", "PREREGISTRATION.md", "README.md",
         "candidate.py", "audit.py", "prepare_fixture.py", "run_baseline.py", "test_repeat.py"]
sources = {name: hashlib.sha256((HERE / name).read_bytes()).hexdigest() for name in FILES}
sources["baseline_A03_candidate.py"] = hashlib.sha256(BASELINE.read_bytes()).hexdigest()
freeze = {
    "schema": "map01-v39-perkey-repeat-episode-freeze-a01",
    "main_sha": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
    "source_sha256": sources,
    "source_input_sha256": hashlib.sha256((HERE / "INPUT_EVENTS.jsonl").read_bytes()).hexdigest(),
    "baseline": "research/doom/map01_v39_perkey_measurement_consumer_a03_20261005/candidate.py",
    "fixture_method": "retained A03 fake-display pair, cloned once with deterministic +1000000 ns timestamps and g2/r3/r4 identities",
    "execution_policy": {"baseline_invocations": 1, "candidate_invocations": 1, "audit_invocations": 1, "retries": 0},
}
(HERE / "FREEZE.json").write_text(json.dumps(freeze, sort_keys=True, indent=2) + "\n")
print(json.dumps(freeze, sort_keys=True))
