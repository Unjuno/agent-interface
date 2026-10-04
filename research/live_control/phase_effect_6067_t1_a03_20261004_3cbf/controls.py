"""Retained saved-cell semantic controls and launch-map admission controls.

Scopes are cell validator and launch custody, not full 114-cell wrapper trials.
"""
import copy
import hashlib
import json
from pathlib import Path
import reference as ref
from saved_audit import load_cell
from cell_validation import validate_cell
from mount_adapter import normalize_launch
from evidence import admit_launch

CELL_NAMES=('wait_bool','cpu_false','missing_wait','post_after_paint',
            'source_wait_id','pixel_hash','source_journal_id','observer_wait_index')
MOUNT_NAMES=('duplicate','wrong_source','wrong_rw','missing','extra','nonbind','bool_rw')

def write(path,value):
    with path.open('x') as f:f.write(json.dumps(value,sort_keys=True,indent=2)+'\n')

def run_controls(raw,freeze,result,out):
    spec=next({k:r[k] for k in ('id','kind','schedule','offsets','phase','width_ms')}
              for r in result['rows'] if r['kind']=='pulse')
    original=raw/'record/cells'/spec['id'];reports=[]
    (out/'cell-controls').mkdir()
    for name in CELL_NAMES:
        trial=out/'cell-controls'/name;trial.mkdir()
        for p in original.iterdir():
            if p.is_file():(trial/p.name).write_bytes(p.read_bytes())
        so,ca=ref.read(trial/'source.json'),ref.read(trial/'capture.json')
        if name=='wait_bool':so['wait_traces'][0]['wait']['return_ns']=False
        elif name=='cpu_false':so['wait_traces'][0]['post']['cpu_stat']['nr_throttled']=False
        elif name=='missing_wait':so['wait_traces'].pop()
        elif name=='post_after_paint':so['wait_traces'][0]['post']['end_ns']=so['events'][0]['draw_start_ns']+1
        elif name=='source_wait_id':so['wait_traces'][0]['id']=99
        elif name=='pixel_hash':ca['frames'][0]['pixel_sha256']='0'*64
        # Derived trial bytes only; original input never changes.
        (trial/'source.json').write_text(json.dumps(so,sort_keys=True)+'\n')
        (trial/'capture.json').write_text(json.dumps(ca,sort_keys=True)+'\n')
        (trial/'source-waits.jsonl').write_text(''.join(json.dumps(t,sort_keys=True)+'\n' for t in so['wait_traces']))
        (trial/'frames.jsonl').write_text(''.join(json.dumps(t,sort_keys=True)+'\n' for t in ca['frames']))
        if name in ('source_journal_id','observer_wait_index'):
            file='source.jsonl' if name=='source_journal_id' else 'waits.jsonl'
            rows=[ref.parse_record(s) for s in (trial/file).read_text().splitlines()]
            rows[0]['id' if name=='source_journal_id' else 'index']=99
            (trial/file).write_text(''.join(json.dumps(t,sort_keys=True)+'\n' for t in rows))
        saved=ref.read(trial/'cell.json')
        saved['files_sha256']={p.name:hashlib.sha256(p.read_bytes()).hexdigest()
                              for p in trial.iterdir() if p.is_file() and p.name!='cell.json'}
        (trial/'cell.json').write_text(json.dumps(saved,sort_keys=True)+'\n')
        try:
            cell,_=load_cell(trial);validate_cell(spec,cell)
        except (ValueError,KeyError,TypeError) as exc:
            reports.append({'name':name,'scope':'cell','rejected':True,'reason':str(exc)})
        else:raise ValueError('ineffective cell control '+name)
    (out/'mount-controls').mkdir()
    original_launch=ref.read(raw/'launch.json')
    for name in MOUNT_NAMES:
        launch=copy.deepcopy(original_launch);state=ref.parse_record(launch['inspect_stdout'])
        mounts=state['Mounts'];src=next(m for m in mounts if m['Destination']=='/src')
        if name=='duplicate':mounts.append(copy.deepcopy(src))
        elif name=='wrong_source':src['Source']+='/different'
        elif name=='wrong_rw':src['RW']=True
        elif name=='missing':mounts.remove(src)
        elif name=='extra':mounts.append({'Type':'bind','Source':'/different','Destination':'/extra','RW':False})
        elif name=='nonbind':src['Type']='volume'
        else:src['RW']=0
        launch['inspect_stdout']=json.dumps(state,sort_keys=True)
        write(out/'mount-controls'/(name+'.json'),launch)
        try:admit_launch(normalize_launch(launch,freeze),freeze)
        except (ValueError,KeyError,TypeError) as exc:
            reports.append({'name':name,'scope':'launch','rejected':True,'reason':str(exc)})
        else:raise ValueError('ineffective mount control '+name)
    write(out/'controls.json',reports)
    return reports
