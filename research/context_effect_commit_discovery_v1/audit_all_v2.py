"""Independent cross-run semantic audit. Does not import experiment modules."""
import json,sys,hashlib,collections,copy,shutil,tempfile
from pathlib import Path

def sha(b): return hashlib.sha256(b).hexdigest()
def loadj(p): return json.loads(p.read_text())
def rows(root): return [json.loads(x) for x in (root/'raw.jsonl').read_text().splitlines() if x.strip()]
def verify_manifest(root):
    m=loadj(root/'manifest.json')
    for n,h in m.items():
        if sha((root/n).read_bytes())!=h: raise AssertionError(('hash',root.name,n))
def effect_obj(root,r): return loadj(root/r['effect_file']) if r.get('effect_file') else None
def reject_obj(root,r): return loadj(root/r['reject_file']) if r.get('reject_file') else None
def correct_effect(e, key='before'):
    b=e[key]; a=b['active']; d=b['docs'][a]
    return a=='A' and d['revision']==0 and d['value']==0

def common(root,r):
    if not all(r['checks'].values()): raise AssertionError(('mechanics',root.name,r['id']))
    if r.get('precheck') is False: raise AssertionError(('precheck_false',root.name,r['id']))
    ev=r['input_events']
    if len(ev)!=2 or ev[0]['kind']!='press' or ev[1]['kind']!='release': raise AssertionError(('input',root.name,r['id']))
    if ev[0]['ns']>ev[1]['ns']: raise AssertionError(('input_order',root.name,r['id']))

def audit_r1(root):
    safe={'stable','unrelated_B_edit_after_precheck','ABA_unchanged_after_precheck'}; out=collections.Counter()
    rs=rows(root); assert len(rs)==240
    for r in rs:
        common(root,r); e=effect_obj(root,r); q=reject_obj(root,r); assert (e is not None)+(q is not None)==1
        if r['mode']=='client_precheck':
            if not e: raise AssertionError(('blind_reject',r['id']))
            c=correct_effect(e); expected=r['case'] in safe
            if c!=expected: raise AssertionError(('blind_class',r['id'],c,expected))
        elif r['mode']=='effect_cas':
            if r['case'] in safe:
                if not e or not correct_effect(e): raise AssertionError(('cas_false_reject_or_wrong',r['id']))
            else:
                if not q: raise AssertionError(('cas_unsafe_accept',r['id']))
        else: raise AssertionError(('mode',r['id']))
        out[(r['mode'],r['case'],'effect' if e else 'reject','correct' if e and correct_effect(e) else 'wrong_or_na')]+=1
    return out

def audit_r2(root):
    safe={'stable','unrelated_B_edit_after_precheck','ABA_unchanged_after_precheck'}; rs=rows(root); assert len(rs)==240; out=collections.Counter()
    for r in rs:
        common(root,r); e=effect_obj(root,r);q=reject_obj(root,r);assert (e is not None)+(q is not None)==1
        if r['mode']=='effect_cas_relevant': expected_effect=r['case'] in safe
        elif r['mode']=='effect_cas_global': expected_effect=r['case']=='stable'
        else: raise AssertionError(('mode',r['id']))
        if expected_effect:
            if not e or not correct_effect(e): raise AssertionError(('false_reject_or_wrong',r['id']))
        elif not q: raise AssertionError(('unsafe_or_overbroad_accept',r['id']))
        out[(r['mode'],r['case'],'effect' if e else 'reject')]+=1
    return out

def audit_r3(root):
    rs=rows(root); assert len(rs)==180; out=collections.Counter()
    for r in rs:
        common(root,r);e=effect_obj(root,r);q=reject_obj(root,r)
        if not e or q: raise AssertionError(('terminal',r['id']))
        c=correct_effect(e,'before_write')
        if r['case']=='stable':
            if not c or r['transitions']: raise AssertionError(('stable',r['id']))
        else:
            if len(r['transitions'])!=1: raise AssertionError(('transition_count',r['id']))
            t=r['transitions'][0]['ns']; mut=e['mutated_ns']; chk=e['check'][1]
            if chk>min(t,mut): raise AssertionError(('check_order',r['id']))
            if r['mode']=='effect_atomic':
                if not c or not mut<=t: raise AssertionError(('atomic',r['id'],c,mut,t))
            elif r['mode']=='effect_nonatomic':
                if c or not t<=mut: raise AssertionError(('nonatomic',r['id'],c,t,mut))
            else: raise AssertionError(('mode',r['id']))
        out[(r['mode'],r['case'],'correct' if c else 'wrong')]+=1
    return out

def audit_r4(root):
    rs=rows(root); assert len(rs)==180; out=collections.Counter()
    for r in rs:
        common(root,r);e=effect_obj(root,r);q=reject_obj(root,r);assert (e is not None)+(q is not None)==1
        if r['case']=='stable':
            if not e or not correct_effect(e): raise AssertionError(('stable',r['id']))
        elif r['mode']=='plan_bound_token':
            if not q: raise AssertionError(('plan_bound_accept',r['id']))
        elif r['mode']=='refreshed_token':
            if not e or correct_effect(e): raise AssertionError(('refreshed_not_wrong',r['id']))
        else: raise AssertionError(('mode',r['id']))
        out[(r['mode'],r['case'],'effect' if e else 'reject','correct' if e and correct_effect(e) else 'wrong_or_na')]+=1
    return out

def paired_frames(root):
    by=collections.defaultdict(list)
    for r in rows(root): by[r['ordinal']].append(r)
    for ordinal,pair in by.items():
        if len(pair)!=2: raise AssertionError(('pair_count',root.name,ordinal))
        if pair[0]['case']!=pair[1]['case'] or pair[0]['frames']!=pair[1]['frames'] or pair[0]['bound']['parsed']!=pair[1]['bound']['parsed'] or pair[0]['current']['parsed']!=pair[1]['current']['parsed']:
            raise AssertionError(('pair_inputs',root.name,ordinal))

def main(base):
    base=Path(base); specs=[('run-a1',audit_r1),('run-r2-a1',audit_r2),('run-r3-a1',audit_r3),('run-r4-a1',audit_r4)]; result={'runs':{},'total_rows':0}
    for name,fn in specs:
        root=base/name;verify_manifest(root);paired_frames(root);counts=fn(root);n=len(rows(root));result['total_rows']+=n;result['runs'][name]={'rows':n,'counts':{'|'.join(map(str,k)):v for k,v in counts.items()}}
    if result['total_rows']!=840: raise AssertionError(result['total_rows'])
    (base/'audit_all_v2_result.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n');print(json.dumps({'passed':True,'total_rows':840,'run_rows':{k:v['rows'] for k,v in result['runs'].items()}},indent=2))
if __name__=='__main__': main(sys.argv[1])
