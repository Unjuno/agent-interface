from __future__ import annotations
import argparse,json,shutil,subprocess,sys,tempfile
from pathlib import Path
HERE=Path(__file__).resolve().parent
def audit(p): return subprocess.run([sys.executable,str(HERE/'audit.py'),str(p)],capture_output=True,text=True)
def main(base):
    if audit(base).returncode!=0: raise SystemExit('base audit failed')
    muts=[]
    with tempfile.TemporaryDirectory() as td:
        td=Path(td)
        def clone(n): d=td/n; shutil.copytree(base,d); return d
        d=clone('text'); p=d/'rep-0'/'report.json'; r=json.loads(p.read_text()); r['trials'][3]['actual']='X'; p.write_text(json.dumps(r)); muts.append(('wrong_text',audit(d).returncode))
        d=clone('emission'); p=d/'rep-0'/'report.json'; r=json.loads(p.read_text()); r['trials'][12]['candidate']['emissions']=2; p.write_text(json.dumps(r)); muts.append(('rejection_emission',audit(d).returncode))
        d=clone('map'); p=d/'rep-0'/'applied_mapping.json'; m=json.loads(p.read_text()); m[0][0]=(m[0][0]+1)%65536; p.write_text(json.dumps(m)); muts.append(('mapping',audit(d).returncode))
        d=clone('mod'); p=d/'rep-0'/'modifier_mapping.json'; m=json.loads(p.read_text()); m[7]=[]; p.write_text(json.dumps(m)); muts.append(('modifier',audit(d).returncode))
        d=clone('xkb'); p=d/'rep-0'/'layout.resolved.xkb'; p.write_text(p.read_text()+'\n//corrupt\n'); muts.append(('resolved_xkb',audit(d).returncode))
    if not all(code!=0 for _,code in muts): raise SystemExit(muts)
    print(json.dumps({'status':'PASS_AUDIT_MUTATIONS','mutations':muts},sort_keys=True))
if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('formal',type=Path); main(ap.parse_args().formal.resolve())
