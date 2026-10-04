import json,pathlib,subprocess,time,uuid
from PIL import Image,ImageOps
def read_values(path):
    image=Image.open(path);values=[]
    for box in [(37,161,124,175),(127,161,215,175),(217,161,305,175)]:
        p=pathlib.Path('/out')/('ocr-'+uuid.uuid4().hex+'.png');ImageOps.expand(image.convert('RGB').crop(box).resize((4*(box[2]-box[0]),4*(box[3]-box[1]))),border=20,fill='white').save(p)
        args=['tesseract',str(p),'stdout','--psm','7','-l','eng','-c','tessedit_char_whitelist=0123456789'];start=time.monotonic_ns();r=subprocess.run(args,text=True,capture_output=True,timeout=10);end=time.monotonic_ns()
        with pathlib.Path('/out/OCR_ATTEMPTS.jsonl').open('a') as f:f.write(json.dumps({'source':path,'crop':str(p),'argv':args,'start_ns':start,'end_ns':end,'exit_code':r.returncode,'stdout':r.stdout,'stderr':r.stderr})+'\n')
        value=r.stdout.strip()
        if r.returncode or not value or not value.isascii() or not value.isdigit():return None
        values.append(value)
    return values
