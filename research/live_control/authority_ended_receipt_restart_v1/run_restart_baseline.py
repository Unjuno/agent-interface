from __future__ import annotations
import hashlib, json, os, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
UP=ROOT/'upstream'
fixture=(UP/'receipt-fixture.json').read_bytes()
fixture_sha=hashlib.sha256(fixture).hexdigest()
code="""
import json,sys
from pathlib import Path
root=Path(sys.argv[1]); sys.path.insert(0,str(root))
from replan_receipt_ledger_v1 import ReplanReceiptLedger, consume_for_execute
r=json.loads((root/'receipt-fixture.json').read_text())
l=ReplanReceiptLedger(); t=l.issue(r); consume_for_execute(t)
print(json.dumps({'authority_end_id':t.authority_end_id,'post_sequence':t.post_sequence,'used':t.used,'issued_ids':sorted(l.issued_ids)}))
"""
a=subprocess.run([sys.executable,'-c',code,str(UP)],check=True,text=True,capture_output=True)
first=json.loads(a.stdout)
code2="""
import json,sys
from pathlib import Path
root=Path(sys.argv[1]); sys.path.insert(0,str(root))
from replan_receipt_ledger_v1 import ReplanReceiptLedger, DuplicateAuthorityEndedReceipt
r=json.loads((root/'receipt-fixture.json').read_text())
l=ReplanReceiptLedger()
try:
 t=l.issue(r); print(json.dumps({'replay':'MINTED','authority_end_id':t.authority_end_id,'post_sequence':t.post_sequence,'issued_ids':sorted(l.issued_ids)}))
except DuplicateAuthorityEndedReceipt as e:
 print(json.dumps({'replay':'REJECTED','error':str(e),'issued_ids':sorted(l.issued_ids)}))
"""
b=subprocess.run([sys.executable,'-c',code2,str(UP)],check=True,text=True,capture_output=True)
second=json.loads(b.stdout)
result={
 'schema':'authority-ended-restart-baseline-v1-result',
 'base_commit':'a1ea4cbfac735eafb1f8901dd6c32a890bed015c',
 'python':sys.version.split()[0],
 'fixture_sha256':fixture_sha,
 'first_process':first,
 'second_process':second,
 'decision':'FAIL_CURRENT_CANDIDATE_RESTART_REPLAY' if second['replay']=='MINTED' and second['authority_end_id']==first['authority_end_id'] else 'UNEXPECTED',
}
print(json.dumps(result,indent=2,sort_keys=True))
