import argparse,copy,json,shutil,tempfile
from pathlib import Path
from audit import audit
M=[('flip_ready',lambda c:c['measurement'].__setitem__('ready',not c['measurement']['ready'])),('drop_measurement',lambda c:c.pop('measurement')),('bad_status',lambda c:c.__setitem__('status','x')),('bad_policy',lambda c:c['measurement'].__setitem__('policy','FIXED_100MS' if c['policy']!='FIXED_100MS' else 'NO_EXTRA_WAIT')),('drop_process',lambda c:c.__setitem__('processes',[p for p in c['processes'] if p['name']!='chromium'])),('break_setup',lambda c:c.get('setup',{}).__setitem__('ready',False))]
def main(root):
 root=Path(root); b=audit(root)
 if b['errors']: raise SystemExit('baseline invalid')
 target_id=next(x['case_id'] for x in json.loads((root/'LAUNCHER.json').read_text()) if x['phase']=='SEQUENTIAL')
 original=json.loads((root/target_id/'CASE.json').read_text()); out=[]
 for name,fn in M:
  with tempfile.TemporaryDirectory() as td:
   d=Path(td)/'r'; shutil.copytree(root,d); c=copy.deepcopy(original); fn(c); (d/target_id/'CASE.json').write_text(json.dumps(c,indent=2)+'\n'); r=audit(d); out.append({'name':name,'rejected':bool(r['errors']),'errors':r['errors'][:6]})
 print(json.dumps({'baseline_decision':b['decision'],'controls':out,'all_rejected':all(x['rejected'] for x in out)},indent=2,sort_keys=True))
if __name__=='__main__':
 ap=argparse.ArgumentParser(); ap.add_argument('root'); a=ap.parse_args(); main(a.root)
