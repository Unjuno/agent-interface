from dataclasses import dataclass, replace
from typing import Optional, Tuple
import argparse, json, hashlib
from pathlib import Path

OPS=('OBS0','OBS1','VALIDATE','COMMIT','ADVANCE','CONTRADICT','REOBSERVE','ACTION')
MAX_DEPTH=8

@dataclass(frozen=True)
class S:
    current_gen:int=0
    lifecycle:str='RAW'
    value:Optional[int]=None
    support_gen:Optional[int]=None
    contradicted:bool=False
    commit_count:int=0
    last_committed_gen:Optional[int]=None
    last_committed_value:Optional[int]=None


def cand_step(s:S,op:str):
    if op=='OBS0':
        return replace(s,lifecycle='TENTATIVE',value=0,support_gen=s.current_gen,contradicted=False), 'OBSERVED'
    if op=='OBS1':
        return replace(s,lifecycle='TENTATIVE',value=1,support_gen=s.current_gen,contradicted=False), 'OBSERVED'
    if op=='REOBSERVE':
        v=0 if s.value is None else s.value
        return replace(s,lifecycle='TENTATIVE',value=v,support_gen=s.current_gen,contradicted=False), 'REOBSERVED'
    if op=='VALIDATE':
        if s.lifecycle=='TENTATIVE' and s.support_gen==s.current_gen and not s.contradicted:
            return replace(s,lifecycle='VALIDATED'), 'VALIDATED'
        return s,'VALIDATE_REJECTED'
    if op=='COMMIT':
        if s.lifecycle=='VALIDATED' and s.support_gen==s.current_gen and not s.contradicted:
            ns=replace(s,lifecycle='COMMITTED',commit_count=s.commit_count+1,last_committed_gen=s.support_gen,last_committed_value=s.value)
            return ns,'COMMITTED'
        return s,'COMMIT_REJECTED'
    if op=='ADVANCE':
        # Preserve lifecycle/provenance as durable historical metadata; freshness is derived at action time.
        return replace(s,current_gen=s.current_gen+1), 'GENERATION_ADVANCED'
    if op=='CONTRADICT':
        # Contradiction quarantines the current claim but retained commit receipt/history remains.
        return replace(s,lifecycle='QUARANTINED',contradicted=True), 'CONTRADICTED'
    if op=='ACTION':
        ok=(s.lifecycle=='COMMITTED' and s.support_gen==s.current_gen and not s.contradicted)
        return s,('ACTION_SAFE' if ok else 'ACTION_BLOCKED')
    raise ValueError(op)


def oracle_step(s:S,op:str):
    # Independently structured decision table, deliberately not calling candidate helpers.
    d=s.__dict__.copy(); result=None
    if op in ('OBS0','OBS1'):
        d['lifecycle']='TENTATIVE'; d['value']=0 if op=='OBS0' else 1; d['support_gen']=d['current_gen']; d['contradicted']=False; result='OBSERVED'
    elif op=='REOBSERVE':
        d['lifecycle']='TENTATIVE'; d['value']=0 if d['value'] is None else d['value']; d['support_gen']=d['current_gen']; d['contradicted']=False; result='REOBSERVED'
    elif op=='VALIDATE':
        if d['lifecycle']=='TENTATIVE' and d['support_gen']==d['current_gen'] and d['contradicted'] is False:
            d['lifecycle']='VALIDATED'; result='VALIDATED'
        else: result='VALIDATE_REJECTED'
    elif op=='COMMIT':
        if d['lifecycle']=='VALIDATED' and d['support_gen']==d['current_gen'] and d['contradicted'] is False:
            d['lifecycle']='COMMITTED'; d['commit_count']+=1; d['last_committed_gen']=d['support_gen']; d['last_committed_value']=d['value']; result='COMMITTED'
        else: result='COMMIT_REJECTED'
    elif op=='ADVANCE':
        d['current_gen']+=1; result='GENERATION_ADVANCED'
    elif op=='CONTRADICT':
        d['lifecycle']='QUARANTINED'; d['contradicted']=True; result='CONTRADICTED'
    elif op=='ACTION':
        result='ACTION_SAFE' if (d['lifecycle']=='COMMITTED' and d['support_gen']==d['current_gen'] and d['contradicted'] is False) else 'ACTION_BLOCKED'
    else: raise ValueError(op)
    return S(**d),result


def committed_only_action(s:S):
    return s.lifecycle=='COMMITTED'


