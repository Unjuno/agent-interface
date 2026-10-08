from collections import defaultdict
import argparse,hashlib,json
from pathlib import Path
OPS=('OBSERVE_CURRENT','VALIDATE','COMMIT','PREPARE_ACTION','INVALIDATE','REOBSERVE_CURRENT','TRY_ACTION','CONTRADICT')
DEPTH=9
INIT=(0,'RAW',None,False,0,None,0,0,None,None)
def safe(s):
    g,life,og,con,ce,cg,cc,arch,pe,pc=s
    return life=='COMMITTED' and cg==g and not con
def fresh_step(s,op):
    g,life,og,con,ce,cg,cc,arch,pe,pc=s
    if op in ('OBSERVE_CURRENT','REOBSERVE_CURRENT'):return (g,'TENTATIVE',g,False,ce,cg,cc,arch,pe,pc),'OBSERVED'
    if op=='VALIDATE':return ((g,'VALIDATED',og,con,ce,cg,cc,arch,pe,pc),'VALIDATED') if life=='TENTATIVE' and og==g and not con else (s,'VALIDATE_REJECTED')
    if op=='COMMIT':
        if life=='VALIDATED' and og==g and not con:return (g,'COMMITTED',og,con,ce+1,g,cc+1,arch+(1 if cc>0 else 0),pe,pc),'COMMITTED'
        return s,'COMMIT_REJECTED'
    if op=='PREPARE_ACTION':return ((g,life,og,con,ce,cg,cc,arch,ce,cc),'PREPARED') if safe(s) else (s,'PREPARE_REJECTED')
    if op=='INVALIDATE':return (g+1,life,og,con,ce,cg,cc,arch,pe,pc),'INVALIDATED'
    if op=='CONTRADICT':return (g,'QUARANTINED',og,True,ce,cg,cc,arch,pe,pc),'CONTRADICTED'
    if op=='TRY_ACTION':return s,('ACTION_ADMITTED' if safe(s) and pe is not None and pe==ce else 'ACTION_BLOCKED')
    raise ValueError(op)
def reused_step(s,op):
    g,life,og,con,ce,cg,cc,arch,pe,pc=s
    if op in ('OBSERVE_CURRENT','REOBSERVE_CURRENT'):return (g,'TENTATIVE',g,False,ce,cg,cc,arch,pe,pc),'OBSERVED'
    if op=='VALIDATE':return ((g,'VALIDATED',og,con,ce,cg,cc,arch,pe,pc),'VALIDATED') if life=='TENTATIVE' and og==g and not con else (s,'VALIDATE_REJECTED')
    if op=='COMMIT':
        if life=='VALIDATED' and og==g and not con:return (g,'COMMITTED',og,con,1,g,cc+1,arch+(1 if cc>0 else 0),pe,pc),'COMMITTED'
        return s,'COMMIT_REJECTED'
    if op=='PREPARE_ACTION':return ((g,life,og,con,ce,cg,cc,arch,ce,cc),'PREPARED') if safe(s) else (s,'PREPARE_REJECTED')
    if op=='INVALIDATE':return (g+1,life,og,con,ce,cg,cc,arch,pe,pc),'INVALIDATED'
    if op=='CONTRADICT':return (g,'QUARANTINED',og,True,ce,cg,cc,arch,pe,pc),'CONTRADICTED'
    if op=='TRY_ACTION':return s,('ACTION_ADMITTED' if safe(s) and pe is not None and pe==ce else 'ACTION_BLOCKED')
    raise ValueError(op)
def dp():
    current={(INIT,INIT):1}
    st={'depth':DEPTH,'trace_prefix_nodes':1,'transitions':0,'mismatch':0,'old_epoch_action_admissions':0,'stale_or_contradicted_action_admissions':0,'fresh_current_action_admissions':0,'successful_commits':0,'nonincreasing_successful_commit_epochs':0,'archived_old_commit_witnesses':0,'reused_id_aba_admissions':0,'replayed_old_receipt_attempts_after_recommit':0}
    for _ in range(DEPTH):
        nxt=defaultdict(int)
        for (sf,sr),mult in current.items():
            for op in OPS:
                nf,rf=fresh_step(sf,op);nr,rr=reused_step(sr,op);st['transitions']+=mult
                if op=='COMMIT' and rf=='COMMITTED':
                    st['successful_commits']+=mult
                    if nf[4]<=sf[4]:st['nonincreasing_successful_commit_epochs']+=mult
                    if nf[7]>sf[7]:st['archived_old_commit_witnesses']+=mult
                if op=='TRY_ACTION':
                    if sf[9] is not None and sf[9]<sf[6]:
                        st['replayed_old_receipt_attempts_after_recommit']+=mult
                        if rf=='ACTION_ADMITTED':st['old_epoch_action_admissions']+=mult
                    if rf=='ACTION_ADMITTED':
                        if not safe(sf):st['stale_or_contradicted_action_admissions']+=mult
                        if sf[8]==sf[4] and safe(sf):st['fresh_current_action_admissions']+=mult
                    if rr=='ACTION_ADMITTED' and sr[9] is not None and sr[9]<sr[6]:st['reused_id_aba_admissions']+=mult
                nxt[(nf,nr)]+=mult
        st['trace_prefix_nodes']+=sum(nxt.values());current=nxt
    return st
def h(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--result',required=True);ap.add_argument('--freeze',required=True);ap.add_argument('--output',required=True);a=ap.parse_args();o=Path(a.output);assert not o.exists();R=json.loads(Path(a.result).read_text());F=json.loads(Path(a.freeze).read_text());S=dp();rs=R['stats']
    checks={'decision':R['decision']=='PASS_BELIEF_RECOMMIT_EPOCH_ABA_SCOPED','stats':rs==S,'mismatch':rs['mismatch']==0,'old_epoch_block':rs['old_epoch_action_admissions']==0,'stale_action':rs['stale_or_contradicted_action_admissions']==0,'fresh_action':rs['fresh_current_action_admissions']>0,'epoch_monotone':rs['nonincreasing_successful_commit_epochs']==0,'archive':rs['archived_old_commit_witnesses']>0,'replay_attempts':rs['replayed_old_receipt_attempts_after_recommit']>0,'comparator_aba':rs['reused_id_aba_admissions']>0,'directed':all(R['directed'].values()),'corruptions':all(R['corruptions'].values()),'formal':R['formal_invocations']==1 and R['reruns']==0 and R['replacements']==0 and R['tuning']==0,'source_plan':h('PLAN.md')==F['sha256']['PLAN.md'],'source_formal':h('formal.py')==F['sha256']['formal.py'],'source_audit':h('audit.py')==F['sha256']['audit.py']}
    Z={'status':'PASS' if all(checks.values()) else 'FAIL','checks':checks,'dp_stats':S,'result_sha256':h(a.result),'freeze_sha256':h(a.freeze)};o.write_text(json.dumps(Z,indent=2,sort_keys=True)+'\n');print(json.dumps(Z,indent=2,sort_keys=True));raise SystemExit(0 if Z['status']=='PASS' else 1)
if __name__=='__main__':main()
