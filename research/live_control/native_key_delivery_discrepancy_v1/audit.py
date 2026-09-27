"""Compare retained operation emission and application effect; no live input."""
import hashlib,json
from pathlib import Path
import xml.etree.ElementTree as ET
root=Path(__file__).resolve().parents[3]
rows=[]
for name in ('native-target-recovery-01','native-multiapp-integration-01'):
    run=root/'runtime/results'/name/'allocation/run'
    raw=(run/'actions.json').read_bytes();action=json.loads(raw)[0]
    programs=[]
    for path in (run/'bridge').glob('program-*.json'):
        data=path.read_bytes();program=json.loads(data)
        if any(op.get('keys')==['Right'] for op in program['ops']):
            programs.append((path,data,program))
    assert len(programs)==1
    path,data,program=programs[0]
    rect=next(n for n in ET.parse(run/'shape.svg').iter() if n.tag.endswith('}rect'))
    rows.append({'run':name,'actions_sha256':hashlib.sha256(raw).hexdigest(),
        'program_path':str(path.relative_to(root)), 'program_sha256':hashlib.sha256(data).hexdigest(),
        'operations':program['ops'], 'execution':action['result']['execution'],
        'saved_geometry':{k:rect.get(k) for k in ('x','y','width','height','transform')},
        'evaluation':json.loads((run/'evaluation.json').read_bytes())})
assert rows[0]['operations']==rows[1]['operations']
assert sum(op.get('keys')==['Right'] for op in rows[0]['operations'])==6
assert all(r['execution']['emissions']==19 for r in rows)
assert all(r['execution']['completed_ops']==list(range(12)) for r in rows)
assert [r['saved_geometry']['x'] for r in rows]==['60','62']
assert all(r['evaluation']['success'] is True for r in rows)
print(json.dumps({'status':'SAME_OPERATIONS_DIFFERENT_SAVED_EFFECT','root_cause':'unknown',
    'controlled_comparison':False,'rows':rows},indent=2))
