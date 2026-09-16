from __future__ import annotations
import argparse, hashlib, json, platform, subprocess, sys, time
from pathlib import Path
from xml.etree import ElementTree as ET
import cv2
import numpy as np
from PIL import Image
import upstream_resolver

W,H=600,400
SRC=(175,155)
TEMPLATE=61
ROOT=Path(__file__).resolve().parent

def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def git_blob(data: bytes) -> str:
    return hashlib.sha1(f'blob {len(data)}\0'.encode()+data).hexdigest()

def svg_text(target_id: str, center, color: str) -> str:
    x,y=center
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
<rect x="0" y="0" width="{W}" height="{H}" fill="#f7f7f4"/>
<g id="background-decor" opacity="1"><rect x="35" y="50" width="70" height="28" rx="7" fill="#79a9d1" stroke="#24313f" stroke-width="3"/><circle cx="490" cy="85" r="22" fill="#78b87a" stroke="#24313f" stroke-width="3"/><path d="M430 310 L475 270 L520 310 Z" fill="#7e68b7" stroke="#24313f" stroke-width="3"/></g>
<g id="{target_id}">
  <rect x="{x-22}" y="{y-18}" width="44" height="36" rx="5" fill="{color}" stroke="#191919" stroke-width="3"/>
  <circle cx="{x+9}" cy="{y-7}" r="5" fill="#ffe04f" stroke="#191919" stroke-width="2"/>
  <path d="M{x-13} {y+8} L{x+7} {y+8}" stroke="#f8f8f8" stroke-width="3" stroke-linecap="round"/>
</g>
<g id="distractor"><rect x="330" y="210" width="52" height="31" rx="3" fill="#cf544f" stroke="#202020" stroke-width="2"/><circle cx="372" cy="232" r="4" fill="#ffd14a"/></g>
</svg>'''

def render(svg: Path, png: Path) -> dict:
    cmd=['inkscape',str(svg),'--export-type=png',f'--export-filename={png}',f'--export-width={W}',f'--export-height={H}']
    t0=time.monotonic_ns(); cp=subprocess.run(cmd,capture_output=True,text=True); t1=time.monotonic_ns()
    if cp.returncode != 0:
        raise RuntimeError(f'inkscape failed: {cp.returncode}: {cp.stderr}')
    return {'argv':cmd,'returncode':cp.returncode,'stdout':cp.stdout,'stderr':cp.stderr,'elapsed_ns':t1-t0}

def rgb(path: Path) -> np.ndarray:
    return np.array(Image.open(path).convert('RGB'))

def ids(path: Path) -> list[str]:
    return sorted(e.attrib['id'] for e in ET.parse(path).iter() if 'id' in e.attrib)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('out',type=Path); ap.add_argument('--construction',action='store_true'); args=ap.parse_args()
    if args.out.exists(): raise SystemExit('refuse existing output directory')
    args.out.mkdir(parents=True)
    schedule=json.loads((ROOT/'schedule.json').read_text())
    pairs=schedule['pairs'][:2] if args.construction else schedule['pairs']
    mode='construction' if args.construction else 'formal'
    source_bytes=(ROOT/'upstream_resolver.py').read_bytes()
    if git_blob(source_bytes) != 'a8bb0e564bae738c9091b737ff2abe1922520ec1':
        raise SystemExit('upstream resolver snapshot blob mismatch')
    records=[]
    for spec in pairs:
        p=spec['pair']; dx=spec['dx']; dy=spec['dy']; color=spec['color']; cur=(SRC[0]+dx,SRC[1]+dy)
        for arm in spec['arm_order']:
            case=f'p{p:02d}-{arm}'
            d=args.out/case; d.mkdir()
            target_id='target-A' if arm=='stable' else 'replacement-X'
            ref_svg=d/'reference.svg'; cur_svg=d/'current.svg'; ref_png=d/'reference.png'; cur_png=d/'current.png'
            ref_svg.write_text(svg_text('target-A',SRC,color)); cur_svg.write_text(svg_text(target_id,cur,color))
            rlog=render(ref_svg,ref_png); clog=render(cur_svg,cur_png)
            ref=rgb(ref_png); current=rgb(cur_png); rr=TEMPLATE//2; sx,sy=SRC
            template=ref[sy-rr:sy+rr+1,sx-rr:sx+rr+1].copy()
            result=upstream_resolver.resolve(current,template,list(SRC))
            rec={
                'task':'FOOTPRINT-IDENTICAL-REPLACEMENT-20260916-001','mode':mode,'case':case,'pair':p,'arm':arm,
                'translation':[dx,dy],'color':color,'source_center':list(SRC),'expected_current_center':list(cur),
                'reference_ids':ids(ref_svg),'current_ids':ids(cur_svg),'resolver':result,
                'reference_png_sha256':sha256_bytes(ref_png.read_bytes()),'current_png_sha256':sha256_bytes(cur_png.read_bytes()),
                'reference_rgb_sha256':sha256_bytes(ref.tobytes()),'current_rgb_sha256':sha256_bytes(current.tobytes()),
                'reference_svg_sha256':sha256_bytes(ref_svg.read_bytes()),'current_svg_sha256':sha256_bytes(cur_svg.read_bytes()),
                'reference_render':rlog,'current_render':clog,
                'upstream_resolver_git_blob':git_blob(source_bytes),'python':sys.version,'platform':platform.platform()
            }
            (d/'result.json').write_text(json.dumps(rec,indent=2,sort_keys=True)+'\n')
            records.append(rec)
    summary={'task':'FOOTPRINT-IDENTICAL-REPLACEMENT-20260916-001','mode':mode,'records':len(records),'cases':[r['case'] for r in records]}
    (args.out/'run_summary.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n')
    print(json.dumps(summary,sort_keys=True))
if __name__=='__main__': main()
