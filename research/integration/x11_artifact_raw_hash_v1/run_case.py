from __future__ import annotations
import argparse, hashlib, importlib.util, json, subprocess, sys
from pathlib import Path

HERE=Path(__file__).resolve().parent
SRC=HERE/'vendor/capture_artifacts.py'
CASES={
 'bgrx_base': (0, bytes([0x11,0x22,0x33,0x00])),
 'bgrx_xdiff':(0, bytes([0x11,0x22,0x33,0x7f])),
 'bgrx_vis':  (0, bytes([0x11,0x22,0x34,0x00])),
 'xrgb_base': (1, bytes([0x00,0x33,0x22,0x11])),
 'xrgb_xdiff':(1, bytes([0x7f,0x33,0x22,0x11])),
 'xrgb_vis':  (1, bytes([0x00,0x34,0x22,0x11])),
}

def load():
 spec=importlib.util.spec_from_file_location('frozen_capture_artifacts',SRC)
 mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod

def worker(case,out):
 bo,raw=CASES[case]
 out=Path(out); out.mkdir(parents=True,exist_ok=False)
 mod=load(); row=mod.CaptureArtifacts(out/'images').write(raw,1,1,depth=24,bits_per_pixel=32,scanline_pad=32,byte_order=bo,masks=(0xff0000,0x00ff00,0x0000ff),true_color=True)
 png=Path(row['path']).read_bytes()
 result={'case':case,'byte_order':bo,'raw_hex':raw.hex(),'raw_sha256':hashlib.sha256(raw).hexdigest(),'artifact':{**row,'path':Path(row['path']).name},'png_hex':png.hex(),'png_sha256':hashlib.sha256(png).hexdigest()}
 (out/'result.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
 print(json.dumps(result,sort_keys=True,separators=(',',':')))

def orchestrate(root):
 root=Path(root); root.mkdir(parents=True,exist_ok=False)
 rows=[]
 for idx,name in enumerate(CASES):
  dst=root/f'{idx:02d}-{name}'
  p=subprocess.run([sys.executable,'-B',str(Path(__file__).resolve()),'worker',name,str(dst)],capture_output=True,text=True,timeout=5)
  rec={'index':idx,'case':name,'returncode':p.returncode,'stdout':p.stdout,'stderr':p.stderr}
  (dst/'process.json').write_text(json.dumps(rec,sort_keys=True,indent=2)+'\n')
  if p.returncode!=0: raise SystemExit('worker failed '+name)
  rows.append(json.loads((dst/'result.json').read_text()))
 (root/'rows.json').write_text(json.dumps(rows,sort_keys=True,indent=2)+'\n')
 print(json.dumps({'cases':len(rows),'status':'COMPLETE'},sort_keys=True))

if __name__=='__main__':
 ap=argparse.ArgumentParser(); sub=ap.add_subparsers(dest='cmd',required=True)
 w=sub.add_parser('worker'); w.add_argument('case'); w.add_argument('out')
 r=sub.add_parser('run'); r.add_argument('out')
 a=ap.parse_args(); worker(a.case,a.out) if a.cmd=='worker' else orchestrate(a.out)
