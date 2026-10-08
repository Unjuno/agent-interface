"""Opt-in V15 session with acknowledged, GameState-backed scorer samples."""
import hashlib
import json
from pathlib import Path
import uuid

from acknowledged_scorer_v1 import AcknowledgedSampler
from state_snapshot_sampler import coherent_snapshot_sample
import session_map01_v15 as previous


def main():
    out = Path(previous._option("--out"))
    run_id = str(uuid.uuid4())
    original = previous._coherent_progress_sample

    def emit(row):
        out.mkdir(parents=True, exist_ok=True)
        with (out / "scorer-client-updates.jsonl").open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(row, sort_keys=True) + "\n")

    sampler = AcknowledgedSampler(coherent_snapshot_sample, run_id, emit)
    previous._coherent_progress_sample = sampler
    try:
        return previous.main()
    finally:
        previous._coherent_progress_sample = original
        sources = out / "sources.json"
        if sources.exists():
            data = json.loads(sources.read_text(encoding="utf-8"))
            source_paths = {
                "session_map01_v17.py": Path(__file__),
                "state_snapshot_sampler.py": Path(__file__).parent / "state_snapshot_sampler.py",
                "acknowledged_scorer_v1.py": Path(previous.__file__).parent / "acknowledged_scorer_v1.py",
            }
            for name, path in source_paths.items():
                data["doom/" + name] = hashlib.sha256(path.read_bytes()).hexdigest()
            sources.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n",
                               encoding="utf-8")


if __name__ == "__main__":
    main()
