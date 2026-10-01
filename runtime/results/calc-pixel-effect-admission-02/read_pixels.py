import csv,hashlib,io,json,subprocess,sys,time
from pathlib import Path
from PIL import Image
image=Path(sys.argv[1]);contract=json.loads(Path(sys.argv[2]).read_text());out=Path(sys.argv[3]);out.mkdir(exist_ok=False)
rgb=Image.open(image).convert('RGB');rows=[]
for name,box in contract['regions'].items():
 crop=rgb.crop(box).resize(((box[2]-box[0])*4,(box[3]-box[1])*4),Image.Resampling.NEAREST)
 data=io.BytesIO();crop.save(data,format='PNG');payload=data.getvalue();(out/(name+'.png')).write_bytes(payload)
 started=time.monotonic_ns()
 p=subprocess.run(['tesseract','stdin','stdout','-l','eng','--psm','7','tsv'],input=payload,capture_output=True,timeout=2)
 ended=time.monotonic_ns();(out/(name+'.tsv')).write_bytes(p.stdout);(out/(name+'.stderr')).write_bytes(p.stderr)
 words=[r for r in csv.DictReader(io.StringIO(p.stdout.decode()),delimiter='\t') if r.get('level')=='5' and r.get('text','').strip()]
 value=words[0]['text'] if p.returncode==0 and len(words)==1 and float(words[0]['conf'])>=90 else 'unknown'
 rows.append(dict(region=name,box=box,value=value,words=words,returncode=p.returncode,started_ns=started,ended_ns=ended,crop_sha256=hashlib.sha256(payload).hexdigest()))
result=dict(source=str(image),source_sha256=hashlib.sha256(image.read_bytes()).hexdigest(),rows=rows,scope='visible text; no persisted effect, task score or input authority')
(out/'reading.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
