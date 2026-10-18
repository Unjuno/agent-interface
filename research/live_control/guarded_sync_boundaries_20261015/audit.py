"""Saved raw only; no runtime imports or collector execution."""
import argparse
import copy
import hashlib
import json
from pathlib import Path

MATRIX = [('healthy','none')] + [(boundary,trigger) for boundary in
          ('capture','persistence','callback') for trigger in ('cancel','expiry')]


def validate(raw, freeze_hash):
    checks = []
    def require(name, condition):
        if not condition: raise ValueError(name)
        checks.append(name)
    require('scope',raw['scope']=='FAKE_X_SYNC_BOUNDARY_CHARACTERIZATION')
    require('freeze',raw['freeze_sha256']==freeze_hash)
    require('postcheck',raw['source_postcheck'] is True)
    require('matrix',[(r['boundary'],r['trigger']) for r in raw['cases']]==MATRIX)
    for row in raw['cases']:
        label = row['boundary']+'-'+row['trigger']
        require(label+' neutral',row['fake_keys_down']==[] and row['reader_closed'] is True)
        require(label+' no live',row['consumed_live_allocations']==0)
        execution = row['result']['execution']
        require(label+' release verified',bool(execution['releases']) and
                execution['releases'][-1]['verified'] is True)
        if row['boundary']=='healthy':
            require(label+' completes',row['result']['status']=='completed')
            require(label+' input exercised',row['emissions']==[[2,1],[2,2],[3,2],[3,1]])
            require(label+' no gate',row['blocked'] is None)
            continue
        blocked = row['blocked']
        require(label+' held',blocked['fake_keys_down']==[1])
        require(label+' blocked',blocked['gate_open'] is False and blocked['returned'] is False
                and blocked['release_receipt_returned'] is False)
        require(label+' prefix',blocked['emissions']==[[2,1]])
        require(label+' no task continuation',row['emissions']==[[2,1],[3,1]])
        require(label+' fails',row['result']['status']=='execution_failed')
        require(label+' query not blocked',blocked['query_worker']['pending'] is False
                and blocked['query_worker']['retired'] is False)
        if row['trigger']=='cancel':
            require(label+' cancel accepted',blocked['ack']['status']=='cancel_requested'
                    and blocked['ack']['release_confirmed'] is False
                    and blocked['clock_ns']<blocked['original_deadline_ns'])
        else:
            require(label+' original expiry',blocked['ack'] is None
                    and blocked['clock_ns']==blocked['original_deadline_ns'])
    return checks


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('directory',type=Path)
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    if args.output.exists(): parser.error('output exists')
    hash_file = lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    manifest = json.loads((args.directory/'FILES.json').read_bytes())
    actual = {p.relative_to(args.directory).as_posix():hash_file(p) for p in args.directory.rglob('*')
              if p.is_file() and p.name!='FILES.json'}
    if actual!=manifest: raise ValueError('artifact manifest differs')
    raw = json.loads((args.directory/'raw.json').read_bytes())
    sha = hash_file(Path(__file__).with_name('SOURCE_FREEZE.json'))
    checks = validate(raw,sha)
    mutations = [lambda r:r['cases'][1]['blocked'].__setitem__('fake_keys_down',[]),
        lambda r:r['cases'][1]['blocked'].__setitem__('returned',True),
        lambda r:r['cases'][1]['emissions'].append([2,2]),
        lambda r:r['cases'][1]['result']['execution']['releases'][-1].__setitem__('verified',False)]
    for mutate in mutations:
        changed = copy.deepcopy(raw);mutate(changed)
        try: validate(changed,sha)
        except ValueError: continue
        raise ValueError('mutation accepted')
    with args.output.open('x',encoding='utf-8',newline='\n') as output:
        json.dump(dict(status='PASS_COUNTEREXAMPLE_NOT_RELEASE_BOUND',checks=checks,
            mutations_rejected=len(mutations),artifact_hashes=len(manifest),
            raw_sha256=hash_file(args.directory/'raw.json')),output,indent=2);output.write('\n')
    print(len(checks),'checks;',len(mutations),'mutations rejected')


if __name__=='__main__': main()
