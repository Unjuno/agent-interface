"""Download and hash-check the immutable predecessor candidate and raw inputs."""
import hashlib
import json
from pathlib import Path
from urllib.request import urlopen

HERE = Path(__file__).resolve().parent
FREEZE = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))
RAW_PATHS = {
    "doom-v38-events.jsonl": "research/doom/results/map01-v38-integrated-threat-live-01/runtime/events.jsonl",
    "doom-v39-events.jsonl": "research/doom/results/map01-v39-coast-liveness-live-01/runtime/events.jsonl",
    "doom-analysis.json": "research/doom/results/map01-v38-v39-control-tempo-posthoc-v1/analysis.json",
    "openttd-events.jsonl": "research/live_control/results/timing-envelope-openttd-l-06/fixed-astra/runtime/events.jsonl",
    "openttd-observer.txt": "research/live_control/results/timing-envelope-openttd-l-06/fixed-astra/runtime/game-stderr.txt",
    "openttd-audit.json": "research/live_control/results/timing-envelope-openttd-l-06/posthoc-audit.json",
}
PREDECESSOR = (
    "https://raw.githubusercontent.com/Unjuno/agent-interface/"
    + FREEZE["predecessor"]["branch_head"] + "/"
    "research/analysis/map01_crossdomain_time_coverage_59_t0_20261002_01/"
)


def fetch(url, expected, destination):
    with urlopen(url, timeout=30) as response:
        data = response.read()
    observed = hashlib.sha256(data).hexdigest()
    if observed != expected:
        raise SystemExit(f"STOP_INPUT_HASH_MISMATCH:{destination.name}:{observed}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(data)
    print(f"PASS_INPUT:{destination.name}:{observed}")


def main():
    inputs = HERE / "_run" / "inputs"
    base = "https://raw.githubusercontent.com/Unjuno/agent-interface/"
    commit = FREEZE["input_source_commit"]
    for name, path in RAW_PATHS.items():
        fetch(base + commit + "/" + path, FREEZE["inputs"][name], inputs / name)
    fetch(PREDECESSOR + "candidate_result.json",
          FREEZE["candidate_result_sha256"], inputs / "candidate_result.json")
    fetch(PREDECESSOR + "FREEZE.json", FREEZE["predecessor"]["freeze_sha256"],
          inputs / "predecessor-FREEZE.json")


if __name__ == "__main__":
    main()
