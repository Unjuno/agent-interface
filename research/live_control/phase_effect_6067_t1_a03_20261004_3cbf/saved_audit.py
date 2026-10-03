"""Saved-only A03 audit; never imports acquisition or producer."""
import argparse
import hashlib
import json
from pathlib import Path
import reference as ref
from evidence import admit_launch, admit_transport
from mount_adapter import normalize_launch, guard_output
from protocol import cases_for, admit_stage
from cell_validation import validate_cell
from decision import evaluate

def load_cell(path):
    saved=ref.read(path/'cell.json')
    files={p.name for p in path.iterdir() if p.is_file() and p.name!='cell.json'}
    ref.need(set(saved['files_sha256'])==files,'complete cell raw denominator')
    for name,digest in saved['files_sha256'].items():
        ref.need(Path(name).name==name and hashlib.sha256((path/name).read_bytes()).hexdigest()==digest,
                 'exact cell raw bytes')
    def journal(name):
        return [ref.parse_record(s) for s in (path/name).read_text().splitlines()]
    return {'source':ref.read(path/'source.json'),'capture':ref.read(path/'capture.json'),
            'lifecycle':saved['lifecycle'],'source_journal':journal('source.jsonl'),
            'source_waits':journal('source-waits.jsonl'),'frames':journal('frames.jsonl'),
            'observer_waits':journal('waits.jsonl')},saved

