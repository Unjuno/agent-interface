import json,sys
from pathlib import Path
import audit
rows=[]
for d in sys.argv[1:]: rows += json.loads((Path(d)/'RAW.json').read_text())['rows']
base=audit.evaluate(rows); errors=list(base['errors'])
process={'calc_exit_255':0,'xvfb_exit_0':0,'helper_exit_expected':0,'helper_exit_none':0}
for r in rows:
 cid=r['case_id']
 if 'calc_exit' not in r or 'xvfb_exit' not in r or 'helper_exit' not in r: errors.append('missing_process_receipt:'+cid); continue
 if r['calc_exit']==255: process['calc_exit_255']+=1
 else: errors.append('calc_exit:'+cid+':'+str(r['calc_exit']))
 if r['xvfb_exit']==0: process['xvfb_exit_0']+=1
 else: errors.append('xvfb_exit:'+cid+':'+str(r['xvfb_exit']))
 if r['scenario']=='focus_transferred':
  if r['helper_exit']==-15: process['helper_exit_expected']+=1
  else: errors.append('helper_exit:'+cid+':'+str(r['helper_exit']))
 else:
  if r['helper_exit'] is None: process['helper_exit_none']+=1
  else: errors.append('unexpected_helper:'+cid+':'+str(r['helper_exit']))
out={'base_decision':base['decision'],'rows':len(rows),'process_receipts':process,'errors':errors,'audit_v2_pass':not errors}
print(json.dumps(out,sort_keys=True)); raise SystemExit(0 if not errors else 2)
