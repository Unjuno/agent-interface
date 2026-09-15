from __future__ import annotations
import copy, hashlib, json, os, shutil, subprocess, sys, tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parent
UP=ROOT/'upstream'
fixture=json.loads((UP/'receipt-fixture.json').read_text())
source_sha={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in ['replan_receipt_journal_v1.py','prereg-candidate.json']}
source_sha.update({f'upstream/{p}':hashlib.sha256((UP/p).read_bytes()).hexdigest() for p in ['authority_ended_bridge_v1.py','replan_receipt_ledger_v1.py','receipt-fixture.json']})
rows=[]
def add(case, ok, detail): rows.append({'case':case,'pass':bool(ok),'detail':detail})

def run(code,*args):
    return subprocess.run([sys.executable,'-c',code,*map(str,args)],text=True,capture_output=True)

with tempfile.TemporaryDirectory(prefix='receipt-journal-v1-') as td:
    td=Path(td); journal=td/'issued.jsonl'
    code_issue="""
import json,sys
from pathlib import Path
root=Path(sys.argv[1]); journal=Path(sys.argv[2]); sys.path.insert(0,str(root)); sys.path.insert(0,str(root/'upstream'))
from replan_receipt_journal_v1 import JournalBackedReplanReceiptLedger
from replan_receipt_ledger_v1 import consume_for_execute
r=json.loads((root/'upstream'/'receipt-fixture.json').read_text())
l=JournalBackedReplanReceiptLedger(journal); t=l.issue(r); consume_for_execute(t)
print(json.dumps({'id':t.authority_end_id,'used':t.used,'issued_ids':sorted(l.issued_ids)}))
"""
    p1=run(code_issue,ROOT,journal)
    first=json.loads(p1.stdout) if p1.returncode==0 else {'stderr':p1.stderr,'returncode':p1.returncode}
    add('first_issue_persists', p1.returncode==0 and first.get('used') is True and journal.exists() and fixture['authority_end_id'] in journal.read_text(), first)

    code_replay="""
import json,sys
from pathlib import Path
root=Path(sys.argv[1]); journal=Path(sys.argv[2]); sys.path.insert(0,str(root)); sys.path.insert(0,str(root/'upstream'))
from replan_receipt_journal_v1 import JournalBackedReplanReceiptLedger
from replan_receipt_ledger_v1 import DuplicateAuthorityEndedReceipt
r=json.loads((root/'upstream'/'receipt-fixture.json').read_text()); l=JournalBackedReplanReceiptLedger(journal)
try:
 t=l.issue(r); print(json.dumps({'status':'MINTED','id':t.authority_end_id,'issued_ids':sorted(l.issued_ids)}))
except DuplicateAuthorityEndedReceipt as e:
 print(json.dumps({'status':'REJECTED','error':str(e),'issued_ids':sorted(l.issued_ids)}))
"""
    p2=run(code_replay,ROOT,journal); replay=json.loads(p2.stdout) if p2.returncode==0 else {'stderr':p2.stderr,'returncode':p2.returncode}
    add('clean_restart_duplicate_rejected', p2.returncode==0 and replay.get('status')=='REJECTED', replay)

    code_distinct="""
import json,sys
from pathlib import Path
root=Path(sys.argv[1]); journal=Path(sys.argv[2]); sys.path.insert(0,str(root)); sys.path.insert(0,str(root/'upstream'))
from replan_receipt_journal_v1 import JournalBackedReplanReceiptLedger
r=json.loads((root/'upstream'/'receipt-fixture.json').read_text()); r['authority_end_id']='distinct-runtime-authority-end-restart-v1'; r['post_authority']['sequence']=4
l=JournalBackedReplanReceiptLedger(journal); t=l.issue(r)
print(json.dumps({'status':'MINTED','id':t.authority_end_id,'issued_ids':sorted(l.issued_ids)}))
"""
    p3=run(code_distinct,ROOT,journal); distinct=json.loads(p3.stdout) if p3.returncode==0 else {'stderr':p3.stderr,'returncode':p3.returncode}
    add('distinct_new_identity_issues_after_restart', p3.returncode==0 and distinct.get('status')=='MINTED' and distinct.get('id')=='distinct-runtime-authority-end-restart-v1', distinct)

    code_distinct_replay="""
import json,sys
from pathlib import Path
root=Path(sys.argv[1]); journal=Path(sys.argv[2]); sys.path.insert(0,str(root)); sys.path.insert(0,str(root/'upstream'))
from replan_receipt_journal_v1 import JournalBackedReplanReceiptLedger
from replan_receipt_ledger_v1 import DuplicateAuthorityEndedReceipt
r=json.loads((root/'upstream'/'receipt-fixture.json').read_text()); r['authority_end_id']='distinct-runtime-authority-end-restart-v1'; r['post_authority']['sequence']=4
l=JournalBackedReplanReceiptLedger(journal)
try:
 l.issue(r); print(json.dumps({'status':'MINTED'}))
except DuplicateAuthorityEndedReceipt as e:
 print(json.dumps({'status':'REJECTED','error':str(e),'issued_ids':sorted(l.issued_ids)}))
"""
    p4=run(code_distinct_replay,ROOT,journal); drep=json.loads(p4.stdout) if p4.returncode==0 else {'stderr':p4.stderr,'returncode':p4.returncode}
    add('second_restart_distinct_duplicate_rejected', p4.returncode==0 and drep.get('status')=='REJECTED', drep)

    pre=td/'pre-fail.jsonl'
    code_pre="""
import json,sys
from pathlib import Path
root=Path(sys.argv[1]); journal=Path(sys.argv[2]); sys.path.insert(0,str(root)); sys.path.insert(0,str(root/'upstream'))
from replan_receipt_journal_v1 import JournalBackedReplanReceiptLedger
r=json.loads((root/'upstream'/'receipt-fixture.json').read_text())
class FailBefore(JournalBackedReplanReceiptLedger):
 def _persist(self,rid): raise OSError('injected before persist')
try:
 FailBefore(journal).issue(r); print(json.dumps({'status':'UNEXPECTED_MINT'}))
except OSError as e:
 print(json.dumps({'status':'FAILED_BEFORE_PERSIST','error':str(e),'journal_exists':journal.exists(),'size':journal.stat().st_size if journal.exists() else 0}))
"""
    pf=run(code_pre,ROOT,pre); pred=json.loads(pf.stdout) if pf.returncode==0 else {'stderr':pf.stderr,'returncode':pf.returncode}
    add('pre_persist_failure_leaves_no_mark', pf.returncode==0 and pred.get('status')=='FAILED_BEFORE_PERSIST' and pred.get('size')==0, pred)
    pfr=run(code_issue,ROOT,pre); pr2=json.loads(pfr.stdout) if pfr.returncode==0 else {'stderr':pfr.stderr,'returncode':pfr.returncode}
    add('after_pre_persist_failure_restart_can_issue', pfr.returncode==0 and pr2.get('used') is True, pr2)

    crash=td/'crash-after-persist.jsonl'
    code_crash="""
import json,os,sys
from pathlib import Path
root=Path(sys.argv[1]); journal=Path(sys.argv[2]); sys.path.insert(0,str(root)); sys.path.insert(0,str(root/'upstream'))
from replan_receipt_journal_v1 import JournalBackedReplanReceiptLedger
r=json.loads((root/'upstream'/'receipt-fixture.json').read_text())
class CrashAfter(JournalBackedReplanReceiptLedger):
 def _persist(self,rid):
  super()._persist(rid)
  os._exit(73)
CrashAfter(journal).issue(r)
print('TOKEN_RETURNED')
"""
    pc=run(code_crash,ROOT,crash)
    crash_persisted=crash.exists() and fixture['authority_end_id'] in crash.read_text()
    add('crash_after_persist_before_token_return_is_reachable', pc.returncode==73 and pc.stdout=='' and crash_persisted, {'returncode':pc.returncode,'stdout':pc.stdout,'stderr':pc.stderr,'journal':crash.read_text() if crash.exists() else None})
    pcr=run(code_replay,ROOT,crash); cr=json.loads(pcr.stdout) if pcr.returncode==0 else {'stderr':pcr.stderr,'returncode':pcr.returncode}
    add('restart_after_crash_rejects_same_receipt', pcr.returncode==0 and cr.get('status')=='REJECTED', cr)

    trunc=td/'truncated.jsonl'; trunc.write_text('{"authority_end_id":"partial"',encoding='utf-8')
    code_load="""
import json,sys
from pathlib import Path
root=Path(sys.argv[1]); journal=Path(sys.argv[2]); sys.path.insert(0,str(root)); sys.path.insert(0,str(root/'upstream'))
from replan_receipt_journal_v1 import JournalBackedReplanReceiptLedger, ReceiptJournalCorrupt
try:
 JournalBackedReplanReceiptLedger(journal); print(json.dumps({'status':'LOADED'}))
except ReceiptJournalCorrupt as e:
 print(json.dumps({'status':'CORRUPT_REJECTED','error':str(e)}))
"""
    pt=run(code_load,ROOT,trunc); tr=json.loads(pt.stdout) if pt.returncode==0 else {'stderr':pt.stderr,'returncode':pt.returncode}
    add('truncated_journal_fails_closed', pt.returncode==0 and tr.get('status')=='CORRUPT_REJECTED', tr)

    journal_bytes=journal.read_bytes()
    journal_sha=hashlib.sha256(journal_bytes).hexdigest()

safety_cases=[r for r in rows if r['case'] not in {'crash_after_persist_before_token_return_is_reachable'}]
safety_pass=all(r['pass'] for r in safety_cases)
crash_window=next(r for r in rows if r['case']=='crash_after_persist_before_token_return_is_reachable')['pass']
result={
 'schema':'authority-ended-receipt-restart-journal-v1-result',
 'base_commit':'a1ea4cbfac735eafb1f8901dd6c32a890bed015c',
 'python':sys.version.split()[0],
 'rows':rows,
 'restart_safety_gate_pass':safety_pass,
 'crash_after_persist_liveness_gap_observed':crash_window,
 'decision':'PASS_RESTART_SAFETY_HOLD_CRASH_LIVENESS' if safety_pass and crash_window else 'RETAIN_FAILURE',
 'source_sha256':source_sha,
 'two_id_journal_sha256':journal_sha,
}
print(json.dumps(result,indent=2,sort_keys=True))
