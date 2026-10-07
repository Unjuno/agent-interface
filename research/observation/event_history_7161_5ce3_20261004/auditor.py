"""Literal oracle and exhaustive membership audit, no candidate imports."""
if not __debug__: raise RuntimeError('STOP_OPTIMIZED_AUDITOR_UNSUPPORTED')
import copy,hashlib,itertools,json,sys
from pathlib import Path
from fixtures import CASES,COUNTS
def canonical(x):return json.dumps(x,sort_keys=True,separators=(',',':'))
def check(rows):
    expected={}
    for name,events,want in CASES:
        for i,p in enumerate(itertools.permutations(events)):expected[(name,i)]=(list(p),want)
    assert len(rows)==len(expected)
    seen=set(); correct={a:0 for a in ['final_only','raw_chain','typed_event']}; rb=eb=ib=0
    for row in rows:
        assert type(row['delivery']) is int
        key=(row['case'],row['delivery']);assert key not in seen and key in expected;seen.add(key)
        chain,want=expected[key];assert canonical(row['chain'])==canonical(chain)
        assert type(row['expected_count']) is int and row['expected_count']==COUNTS[row['case']]
        assert type(row['final_state']) is int and row['final_state']==0
        assert canonical(row['capsule'])==canonical({'object_ref':'object-A','events':chain,'expected_count':COUNTS[row['case']],'predictions_are_observed':False,'input_authority':False})
        assert row['final_only']=='NOT_RUN'
        assert row['raw_chain']==want and row['typed_event']==want
        assert type(row['raw_bytes']) is int and row['raw_bytes']==len(canonical(chain).encode())
        assert type(row['raw_input_bytes']) is int and row['raw_input_bytes']==len(canonical({'events':chain,'expected_count':COUNTS[row['case']]}).encode())
        assert type(row['event_bytes']) is int and row['event_bytes']==len(canonical(row['capsule']).encode())
        for arm in correct:correct[arm]+=int(row[arm]==want)
        rb+=row['raw_bytes'];eb+=row['event_bytes'];ib+=row['raw_input_bytes']
    assert seen==set(expected)
    return {'first_status':'PASS_METHOD_SCOPED_HOLD_NO_INCREMENTAL_EVENT_GAIN','rows':len(rows),'correct':correct,'raw_chain_bytes':rb,'raw_complete_input_bytes':ib,'typed_event_bytes':eb,'native_calls':0,'model_calls':0}
def controls(rows):
    copies=[]
    for field,value in [('typed_event','SUCCESS'),('raw_chain','SUCCESS'),('final_state',True),('delivery',True)]:
        c=copy.deepcopy(rows);r=next(r for r in c if r['case']=='pending');r[field]=value;copies.append(c)
    c=copy.deepcopy(rows);c.pop();copies.append(c)
    c=copy.deepcopy(rows);c[0]['capsule']['input_authority']=True;copies.append(c)
    c=copy.deepcopy(rows);c[0]['raw_bytes']+=1;copies.append(c)
    c=copy.deepcopy(rows);c.append(copy.deepcopy(c[0]));copies.append(c)
    c=copy.deepcopy(rows);c[-1]=copy.deepcopy(c[0]);copies.append(c)
    c=copy.deepcopy(rows);c[-1]['chain'][0]['source']='object-B';copies.append(c)
    c=copy.deepcopy(rows);c[0]['event_bytes']+=1;copies.append(c)
    c=copy.deepcopy(rows);c[0]['capsule']['object_ref']='object-B';copies.append(c)
    c=copy.deepcopy(rows);c[-1]['expected_count']=2;copies.append(c)
    c=copy.deepcopy(rows);c[0]['raw_input_bytes']+=1;copies.append(c)
    for c in copies:
        assert canonical(c)!=canonical(rows)
        rejected=False
        try:check(c)
        except AssertionError:rejected=True
        assert rejected
    return len(copies)
def main():
    raw=Path(sys.argv[1]);rows=[json.loads(s) for s in raw.read_text().splitlines()];result=check(rows)
    result.update(raw_sha256=hashlib.sha256(raw.read_bytes()).hexdigest(),controls_rejected=controls(rows))
    with Path(sys.argv[2]).open('x') as f:json.dump(result,f,indent=2);f.write('\n')
    print(json.dumps(result))
if __name__=='__main__':main()
