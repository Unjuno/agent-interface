from __future__ import annotations
import hashlib,json,xml.etree.ElementTree as ET
from pathlib import Path
from PIL import Image
HERE=Path(__file__).resolve().parent; OUT=HERE/'formal-output'
R=json.loads((OUT/'result.json').read_text())

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def gate_independent(refp,curp,A):
    ref=Image.open(refp).convert('RGB');cur=Image.open(curp).convert('RGB');x,y=map(int,A);r=5
    if ref.size!=cur.size or not(r<=x<cur.width-r and r<=y<cur.height-r): return False,None
    rb=ref.crop((x-r,y-r,x+r+1,y+r+1)).tobytes();cb=cur.crop((x-r,y-r,x+r+1,y+r+1)).tobytes()
    d=max(abs(a-b) for a,b in zip(rb,cb));return d<=8,float(d)
def oracle(svg,A):
    root=ET.parse(svg).getroot(); ids=[]
    for e in root.iter():
      if e.tag.endswith('circle') and float(e.attrib['cx'])==float(A[0]) and float(e.attrib['cy'])==float(A[1]):ids.append(e.attrib.get('id'))
    if len(ids)!=1: raise ValueError(ids)
    return ids[0]
def main():
    errors=[]
    if R.get('formal_deterministic_invocations')!=1:errors.append('invocations')
    if R.get('reruns')!=0:errors.append('reruns')
    if R.get('controller_blob')!='0e44f30660d4ef2b4a78ac2b92db7991e7d1c48a':errors.append('controller_blob')
    if R.get('gate_contract')!={'radius':5,'max_pixel_error_le':8.0}:errors.append('gate_contract')
    if R.get('source_sha256',{}).get('gate.py')!=sha(HERE/'gate.py'):errors.append('gate_sha')
    if R.get('source_sha256',{}).get('run.py')!=sha(HERE/'run.py'):errors.append('run_sha')
    counts={'stable':0,'swap':0,'changed':0};false_accept=0
    for row in R['rows']:
      v=row['variant'];counts[v]+=1;d=OUT/f"seed-{row['seed']}";ref=d/'reference.png';cur=d/f'{v}.png';svg=d/f'{v}.svg'
      ok,diff=gate_independent(ref,cur,row['A']); oid=oracle(svg,row['A'])
      if ok!=row['gate']['eligible'] or diff!=row['gate']['max_pixel_error']:errors.append(f"gate:{row['seed']}:{v}")
      if oid!=row['oracle_id_at_A']:errors.append(f"oracle:{row['seed']}:{v}")
      rgb_equal=Image.open(ref).convert('RGB').tobytes()==Image.open(cur).convert('RGB').tobytes()
      if rgb_equal!=row['rgb_identical']:errors.append(f"rgb_flag:{row['seed']}:{v}")
      if v=='stable' and not(ok and oid=='task-target' and rgb_equal):errors.append(f"stable:{row['seed']}")
      if v=='swap':
        if not (ok and oid=='decoy' and rgb_equal):errors.append(f"swap:{row['seed']}")
        if ok and oid=='decoy':false_accept+=1
      if v=='changed' and ok:errors.append(f"changed_not_rejected:{row['seed']}")
    if counts!={'stable':4,'swap':4,'changed':4}:errors.append('counts')
    decision='REJECT_LOCAL_PATCH_AS_SEMANTIC_IDENTITY_SCOPED' if not errors and false_accept==4 else ('HOLD_RENDERER_NOT_PIXEL_EQUIVALENT' if not errors else 'FAIL_INTEGRITY_OR_DISCRIMINATOR')
    report={'decision':decision,'errors':errors,'counts':counts,'false_alias_acceptances':false_accept}
    (OUT/'audit.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');print(json.dumps(report,sort_keys=True));raise SystemExit(bool(errors))
if __name__=='__main__':main()