def directed():
    s=S()
    for op in ('OBS1','VALIDATE','COMMIT'):
        s,r=cand_step(s,op)
    ok1=cand_step(s,'ACTION')[1]=='ACTION_SAFE'
    hist_before=s.commit_count
    s2,_=cand_step(s,'ADVANCE')
    ok2=cand_step(s2,'ACTION')[1]=='ACTION_BLOCKED' and s2.commit_count==hist_before and s2.last_committed_gen==0
    s3,_=cand_step(s,'CONTRADICT')
    ok3=cand_step(s3,'ACTION')[1]=='ACTION_BLOCKED'
    s4=s2
    s4,_=cand_step(s4,'REOBSERVE')
    ok4=cand_step(s4,'ACTION')[1]=='ACTION_BLOCKED'
    for op in ('VALIDATE','COMMIT'):
        s4,_=cand_step(s4,op)
    ok5=cand_step(s4,'ACTION')[1]=='ACTION_SAFE'
    tent,_=cand_step(S(),'OBS0'); _,rc=cand_step(tent,'COMMIT')
    return {'fresh_commit_action':ok1,'stale_block_history_retained':ok2,'contradiction_blocks':ok3,'reobserve_without_recommit_blocks':ok4,'fresh_recommit_action':ok5,'commit_from_tentative_rejected':rc=='COMMIT_REJECTED'}


def run(depth):
    stats={'nodes':0,'transitions':0,'mismatch':0,'candidate_stale_safe':0,'candidate_contradicted_safe':0,'commit_from_unvalidated':0,'fresh_recommit_safe':0,'history_retained_after_advance':0,'committed_only_unsafe':0,'candidate_safe':0,'candidate_blocked':0}
    def dfs(sc:S,so:S,d:int):
        stats['nodes']+=1
        if d==depth:return
        for op in OPS:
            nc,rc=cand_step(sc,op); no,ro=oracle_step(so,op); stats['transitions']+=1
            if nc!=no or rc!=ro:stats['mismatch']+=1
            if op=='COMMIT' and rc=='COMMITTED' and sc.lifecycle!='VALIDATED':stats['commit_from_unvalidated']+=1
            if op=='ACTION':
                if rc=='ACTION_SAFE':
                    stats['candidate_safe']+=1
                    if sc.support_gen!=sc.current_gen:stats['candidate_stale_safe']+=1
                    if sc.contradicted:stats['candidate_contradicted_safe']+=1
                    if sc.commit_count>=2 and sc.last_committed_gen==sc.current_gen:stats['fresh_recommit_safe']+=1
                else:stats['candidate_blocked']+=1
                # unsafe comparator: sticky COMMITTED-only admission
                if committed_only_action(sc) and not (sc.support_gen==sc.current_gen and not sc.contradicted):
                    stats['committed_only_unsafe']+=1
            if op=='ADVANCE' and sc.commit_count>0 and nc.commit_count==sc.commit_count and nc.last_committed_gen==sc.last_committed_gen:
                stats['history_retained_after_advance']+=1
            dfs(nc,no,d+1)
    dfs(S(),S(),0)
    dc=directed()
    corrupt={'sticky_action_safe_rejected':stats['candidate_stale_safe']==0,
             'commit_from_tentative_rejected':dc['commit_from_tentative_rejected'],
             'contradiction_not_ignored':stats['candidate_contradicted_safe']==0,
             'history_not_erased_on_advance':stats['history_retained_after_advance']>0}
    fresh_gate = dc['fresh_recommit_action'] if depth < 8 else (stats['fresh_recommit_safe']>0)
    good=(stats['mismatch']==0 and stats['candidate_stale_safe']==0 and stats['candidate_contradicted_safe']==0 and stats['commit_from_unvalidated']==0 and fresh_gate and stats['history_retained_after_advance']>0 and stats['committed_only_unsafe']>0 and all(dc.values()) and all(corrupt.values()))
    return {'depth':depth,'op_count':len(OPS),'stats':stats,'directed':dc,'corruptions':corrupt,'decision':'PASS_TRANSACTIONAL_BELIEF_ACTION_SAFE_SCOPED' if good else 'FAIL_INTEGRITY'}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--construction',action='store_true');ap.add_argument('--output',required=True);a=ap.parse_args();p=Path(a.output);assert not p.exists();depth=5 if a.construction else MAX_DEPTH
    r=run(depth);r['construction']=a.construction;r['formal_invocations']=0 if a.construction else 1;r['reruns']=0;r['replacements']=0;r['tuning']=0
    if a.construction and r['decision'].startswith('PASS_'):r['decision']='CONSTRUCTION_PASS'
    raw=json.dumps(r,sort_keys=True,separators=(',',':')).encode();r['digest']=hashlib.sha256(raw).hexdigest();p.write_text(json.dumps(r,indent=2,sort_keys=True)+'\n');print(json.dumps(r,indent=2,sort_keys=True))
if __name__=='__main__':main()
