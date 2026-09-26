"""Independent raw-only audit: enumerate 2D half-plane boundary intersections.

Does not import clock_bounds, corpus, run_check, or any GUI/runtime module.
"""
from __future__ import annotations
import argparse,json,hashlib
from fractions import Fraction
from itertools import combinations
from functools import lru_cache
from pathlib import Path

class EvidenceError(ValueError):
    pass

def number(v):
    if type(v) is not str or not 1 <= len(v) <= 128:
        raise EvidenceError('rational_string_required')
    try:
        x=Fraction(v)
    except (ValueError,ZeroDivisionError):
        raise EvidenceError('rational_string_required') from None
    if str(x)!=v:raise EvidenceError('noncanonical_rational')
    return x

def interval(v):
    if type(v) is not list or len(v)!=2:raise EvidenceError('pair_required')
    return tuple(number(x) for x in v)

def decode(d):
    if type(d) is not dict:raise EvidenceError('object_required')
    if d.get('scope')!=d.get('expected_scope'):raise EvidenceError('scope_mismatch')
    scope=d.get('scope')
    if type(scope) is not dict or set(scope)!={'from','to','epoch'} or any(type(x) is not str or not x for x in scope.values()):
        raise EvidenceError('invalid_scope')
    for k in ('rate','offset','valid_s','release','deadline','samples'):
        if k not in d:raise EvidenceError('missing_'+k)
    a=interval(d['rate']);b=interval(d['offset']);h=interval(d['valid_s']);r=interval(d['release']);deadline=number(d['deadline'])
    if a[0]<=0 or a[0]>a[1]:raise EvidenceError('invalid_positive_rate')
    if b[0]>b[1] or h[0]>h[1]:raise EvidenceError('invalid_bound')
    if r[0]>=r[1]:raise EvidenceError('empty_or_reversed_release')
    if r[0]<h[0] or r[1]>h[1]:raise EvidenceError('outside_clock_horizon')
    if type(d['samples']) is not list or not 1<=len(d['samples'])<=32:
        raise EvidenceError('calibration_missing_or_excessive')
    samples=[]
    for q in d['samples']:
        if type(q) is not dict or set(q)!={'s','lo','hi'}:raise EvidenceError('invalid_sample')
        s,lo,hi=number(q['s']),number(q['lo']),number(q['hi'])
        if not h[0]<=s<=h[1] or lo>hi:raise EvidenceError('invalid_sample_bound')
        samples.append((s,lo,hi))
    return a,b,tuple(samples),r,deadline

@lru_cache(maxsize=4096)
def polygon(a,b,samples):
    # A*x+B*y <= C; unlike the candidate this never eliminates an axis.
    halfplanes=[(1,0,a[1]),(-1,0,-a[0]),(0,1,b[1]),(0,-1,-b[0])]
    for s,lo,hi in samples:halfplanes += [(s,1,hi),(-s,-1,-lo)]
    vertices=set()
    for (A,B,C),(D,E,G) in combinations(halfplanes,2):
        det=A*E-B*D
        if det==0:continue
        x=Fraction(C*E-B*G,det);y=Fraction(A*G-C*D,det)
        if all(p*x+q*y<=z for p,q,z in halfplanes):vertices.add((x,y))
    return tuple(sorted(vertices)),tuple(halfplanes)

def label(low,high,deadline):
    if high<=deadline:return 'ON_TIME'
    if deadline<=low:return 'LATE'
    return 'UNRESOLVED'

