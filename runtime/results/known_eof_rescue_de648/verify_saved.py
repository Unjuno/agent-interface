"""Decode public data in memory and call only the original pure check function."""
import ast
import gzip
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PACKET = ROOT / 'research/live_control/appserver_known_eof_admission_59_20261003_93c2_A01'

def require(ok, reason):
    if not ok:
        raise ValueError(reason)

def main():
    manifest = json.loads((PACKET / 'MANIFEST.json').read_bytes())
    for name, pin in manifest.items():
        data = (PACKET / name).read_bytes()
        require(len(data) == pin['bytes'] and hashlib.sha256(data).hexdigest() == pin['sha256'], name)
    capsule = json.loads(gzip.decompress((PACKET / 'proof.json.gz').read_bytes()))
    files = {}
    for row in capsule['files']:
        name = row['path']
        require(name not in files and not Path(name).is_absolute() and '..' not in Path(name).parts, 'member path')
        data = row['data_utf8'].encode('utf-8')
        require(len(data) == row['bytes'] and hashlib.sha256(data).hexdigest() == row['sha256'], name)
        files[name] = data
    tree = ast.parse(files['audit.py'])
    kept = []
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name in ('require', 'exact', 'check'):
            kept.append(node)
    require([n.name for n in kept] == ['require', 'exact', 'check'], 'original pure checker shape')
    env = {'digest': lambda data: hashlib.sha256(data).hexdigest(), 'json': json}
    exec(compile(ast.Module(body=kept, type_ignores=[]), 'retained-audit-pure-check', 'exec'), env)
    plan = json.loads(files['PLAN.json'])
    original = json.loads(files['AUDIT.json'])
    result = env['check'](json.loads(files['RAW.json']), files, plan)
    require(all(original[key] == value for key, value in result.items()), 'original positive report')
    refusals = []
    for control in original['copied_controls']:
        prefix = 'copied-controls/' + control['name'] + '/'
        copied = dict(files)
        for name, data in files.items():
            if name.startswith(prefix):
                copied[name[len(prefix):]] = data
        try:
            env['check'](json.loads(copied['RAW.json']), copied, plan)
        except ValueError as error:
            require(str(error) == control['reason'], 'refusal reason: ' + control['name'])
            refusals.append({'name': control['name'], 'reason': str(error)})
        else:
            raise ValueError('accepted corruption: ' + control['name'])
    print(json.dumps({'manifest_entries': len(manifest), 'capsule_members': len(files),
                      'saved_result': result, 'refusals': refusals,
                      'scope': 'saved consistency only; no producer/live PID probe or current product certification'},
                     indent=2, sort_keys=True))

if __name__ == '__main__':
    main()
