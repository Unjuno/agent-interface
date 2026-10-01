from dataclasses import dataclass, replace
from collections import defaultdict
from typing import Optional
import argparse, hashlib, json
from pathlib import Path

OPS=(
    'OBSERVE_CURRENT','VALIDATE','COMMIT','PREPARE_ACTION',
    'INVALIDATE','REOBSERVE_CURRENT','TRY_ACTION','CONTRADICT'
)
DEPTH=9

@dataclass(frozen=True)
class State:
    support_generation:int=0
    lifecycle:str='RAW'
    observed_generation:Optional[int]=None
    contradicted:bool=False
    commit_epoch:int=0
    commit_support_generation:Optional[int]=None
    commit_count:int=0
    archived_commits:int=0
    prepared_epoch:Optional[int]=None
    prepared_commit_count:Optional[int]=None


def action_safe(s:State):
    return (
        s.lifecycle=='COMMITTED' and
        s.commit_support_generation==s.support_generation and
        not s.contradicted
    )


def candidate_step(s:State, op:str):
    if op in ('OBSERVE_CURRENT','REOBSERVE_CURRENT'):
        return replace(s,lifecycle='TENTATIVE',observed_generation=s.support_generation,contradicted=False), 'OBSERVED'
    if op=='VALIDATE':
        if s.lifecycle=='TENTATIVE' and s.observed_generation==s.support_generation and not s.contradicted:
            return replace(s,lifecycle='VALIDATED'), 'VALIDATED'
        return s,'VALIDATE_REJECTED'
    if op=='COMMIT':
        if s.lifecycle=='VALIDATED' and s.observed_generation==s.support_generation and not s.contradicted:
            new_epoch=s.commit_epoch+1
            return replace(
                s,lifecycle='COMMITTED',commit_epoch=new_epoch,
                commit_support_generation=s.support_generation,
                commit_count=s.commit_count+1,
                archived_commits=s.archived_commits + (1 if s.commit_count>0 else 0)
            ), 'COMMITTED'
        return s,'COMMIT_REJECTED'
    if op=='PREPARE_ACTION':
        if action_safe(s):
            return replace(s,prepared_epoch=s.commit_epoch,prepared_commit_count=s.commit_count),'PREPARED'
        return s,'PREPARE_REJECTED'
    if op=='INVALIDATE':
        return replace(s,support_generation=s.support_generation+1),'INVALIDATED'
    if op=='CONTRADICT':
        return replace(s,lifecycle='QUARANTINED',contradicted=True),'CONTRADICTED'
    if op=='TRY_ACTION':
        ok=action_safe(s) and s.prepared_epoch is not None and s.prepared_epoch==s.commit_epoch
        return s,('ACTION_ADMITTED' if ok else 'ACTION_BLOCKED')
    raise ValueError(op)


def oracle_step(s:State,op:str):
    d=s.__dict__.copy()
    if op in ('OBSERVE_CURRENT','REOBSERVE_CURRENT'):
        d['lifecycle']='TENTATIVE'; d['observed_generation']=d['support_generation']; d['contradicted']=False; r='OBSERVED'
    elif op=='VALIDATE':
        if d['lifecycle']=='TENTATIVE' and d['observed_generation']==d['support_generation'] and d['contradicted'] is False:
            d['lifecycle']='VALIDATED'; r='VALIDATED'
        else:r='VALIDATE_REJECTED'
    elif op=='COMMIT':
        if d['lifecycle']=='VALIDATED' and d['observed_generation']==d['support_generation'] and d['contradicted'] is False:
            previous=d['commit_count']
            d['commit_epoch']=d['commit_epoch']+1
            d['lifecycle']='COMMITTED'; d['commit_support_generation']=d['support_generation']; d['commit_count']=previous+1
            if previous>0:d['archived_commits']=d['archived_commits']+1
            r='COMMITTED'
        else:r='COMMIT_REJECTED'
    elif op=='PREPARE_ACTION':
        safe=d['lifecycle']=='COMMITTED' and d['commit_support_generation']==d['support_generation'] and d['contradicted'] is False
        if safe:d['prepared_epoch']=d['commit_epoch'];d['prepared_commit_count']=d['commit_count'];r='PREPARED'
        else:r='PREPARE_REJECTED'
    elif op=='INVALIDATE':d['support_generation']+=1;r='INVALIDATED'
    elif op=='CONTRADICT':d['lifecycle']='QUARANTINED';d['contradicted']=True;r='CONTRADICTED'
    elif op=='TRY_ACTION':
        safe=d['lifecycle']=='COMMITTED' and d['commit_support_generation']==d['support_generation'] and d['contradicted'] is False
        r='ACTION_ADMITTED' if safe and d['prepared_epoch'] is not None and d['prepared_epoch']==d['commit_epoch'] else 'ACTION_BLOCKED'
    else:raise ValueError(op)
    return State(**d),r


