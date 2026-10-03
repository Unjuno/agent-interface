import json,pathlib
from PIL import Image
def split(image,box):
    im=image.convert('RGB').crop(box);w,h=im.size
    pix=[[(max(im.getpixel((x,y)))<130) for x in range(w)] for y in range(h)]
    active=[any(row[x] for row in pix) for x in range(w)];segments=[];x=0
    while x<w:
        if not active[x]:x+=1;continue
        start=x
        while x<w and active[x]:x+=1
        cols=range(start,x);ys=[y for y in range(h) if any(pix[y][c] for c in cols)]
        bits='\n'.join(''.join('1' if pix[y][c] else '0' for c in cols) for y in range(min(ys),max(ys)+1))
        segments.append(bits)
    return segments

def read_values(path):
    model=json.loads((pathlib.Path(__file__).parent/'DIGIT_TEMPLATES.json').read_text())['glyphs'];image=Image.open(path);values=[]
    for box in [(37,161,124,175),(127,161,215,175),(217,161,305,175)]:
        segments=split(image,box)
        if not segments or any(bits not in model for bits in segments):return None
        values.append(''.join(model[bits] for bits in segments))
    return values
