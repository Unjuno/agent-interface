"""Read-only, separately implemented audit; imports no Tk, runner or candidate."""
import copy
import hashlib
import json
import math
from pathlib import Path
import sys

SCENARIOS = ['fast','delayed','absent','late','blocked_fast','blocked_absent']
POLICIES = ['PRECHECK_ONLY','POST_OBSERVATION']

def check_record(envelope):
    assert type(envelope['repetition']) is int
    assert type(envelope['returncode']) is int and envelope['returncode']==0
    assert envelope['stderr']==''
    item = json.loads(envelope['stdout'])
    assert item['policy']==envelope['policy'] and item['scenario']==envelope['scenario']
    assert type(item['pid']) is int and item['pid']>0
    assert item['original_blob']=='f60bd81d37f574337d8aebb9a02fe35b12ab26fd'
    assert item['grants_input_authority'] is False
    assert json.loads(item['original_stdout'])==item['result']
    assert len(item['result']['rows'])==1
    result=item['result']['rows'][0]
    scenario,policy=item['scenario'],item['policy']
    assert scenario in SCENARIOS and policy in POLICIES
    assert result['case']==scenario
    horizon=.5 if scenario=='late' else .2
    delay=.35 if scenario in ('late','delayed') else None if scenario in ('absent','blocked_absent') else .05
    assert result['horizon']==horizon and result['effect_delay']==delay
    events=item['events']
    assert all(type(e['ns']) is int for e in events)
    times=[e['ns'] for e in events]
    assert times==sorted(times) and envelope['started_ns']<=times[0]<=times[-1]<=envelope['ended_ns']
    assert events[0]['kind']=='root_created' and events[-1]['kind']=='worker_complete'
    assert sum(e['kind']=='destroyed' for e in events)==1
    assert not any(e['kind']=='callback_error' for e in events)
    origin=[e for e in events if e['kind']=='origin']
    assert len(origin)==1 and type(origin[0]['seconds']) is float
    start=origin[0]['seconds']
    assert math.isfinite(start) and start*1e9<=origin[0]['ns']+1000
    done=[e for e in events if e['kind']=='read_end' and e['value']=='done']
    effects=[e for e in events if e['kind']=='config_end']
    assert all(e['text']=='done' for e in effects)
    assert len(effects)==len(done) and len(done)<=1
    # Reconstruct update/read bracket pairing, rather than accepting aggregate labels.
    updates={}
    read_pending=False
    for e in events:
        if e['kind']=='update_start':
            assert e['call'] not in updates
            updates[e['call']]=[e['ns']]
        elif e['kind']=='update_end':
            assert e['call'] in updates and len(updates[e['call']])==1
            updates[e['call']].append(e['ns'])
        elif e['kind']=='read_start':
            assert not read_pending; read_pending=True
        elif e['kind']=='read_end':
            assert read_pending; read_pending=False
    assert not read_pending and all(len(v)==2 for v in updates.values())
    assert sorted(updates)==list(range(1,len(updates)+1))
    block=[e for e in events if e['kind'] in ('block_start','block_end')]
    if scenario.startswith('blocked'):
        assert [e['kind'] for e in block]==['block_start','block_end']
        assert block[1]['ns']-block[0]['ns']>=300_000_000
        assert updates[2][0]<=block[0]['ns']<block[1]['ns']<=updates[2][1]
    else:
        assert block==[]
    expected_done=scenario in ('fast','late','blocked_fast')
    assert bool(done)==expected_done
    if done:
        assert effects[0]['ns']<=done[0]['ns']
        age=done[0]['ns']/1e9-start
        observed=result['observed_at']
        assert type(observed) is float and math.isfinite(observed)
        assert observed>=age-2e-6 and observed<=(times[-1]/1e9-start)+2e-6
        if scenario=='blocked_fast':
            assert age>=horizon and effects[0]['ns']>=block[1]['ns']
        else:
            assert 0<age<horizon
        expected='COMPLETED' if policy=='PRECHECK_ONLY' or observed<horizon else 'UNKNOWN'
    else:
        age=None
        assert result['observed_at'] is None
        expected='UNKNOWN'
    assert result['state']==expected and result['proceeded'] is (expected=='COMPLETED')
    assert item['result']['unknown_count']==int(expected=='UNKNOWN')
    return {'scenario':scenario,'policy':policy,'repetition':envelope['repetition'],
            'state':expected,'observed_at_s':result['observed_at'],
            'late_completion':bool(done and age>=horizon and expected=='COMPLETED'),
            'late_effect_retained':bool(done and age>=horizon),
            'effective_ast_sha256':item['effective_ast_sha256']}

