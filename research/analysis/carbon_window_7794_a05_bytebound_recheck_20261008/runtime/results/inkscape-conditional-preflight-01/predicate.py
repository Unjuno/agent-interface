"""Finite Inkscape screen-cue candidate. No observation/input or task oracle."""
import hashlib,io
from PIL import Image
LAYOUTS = {
 'diagonal_down': ((330,290,420,330),(500,380,610,430),(500,290,610,330),(330,380,420,430)),
 'diagonal_up': ((510,290,620,330),(330,380,420,430),(330,290,420,330),(510,380,620,430)),
}
def classify(rgb, layout):
    if layout not in LAYOUTS: raise ValueError('undeclared layout')
    if rgb.mode != 'RGB' or rgb.size != (1000,700): return None
    patches=[]
    for box in LAYOUTS[layout]:
        pixels=list(rgb.crop(box).getdata())
        dark=sum(max(p)<=16 for p in pixels)/len(pixels)
        light=sum(min(p)>=240 for p in pixels)/len(pixels)
        patches.append((dark,light))
    if all(p[0]>=.98 for p in patches[:2]) and all(p[1]>=.98 for p in patches[2:]): return True
    if all(p[1]>=.98 for p in patches): return False
    return None

def retained_cue(data, expected_sha256, layout):
    if hashlib.sha256(data).hexdigest()!=expected_sha256: raise ValueError('capture digest mismatch')
    with Image.open(io.BytesIO(data)) as image:
        image.load()
        return classify(image.convert('RGB'),layout)
