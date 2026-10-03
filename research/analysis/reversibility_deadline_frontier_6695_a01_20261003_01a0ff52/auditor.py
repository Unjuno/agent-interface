"""Raw-only algebraic oracle: imports neither simulator nor predecessor code."""
import argparse,collections,hashlib,json,pathlib
ARMS=('IMMEDIATE','WAIT_THEN_PREPARE','STAGE_THEN_CORRECT')
def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':'))
def derive(c,arm):
    p,s,e,d=(c[k] for k in ('prep_ms','signal_ms','edit_ms','deadline_ms'))
    sig=c['signal']; target=sig if arm=='WAIT_THEN_PREPARE' and sig!='UNKNOWN' else 'A'
    start=s if arm=='WAIT_THEN_PREPARE' else 0
    finish=start+p; edited=arm=='STAGE_THEN_CORRECT' and sig=='B' and c['correction_route']
    ready=(max(p,s)+e*edited+1) if arm=='STAGE_THEN_CORRECT' else finish+1
    if edited:target='B'
    ev=[]
    if arm=='WAIT_THEN_PREPARE':ev.append(dict(at_ms=s,event='observe',value=sig))
    prep_target=sig if arm=='WAIT_THEN_PREPARE' and sig!='UNKNOWN' else 'A'
    ev.extend([dict(at_ms=start,event='prepare_start',target=prep_target),dict(at_ms=finish,event='prepare_done',target=prep_target)])
    if arm=='STAGE_THEN_CORRECT':
        ev.append(dict(at_ms=s,event='observe',value=sig))
        if edited:ev.extend([dict(at_ms=max(p,s),event='edit_start',target='B'),dict(at_ms=max(p,s)+e,event='edit_done',target='B')])
    ev.append(dict(at_ms=ready if ready<=d else d,event='commit' if ready<=d else 'deadline_refusal',target=target))
    return dict(id=c['id'],policy=arm,ready_ms=ready,target=target,committed=ready<=d,events=sorted(ev,key=lambda x:x['at_ms']))
def audit(cases,truth,rows):
    expected={(c['id'],a):derive(c,a) for c in cases for a in ARMS}
    errors=[];seen=set();counts={a:collections.Counter() for a in ARMS}; lookup={}
    for i,row in enumerate(rows):
        key=(row.get('id'),row.get('policy'))
        if key in seen:errors.append(f'duplicate:{i}')
        seen.add(key)
        if key not in expected or canonical(row)!=canonical(expected[key]):errors.append(f'reconstruction:{i}');continue
        lookup[key]=row; n=counts[key[1]];n['rows']+=1
        n['deadline_refusal']+=not row['committed']
        n['correct_commit']+=row['committed'] and row['target']==truth[key[0]]
        n['wrong_commit']+=row['committed'] and row['target']!=truth[key[0]]
    if seen!=set(expected):errors.append('denominator')
    diagnostics=collections.Counter()
    if not errors:
        for c in cases:
            w=lookup[(c['id'],ARMS[1])];st=lookup[(c['id'],ARMS[2])]
            # The exact incremental preparation-cost discriminator, only on informative correctable B.
            if c['signal']=='B' and c['correction_route']:
                sign=(st['ready_ms']>w['ready_ms'])-(st['ready_ms']<w['ready_ms'])
                delta=c['edit_ms']-min(c['prep_ms'],c['signal_ms'])
                if sign!=(delta>0)-(delta<0):errors.append('frontier')
                if st['committed'] and not w['committed']:diagnostics['stage_only_correct_on_time']+=1
                if w['committed'] and not st['committed']:diagnostics['wait_only_correct_on_time']+=1
                if c['deadline_ms']==st['ready_ms']:diagnostics['stage_equality_admits']+=1
                if c['deadline_ms']==st['ready_ms']-1:diagnostics['stage_one_ms_short_refuses']+=1
            if c['signal']=='UNKNOWN' and st['target']!=w['target']:errors.append('uninformative_target_change')
            if not c['correction_route'] and st['target']!='A':errors.append('unavailable_correction')
    gates={'exact_reconstruction':not errors,'stage_advantage_witness':diagnostics['stage_only_correct_on_time']>0,'stage_disadvantage_witness':diagnostics['wait_only_correct_on_time']>0,'equality_and_short_controls':diagnostics['stage_equality_admits']>0 and diagnostics['stage_one_ms_short_refuses']>0}
    return dict(result='PASS_METHOD_SCOPED' if all(gates.values()) else 'FAIL_METHOD',errors=errors,rows=len(rows),counts={k:dict(v) for k,v in counts.items()},diagnostics=dict(diagnostics),gates=gates)
def main():
    ap=argparse.ArgumentParser();ap.add_argument('fixtures');ap.add_argument('truth');ap.add_argument('raw');ap.add_argument('output');a=ap.parse_args()
    raw=pathlib.Path(a.raw).read_bytes();rows=[json.loads(x) for x in raw.splitlines()]
    result=audit(json.loads(pathlib.Path(a.fixtures).read_text()),json.loads(pathlib.Path(a.truth).read_text()),rows)
    result['raw_sha256']=hashlib.sha256(raw).hexdigest()
    pathlib.Path(a.output).open('x').write(json.dumps(result,sort_keys=True,indent=2)+'\n');print(result['result'],result['rows'],len(result['errors']))
    raise SystemExit(0 if result['result']=='PASS_METHOD_SCOPED' else 2)
if __name__=='__main__':main()