def audit(root, repetitions):
    freeze_path=Path(__file__).with_name('FREEZE.json')
    freeze=json.loads(freeze_path.read_text()) if freeze_path.exists() else None
    if freeze:
        for name,digest in freeze['source_sha256'].items():
            assert hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()==digest
    all_rows=[]
    summaries=[]
    for rep in repetitions:
        directory=root/('batch-'+str(rep))
        terminal=json.loads((directory/'terminal.json').read_text())
        assert terminal['rows']==12 and terminal['errors']==[] and terminal['repetition']==rep
        assert type(terminal['server_exit']) is int and terminal['server_exit']==0
        assert terminal['socket_absent'] is True and terminal['input_calls']==terminal['model_calls']==0
        assert int((directory/'external_exit.txt').read_text())==0
        rows=[json.loads(s) for s in (directory/'raw.jsonl').read_text().splitlines()]
        expected=[(s,p) for s in SCENARIOS for p in (POLICIES if rep%2==0 else POLICIES[::-1])]
        assert [(r['scenario'],r['policy']) for r in rows]==expected and len(rows)==12
        for row in rows:
            assert row['repetition']==rep
            summary=check_record(row)
            if freeze:
                assert summary['effective_ast_sha256']==freeze['effective_ast_sha256'][row['policy']+'/'+row['scenario']]
            summaries.append(summary)
        all_rows.extend(rows)
    assert len(set(json.loads(r['stdout'])['pid'] for r in all_rows))==len(all_rows)
    assert sum(r['late_completion'] for r in summaries)==len(repetitions)
    assert all(not r['late_completion'] for r in summaries if r['policy']=='POST_OBSERVATION')
    controls=[]
    # These checks challenge copies; no execution of a formal worker is repeated.
    base=next(r for r in all_rows if r['scenario']=='blocked_fast' and r['policy']=='POST_OBSERVATION')
    for name in ['exit','stderr','source','authority','missing_effect','early_effect','false_complete','wrong_horizon','boolean_pid']:
        bad=copy.deepcopy(base); item=json.loads(bad['stdout'])
        if name=='exit': bad['returncode']=1
        elif name=='stderr': bad['stderr']='lost evidence'
        elif name=='source': item['original_blob']='0'*40
        elif name=='authority': item['grants_input_authority']=True
        elif name=='missing_effect': item['events']=[e for e in item['events'] if e['kind']!='config_end']
        elif name=='early_effect':
            next(e for e in item['events'] if e['kind']=='config_end')['ns']=item['events'][0]['ns']
        elif name=='false_complete':
            item['result']['rows'][0].update(state='COMPLETED',proceeded=True)
            item['original_stdout']=json.dumps(item['result'])
        elif name=='wrong_horizon':
            item['result']['rows'][0]['horizon']=.5; item['original_stdout']=json.dumps(item['result'])
        elif name=='boolean_pid': item['pid']=True
        bad['stdout']=json.dumps(item)
        rejected=False
        try: check_record(bad)
        except (AssertionError,KeyError,ValueError,TypeError): rejected=True
        assert rejected,name
        controls.append(name)
    return {'decision':'PASS_OBSERVATION_HORIZON_BOUNDARY_SCOPED','rows':len(all_rows),
            'precheck_late_completions':len(repetitions),'post_observation_late_completions':0,
            'controls_rejected':controls,'errors':[],'summaries':summaries}

if __name__=='__main__':
    print(json.dumps(audit(Path(sys.argv[1]),[int(x) for x in sys.argv[2:]]),indent=2,sort_keys=True))
