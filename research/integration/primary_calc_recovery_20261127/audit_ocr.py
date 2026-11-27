"""Independently reproduce the retained fixture-specific OCR from the original PNG."""
import hashlib,io,json,subprocess,zipfile
from pathlib import Path
from PIL import Image
p=Path('/input/trial.zip')
with zipfile.ZipFile(p) as z:
 with Image.open(io.BytesIO(z.read('output/second-exchange/image-1-1.png'))) as raw:
  image=raw.convert('RGB')
  if hashlib.sha256(image.crop((0,97,42,119)).tobytes()).hexdigest()!='2e86f3a0f6d87ee4fb4e5ffeb7cfd159d715cb5f6f8177b0ede83784d49088cf':raise ValueError('A1 name box differs')
  crop=image.crop((230,97,275,119)).resize((450,220),Image.Resampling.NEAREST)
  with Image.open(io.BytesIO(z.read('output/recovery-formula.png'))) as saved:
   if crop.tobytes()!=saved.convert('RGB').tobytes():raise ValueError('crop pixels differ')
  buf=io.BytesIO();crop.save(buf,format='PNG')
  r=subprocess.run(['tesseract','stdin','stdout','--psm','8','-c','tessedit_char_whitelist=0123456789'],input=buf.getvalue(),capture_output=True,timeout=10)
  text=r.stdout.decode().strip()
  if r.returncode!=0 or text!='7':raise ValueError('OCR replay differs')
  print(json.dumps({'status':'audited','name_box':'A1 fixture pixel match','crop_pixels_match':True,'ocr':text,'exit_code':r.returncode},sort_keys=True))
