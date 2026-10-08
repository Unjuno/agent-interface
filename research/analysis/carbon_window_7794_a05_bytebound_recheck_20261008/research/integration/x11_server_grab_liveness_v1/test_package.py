import json,shutil,subprocess,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parent
M=['missing_part','alter_part','reorder_parts','wrong_xz','wrong_manifest_commitment','existing_destination']
def run(root,out): return subprocess.run([sys.executable,str(root/'restore_evidence.py'),str(out)],cwd=root,text=True,capture_output=True)
def main():
 res=[]
 for m in M:
  with tempfile.TemporaryDirectory() as td:
   r=Path(td)/'pkg'; r.mkdir(); (r/'evidence_parts').mkdir()
   for name in ['restore_evidence.py','PARTS.json','COMPACT_EVIDENCE.json']: shutil.copy2(ROOT/name,r/name)
   manifest=json.loads((ROOT/'PARTS.json').read_text())
   for item in manifest['parts']:
    p0=ROOT/item['path']; shutil.copy2(p0,r/'evidence_parts'/p0.name)
   out=Path(td)/'out'
   if m=='missing_part': (r/manifest['parts'][3]['path']).unlink()
   elif m=='alter_part':
    p=r/manifest['parts'][3]['path']; s=p.read_text(); p.write_text(('A' if s[0]!='A' else 'B')+s[1:])
   elif m=='reorder_parts':
    p=r/'PARTS.json'; x=json.loads(p.read_text()); x['parts'][2],x['parts'][3]=x['parts'][3],x['parts'][2]; p.write_text(json.dumps(x,indent=2,sort_keys=True)+'\n')
   elif m=='wrong_xz':
    p=r/'COMPACT_EVIDENCE.json'; x=json.loads(p.read_text()); x['xz_sha256']='0'*64; p.write_text(json.dumps(x,indent=2,sort_keys=True)+'\n')
   elif m=='wrong_manifest_commitment':
    p=r/'COMPACT_EVIDENCE.json'; x=json.loads(p.read_text()); x['original_manifest_sha256']='0'*64; p.write_text(json.dumps(x,indent=2,sort_keys=True)+'\n')
   elif m=='existing_destination': out.mkdir()
   q=run(r,out); res.append({'mutation':m,'rejected':q.returncode!=0,'returncode':q.returncode})
 o={'controls':res,'rejected':sum(x['rejected'] for x in res),'total':len(res)}; (ROOT/'PACKAGE_CONTROLS.json').write_text(json.dumps(o,indent=2,sort_keys=True)+'\n'); print(json.dumps(o,sort_keys=True)); raise SystemExit(0 if o['rejected']==len(M) else 1)
if __name__=='__main__': main()
