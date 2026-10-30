from PIL import Image,ImageOps
from pathlib import Path
import subprocess,json,hashlib
img=Image.open('/in/source.png').convert('RGB');out=Path('/out');results=[]
for name,box in [('A1',(95,144,126,159)),('A2',(95,161,126,176))]:
 crop=img.crop(box);crop.putdata([(255,255,255) if b>r+30 and b>g+20 else (r,g,b) for r,g,b in crop.getdata()]);crop=crop.convert('L').resize(((box[2]-box[0])*4,(box[3]-box[1])*4),Image.Resampling.LANCZOS);crop=ImageOps.expand(crop,border=16,fill=255);path=out/(name+'.png');crop.save(path)
 r=subprocess.run(['tesseract',str(path),'stdout','--psm','7','-c','tessedit_char_whitelist=0123456789','tsv'],capture_output=True,timeout=10);(out/(name+'.tsv')).write_bytes(r.stdout);(out/(name+'.stderr')).write_bytes(r.stderr);results.append({'name':name,'box':box,'crop_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'exit':r.returncode})
(out/'ocr-receipt.json').write_text(json.dumps(results,indent=2)+'\n')
