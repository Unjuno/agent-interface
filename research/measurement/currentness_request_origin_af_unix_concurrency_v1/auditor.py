import argparse, hashlib, json
from oracle import empty_state, apply, snapshot

TASK='CURRENTNESS-REQUEST-ORIGIN-AF_UNIX-CONCURRENCY-20260918-007'


def validate_summary(r,a):
    errs=[]; e=a['expected']
    for k in ['formal_cases','cases_completed','stale_response_installs','stale_old_epoch_admissions','race_order_wrong','response_replay_rebindings','duplicate_invalidation_double_advances','authority_promotions','malformed_controls_passed','malformed_controls_total','ledger_sha256','peer_client_pid_count','server_client_exceptions','primary_invocations','reruns']:
        if r.get(k)!=e.get(k): errs.append(k)
    return errs


def audit(result_path, ledger_path):
    r=json.load(open(result_path)); h=hashlib.sha256(); cases=0; mism=0; family_errors=0; authority=0; stale_installs=0; stale_admits=0; race_wrong=0; cross=0; replay_rebind=0; dup_double=0; race_i=0; race_v=0
    with open(ledger_path) as f:
        for line in f:
            h.update(line.encode()); row=json.loads(line); cases+=1
            if row.get('error'):
                family_errors+=1; continue
            state=empty_state(); receipts=sorted(row['receipts'],key=lambda x:x['seq']); prev=None
            for x in receipts:
                want=apply(state,x['request']); got=x['output']; ws=snapshot(state)
                if want!=got or ws!=x['snapshot']: mism+=1
                if got.get('grants_input_authority') is not False: authority+=1
                if row['family']=='cross_scope' and x['op']=='invalidate' and prev is not None:
                    before={tuple(z[:2]):z[2] for z in prev}; after={tuple(z[:2]):z[2] for z in x['snapshot']['epochs']}; target=tuple(x['request']['scope'])
                    if any(k!=target and before.get(k,0)!=after.get(k,0) for k in set(before)|set(after)): cross+=1
                prev=x['snapshot']['epochs']
            sts=[x['output']['status'] for x in receipts]; fam=row['family']
            if fam=='stale_response':
                if sts!=['REQUEST_BEGUN','CURRENTNESS_INVALIDATED','STALE_RESPONSE_REFUSED','UNKNOWN_DECISION']: family_errors+=1
                if sts[2]=='DECISION_INSTALLED': stale_installs+=1
            elif fam=='fresh_after_invalidation':
                if sts!=['CURRENTNESS_INVALIDATED','REQUEST_BEGUN','DECISION_INSTALLED','ADMITTED']: family_errors+=1
            elif fam=='overlap_old_new':
                if sts!=['REQUEST_BEGUN','CURRENTNESS_INVALIDATED','REQUEST_BEGUN','STALE_RESPONSE_REFUSED','DECISION_INSTALLED','UNKNOWN_DECISION','ADMITTED']: family_errors+=1
                if receipts[3]['output']['status']=='DECISION_INSTALLED': stale_installs+=1
            elif fam=='cross_scope':
                if sts!=['REQUEST_BEGUN','CURRENTNESS_INVALIDATED','DECISION_INSTALLED','ADMITTED']: family_errors+=1
            elif fam=='response_replay':
                if sts!=['REQUEST_BEGUN','DECISION_INSTALLED','RESPONSE_REPLAY_REFUSED','ADMITTED','UNKNOWN_DECISION']: family_errors+=1
                if sts.count('DECISION_INSTALLED')>1: replay_rebind+=1
            elif fam=='duplicate_invalidation':
                if sts!=['CURRENTNESS_INVALIDATED','DUPLICATE_INVALIDATION_NOOP','REQUEST_BEGUN','DECISION_INSTALLED','ADMITTED']: family_errors+=1
                if sts[1]!='DUPLICATE_INVALIDATION_NOOP': dup_double+=1
            elif fam=='installed_then_invalidated':
                if sts!=['REQUEST_BEGUN','DECISION_INSTALLED','CURRENTNESS_INVALIDATED','STALE_EPOCH_REFUSED']: family_errors+=1
                if sts[-1]=='ADMITTED': stale_admits+=1
            elif fam=='race_install_invalidate':
                ins=next(x for x in receipts if x['op']=='install'); inv=next(x for x in receipts if x['op']=='invalidate'); use=next(x for x in receipts if x['op']=='use')
                if ins['seq']<inv['seq']:
                    race_i+=1; ok=ins['output']['status']=='DECISION_INSTALLED' and use['output']['status']=='STALE_EPOCH_REFUSED'
                else:
                    race_v+=1; ok=ins['output']['status']=='STALE_RESPONSE_REFUSED' and use['output']['status']=='UNKNOWN_DECISION'
                if not ok: race_wrong+=1; family_errors+=1
                if use['output']['status']=='ADMITTED': stale_admits+=1
            else: family_errors+=1
    cleanup=r.get('cleanup',{}); exceptions=r.get('server_client_exceptions',0)+len(cleanup.get('client_errors',[]))
    cleanup_ok=(cleanup.get('server_exit') in (-15,0) and not cleanup.get('server_stderr') and not cleanup.get('client_errors'))
    expected={
      'formal_cases':20000,'cases_completed':cases,'candidate_oracle_mismatches':mism,'stale_response_installs':stale_installs,'stale_old_epoch_admissions':stale_admits,'race_order_wrong':race_wrong,'cross_scope_mutations':cross,'response_replay_rebindings':replay_rebind,'duplicate_invalidation_double_advances':dup_double,'authority_promotions':authority,'malformed_controls_passed':r.get('malformed_controls_passed'),'malformed_controls_total':r.get('malformed_controls_total'),'ledger_sha256':h.hexdigest(),'peer_client_pid_count':r.get('peer_client_pid_count'),'server_client_exceptions':exceptions,'primary_invocations':1,'reruns':0}
    gates=(cases==20000 and exceptions==0 and cleanup_ok and mism==0 and family_errors==0 and stale_installs==0 and stale_admits==0 and race_wrong==0 and cross==0 and replay_rebind==0 and dup_double==0 and authority==0 and r.get('malformed_controls_passed')==r.get('malformed_controls_total') and r.get('peer_client_pid_count',0)>=4 and h.hexdigest()==r.get('ledger_sha256') and r.get('primary_invocations')==1 and r.get('reruns')==0)
    return {'task':TASK,'audit':'PASS' if gates else 'FAIL','errors':[] if gates else ['gate_failure'],'expected':expected,'family_invariant_errors':family_errors,'server_client_exceptions':exceptions,'cleanup_ok':cleanup_ok,'race_install_first':race_i,'race_invalidation_first':race_v}


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--result',required=True); ap.add_argument('--ledger',required=True); ap.add_argument('--out',required=True); a=ap.parse_args()
    z=audit(a.result,a.ledger); open(a.out,'w').write(json.dumps(z,indent=2,sort_keys=True)+'\n'); print(json.dumps({'audit':z['audit'],'race_install_first':z['race_install_first'],'race_invalidation_first':z['race_invalidation_first']},sort_keys=True)); raise SystemExit(0 if z['audit']=='PASS' else 2)
if __name__=='__main__': main()
