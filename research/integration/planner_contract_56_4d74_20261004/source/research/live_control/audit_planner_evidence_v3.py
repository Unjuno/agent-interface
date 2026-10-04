"""Recompute the archived v3 binding controls from pinned inputs."""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

H = Path(__file__).resolve().parent
R = H / 'results/planner-evidence-controls-03'
recorded = json.loads((R / 'result.json').read_text(encoding='utf-8'))
for name, digest in recorded['sources'].items():
    import hashlib
    assert hashlib.sha256((H / name.replace('\\', '/')).read_bytes()).hexdigest() == digest, name
with tempfile.TemporaryDirectory(prefix='planner-evidence-v3-audit-') as directory:
    environment = os.environ.copy()
    environment['PLANNER_EVIDENCE_V3_OUT'] = str(Path(directory) / 'result')
    process = subprocess.run([sys.executable, str(H / 'probe_planner_evidence_v3.py')],
                             cwd=H, env=environment, capture_output=True,
                             text=True, timeout=30)
    assert process.returncode == 0, process.stderr
    replayed = json.loads((Path(directory) / 'result/result.json').read_text(encoding='utf-8'))
    def normalized(value):
        value = dict(value)
        value['sources'] = {name.replace('\\', '/'): digest
                            for name, digest in value['sources'].items()}
        return value
    assert normalized(replayed) == normalized(recorded)
print(json.dumps({'audit': 'passed', 'controls': len(recorded['adversarial_refusals']),
                  'valid_cases': len(recorded['valid_prior_views_preserved_except_explicit_binding']),
                  'model_calls': 0, 'actions_executed': 0}, indent=2))
