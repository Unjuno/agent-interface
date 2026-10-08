"""Pre-run saved-evidence checker; no policy import, no native input."""
if not __debug__:raise RuntimeError('STOP_OPTIMIZED_AUDIT')
import copy,hashlib,json,sys
from pathlib import Path
FIELDS=('cover','geometry','focus','pending','business')
MODES=('RECUR','CLEAR','WITHHELD','NEW_FAILURE')
ARMS=('NO_MEMORY','NOTE','TYPED','FRESH','TYPED_PLUS_FRESH')
def require(condition,message):
    if not condition:raise ValueError(message)
def events(row,bad):
    target=row['target'];cover=row['cover'];key=row['keycode']
    mouse=cover if bad=='cover' else target
    result=[] if bad=='geometry' else [dict(type=4,window=mouse,detail=1),dict(type=5,window=mouse,detail=1)]
    result.extend([dict(type=2,window=cover if bad=='focus' else target,detail=key),dict(type=3,window=cover if bad=='focus' else target,detail=key)])
    return result
def typed_equal(actual,expected):
    if type(actual) is not type(expected):return False
    if isinstance(expected,dict):return actual.keys()==expected.keys() and all(typed_equal(actual[k],v) for k,v in expected.items())
    if isinstance(expected,list):return len(actual)==len(expected) and all(typed_equal(a,b) for a,b in zip(actual,expected))
    return actual==expected
def check(rows,root=None):
    require(len(rows)==100,'matrix length')
    matrix=[(f,m,a) for f in FIELDS for m in MODES for a in ARMS]
    for row,(field,mode,arm) in zip(rows,matrix):
        require((row['field'],row['mode'],row['arm'])==(field,mode,arm),'ordered matrix')
        require('error' not in row and row['cleanup_errors']==[],'error or cleanup')
        for key in ('target','cover','keycode'):require(type(row[key]) is int and row[key]>0,'native integer')
        require(row['target']!=row['cover'],'distinct IDs')
        require(row['keymap_empty'] is True and row['buttons_neutral'] is True and row['server_exit']==0 and type(row['server_exit']) is int,'terminal')
        prior={k:k!=field for k in FIELDS}
        require(typed_equal(row['prior_observed'],prior),'prior observation')
        expectedprior=dict(events=events(row,field),committed=False,saved_bytes=None)
        require(typed_equal(row['prior'],expectedprior),'prior native event/effect')
        memory=row['memory'];require(memory['observed_preconditions']==prior and memory['target']==str(row['target']) and memory['attempted_action']=='click_then_F8','memory binding')
        require(typed_equal(memory['applicability_envelope'],{'field':field,'value':False}),'envelope')
        require(memory['outcome']=='NOT_COMMITTED' and memory['evidence']==hashlib.sha256(json.dumps(row['prior'],sort_keys=True).encode()).hexdigest(),'failure evidence')
        bad=field if mode=='RECUR' else (FIELDS[(FIELDS.index(field)+1)%5] if mode=='NEW_FAILURE' else None)
        current={k:k!=bad for k in FIELDS};require(typed_equal(row['current_observed'],current),'current observation')
        obs=dict(current)
        if mode=='WITHHELD':obs[field]=None
        require(typed_equal(row['supplied_observed'],{field:obs[field]} if arm=='TYPED' else obs),'supplied observation')
        want='TRY' if arm=='NO_MEMORY' else 'BLOCK' if arm=='NOTE' else ('UNKNOWN' if mode=='WITHHELD' else 'BLOCK' if mode=='RECUR' or (mode=='NEW_FAILURE' and arm!='TYPED') else 'TRY')
        require(row['decision']==want,'decision')
        committed=want=='TRY' and bad is None
        expected=dict(events=events(row,bad) if want=='TRY' else [],committed=committed,saved_bytes=b'COMMITTED\n'.hex() if committed else None)
        require(typed_equal(row['attempt'],expected),'attempt native event/effect')
        require(row['memory_unchanged'] is True,'memory mutation')
        if root is not None:
            cell=root/f'{field}-{mode}-{arm}'
            require(hashlib.sha256((cell/'memory.json').read_bytes()).hexdigest()==row['memory_sha256'],'persisted memory hash')
            require(typed_equal(json.loads((cell/'memory.json').read_text()),memory),'persisted memory content')
            require(not (cell/'prior.saved').exists(),'unexpected prior saved file')
            require((cell/'attempt.saved').exists()==committed,'saved file presence')
            if committed:require((cell/'attempt.saved').read_bytes()==b'COMMITTED\n','saved file bytes')
    return {'status':'PASS_METHOD_SCOPED_FAIL_SELECTIVE_TRANSFER_AUTHORITY',
            'rows':100,'typed_recurring_blocks':5,'typed_cleared_commits':5,'typed_withheld_unknown':5,
            'typed_new_failure_attempts_without_commit':5,
            'fresh_and_typed_plus_fresh_identical_decisions':20,
            'formal_candidate_runs_declared':0,'formal_auditor_runs_declared':0,
            'interpretation':'persisted one-field memory works on known conditions but cannot replace fresh all-condition admission; no incremental efficacy over fresh guard'}
def controls(rows):
    mutations=[lambda r:r.pop(),lambda r:r[2].update(decision='TRY'),lambda r:r[10]['attempt'].update(committed=False),
               lambda r:r[0]['prior']['events'][0].update(detail=True),lambda r:r[0]['current_observed'].update(cover=0),
               lambda r:r[0]['memory']['applicability_envelope'].update(value=0),lambda r:r[0].update(keymap_empty=False),
               lambda r:r[0].update(memory_unchanged=False),lambda r:r.__setitem__(-1,copy.deepcopy(r[0]))]
    for mutate in mutations:
        copied=copy.deepcopy(rows);mutate(copied)
        require(not typed_equal(copied,rows),'ineffective corruption')
        try:check(copied)
        except (ValueError,KeyError):continue
        raise ValueError('corruption accepted')
    return len(mutations)
def main():
    root=Path(sys.argv[1]);raw=(root/'raw.jsonl').read_bytes();rows=[json.loads(line) for line in raw.splitlines()]
    result=check(rows,root);result.update(raw_sha256=hashlib.sha256(raw).hexdigest(),copied_controls_rejected=controls(rows),auditor_created_before_run=True)
    with (root.parent/'AUDIT.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
    print(json.dumps(result))
if __name__=='__main__':main()
