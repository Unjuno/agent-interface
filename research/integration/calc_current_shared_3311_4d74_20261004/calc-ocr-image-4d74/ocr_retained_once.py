import json,pathlib,subprocess,hashlib
from PIL import Image,ImageOps
root=pathlib.Path('/data');out=pathlib.Path('/out');results=[]
for name,relative,stage,expected in [('heldout','calc-compiled-digits-4d74','compiled_digits08',['23','31','713']),('unsupported','calc-compiled-digitunavailable-4d74','compiled_digitunavailable09',['20','31','620'])]:
    folder=root/relative/'runs'/stage;raw=json.loads((folder/'raw.json').read_text());art=raw['images'][1]['native']['artifact'];path=folder/'guarded/images'/art['path'].rsplit('/',1)[-1]
    image=Image.open(path);original=path.read_bytes()
    if hashlib.sha256(original).hexdigest()!=art['sha256']:raise RuntimeError('source image digest')
    values=[];receipts=[]
    for i,box in enumerate([(37,161,124,175),(127,161,215,175),(217,161,305,175)]):
        crop=ImageOps.expand(image.convert('RGB').crop(box).resize((4*(box[2]-box[0]),4*(box[3]-box[1]))),border=20,fill='white');p=out/(name+'-'+str(i)+'.png');crop.save(p)
        args=['tesseract',str(p),'stdout','--psm','7','-l','eng','-c','tessedit_char_whitelist=0123456789'];r=subprocess.run(args,text=True,capture_output=True,timeout=10);value=r.stdout.strip();values.append(value);receipts.append({'argv':args,'exit_code':r.returncode,'stdout':r.stdout,'stderr':r.stderr})
    results.append({'case':name,'source_png_sha256':art['sha256'],'recognized':values,'expected_scoring_only':expected,'correct':values==expected,'receipts':receipts})
record={'scope':'new OCR diagnostic on immutable retained real-app images; no native replay or G08 regrading','version':subprocess.run(['tesseract','--version'],text=True,capture_output=True).stdout,'results':results}
(out/'RAW.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps({'results':[{'case':r['case'],'recognized':r['recognized'],'correct':r['correct']} for r in results]}))