def reused_id_step(s:State,op:str):
    if op in ('OBSERVE_CURRENT','REOBSERVE_CURRENT'):
        return replace(s,lifecycle='TENTATIVE',observed_generation=s.support_generation,contradicted=False),'OBSERVED'
    if op=='VALIDATE':
        return (replace(s,lifecycle='VALIDATED'),'VALIDATED') if s.lifecycle=='TENTATIVE' and s.observed_generation==s.support_generation and not s.contradicted else (s,'VALIDATE_REJECTED')
    if op=='COMMIT':
        if s.lifecycle=='VALIDATED' and s.observed_generation==s.support_generation and not s.contradicted:
            stable=1
            return replace(s,lifecycle='COMMITTED',commit_epoch=stable,commit_support_generation=s.support_generation,commit_count=s.commit_count+1,archived_commits=s.archived_commits+(1 if s.commit_count>0 else 0)),'COMMITTED'
        return s,'COMMIT_REJECTED'
    if op=='PREPARE_ACTION':
        if action_safe(s):return replace(s,prepared_epoch=s.commit_epoch,prepared_commit_count=s.commit_count),'PREPARED'
        return s,'PREPARE_REJECTED'
    if op=='INVALIDATE':return replace(s,support_generation=s.support_generation+1),'INVALIDATED'
    if op=='CONTRADICT':return replace(s,lifecycle='QUARANTINED',contradicted=True),'CONTRADICTED'
    if op=='TRY_ACTION':
        ok=action_safe(s) and s.prepared_epoch is not None and s.prepared_epoch==s.commit_epoch
        return s,('ACTION_ADMITTED' if ok else 'ACTION_BLOCKED')
    raise ValueError(op)


def directed():
    s=State()
    for op in ('OBSERVE_CURRENT','VALIDATE','COMMIT','PREPARE_ACTION'):
        s,_=candidate_step(s,op)
    normal=candidate_step(s,'TRY_ACTION')[1]=='ACTION_ADMITTED'
    old_epoch=s.prepared_epoch
    for op in ('INVALIDATE','REOBSERVE_CURRENT','VALIDATE','COMMIT'):
        s,_=candidate_step(s,op)
    stale_block=(s.commit_epoch==2 and old_epoch==1 and candidate_step(s,'TRY_ACTION')[1]=='ACTION_BLOCKED')
    s,_=candidate_step(s,'PREPARE_ACTION')
    fresh_accept=(s.prepared_epoch==2 and candidate_step(s,'TRY_ACTION')[1]=='ACTION_ADMITTED')
    contrad,_=candidate_step(s,'CONTRADICT')
    contradiction_block=candidate_step(contrad,'TRY_ACTION')[1]=='ACTION_BLOCKED'
    c=State()
    for op in ('OBSERVE_CURRENT','VALIDATE','COMMIT','PREPARE_ACTION','INVALIDATE','REOBSERVE_CURRENT','VALIDATE','COMMIT'):
        c,_=reused_id_step(c,op)
    comparator_aba=(c.commit_count==2 and c.prepared_epoch==1 and c.commit_epoch==1 and reused_id_step(c,'TRY_ACTION')[1]=='ACTION_ADMITTED')
    return {'normal_action':normal,'stale_old_epoch_blocked':stale_block,'fresh_epoch_accepted':fresh_accept,'contradiction_blocks':contradiction_block,'reused_id_exposes_aba':comparator_aba}


