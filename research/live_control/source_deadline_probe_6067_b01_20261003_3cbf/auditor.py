"""One saved-only diagnostic invocation; imports no acquisition or candidate."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import reference as ref
import profile_reference as structural
from evidence import admit_launch, check_trace, admit_transport, check_continuity, check_shared_cpu
from profile import decompose, classify

SPEC={'id':'b000','kind':'pulse','schedule':'fixed','offsets':[0,0,0,0],'phase':0,'width_ms':20}

def validate(root, freeze):
    launch=ref.read(root/'launch.json')
    state=admit_launch(launch,freeze)
    admit_transport(ref.read(root/'consumed.json'),launch,ref.read(root/'copy.json'),ref.read(root/'post_source.json'),freeze)
    ref.need(ref.integer(ref.read(root/'copy.json')['exit_code'])==0,'copied full raw')
    before=ref.read(root/'consumed.json')['readiness']['guest_sha256']
    after=ref.read(root/'post_source.json')
    ref.need(ref.integer(after['exit_code'])==0,'post source read')
    ref.join(before['command'],after['command'],'pre/post guest hash command')
    ref.need(before['stdout']==after['stdout'],'pre/post source identity')
    expected={freeze['guest_source']+'/'+n:d for n,d in freeze['source_sha256'].items()}
    expected[freeze['guest_source']+'/FREEZE.json']=hashlib.sha256((Path(__file__).parent/'FREEZE.json').read_bytes()).hexdigest()
    actual={line.split()[1]:line.split()[0] for line in before['stdout'].splitlines()}
    ref.join(actual,expected,'full staged freeze/source receipt')
    cell=root/'record'
    saved=ref.read(cell/'cell.json')
    ref.need(saved['status']=='COLLECTED_SOURCE_DIAGNOSTIC' and saved['mode']=='source-boundary-diagnostic','complete diagnostic collection')
    ref.need(saved['allocation']=='SOURCE-DEADLINE-6067-B01-20261003-3CBF','new allocation')
    ref.join(saved['case'],SPEC,'frozen typed single case')
    ref.join(saved['source_sha256'],freeze['source_sha256'],'native source receipt')
    ref.join(saved['cgroups'],{'cpu.max':'100000 100000','memory.max':'536870912','memory.swap.max':'0','pids.max':'64'},'actual cgroups')
    for k in ('input_events','model_calls','scientific_t1_cells'):
        ref.need(ref.integer(saved[k])==0,'no input/model/scientific invocation')
    ref.need(set(saved['files_sha256'])=={p.name for p in cell.iterdir() if p.is_file() and p.name!='cell.json'},
             'complete raw file denominator')
    for name,digest in saved['files_sha256'].items():
        ref.need(Path(name).name==name and hashlib.sha256((cell/name).read_bytes()).hexdigest()==digest,'raw exact file bytes')
    so,ca=ref.read(cell/'source.json'),ref.read(cell/'capture.json')
    outcome=structural.audit_cell(SPEC,so,ca,saved['lifecycle'])
    ref.join([ref.parse_record(s) for s in (cell/'frames.jsonl').read_text().splitlines()],ca['frames'],'typed observer frame join')
    ref.join([ref.parse_record(s) for s in (cell/'source-waits.jsonl').read_text().splitlines()],so['wait_traces'],'typed source wait join')
    ref.need(len(so['wait_traces'])==16,'all sixteen source waits')
    source_journal=[ref.parse_record(s) for s in (cell/'source.jsonl').read_text().splitlines()]
    ref.need(len(source_journal)==16,'all sixteen source draw/clear records')
    source_metrics=[]
    previous=None
    previous_end=None
    snapshots=[]
    rows=[]
    for i,event in enumerate(so['events']):
        for j,kind in enumerate(('draw','clear')):
            t=so['wait_traces'][2*i+j]
            ref.need(t['kind']==kind and ref.integer(t['id'])==i+1,'ordered source wait identity')
            due=event['onset_ns'] if kind=='draw' else event['due_clear_ns']
            ref.need(ref.integer(t['due_ns'])==due,'wait intended source deadline')
            start,end=event[kind+'_start_ns'],event[kind+'_end_ns']
            ref.join([t['paint_start_ns'],t['paint_end_ns']],[start,end],'source wait/native typed join')
            ref.join(source_journal[2*i+j],{'event':kind,'id':i+1,'start':start,'end':end},'source event typed join')
            source_metrics.append({'kind':kind,'id':i+1,**check_trace(t,start,end)})
            if previous is not None: check_continuity(previous,t,previous_end)
            previous,previous_end=t,end
            snapshots.extend([t['pre'],t['post']])
        row={'id':i+1,**decompose(event,so['wait_traces'][2*i])}
        ref.need(row['shortfall_ns']==row['draw_wait_lateness_ns']+row['post_wait_to_paint_ns']+row['draw_xsync_ns']-row['clear_lateness_ns'],
                 'exact exposure decomposition')
        rows.append(row)
    waits=[ref.parse_record(s) for s in (cell/'waits.jsonl').read_text().splitlines()]
    ref.need(len(waits)==8,'all eight observer wait records')
    observer=[]
    previous=None
    for i,frame in enumerate(ca['frames']):
        ref.join(waits[i],{k:frame[k] for k in ('index','due_ns','pre','wait','post')},'observer wait stream typed join')
        observer.append({'index':i,**check_trace(frame,frame['start_ns'],frame['native_return_ns'])})
        if previous is not None: check_continuity(previous,frame,previous['extracted_ns'])
        previous=frame
        snapshots.extend([frame['pre'],frame['post']])
    check_shared_cpu(snapshots)
    try:
        ref.audit_cell(SPEC,so,ca,saved['lifecycle'])
        eligibility={'original_cell_gates_met':True,'first_failure':None}
    except ValueError as exc:
        eligibility={'original_cell_gates_met':False,'first_failure':str(exc)}
    return {'status':classify(rows),'source_events_checked':8,'source_waits_checked':16,'captures_checked':8,
            'decomposition':rows,'source_wait_metrics':source_metrics,'observer_wait_metrics':observer,
            'original_single_cell_eligibility':eligibility,
            'structural_metrics':outcome,'input_events':0,'model_calls':0,'scientific_t1_cells':0,
            'scope':'one instrumented native private profile; not original A02 rootcause, phase efficacy, rare-tail or safety'}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--raw',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True)
    args=ap.parse_args()
    here=Path(__file__).resolve().parent
    freeze=ref.read(here/'FREEZE.json')
    for name,digest in freeze['source_sha256'].items():
        ref.need(hashlib.sha256((here/name).read_bytes()).hexdigest()==digest,'frozen auditor/candidate source')
    result=validate(args.raw,freeze)
    source=ref.read(args.raw/'record/source.json')
    capture=ref.read(args.raw/'record/capture.json')
    args.out.mkdir(exist_ok=False)
    controls=[]
    mutations=('wait_bool','cpu_false','missing_wait','post_after_paint','source_wait_id','pixel_hash')
    for name in mutations:
        so,ca=copy.deepcopy(source),copy.deepcopy(capture)
        if name=='wait_bool': so['wait_traces'][0]['wait']['return_ns']=False
        elif name=='cpu_false': so['wait_traces'][0]['post']['cpu_stat']['nr_throttled']=False
        elif name=='missing_wait': so['wait_traces'].pop()
        elif name=='post_after_paint': so['wait_traces'][0]['post']['end_ns']=so['events'][0]['draw_start_ns']+1
        elif name=='source_wait_id': so['wait_traces'][0]['id']=99
        else: ca['frames'][0]['pixel_sha256']='0'*64
        trial=args.out/'trials'/name
        trial.mkdir(parents=True,exist_ok=False)
        for original in args.raw.rglob('*'):
            if original.is_file():
                target=trial/original.relative_to(args.raw)
                target.parent.mkdir(parents=True,exist_ok=True)
                target.write_bytes(original.read_bytes())
        cell=trial/'record'
        (cell/'source.json').write_text(json.dumps(so,sort_keys=True)+'\n')
        (cell/'capture.json').write_text(json.dumps(ca,sort_keys=True)+'\n')
        (cell/'source-waits.jsonl').write_text(''.join(json.dumps(t,sort_keys=True)+'\n' for t in so['wait_traces']))
        (cell/'frames.jsonl').write_text(''.join(json.dumps(f,sort_keys=True)+'\n' for f in ca['frames']))
        saved=ref.read(cell/'cell.json')
        saved['files_sha256']={p.name:hashlib.sha256(p.read_bytes()).hexdigest()
                              for p in cell.iterdir() if p.is_file() and p.name!='cell.json'}
        (cell/'cell.json').write_text(json.dumps(saved,sort_keys=True)+'\n')
        try:
            validate(trial,freeze)
        except (ValueError,KeyError,TypeError) as exc:
            controls.append({'mutation':name,'rejected':True,'reason':str(exc),'trial':'trials/'+name})
        else:
            raise ValueError('ineffective saved control '+name)
    (args.out/'RESULT.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    (args.out/'controls.json').write_text(json.dumps(controls,sort_keys=True)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('decomposition','source_wait_metrics','observer_wait_metrics','structural_metrics')},sort_keys=True))

if __name__=='__main__': main()
