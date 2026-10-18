"""Generate all input and source pins from bytes instead of transcribing digests."""
from __future__ import annotations
import hashlib
import json
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
SOURCE = "research/doom/map01_v39_perkey_bridge_a01/results/construction-a01/candidate-events.jsonl"
INPUT_FILES = ("candidate.py", "audit.py", "run.py", "test_consumer.py",
               "generate_freeze.py", "PLAN.md", "INPUT_EVENTS.jsonl")


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=REPO, check=True, text=True,
                          capture_output=True).stdout.strip()


def main() -> None:
    commit = git("rev-parse", "HEAD")
    source_bytes = subprocess.run(["git", "show", f"{commit}:{SOURCE}"],
                                  cwd=REPO, check=True, capture_output=True).stdout
    input_path = HERE / "INPUT_EVENTS.jsonl"
    input_path.write_bytes(source_bytes)
    source_blob = git("rev-parse", f"{commit}:{SOURCE}")
    if git("hash-object", str(input_path.relative_to(REPO))) != git("hash-object", SOURCE):
        raise RuntimeError("copied input does not match the source Git object")
    sha = lambda b: hashlib.sha256(b).hexdigest()
    source_sha = {name: sha((HERE / name).read_bytes()) for name in INPUT_FILES}
    payload = {
        "schema": "map01_v39_perkey_measurement_consumer_freeze_v3",
        "run_id": "MAP01-V39-PERKEY-MEASUREMENT-CONSUMER-A03-20261005",
        "base_commit": commit,
        "hypothesis": "A generated freeze can bind retained V12 per-key down/up brackets to a fail-closed consumer without hand-transcribed digests or event relabeling.",
        "candidate_argv": ["python3", "run.py"],
        "candidate_invocations_allowed": 1,
        "audit_argv": ["python3", "audit.py"],
        "tests_argv": ["python3", "-B", "-m", "unittest", "-v", "test_consumer.py"],
        "output_path": "research/doom/map01_v39_perkey_measurement_consumer_a03_20261005/results/a03",
        "source_input": {"path": SOURCE, "git_blob": source_blob,
                         "sha256": sha(source_bytes)},
        "predecessor_stops": [
            "research/doom/map01_v39_perkey_measurement_consumer_a01_20261005/results/a01/STOP.json",
            "research/doom/map01_v39_perkey_measurement_consumer_a02_20261005/results/a02/STOP.json"
        ],
        "source_sha256": source_sha,
        "source_bridge_sha256": sha((REPO / "research/doom/map01_v39_perkey_bridge_a01/bridge.py").read_bytes()),
        "source_input_owner_v12_sha256": sha((REPO / "research/doom/map01_attack_onset_phase_allocation_02_v1/dependencies/v12/input_owner_v12.py").read_bytes()),
        "environment": {"python": "3.14.5", "host": "macOS arm64",
                        "container": False, "new_os_input": False,
                        "new_gui_or_game": False, "new_model_call": False},
        "scope": "Offline replay of one retained fake-display event pair; not live physical/game occupancy, application effect, threat response, recovery, or performance."
    }
    (HERE / "FREEZE.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"base_commit": commit, "input_sha256": payload["source_input"]["sha256"],
                      "input_git_blob": source_blob, "source_sha256": source_sha},
                     sort_keys=True))


if __name__ == "__main__":
    main()
