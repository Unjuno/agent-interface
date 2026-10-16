"""Replay overwritten/deleted workbook snapshots and reject corrupted archives."""
import hashlib,json,tempfile
from pathlib import Path
from openpyxl import Workbook
from effect_checkpoint import sample
from effect_checkpoint_v2 import archived_sample
HERE=Path(__file__).resolve().parent;out=HERE/'results/checkpoint-archive-01';out.mkdir(exist_ok=False)
contract=dict(kind='saved_cells',expected=dict(A1=612,A2=129))
with tempfile.TemporaryDirectory() as temporary:
    source=Path(temporary)/'book.xlsx';archive=out/'artifacts'
    wb=Workbook();wb.save(source);wb.close()
    before=archived_sample(source,contract,archive);assert before['status']=='UNKNOWN'
    wb=Workbook();wb.active['A1']=612;wb.active['A2']=129;wb.save(source);wb.close()
    after=archived_sample(source,contract,archive);assert after['status']=='VERIFIED'
    again=archived_sample(source,contract,archive);assert again['archive_path']==after['archive_path']
    source.unlink()
    for evidence in (before,after):
        path=Path(evidence['archive_path']);assert hashlib.sha256(path.read_bytes()).hexdigest()==evidence['artifact_sha256']
        replay=sample(path,contract);assert replay['status']==evidence['status'] and replay['actual']==evidence['actual']
    missing=archived_sample(source,contract,archive);assert missing['status']=='UNKNOWN'
    source.write_text('value=right');form=dict(kind='saved_form_value',expected='right')
    good=archived_sample(source,form,out/'corrupt-control');assert good['status']=='VERIFIED'
    Path(good['archive_path']).write_bytes(b'corrupted intentionally')
    corrupt=archived_sample(source,form,out/'corrupt-control');assert corrupt['status']=='UNKNOWN'
    source.write_bytes(b'x'*65537);oversized=archived_sample(source,form,archive);assert oversized['status']=='UNKNOWN'
result=dict(before=before,after=after,replay_after_source_deleted=True,duplicate_reuses_snapshot=True,
    missing=missing,corrupt=corrupt,oversized=oversized,
    scope='filesystem replay and controls; no GUI performance or power-loss durability measurement')
(out/'results.json').write_text(json.dumps(result,indent=2)+'\n')
(out/'sources.json').write_text(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in
    (Path(__file__),HERE/'effect_checkpoint_v2.py',HERE/'effect_checkpoint.py',HERE/'saved_effect.py')},indent=2)+'\n')
print('Workbook UNKNOWN and VERIFIED replay after overwrite/delete; duplicate, missing, corruption, size controls passed')
