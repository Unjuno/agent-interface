import json,subprocess,hashlib
from pathlib import Path
from PIL import Image
out=Path('/out');rows=[]
for arm,task,box in [('B',1,(120,394,332,409)),('B',4,(499,544,799,573))]:
 root=Path('/prior/formal-output/block-1')/arm;row=json.loads((root/f'task-{task}.json').read_text());program=next(p for p in row['programs'] if p['label']==f'check-submit-task-{task}');obs=program['observations'][-1];image=root/'client/runtime'/Path(obs['image']).name
 crop=out/f'qualification-{task}.png'
 with Image.open(image) as im:im.crop(box).resize(((box[2]-box[0])*4,(box[3]-box[1])*4)).save(crop)
 result=subprocess.run(['tesseract',str(crop),'stdout','--psm','7','-c','tessedit_char_whitelist=abcdefghijklmnopqrstuvwxyz0123456789-'],text=True,capture_output=True)
 rows.append({'task':task,'expected':row['task']['token'],'stdout':result.stdout,'exit':result.returncode,'exact':result.returncode==0 and result.stdout.strip()==row['task']['token'],'source_sha256':hashlib.sha256(image.read_bytes()).hexdigest(),'box':box})
(out/'SAVED_OCR_QUALIFICATION.json').write_text(json.dumps({'scope':'post-run saved screenshot compatibility only; no compiled graph execution','rows':rows},indent=2));print(json.dumps(rows));assert all(x['exact'] for x in rows)
