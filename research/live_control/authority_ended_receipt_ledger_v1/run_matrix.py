from __future__ import annotations
import copy,json,statistics,time,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from authority_ended_bridge_v1 import AuthorityEndedNotReady
from replan_receipt_ledger_v1 import ReplanReceiptLedger,DuplicateAuthorityEndedReceipt,InvalidAuthorityEndIdentity,current_revalidation,consume_for_execute
receipt=json.loads((ROOT/'receipt-fixture.json').read_text())
rows=[]
def row(case,ok,detail): rows.append({'case':case,'pass':bool(ok),'detail':detail})
l=ReplanReceiptLedger(); t=l.issue(copy.deepcopy(receipt)); row('valid_first_issue',t.authority_end_id==receipt['authority_end_id'] and t.post_sequence==receipt['post_authority']['sequence'] and not t.used,repr(t))
try:l.issue(copy.deepcopy(receipt))
except DuplicateAuthorityEndedReceipt as e: row('duplicate_before_consume_rejected',True,str(e))
else:row('duplicate_before_consume_rejected',False,'duplicate minted')
consume_for_execute(t)
try:l.issue(copy.deepcopy(receipt))
except DuplicateAuthorityEndedReceipt as e: row('duplicate_after_consume_rejected',True,str(e))
else:row('duplicate_after_consume_rejected',False,'duplicate minted')
alt=copy.deepcopy(receipt); alt['post_authority']['sequence']+=100
try:l.issue(alt)
except DuplicateAuthorityEndedReceipt as e: row('same_id_altered_post_sequence_rejected',True,str(e))
else:row('same_id_altered_post_sequence_rejected',False,'duplicate minted')
missing=copy.deepcopy(receipt); missing.pop('authority_end_id')
try:ReplanReceiptLedger().issue(missing)
except InvalidAuthorityEndIdentity as e: row('missing_identity_rejected',True,str(e))
else:row('missing_identity_rejected',False,'missing id accepted')
early=copy.deepcopy(receipt); early['post_authority']=None
try:ReplanReceiptLedger().issue(early)
except AuthorityEndedNotReady as e: row('early_incomplete_receipt_still_rejected_by_bridge',str(e)=='post-authority observation required',str(e))
else:row('early_incomplete_receipt_still_rejected_by_bridge',False,'early accepted')
row('same_token_after_consume_reports_token_replay',current_revalidation(t,3)=={'status':'token_replay'},str(current_revalidation(t,3)))
other=copy.deepcopy(receipt);other['authority_end_id']='distinct-runtime-authority-end-fixture';other['post_authority']['sequence']=4
u=l.issue(other); row('distinct_new_identity_with_new_post_sequence_issues_once',u.authority_end_id==other['authority_end_id'] and current_revalidation(u,5)=={'status':'revalidated'},repr(u))
repeats=7;n=200_000
issue_ns=[]; dup_ns=[]
for _ in range(repeats):
    t0=time.perf_counter_ns()
    for i in range(n):
        x=copy.deepcopy(receipt);x['authority_end_id']=f'bench-{i}';ReplanReceiptLedger().issue(x)
    issue_ns.append((time.perf_counter_ns()-t0)/n)
    led=ReplanReceiptLedger();led.issue(receipt)
    t0=time.perf_counter_ns()
    for _i in range(n):
        try:led.issue(receipt)
        except DuplicateAuthorityEndedReceipt:pass
    dup_ns.append((time.perf_counter_ns()-t0)/n)
result={'schema':'authority-ended-receipt-ledger-result-v1','rows':rows,'hard_gate_pass':all(x['pass'] for x in rows) and len(rows)==8,
        'benchmark':{'python':sys.version.split()[0],'repeats':repeats,'n_per_repeat':n,'valid_issue_ns_per_call':issue_ns,'duplicate_reject_ns_per_call':dup_ns,
                     'valid_issue_median_ns':statistics.median(issue_ns),'duplicate_reject_median_ns':statistics.median(dup_ns)},
        'decision':'RETAIN_LEDGER_CANDIDATE' if all(x['pass'] for x in rows) and len(rows)==8 else 'RETAIN_FAILURE'}
print(json.dumps(result,indent=2,sort_keys=True))
