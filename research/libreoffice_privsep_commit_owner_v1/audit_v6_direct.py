#!/usr/bin/env python3
import argparse,json,hashlib,errno
from pathlib import Path
EXPECTED_BLOBS={'backend_x11.py':'b4f8e043ce4f8929d446e038418ea0fd3655bab0','office_backend.py':'3aeca10f62fb1366bcdd5fad561509cfcc0d91ab'}
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def gitblob(p):
 b=Path(p).read_bytes(); return hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
def check(root):
 root=Path(root); s=json.loads((root/'SUMMARY.json').read_text()); errors=[]
 if s.get('allocation')!='c318-privsep-06' or len(s.get('rows',[]))!=2: errors.append('summary shape')
 for n,g in EXPECTED_BLOBS.items():
  p=Path(__file__).resolve().parent/'source'/n
  if gitblob(p)!=g: errors.append('blob:'+n)
 for i,r in enumerate(s.get('rows',[])):
  tag=f'row{i}'
  if r.get('classification')!='PASS_CAPABILITY_COMMIT_OWNER': errors.append(tag+':classification')
  if not r.get('release',{}).get('verified') or r['release'].get('keys_down') or r['release'].get('buttons_down'): errors.append(tag+':release')
  if not r.get('plan_valid_at_check') or not r.get('publish_recheck_valid') or not r.get('published'): errors.append(tag+':gate')
  if r.get('gui_uid')==0: errors.append(tag+':gui-root')
  if not r.get('soffice_processes') or any(p.get('euid')!=r.get('gui_uid') for p in r['soffice_processes']): errors.append(tag+':soffice-euid')
  ad=r.get('authority_dir_initial',{}); mode=int(ad.get('mode','0o0'),8)
  if ad.get('uid')!=0 or mode & 0o022: errors.append(tag+':authority-dir-writable')
  st=r.get('staging_score',{}).get('cells',{}); fin=r.get('final_score',{}).get('cells',{})
  if st.get('A1')!='office' or st.get('A2')!='preview' or fin.get('A1')!='office' or fin.get('A2')!='preview': errors.append(tag+':cells')
  if r.get('adversarial'):
   w=r.get('writer') or {}
   if w.get('euid')!=r.get('gui_uid') or w.get('ok') is not False or w.get('errno') not in [errno.EACCES,errno.EPERM]: errors.append(tag+':writer-not-denied')
   a=r.get('target_after_writer_attempt',{}); plan=r.get('plan_target',{})
   if a.get('sha256')!=plan.get('sha256') or a.get('ino')!=plan.get('ino'): errors.append(tag+':writer-changed-target')
   if not r.get('external_exists_after_writer_attempt'): errors.append(tag+':source-consumed')
 return {'pass':not errors,'errors':errors,'rows':len(s.get('rows',[]))}
def main():
 ap=argparse.ArgumentParser(); ap.add_argument('root',type=Path); a=ap.parse_args(); r=check(a.root); print(json.dumps(r,indent=2)); (a.root/'AUDIT.json').write_text(json.dumps(r,indent=2)+'\n'); raise SystemExit(0 if r['pass'] else 1)
if __name__=='__main__': main()