def audit(root:Path, data:Path):
    errors=[];checks=0
    stats={'rows':0,'feasible_rows':0,'inconsistent_rows':0,'invalid_rows':0,
           'nominal_false_ontime':0,'nominal_false_late':0,'marginal_unresolved_but_exact_decisive':0,
           'candidate_status_counts':{},'directed':{}}
    def check(ok, message):
        nonlocal checks
        checks+=1
        if not ok:errors.append(message)
    try:
        freeze=json.loads((root/'FREEZE.json').read_text())
        for name,h in freeze['files'].items():
            check(hashlib.sha256((root/name).read_bytes()).hexdigest()==h,'source:'+name)
        expected=[json.loads(x) for x in (root/'INPUTS.jsonl').read_text().splitlines()]
        rows=[json.loads(x) for x in (data/'raw.jsonl').read_text().splitlines()]
        runner=json.loads((data/'runner.json').read_text())
        launcher=json.loads((data/'launcher.json').read_text())
        check(len(rows)==len(expected)==9088,'denominator')
        check(runner['rows']==9088 and runner['expected']==9088,'runner_denominator')
        check(runner['allocation']==freeze['allocation'],'allocation')
        check(launcher['exit_code']==0 and launcher['timed_out'] is False,'actual_exit')
        check(launcher['started_ns']<=runner['started_ns']<=runner['ended_ns']<=launcher['ended_ns'],'process_clock')
        check(runner['gui_model_input_calls']==0,'no_actuation')
        check(len({x['id'] for x in rows})==len(rows),'unique_ids')
        for idx,(e,row) in enumerate(zip(expected,rows)):
            tag=str(idx)
            check(row['id']==e['id'] and row['input']==e['input'],tag+':input_order')
            out=row['output'];stats['rows']+=1
            check(out.get('grants_input_authority') is False and out.get('task_success','missing') is None,tag+':no_authority')
            try: a,b,samples,r,deadline=decode(row['input'])
            except EvidenceError as err:
                stats['invalid_rows']+=1
                check(out=={'grants_input_authority':False,'task_success':None,'status':'UNKNOWN_INVALID','reason':str(err)},tag+':invalid')
                continue
            vertices,planes=polygon(a,b,samples)
            if not vertices:
                stats['inconsistent_rows']+=1
                check(out=={'grants_input_authority':False,'task_success':None,'status':'UNKNOWN_INCONSISTENT','reason':'empty_clock_set'},tag+':inconsistent')
                continue
            stats['feasible_rows']+=1
            low=min(x*r[0]+y for x,y in vertices);high=max(x*r[1]+y for x,y in vertices)
            decision=label(low,high,deadline)
            stats['candidate_status_counts'][decision]=stats['candidate_status_counts'].get(decision,0)+1
            check(out['status']==decision,tag+':status')
            check(interval(out['interval'])==(low,high),tag+':exact_projection')
            check(out['lower_open'] is True and out['upper_closed'] is True,tag+':endpoint_types')
            xa=min(x for x,y in vertices);xb=max(x for x,y in vertices)
            check(interval(out['feasible_rate'])==(xa,xb),tag+':rate_projection')
            for side,s,value in (('lower',r[0],low),('upper',r[1],high)):
                x,y=interval(out['extremizers'][side])
                check(all(A*x+B*y<=C for A,B,C in planes),tag+':feasible_'+side)
                check(x*s+y==value,tag+':witness_'+side)
            # Bounding box formed by marginal coordinate extrema is conservative.
            blo=min(y for x,y in vertices);bhi=max(y for x,y in vertices)
            ml=min(xa*r[0],xb*r[0])+blo;mh=max(xa*r[1],xb*r[1])+bhi
            check(interval(out['marginal']['interval'])==(ml,mh),tag+':marginal_interval')
            check(out['marginal']['status']==label(ml,mh,deadline),tag+':marginal_status')
            check(ml<=low<high<=mh,tag+':marginal_encloses')
            if label(ml,mh,deadline)=='UNRESOLVED' and decision!='UNRESOLVED':
                stats['marginal_unresolved_but_exact_decisive']+=1
            # Defined nominal feasible section, calculated from half-planes.
            nx=(xa+xb)/2
            lower_y=[(C-A*nx)/B for A,B,C in planes if B<0]
            upper_y=[(C-A*nx)/B for A,B,C in planes if B>0]
            ny=(max(lower_y)+min(upper_y))/2
            nl,nh=nx*r[0]+ny,nx*r[1]+ny
            check(interval(out['nominal']['clock'])==(nx,ny),tag+':nominal_clock')
            check(interval(out['nominal']['interval'])==(nl,nh),tag+':nominal_interval')
            check(out['nominal']['status']==label(nl,nh,deadline),tag+':nominal_status')
            if label(nl,nh,deadline)=='ON_TIME' and high>deadline:stats['nominal_false_ontime']+=1
            if label(nl,nh,deadline)=='LATE' and low<deadline:stats['nominal_false_late']+=1
            if row['id'].startswith('direct-'):
                stats['directed'][row['id']]={'interval':list(map(str,(low,high))), 'status':decision,
                    'nominal_status':label(nl,nh,deadline),'marginal_status':label(ml,mh,deadline)}
        check(stats['nominal_false_ontime']>0,'positive_nominal_counterexample')
        check(stats['nominal_false_late']>0,'negative_nominal_counterexample')
        check(stats['marginal_unresolved_but_exact_decisive']>0,'nontrivial_correlation')
    except (OSError,ValueError,KeyError,TypeError,IndexError,ZeroDivisionError) as exc:
        errors.append('EVIDENCE_UNREADABLE:'+type(exc).__name__+':'+str(exc))
    return {'decision':'PASS_LOCAL_AFFINE_CLOCK_CONTRACT' if not errors else 'HOLD_AUDIT_OR_INTEGRITY',
            'checks':checks,'errors':errors,'statistics':stats,
            'physical_clock_calibration_performed':False,'independent_human_review':False}

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('data');args=ap.parse_args()
    result=audit(Path(__file__).resolve().parent.parent,Path(args.data))
    print(json.dumps(result,indent=2,sort_keys=True));raise SystemExit(bool(result['errors']))
