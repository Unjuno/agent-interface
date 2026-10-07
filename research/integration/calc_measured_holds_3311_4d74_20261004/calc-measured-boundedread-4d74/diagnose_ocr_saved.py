"""Post-run diagnostic of retained C2, not a rerun or regrading of G12."""
import hashlib,json,pathlib,subprocess,time
from PIL import Image,ImageOps
S=pathlib.Path('/data/guarded/images/7f6603128af94a63b82b9de3064c9adb.png')
O=pathlib.Path('/out');im=Image.open(S).convert('RGB');rows=[]
for scale,resample in [(4,Image.Resampling.NEAREST),(8,Image.Resampling.NEAREST),(4,Image.Resampling.BICUBIC),(8,Image.Resampling.BICUBIC)]:
 p=O/f'c2-{scale}-{resample.name}.png';crop=im.crop((217,161,305,175))
 ImageOps.expand(crop.resize((88*scale,14*scale),resample),border=20,fill='white').save(p)
 args=['tesseract',str(p),'stdout','--psm','7','-l','eng','-c','tessedit_char_whitelist=0123456789'];start=time.monotonic_ns();r=subprocess.run(args,text=True,capture_output=True,timeout=10)
 rows.append(dict(scale=scale,resample=resample.name,argv=args,start_ns=start,end_ns=time.monotonic_ns(),exit_code=r.returncode,stdout=r.stdout,stderr=r.stderr,crop_sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
result=dict(scope='POSTRUN_SAVED_IMAGE_DIAGNOSTIC_NOT_HELDOUT',source_sha256=hashlib.sha256(S.read_bytes()).hexdigest(),rows=rows,cgroups={k:pathlib.Path('/sys/fs/cgroup/'+k).read_text().strip() for k in ['cpu.max','memory.max']})
with (O/'RAW.json').open('x') as f:json.dump(result,f,indent=2)
print(json.dumps(result))
