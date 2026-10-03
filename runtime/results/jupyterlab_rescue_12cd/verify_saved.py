"""Original data-only oracle replay; never launch Jupyter or private producers."""
import hashlib
import json
from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parents[3]
PACKET = ROOT / 'research/integration/jupyterlab_endpoint_5442_01a0ff58'

def require(condition, message):
    if not condition:
        raise RuntimeError(message)

def main():
    files = json.loads((PACKET / 'MANIFEST.json').read_bytes())['files']
    for name, pin in files.items():
        target = PACKET / name
        require(target.resolve().is_relative_to(PACKET.resolve()), 'unsafe manifest path')
        data = target.read_bytes()
        require(len(data) == pin['bytes'], 'size: ' + name)
        require(hashlib.sha256(data).hexdigest() == pin['sha256'], 'hash: ' + name)
    audit = runpy.run_path(str(PACKET / 'source/audit_raw.py.txt'), run_name='saved_only')['audit']
    result = audit(PACKET, PACKET / 'primary')
    historical = json.loads((PACKET / 'commands/audit-01/stdout.txt').read_bytes())
    require(result == historical, 'primary saved oracle mismatch')
    controls = json.loads((PACKET / 'independent/RESULT.json').read_bytes())['copied_controls']
    observed = []
    for control in controls:
        try:
            audit(PACKET, PACKET / 'independent' / control['control'])
        except ValueError as error:
            row = {'control': control['control'], 'rejected': True,
                   'error_type': type(error).__name__, 'error': str(error)}
            require(row == control, 'refusal mismatch: ' + control['control'])
            observed.append(row)
        else:
            raise RuntimeError('accepted corruption: ' + control['control'])
    print(json.dumps({'manifest_targets': len(files), 'primary_saved_audit': result,
                      'copied_controls': observed, 'new_app_runs': 0,
                      'scope': 'retained public bytes only; installed assets/private runtime not replayed'},
                     indent=2, sort_keys=True))

if __name__ == '__main__':
    main()
