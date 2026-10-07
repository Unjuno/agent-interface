import json,pathlib,hashlib,subprocess,time
from PIL import Image,ImageOps
R=pathlib.Path('/src');O=pathlib.Path('/out');rows=[]
for case in json.loads((R/'INPUTS.json').read_text()):
 p=R/'inputs'/case['path'];assert hashlib.sha256(p.read_bytes()).hexdigest()==case['sha256']
 im=Image.open(p).convert('RGB');cells=[]
 for i,box in enumerate([(37,161,124,175),(127,161,215,175),(217,161,305,175)]):
  cell=im.crop(box);mask=cell.convert('L').point(lambda v:255 if v<130 else 0);bounds=mask.getbbox()
  if bounds is None:cells.append(dict(index=i,bounds=None,value=None));continue
  c=cell.crop(bounds);dst=O/(case['id']+'-'+str(i)+'.png');ImageOps.expand(c.resize((c.width*4,c.height*4),Image.Resampling.BICUBIC),border=20,fill='white').save(dst)
  args=['tesseract',str(dst),'stdout','--psm','8','-l','eng','-c','tessedit_char_whitelist=0123456789'];s=time.monotonic_ns();r=subprocess.run(args,capture_output=True,text=True,timeout=10);value=r.stdout.strip()
  cells.append(dict(index=i,bounds=bounds,value=value if r.returncode==0 and value.isascii() and value.isdigit() else None,argv=args,start_ns=s,end_ns=time.monotonic_ns(),exit_code=r.returncode,stdout=r.stdout,stderr=r.stderr,crop_sha256=hashlib.sha256(dst.read_bytes()).hexdigest()))
 rows.append(dict(id=case['id'],source_sha256=case['sha256'],cells=cells,values=[c['value'] for c in cells] if all(c['value'] is not None for c in cells) else None))
with (O/'RAW.json').open('x') as f:json.dump(rows,f,indent=2)
print(json.dumps(dict(cases=len(rows),values=[r['values'] for r in rows])))
