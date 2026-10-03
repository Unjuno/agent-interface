"""Single prospective matrix invocation, refuses an occupied output."""
import argparse
import hashlib
import json
from pathlib import Path
from assay import HERE, SCENARIOS, run_case

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    freeze = json.loads((HERE / 'FREEZE.json').read_text())
    for path, digest in freeze['source_sha256'].items():
        if hashlib.sha256((HERE / path).read_bytes()).hexdigest() != digest:
            raise ValueError('frozen input changed: ' + path)
    args.out.mkdir(parents=True, exist_ok=False)
    rows = [run_case(v, c, s) for v in ('retained', 'fair')
            for c in ('loop', 'stdin') for s in SCENARIOS]
    data = ''.join(json.dumps(row, sort_keys=True) + '\n' for row in rows).encode()
    (args.out / 'raw.jsonl').write_bytes(data)
    counts = {}
    for row in rows:
        key = row['variant'] + ':' + row['outcome']
        counts[key] = counts.get(key, 0) + 1
    summary = {'allocation': freeze['allocation'], 'rows': len(rows),
               'counts': counts, 'raw_sha256': hashlib.sha256(data).hexdigest(),
               'freeze_sha256': hashlib.sha256((HERE / 'FREEZE.json').read_bytes()).hexdigest()}
    (args.out / 'candidate.json').write_text(json.dumps(summary, indent=2, sort_keys=True) + '\n')
    print(json.dumps(summary, sort_keys=True))

if __name__ == '__main__':
    main()
