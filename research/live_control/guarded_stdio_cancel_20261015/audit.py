"""Validate retained JSON/artifacts only; never start the stdio server."""
import argparse
import copy
import hashlib
import json
from pathlib import Path

MATRIX=[(arm,condition) for condition in ('healthy','cancel','expiry') for arm in ('coupled','isolated')]


def validate(raw,freeze_sha):
    checks=[]
    def require(name,condition):
        if not condition: raise ValueError(name)
        checks.append(name)
    require('scope',raw['scope']=='REAL_STDIO_FAKE_X_CANCELLATION')
    require('freeze',raw['freeze_sha256']==freeze_sha and raw['source_postcheck'] is True)
    require('no live allocation',raw['live_allocations']==0)
    require('matrix',[(r['arm'],r['condition']) for r in raw['cases']]==MATRIX)
    for row in raw['cases']:
        label=row['arm']+'-'+row['condition'];isolated=row['arm']=='isolated'
        require(label+' stdio bootstrap','research.live_control.guarded_stdio_cancel_20261015.server' in row['child_command'])
        require(label+' selected policy',row['result']['session']['observation_worker'] is isolated)
        require(label+' child process',row['state_after']['pid']!=raw['parent_pid'])
        require(label+' discovered cancel','interface_guarded_cancel' in row['tools'])
        require(label+' closed',row['close']['status']=='closed' and row['transport_context_closed'] is True)
        require(label+' neutral',row['state_after']['fake_keys_down']==[])
        require(label+' lookup no input',row['state_after']==row['state_after_lookup'])
        require(label+' retained result',row['retained_result']==row['result']['result'])
        require(label+' verified release',row['result']['result']['execution']['releases'][-1]['verified'] is True)
        times=row['parent_perf_counter_ns']
        require(label+' chronology',times['start']<times['input_sent']<times['input_result_received']<times['transport_closed'])
        before=row['before_gate_release']
        if row['condition']=='healthy':
            require(label+' healthy',row['result']['status']=='completed' and before is None)
            require(label+' input exercised',row['state_after']['emissions']==[[2,1],[2,2],[3,2],[3,1]])
            continue
        require(label+' held at gate',before['gate']['fake_keys_down']==[1])
        require(label+' gate closed',before['release_flag_exists'] is False)
        require(label+' same child',before['gate']['pid']==before['state']['pid']==row['state_after']['pid'])
        require(label+' failed input',row['result']['status']=='execution_failed')
        require(label+' refused following key',row['state_after']['emissions']==[[2,1],[3,1]])
        require(label+' before release result',before['input_result_received'] is isolated)
        require(label+' before release state',before['state']['fake_keys_down']==([] if isolated else [1]))
        require(label+' receipt ordering',(times['input_result_received']<times['gate_release']) is isolated)
        require(label+' trigger chronology',times['input_sent']<times['trigger_sent']<=times['trigger_returned']<times['gate_release'])
        if row['condition']=='cancel':
            require(label+' actual cancel',before['ack']['status']=='cancel_requested'
                and before['ack']['release_confirmed'] is False and before['wrong']['status']=='not_active')
        else:
            require(label+' original expiry',before['ack'] is None and before['wrong'] is None
                and before['gate']['original_deadline_ns']==5_001_000_000)
    return checks


def main():
    parser=argparse.ArgumentParser();parser.add_argument('directory',type=Path);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if args.output.exists(): parser.error('output exists')
    digest=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
    manifest=json.loads((args.directory/'FILES.json').read_bytes())
    actual={p.relative_to(args.directory).as_posix():digest(p) for p in args.directory.rglob('*') if p.is_file() and p.name!='FILES.json'}
    if actual!=manifest: raise ValueError('artifact hash mismatch')
    raw=json.loads((args.directory/'raw.json').read_bytes())
    frozen=digest(Path(__file__).with_name('SOURCE_FREEZE.json'))
    checks=validate(raw,frozen)
    for row in raw['cases']:
        cell=json.loads((args.directory/(row['arm']+'-'+row['condition'])/'cell.json').read_bytes())
        if cell!=row: raise ValueError('cell/raw mismatch')
    mutations=[lambda r:r['cases'][2]['before_gate_release']['state'].__setitem__('fake_keys_down',[]),
        lambda r:r['cases'][3]['before_gate_release'].__setitem__('input_result_received',False),
        lambda r:r['cases'][3]['before_gate_release']['ack'].__setitem__('release_confirmed',True),
        lambda r:r['cases'][3]['state_after']['emissions'].append([2,2]),
        lambda r:r['cases'][3]['result']['result']['execution']['releases'][-1].__setitem__('verified',False)]
    for mutate in mutations:
        changed=copy.deepcopy(raw);mutate(changed)
        try: validate(changed,frozen)
        except ValueError: continue
        raise ValueError('mutation accepted')
    with args.output.open('x',encoding='utf-8',newline='\n') as output:
        json.dump(dict(status='PASS_STDIO_FAKE_X_NOT_PHYSICAL_BOUND',checks=checks,mutations_rejected=len(mutations),
            artifact_hashes=len(manifest),raw_sha256=digest(args.directory/'raw.json')),output,indent=2);output.write('\n')
    print(len(checks),'checks;',len(mutations),'mutations rejected')


if __name__=='__main__': main()