def run(depth):
    init=(State(),State(),State())
    current={init:1}
    st={'depth':depth,'trace_prefix_nodes':1,'transitions':0,'mismatch':0,'old_epoch_action_admissions':0,'stale_or_contradicted_action_admissions':0,'fresh_current_action_admissions':0,'successful_commits':0,'nonincreasing_successful_commit_epochs':0,'archived_old_commit_witnesses':0,'reused_id_aba_admissions':0,'replayed_old_receipt_attempts_after_recommit':0}
    for _level in range(depth):
        nxt=defaultdict(int)
        for (sc,so,sr),mult in current.items():
            for op in OPS:
                nc,rc=candidate_step(sc,op); no,ro=oracle_step(so,op); nr,rr=reused_id_step(sr,op)
                st['transitions']+=mult
                if nc!=no or rc!=ro:st['mismatch']+=mult
                if op=='COMMIT' and rc=='COMMITTED':
                    st['successful_commits']+=mult
                    if nc.commit_epoch<=sc.commit_epoch:st['nonincreasing_successful_commit_epochs']+=mult
                    if nc.archived_commits>sc.archived_commits:st['archived_old_commit_witnesses']+=mult
                if op=='TRY_ACTION':
                    if sc.prepared_commit_count is not None and sc.prepared_commit_count<sc.commit_count:
                        st['replayed_old_receipt_attempts_after_recommit']+=mult
                        if rc=='ACTION_ADMITTED':st['old_epoch_action_admissions']+=mult
                    if rc=='ACTION_ADMITTED':
                        if not action_safe(sc):st['stale_or_contradicted_action_admissions']+=mult
                        if sc.prepared_epoch==sc.commit_epoch and action_safe(sc):st['fresh_current_action_admissions']+=mult
                    if rr=='ACTION_ADMITTED' and sr.prepared_commit_count is not None and sr.prepared_commit_count<sr.commit_count:
                        st['reused_id_aba_admissions']+=mult
                nxt[(nc,no,nr)]+=mult
        st['trace_prefix_nodes']+=sum(nxt.values())
        current=nxt
    return st


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--construction',action='store_true');ap.add_argument('--output',required=True);a=ap.parse_args();p=Path(a.output);assert not p.exists()
    depth=7 if a.construction else DEPTH
    st=run(depth);dc=directed()
    corrupt={'reuse_epoch_detected':dc['reused_id_exposes_aba'],'stale_prepared_epoch_rejected':dc['stale_old_epoch_blocked'],'fresh_epoch_not_overinvalidated':dc['fresh_epoch_accepted'],'archive_preserved':st['archived_old_commit_witnesses']>0 if depth>=7 else True}
    formal_extra=True if a.construction else (st['replayed_old_receipt_attempts_after_recommit']>0 and st['reused_id_aba_admissions']>0)
    good=(st['mismatch']==0 and st['old_epoch_action_admissions']==0 and st['stale_or_contradicted_action_admissions']==0 and st['fresh_current_action_admissions']>0 and st['nonincreasing_successful_commit_epochs']==0 and st['archived_old_commit_witnesses']>0 and formal_extra and all(dc.values()) and all(corrupt.values()))
    r={'construction':a.construction,'stats':st,'directed':dc,'corruptions':corrupt,'formal_invocations':0 if a.construction else 1,'reruns':0,'replacements':0,'tuning':0,'decision':('CONSTRUCTION_PASS' if a.construction and good else ('PASS_BELIEF_RECOMMIT_EPOCH_ABA_SCOPED' if good else 'FAIL_INTEGRITY'))}
    raw=json.dumps(r,sort_keys=True,separators=(',',':')).encode();r['digest']=hashlib.sha256(raw).hexdigest();p.write_text(json.dumps(r,indent=2,sort_keys=True)+'\n');print(json.dumps(r,indent=2,sort_keys=True))
if __name__=='__main__':main()
