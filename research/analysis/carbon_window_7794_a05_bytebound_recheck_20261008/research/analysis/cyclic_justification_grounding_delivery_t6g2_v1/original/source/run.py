"""Consume the single fixed corpus once; refuse an existing output directory."""
import hashlib
import json
import os
from pathlib import Path
import sys
import time
sys.path.insert(0, str(Path(__file__).resolve().parent))
from corpus import cases
from grounding import evaluate


def main():
    target = Path(sys.argv[1])
    target.mkdir(parents=True, exist_ok=False)
    started = time.monotonic_ns()
    count = 0
    with (target / 'RAW.jsonl').open('x', encoding='utf-8') as output:
        for case in cases():
            identity = json.dumps(case, sort_keys=True, separators=(',', ':'))
            answer = evaluate(case)
            assert identity == json.dumps(case, sort_keys=True, separators=(',', ':'))
            row = {'case': case, 'answer': answer, 'input_unchanged': True,
                   'input_sha256': hashlib.sha256(identity.encode()).hexdigest()}
            output.write(json.dumps(row, sort_keys=True, separators=(',', ':')) + '\n')
            count += 1
    receipt = {'rows': count, 'pid': os.getpid(), 'started_monotonic_ns': started,
               'ended_monotonic_ns': time.monotonic_ns(), 'invocations': 1,
               'classification': 'LOCAL_PROSPECTIVELY_FROZEN_ANALYTICAL_CHECK',
               'gui_calls': 0, 'model_calls': 0}
    (target / 'RUN.json').write_text(json.dumps(receipt, indent=2, sort_keys=True)+'\n')
    print(json.dumps(receipt, sort_keys=True))

if __name__ == '__main__':
    main()
