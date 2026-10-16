from __future__ import annotations
import argparse,copy,json,sys
from pathlib import Path
SAT='SATISFIED'; EXP='EXPIRED'; UG='UNKNOWN_GENERATION'
EXPECTED={'SAME_PROCESS_AB':SAT,'RECONNECT_CROSS_B':UG,'RECONNECT_CROSS_AB':UG,'FRESH_AFTER_RECONNECT':SAT,'MISSING_GENERATION_B':UG,'LATE_SAME_PROCESS_B':EXP}

def reconstruct(r,bound):
    rows=r['rows']; anchor=None; gen=None; last=None
    for x in rows:
        g=x.get('generation'); seq=x.get('seq'); t=x.get('source_ns'); lab=x.get('label')
        if g is None or not isinstance(g,str) or not g: return UG
        if not isinstance(seq,int) or isinstance(seq,bool) or not isinstance(t,int) or isinstance(t,bool): return 'UNKNOWN_ORDER'
        if gen is None:
            if lab=='A': anchor=t; gen=g; last=seq
            continue
        if g!=gen: return UG
        if seq!=last+1: return 'UNKNOWN_ORDER'
        last=seq
        if t<anchor:return 'UNKNOWN_ORDER'
        if lab=='B': return SAT if t-anchor<=bound else EXP
    return 'PENDING'

def check(data):
    errs=[]; expected_n=6 if data['mode']=='construction' else 18
    if len(data['rows'])!=expected_n: errs.append('row_count')
    for i,r in enumerate(data['rows']):
        sc=r['scenario'];
        if r['candidate']!=EXPECTED[sc]: errs.append(f'candidate:{i}')
        if reconstruct(r,data['bound_ns'])!=r['candidate']: errs.append(f'reconstruct:{i}')
        if not r['all_exits_zero'] or any(p['returncode']!=0 for p in r['parts']): errs.append(f'exit:{i}')
        if len(set(r['pids'])) != (1 if sc in {'SAME_PROCESS_AB','LATE_SAME_PROCESS_B'} else 2): errs.append(f'pid_count:{i}')
        if sc in {'RECONNECT_CROSS_B','RECONNECT_CROSS_AB','MISSING_GENERATION_B'} and r['unsafe']!='SATISFIED': errs.append(f'unsafe_discriminator:{i}')
        if sc=='RECONNECT_CROSS_B' and len(r['parts'])==2 and r['parts'][0]['rows'][0]['generation']==r['parts'][1]['rows'][0]['generation']: errs.append(f'gen_not_changed:{i}')
    return errs

def controls(data):
    muts=[]
    def add(name,fn):
        x=copy.deepcopy(data); fn(x); muts.append((name,bool(check(x))))
    add('drop_row',lambda x:x['rows'].pop())
    add('candidate_flip',lambda x:x['rows'][0].__setitem__('candidate','EXPIRED'))
    add('generation',lambda x:x['rows'][1]['rows'][1].__setitem__('generation',x['rows'][1]['rows'][0]['generation']))
    add('seq',lambda x:x['rows'][0]['rows'][1].__setitem__('seq',7))
    add('timestamp',lambda x: next(r for r in x['rows'] if r['scenario']=='LATE_SAME_PROCESS_B')['rows'][1].__setitem__('source_ns', next(r for r in x['rows'] if r['scenario']=='LATE_SAME_PROCESS_B')['rows'][0]['source_ns']))
    add('exit',lambda x:x['rows'][0]['parts'][0].__setitem__('returncode',9))
    add('pid',lambda x:x['rows'][1].__setitem__('pids',[1,1]))
    add('scenario',lambda x:x['rows'][0].__setitem__('scenario','RECONNECT_CROSS_B'))
    return [{'name':n,'rejected':v} for n,v in muts]

def main():
    p=argparse.ArgumentParser();p.add_argument('raw');p.add_argument('--controls',action='store_true');a=p.parse_args();d=json.loads(Path(a.raw).read_text()); e=check(d); o={'errors':e}
    if a.controls:
        c=controls(d);o['controls']=c;o['controls_rejected']=sum(x['rejected'] for x in c)
    print(json.dumps(o,sort_keys=True)); raise SystemExit(1 if e else 0)
if __name__=='__main__':main()
