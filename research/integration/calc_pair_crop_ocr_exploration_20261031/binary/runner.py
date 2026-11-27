from PIL import Image,ImageOps
from pathlib import Path
import subprocess,json,hashlib
out=Path('/out');receipt=[]
for case in ('positive','blank','wrong'):
 img=Image.open('/in/'+case+'.png').convert('RGB')
 for name,box in [('A1',(95,144,126,159)),('A2',(95,161,126,176))]:
  crop=img.crop(box);crop.putdata([(255,255,255) if b>r+30 and b>g+20 else (r,g,b) for r,g,b in crop.getdata()]);crop=crop.convert('L').point(lambda x:0 if x<160 else 255);crop=crop.resize(((box[2]-box[0])*4,(box[3]-box[1])*4),Image.Resampling.NEAREST);crop=ImageOps.expand(crop,border=16,fill=255);path=out/(case+'-'+name+'.png');crop.save(path)
  r=subprocess.run(['tesseract',str(path),'stdout','--psm','7','-c','tessedit_char_whitelist=0123456789','tsv'],capture_output=True,timeout=10);(out/(case+'-'+name+'.tsv')).write_bytes(r.stdout);(out/(case+'-'+name+'.stderr')).write_bytes(r.stderr);receipt.append({'case':case,'cell':name,'exit':r.returncode,'crop_sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
(out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
