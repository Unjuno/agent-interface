"""Copied-data negative controls. Update duplicated receipt joins to target meaning."""
from pathlib import Path
import copy, json, shutil, tempfile
from audit import audit, Rejected

ROOT = Path(__file__).resolve().parent
CONTROLS = [
    ('parent_bool', 'green', 'ready_input', 'actual numeric parent exit'),
    ('fixture_bool', 'green', 'normal_eof', 'actual fixture exit'),
    ('fault_identity', 'green', 'ready_output', 'original error preservation'),
    ('pending_settled', 'pending-green', 'pending_success', 'same pending promise and original error'),
    ('request_duplicate', 'pending-green', 'pending_success', 'single accepted request'),
    ('replay_true', 'pending-green', 'pending_persistence_failure', 'consumed uncertainty no replay'),
    ('consumed_id_float', 'pending-green', 'pending_persistence_failure', 'consumed uncertainty no replay'),
    ('fixture_absent_false', 'green', 'terminal_output', 'actual fixture exit'),
]

def dump(path, data): path.write_text(json.dumps(data, indent=2)+'\n')
results=[]
for name, label, scenario, target in CONTROLS:
    with tempfile.TemporaryDirectory(prefix='primary-owner-audit-') as temporary:
        root=Path(temporary)/'copy'; root.mkdir()
        for entry in ROOT.iterdir():
            if entry.name in ['red','green','pending-green','baseline','candidate','PROJECTIONS.json'] or entry.name in ['relay_fixture.mjs','lifecycle_probe.mjs','collect.py','pending_fixture.mjs','pending_probe.mjs','collect_pending.py']:
                if entry.is_dir(): shutil.copytree(entry,root/entry.name)
                else: shutil.copyfile(entry,root/entry.name)
        raw=json.loads((root/label/'RAW.json').read_bytes())
        row=next(r for r in raw['rows'] if r['scenario']==scenario); d=root/label/scenario
        if name=='parent_bool': row['exit_code']=False
        elif name=='fixture_bool': row['fixture.exit.json']['code']=False; dump(d/'fixture.exit.json',row['fixture.exit.json'])
        elif name=='fault_identity': row['owner.summary.json']['outcome']['original_identity']=False
        elif name=='pending_settled': row['owner.summary.json']['events'][3]['settled']=True
        elif name=='request_duplicate': row['fixture.exit.json']['requests']=2; dump(d/'fixture.exit.json',row['fixture.exit.json'])
        elif name=='replay_true': row['owner.summary.json']['rows'][1]['replay_allowed']=True
        elif name=='consumed_id_float': row['owner.summary.json']['rows'][1]['command_id']=1.0
        elif name=='fixture_absent_false': row['fixture_pid_absent']=False
        if 'owner.summary.json' in row: dump(d/'owner.summary.json',row['owner.summary.json'])
        dump(d/'receipt.json',row); dump(root/label/'RAW.json',raw)
        # These copies are intentionally modified; remove projection entries for
        # semantic records but keep mappings for hashed original channels/helpers.
        if (root/'PROJECTIONS.json').exists():
            projection=json.loads((root/'PROJECTIONS.json').read_bytes())
            projection['files']=[e for e in projection['files'] if e['path'] not in [f'{label}/RAW.json',f'{label}/{scenario}/receipt.json',f'{label}/{scenario}/owner.summary.json']]
            dump(root/'PROJECTIONS.json',projection)
        try: audit(root)
        except Rejected as error:
            assert str(error)==target,(name,str(error),target)
            results.append({'control':name,'status':'REJECTED_EXPECTED','reason':str(error)})
        else: raise AssertionError(f'{name} falsely accepted')
print(json.dumps({'status':'PASS_8_EFFECTIVE_SAVED_DATA_CONTROLS','controls':results},indent=2))
