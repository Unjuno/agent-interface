"""Known live batches: reusable image references and explicit malformed negatives."""
import copy,hashlib,json
from pathlib import Path
from receipt_image import select_image
HERE=Path(__file__).resolve().parent;out=HERE/'results/receipt-image-01';out.mkdir(exist_ok=False);rows=[];sources={}
for cohort in ('send-wait-self-use-01','request-outcome-self-use-01','receipt-clock-self-use-01'):
    root=HERE/'results'/cohort
    for name in ('initial','modal','effect','final'):
        source=root/f'read-{name}.json';batch=json.loads(source.read_text());result=select_image(batch,root)
        if name=='final':assert result['status']=='no_observation'
        else:
            assert result['status']=='image'
            if name=='modal':assert result['relative_path']==('006.png' if cohort=='receipt-clock-self-use-01' else '007.png')
        rows.append(dict(cohort=cohort,batch=name,result=result));sources[str(source.relative_to(HERE))]=hashlib.sha256(source.read_bytes()).hexdigest()
root=HERE/'results/receipt-clock-self-use-01';batch=json.loads((root/'read-modal.json').read_text())
obs=copy.deepcopy(batch['records'][-1]['review']['observation'])
for case in ('missing','conflicting','outside','malformed_latest'):
    altered=copy.deepcopy(obs)
    if case=='missing':altered['image']=str(root/'does-not-exist.png')
    elif case=='conflicting':altered['capture_ns']+=1
    elif case=='outside':altered['image']=str(HERE/'results/modal-focus-01/tab-0.png')
    else:altered.update(sequence=obs['sequence']+1,image=None)
    bad=dict(records=[dict(event='observation',**obs),dict(event='observation',**altered)])
    try:select_image(bad,root)
    except (ValueError,FileNotFoundError) as exc:rows.append(dict(negative=case,rejected=type(exc).__name__))
    else:raise AssertionError(case)
for source in (Path(__file__),HERE/'receipt_image.py'):sources[str(source.relative_to(HERE))]=hashlib.sha256(source.read_bytes()).hexdigest()
(out/'results.json').write_text(json.dumps(rows,indent=2)+'\n');(out/'sources.json').write_text(json.dumps(sources,indent=2)+'\n')
print(json.dumps(dict(replayed_batches=12,negative_controls=4,failed_guess_fixed='receipt-clock modal selects referenced 006.png'),indent=2))
