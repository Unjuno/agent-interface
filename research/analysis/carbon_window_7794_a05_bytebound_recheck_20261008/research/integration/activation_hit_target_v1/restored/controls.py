"""Finite copied-evidence changes. Does not execute a GUI or import the candidate."""
import argparse,copy,json,shutil,tempfile,zlib
from pathlib import Path
from audit import case_audit,expected_rows,sha

def replace_record(path,change):
    p=path/'record.json';r=json.loads(p.read_text());change(r);p.write_text(json.dumps(r,sort_keys=True)+'\n')
def strip_event(path,event_type=None,kind=None):
    p=path/'app-events.jsonl'; rows=[json.loads(x) for x in p.read_text().splitlines()]
    for i,r in enumerate(rows):
        if (event_type is not None and r.get('event')==event_type and r['kind']=='native') or (kind is not None and r['kind']==kind): rows.pop(i);break
    for i,r in enumerate(rows):r['seq']=i+1
    p.write_text(''.join(json.dumps(r,sort_keys=True)+'\n' for r in rows))
def mutate_pixels(path):
    rp=path/'record.json';r=json.loads(rp.read_text()); cap=r['after_capture']; p=path/cap['file']; raw=bytearray(zlib.decompress(p.read_bytes())); x,y=cap['marker_xy']
    for dy in range(10):
        for dx in range(10):
            k=((y+dy)*640+x+dx)*4;raw[k:k+4]=(0x112233).to_bytes(4,'little')
    p.write_bytes(zlib.compress(raw)); cap['sha256']=sha(raw);rp.write_text(json.dumps(r,sort_keys=True)+'\n')
def controls(source_root,output=None):
    source_root=Path(source_root)
    changes=[
      ('final_value',0,lambda d:replace_record(d,lambda r:r['final'].__setitem__('a','wrong'))),
      ('omitted_callback_reindexed',3,lambda d:strip_event(d,kind='callback')),
      ('wrong_hit_leaf',0,lambda d:replace_record(d,lambda r:r['pre_observer'].__setitem__('leaf',r['initial']['ids']['cover']))),
      ('receipt_hit_binding',0,lambda d:replace_record(d,lambda r:r['decisions'][0]['receipt'].__setitem__('hit',r['initial']['ids']['cover']))),
      ('flipped_decision',5,lambda d:replace_record(d,lambda r:r['decisions'][0]['result'].__setitem__('allow',True))),
      ('omitted_key_reindexed',0,lambda d:strip_event(d,event_type='2')),
      ('missing_app_exit',0,lambda d:replace_record(d,lambda r:r.pop('app_exit'))),
      ('bool_app_exit',0,lambda d:replace_record(d,lambda r:r.__setitem__('app_exit',False))),
      ('non_neutral',0,lambda d:replace_record(d,lambda r:r['final_observer']['keymap'].__setitem__(0,1))),
      ('changed_geometry',0,lambda d:replace_record(d,lambda r:r['geometry_after'].__setitem__('x',99))),
      ('marker_with_recomputed_hash',3,mutate_pixels),
      ('reversed_decision_time',0,lambda d:replace_record(d,lambda r:r['decisions'][0].__setitem__('decided_ns',0))),
    ]
    results=[]
    for name,i,change in changes:
        src=source_root/f'case-{i:02d}'; baseline=case_audit(src,expected_rows()[i])
        if baseline['errors']:raise RuntimeError('baseline refused: '+str(baseline['errors']))
        with tempfile.TemporaryDirectory(prefix='hit-audit-') as tmp:
            d=Path(tmp)/'case';shutil.copytree(src,d);change(d);out=case_audit(d,expected_rows()[i])
            results.append({'name':name,'case':i,'rejected':bool(out['errors']),'errors':out['errors']})
    return {'controls':results,'rejected':sum(r['rejected'] for r in results),'total':len(results),'pass':all(r['rejected'] for r in results)}
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('input');args=a.parse_args();r=controls(args.input);print(json.dumps(r,indent=2,sort_keys=True));raise SystemExit(not r['pass'])