def validate(raw,freeze,here):
    fixture=ref.read(here/'fixture.json')
    pins={name:hashlib.sha256((here/name).read_bytes()).hexdigest() for name in freeze['source_sha256']}
    readiness_bytes=(here/'readiness-RESULT.json').read_bytes() if freeze['mode']=='formal' else None
    admit_stage(freeze,freeze['mode'],pins,fixture,readiness_bytes)
    launch=ref.read(raw/'launch.json')
    admit_launch(normalize_launch(launch,freeze),freeze)
    consumed=ref.read(raw/'consumed.json');after=ref.read(raw/'post_source.json')
    admit_transport(consumed,launch,ref.read(raw/'copy.json'),after,freeze)
    pin_names=list(pins)+[freeze['mode']+'-FREEZE.json']
    if freeze['mode']=='formal':pin_names.append('readiness-RESULT.json')
    expected={freeze['guest_source']+'/'+n:hashlib.sha256((here/n).read_bytes()).hexdigest() for n in pin_names}
    actual={line.split()[1]:line.split()[0] for line in consumed['readiness']['guest_sha256']['stdout'].splitlines()}
    ref.join(actual,expected,'full frozen guest source')
    record=raw/'record';summary=ref.read(record/'raw.json')
    native_consumed=ref.read(record/'consumed.json')
    ref.join(native_consumed['allocation'],freeze['allocation'],'native consumed allocation')
    ref.join(native_consumed['mode'],freeze['mode'],'native consumed mode')
    ref.need(ref.integer(native_consumed['pid'])>0 and
             ref.integer(native_consumed['started_ns'])<=ref.integer(summary['finished_ns']),
             'native consumed terminal chronology')
    ref.need(summary['status']=='COMPLETE','complete native block prerequisite')
    ref.join(summary['allocation'],freeze['allocation'],'native allocation')
    ref.join(summary['mode'],freeze['mode'],'native mode')
    ref.join(summary['source_sha256'],pins,'native source receipt')
    ref.join(summary['cgroups'],{'cpu.max':'100000 100000','memory.max':'536870912',
                               'memory.swap.max':'0','pids.max':'64'},'actual native cgroups')
    for key in ('input_events','model_calls'):
        ref.need(ref.integer(summary[key])==0,'no input/model')
    specs=cases_for(freeze['mode'],fixture);ids=[s['id'] for s in specs]
    ref.join(summary['cells'],ids,'complete qualified order')
    ref.join(summary['started_cells'],ids,'complete started order')
    ref.need({p.name for p in (record/'cells').iterdir()}==set(ids),'closed cell directory set')
    rows=[]
    for spec in specs:
        cell,saved=load_cell(record/'cells'/spec['id'])
        ref.join(saved['spec'],spec,'typed native spec')
        path=record/'cells'/spec['id']
        ref.join(ref.read(path/'spec.json'),spec,'actual source input spec')
        ref.need(saved['error'] is None,'collector no child exception')
        ref.join(ref.read(path/'epoch.json'),{'epoch_ns':cell['source']['epoch_ns']},'source assigned epoch')
        ref.join(ref.read(path/'fixture-ready.json'),{'pid':cell['source']['pid'],'window':cell['source']['window']},
                 'fixture readiness identity')
        ref.join(ref.read(path/'observer-ready.json'),{'pid':cell['capture']['pid'],
                 'initial_keymap':cell['capture']['initial_keymap']},'observer readiness identity')
        native_root='/out/result/cells/'+spec['id']
        ref.join(saved['commands'],{
            'xvfb':['Xvfb',':93','-screen','0','64x64x24','-nolisten','tcp','-noreset','-ac'],
            'fixture':['/usr/local/bin/python3','-B','/src/fixture.py','--display',':93',
                       '--cell',native_root+'/spec.json','--out',native_root],
            'observer':['/usr/local/bin/python3','-B','/src/observer.py','--display',':93','--window',
                        str(cell['source']['window']),'--offsets',json.dumps(spec['offsets']),
                        '--out',native_root,'--epoch-file',native_root+'/epoch.json']},
                 'exact private native child commands')
        rows.append({**spec,**validate_cell(spec,cell)})
    if freeze['mode']=='readiness':
        for row in rows:
            expected=[] if row['kind']=='dark' else [1] if row['kind']=='persistent' else list(range(1,9))
            ref.join(row['stable_ids'],expected,'readiness all stable cue IDs')
            ref.need(row['boundary_hits']==0 and row['unknown_frames']==0,'readiness unambiguous pixels')
        decision={'status':'PASS_READINESS_SCOPED','cells':5,'captures':40}
    else:
        pulse=[r for r in rows if r['kind']=='pulse']
        misses={arm:sum(r['historical']['misses']==8 for r in pulse if r['schedule']==arm)
                for arm in ('fixed','irregular','rotated')}
        blind=all(any(r['schedule']=='fixed' and r['width_ms']==w and r['historical']['misses']==8
                      for r in pulse) for w in (10,20,30))
        historical=('PASS_TRANSFER_SCOPED' if blind and misses['irregular']<misses['fixed']
                    and misses['rotated']<misses['fixed'] else 'HOLD_BENEFIT_NOT_ESTABLISHED')
        decision=evaluate(fixture,rows,historical)
        decision['historical_status']=historical
    return {**decision,'allocation':freeze['allocation'],'mode':freeze['mode'],'source_sha256':pins,
            'input_events':0,'model_calls':0,'rows':rows}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--raw',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True);ap.add_argument('--freeze',type=Path,required=True)
    a=ap.parse_args();here=Path(__file__).resolve().parent
    guard_output(a.raw,a.out,here)
    cgroups={name:Path('/sys/fs/cgroup',name).read_text().strip()
             for name in ('cpu.max','memory.max','memory.swap.max','pids.max')}
    ref.join(cgroups,{'cpu.max':'100000 100000','memory.max':'536870912','memory.swap.max':'0','pids.max':'64'},
             'actual saved auditor cgroups')
    result=validate(a.raw,ref.read(a.freeze),here)
    a.out.mkdir(exist_ok=False)
    from controls import run_controls
    result['controls']=run_controls(a.raw,ref.read(a.freeze),result,a.out)
    result['auditor_cgroups']=cgroups
    with (a.out/'RESULT.json').open('x') as f:f.write(json.dumps(result,sort_keys=True,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='rows'},sort_keys=True))

if __name__=='__main__':main()
