"""Read-only saved construction checks; no child/game/model replay."""
from pathlib import Path
import hashlib,json
root=Path(__file__).resolve().parent
manifest=json.loads((root/'FILES.sha256.json').read_bytes())
assert set(manifest)=={p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file() and p.name!='FILES.sha256.json'}
for name,receipt in manifest.items():
    raw=(root/name).read_bytes()
    assert len(raw)==receipt['bytes'] and hashlib.sha256(raw).hexdigest()==receipt['sha256'],name
freeze=json.loads((root/'FREEZE.json').read_bytes())
for name,expected in freeze['files'].items():
    path=root/name if (root/name).exists() else root/'source/research/doom'/name
    assert hashlib.sha256(path.read_bytes()).hexdigest()==expected,name
before=json.loads((root/'BEFORE_EXTERNAL_CLEANUP.json').read_bytes())
assert before['controller_error_type']=='RuntimeError'
assert before['controller_error']=='v28 requires a loaded fixture receipt'
assert before['child_poll'] is None and before['child_commands_present'] is False
assert before['fake_planner_close_present'] is False
commands=[json.loads(x) for x in (root/'child-commands.jsonl').read_bytes().splitlines()]
assert commands==[{'op':'finish'}]
cleanup=json.loads((root/'EXTERNAL_CLEANUP.json').read_bytes())
assert cleanup['actor']=='probe external cleanup, not controller' and cleanup['child_exit']==0
assert json.loads((root/'RESULT.json').read_bytes())['container_exit']==0
print(json.dumps({'members':len(manifest),'scope':'saved construction integrity, not game/input lifecycle'}))
