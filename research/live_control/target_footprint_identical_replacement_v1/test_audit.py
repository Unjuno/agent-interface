from __future__ import annotations
import argparse, json, shutil, subprocess, sys, tempfile
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parent

def audit(path):
    return subprocess.run([sys.executable,str(ROOT/'audit.py'),str(path)],capture_output=True,text=True)

def main(base: Path):
    if audit(base).returncode != 0:
        raise SystemExit('base formal output does not pass before mutation tests')
    with tempfile.TemporaryDirectory() as td:
        td=Path(td); mutations=[]
        for name,mutate in [
            ('semantic_receipt', lambda r: r.update(current_ids=['target-A','replacement-X'])),
            ('resolver_status', lambda r: r['resolver'].update(status='MISSING',eligible=False)),
            ('resolver_point', lambda r: r['resolver'].update(point=[0,0])),
        ]:
            dst=td/name; shutil.copytree(base,dst); p=dst/'p00-replacement'/'result.json'; r=json.loads(p.read_text()); mutate(r); p.write_text(json.dumps(r,indent=2,sort_keys=True)+'\n'); mutations.append((name,audit(dst).returncode))
        dst=td/'pixel'; shutil.copytree(base,dst); p=dst/'p00-replacement'/'current.png'; im=Image.open(p).convert('RGB'); px=im.load(); old=px[0,0]; px[0,0]=((old[0]+1)%256,old[1],old[2]); im.save(p); mutations.append(('pixel',audit(dst).returncode))
        if not all(code!=0 for _,code in mutations): raise SystemExit(mutations)
        print(json.dumps({'status':'PASS_AUDIT_MUTATIONS','mutations':mutations},sort_keys=True))
if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('formal_out',type=Path); main(ap.parse_args().formal_out)
