"""One deterministic implementation-verification invocation, not a GUI trial."""
import hashlib
import json
import os
from pathlib import Path
import sys
from corpus import cases, encoded
from maxima import evaluate

ROOT = Path(__file__).resolve().parent
freeze = json.loads((ROOT/'FREEZE.json').read_text())
for path, digest in freeze['files'].items():
    if hashlib.sha256((ROOT/path).read_bytes()).hexdigest() != digest:
        raise RuntimeError('source changed: ' + path)
if hashlib.sha256(encoded()).hexdigest() != freeze['corpus_sha256']:
    raise RuntimeError('corpus changed')
result = {'allocation': 'shared-score-q2v9-01', 'pid': os.getpid(),
          'python': sys.version, 'freeze_sha256': hashlib.sha256((ROOT/'FREEZE.json').read_bytes()).hexdigest(),
          'rows': [{'input': c, 'output': evaluate(c)} for c in cases()]}
sys.stdout.write(json.dumps(result, sort_keys=True, separators=(',', ':')) + '\n')
