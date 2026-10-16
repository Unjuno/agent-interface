"""Known receipts and malformed controls for manual-field elimination."""
import copy,hashlib,json
from pathlib import Path
from prepare_program import prepare
HERE=Path(__file__).resolve().parent;out=HERE/'results/prepare-program-01';out.mkdir(exist_ok=False);rows=[];sources={}
for cohort,batch_name,command_name in (
    ('receipt-image-self-use-01','read-initial','enter'),
    ('receipt-image-self-use-01','read-modal','confirm'),
    ('prefilled-self-use-01','read-form','submit')):
    root=HERE/'results'/cohort;path=root/f'{batch_name}.json';prior=root/f'{command_name}.json'
    batch=json.loads(path.read_text());expected=json.loads(prior.read_text())
    result=prepare(batch,root,expected['id'],expected['steps'],lease_ms=30000,finish_after=expected.get('finish_after',False))
    assert result['command']==expected
    rows.append(dict(case=cohort+'/'+batch_name,result=result))
    for p in (path,prior):sources[str(p.relative_to(HERE))]=hashlib.sha256(p.read_bytes()).hexdigest()
for case in ('missing_delivery','mismatched_clock','missing_clock','invalid_lease'):
    altered=copy.deepcopy(batch)
    if case=='missing_delivery':altered['records'][-1].pop('delivery_id')
    elif case=='mismatched_clock':altered['records'].append(dict(event='clock',sequence=999,runtime_ns=1))
    elif case=='missing_clock':altered['records'][-1].pop('terminal_ns')
    try:prepare(altered,root,'test',expected['steps'],lease_ms=30001 if case=='invalid_lease' else 30000)
    except ValueError as exc:rows.append(dict(case=case,rejected=str(exc)))
    else:raise AssertionError(case)
for p in (Path(__file__),HERE/'prepare_program.py',HERE/'receipt_image.py'):sources[str(p.relative_to(HERE))]=hashlib.sha256(p.read_bytes()).hexdigest()
(out/'results.json').write_text(json.dumps(rows,indent=2)+'\n');(out/'sources.json').write_text(json.dumps(sources,indent=2)+'\n')
print(json.dumps(dict(exact_prior_commands=3,negative_controls=4)))
