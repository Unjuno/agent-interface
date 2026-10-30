from PIL import Image,ImageOps
from pathlib import Path
import subprocess,json,hashlib
source=Path('/in/source.png');out=Path('/out');img=Image.open(source).convert('L');results=[]
for name,box in [('A1',(95,144,125,158)),('A2',(95,161,125,175))]:
 crop=img.crop(box).resize(((box[2]-box[0])*4,(box[3]-box[1])*4),Image.Resampling.NEAREST)
 crop=ImageOps.expand(crop,border=12,fill=255);path=out/(name+'.png');crop.save(path)
 r=subprocess.run(['tesseract',str(path),'stdout','--psm','7','-c','tessedit_char_whitelist=0123456789','tsv'],capture_output=True,timeout=10)
 (out/(name+'.tsv')).write_bytes(r.stdout);(out/(name+'.stderr')).write_bytes(r.stderr);results.append({'name':name,'box':box,'crop_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'exit':r.returncode})
(out/'ocr-receipt.json').write_text(json.dumps(results,indent=2)+'\n')
