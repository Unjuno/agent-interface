from __future__ import annotations
import hashlib, json, subprocess, xml.etree.ElementTree as ET
from pathlib import Path
from PIL import Image
from gate import gate, RADIUS, MAX_PIXEL_ERROR

HERE=Path(__file__).resolve().parent
OUT=HERE/'formal-output'
W,H=640,480
CONTROLLER_BLOB='0e44f30660d4ef2b4a78ac2b92db7991e7d1c48a'
CASES=[
 {'seed':1,'A':[150,140],'B':[475,335]},
 {'seed':2,'A':[205,330],'B':[445,125]},
 {'seed':3,'A':[335,150],'B':[115,355]},
 {'seed':4,'A':[490,245],'B':[170,240]},
]

def sha256(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rgb_sha(p): return hashlib.sha256(Image.open(p).convert('RGB').tobytes()).hexdigest()

def svg_text(seed,A,B,variant):
    ax,ay=A; bx,by=B
    target_id,decoy_id=('task-target','decoy') if variant!='swap' else ('decoy','task-target')
    acolor='#f000b0' if variant!='changed' else '#00d8e8'
    bcolor='#f000b0'
    bg=[]
    for i in range(12):
        x=(37*i+29*seed)%600+10; y=(83*i+17*seed)%440+10
        ww=18+(i*7)%52; hh=12+(i*11)%40
        col=['#ccddee','#e6ddcc','#d9ead3','#ead1dc'][i%4]
        bg.append(f'<rect x="{x}" y="{y}" width="{ww}" height="{hh}" fill="{col}" opacity="0.75"/>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">' +
            '<rect width="640" height="480" fill="#fafafa"/>' + ''.join(bg) +
            f'<circle id="{target_id}" cx="{ax}" cy="{ay}" r="18" fill="{acolor}" stroke="#501040" stroke-width="2"/>' +
            f'<circle id="{decoy_id}" cx="{bx}" cy="{by}" r="18" fill="{bcolor}" stroke="#501040" stroke-width="2"/>' +
            '</svg>')

def render(svg,png):
    cp=subprocess.run(['inkscape',str(svg),'--export-type=png',f'--export-filename={png}',f'--export-width={W}',f'--export-height={H}'],capture_output=True,text=True,timeout=30)
    if cp.returncode: raise RuntimeError(f'inkscape failed: {cp.stderr}')

def oracle_object_at(svg,A):
    root=ET.parse(svg).getroot(); ax,ay=map(float,A); found=[]
    for el in root.iter():
        if el.tag.endswith('circle'):
            cx=float(el.attrib['cx']);cy=float(el.attrib['cy'])
            if abs(cx-ax)<1e-9 and abs(cy-ay)<1e-9: found.append(el.attrib.get('id'))
    if len(found)!=1: raise RuntimeError(f'oracle ambiguity {found}')
    return found[0]

def main():
    if OUT.exists(): raise RuntimeError('formal output already exists')
    OUT.mkdir()
    rows=[]
    for c in CASES:
        case_dir=OUT/f"seed-{c['seed']}"; case_dir.mkdir()
        ref_svg=case_dir/'reference.svg'; ref_png=case_dir/'reference.png'
        ref_svg.write_text(svg_text(c['seed'],c['A'],c['B'],'stable'))
        render(ref_svg,ref_png)
        for variant in ('stable','swap','changed'):
            cur_svg=case_dir/f'{variant}.svg'; cur_png=case_dir/f'{variant}.png'
            cur_svg.write_text(svg_text(c['seed'],c['A'],c['B'],variant))
            render(cur_svg,cur_png)
            g=gate(ref_png,cur_png,c['A'])
            oracle=oracle_object_at(cur_svg,c['A'])
            rows.append({'seed':c['seed'],'variant':variant,'A':c['A'],'B':c['B'],'gate':g,'oracle_id_at_A':oracle,'reference_rgb_sha256':rgb_sha(ref_png),'current_rgb_sha256':rgb_sha(cur_png),'rgb_identical':Image.open(ref_png).convert('RGB').tobytes()==Image.open(cur_png).convert('RGB').tobytes(),'reference_svg_sha256':sha256(ref_svg),'current_svg_sha256':sha256(cur_svg)})
    result={'task':'VISUAL-REPROJECTION-IDENTITY-ALIAS-20260917-001','formal_deterministic_invocations':1,'reruns':0,'inkscape_version':subprocess.check_output(['inkscape','--version'],text=True).strip(),'controller_blob':CONTROLLER_BLOB,'gate_contract':{'radius':RADIUS,'max_pixel_error_le':MAX_PIXEL_ERROR},'rows':rows,'source_sha256':{'gate.py':sha256(HERE/'gate.py'),'run.py':sha256(HERE/'run.py')}}
    (OUT/'result.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'rows':len(rows),'swap_eligible':sum(r['gate']['eligible'] for r in rows if r['variant']=='swap')},sort_keys=True))
if __name__=='__main__':main()
