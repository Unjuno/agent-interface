"""Opt-in V15 composition with explicit scorer client updates.

Updates change execution timing. This version is unqualified for live efficacy,
controller neutrality and physical-release/recovery claims.
"""
import hashlib
import json
from pathlib import Path
import uuid

from acknowledged_scorer_v1 import AcknowledgedSampler
import session_map01_v15 as previous


def main():
    out = Path(previous._option('--out'))
    run_id = str(uuid.uuid4())
    original = previous._coherent_progress_sample

    def emit(row):
        out.mkdir(parents=True, exist_ok=True)
        with (out / 'scorer-client-updates.jsonl').open('a', encoding='utf-8') as stream:
            stream.write(json.dumps(row, sort_keys=True) + '\n')

    sampler = AcknowledgedSampler(original, run_id, emit)
    previous._coherent_progress_sample = sampler
    try:
        return previous.main()
    finally:
        previous._coherent_progress_sample = original
        sources = out / 'sources.json'
        if sources.exists():
            data = json.loads(sources.read_text(encoding='utf-8'))
            for name in ('session_map01_v16.py', 'acknowledged_scorer_v1.py'):
                path = Path(__file__).parent / name
                data['doom/' + name] = hashlib.sha256(path.read_bytes()).hexdigest()
            sources.write_text(json.dumps(data, indent=2, sort_keys=True) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
