"""Append a visual-only before/after zoom around a pointer action path."""
import argparse,hashlib,json
from pathlib import Path
from PIL import Image,ImageDraw

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def read(path):return json.loads(path.read_text(encoding='utf-8'))

def build(run_root,turn,out,margin_x=72,margin_y=64,scale=2):
    typed=read(run_root/f'typed-{turn}.json');applied=read(run_root/f'applied-{turn}.json')
    drags=[step for step in typed.get('steps',[]) if step.get('op')=='pointer_drag']
    if len(drags)!=1:raise ValueError('exactly one pointer_drag required')
    points=drags[0]['points'];runtime=run_root/'runtime'
    before=runtime/Path(applied['source_observation']['image']).name
    after=runtime/Path(applied['result']['state']['continuation']['observation']['image']).name
    with Image.open(before) as opened:before_image=opened.convert('RGB')
    with Image.open(after) as opened:after_image=opened.convert('RGB')
    if before_image.size!=after_image.size:raise ValueError('frame geometry changed')
    width,height=after_image.size;xs=[p['x'] for p in points];ys=[p['y'] for p in points]
    box=(max(0,min(xs)-margin_x),max(0,min(ys)-margin_y),min(width,max(xs)+margin_x+1),min(height,max(ys)+margin_y+1))
    before_crop=before_image.crop(box).resize(((box[2]-box[0])*scale,(box[3]-box[1])*scale),Image.Resampling.NEAREST)
    after_crop=after_image.crop(box).resize(before_crop.size,Image.Resampling.NEAREST)
    gap=16;label_h=28;strip_w=before_crop.width*2+gap;strip_h=label_h+before_crop.height
    strip=Image.new('RGB',(strip_w,strip_h),'white');draw=ImageDraw.Draw(strip);draw.text((8,7),f'BEFORE action region {box}',fill='black');draw.text((before_crop.width+gap+8,7),f'AFTER action region {box}',fill='black');strip.paste(before_crop,(0,label_h));strip.paste(after_crop,(before_crop.width+gap,label_h))
    canvas=Image.new('RGB',(max(width,strip_w),height+strip_h),(32,32,32));canvas.paste(after_image,(0,0));canvas.paste(strip,(0,height));out.mkdir(parents=True,exist_ok=False);image_path=out/'full-after-plus-action-region.png';canvas.save(image_path,compress_level=6)
    manifest={'format':'action-region-zoom-v1','scope':'archived visual-only presentation; no model call or engine/oracle fields','turn':turn,'crop_box':list(box),'scale':scale,'full_frame_rows':height,'source_dimensions':[width,height],'presentation_dimensions':list(canvas.size),'drag_points':points,'sources':{'script_sha256':sha(Path(__file__)),'typed_sha256':sha(run_root/f'typed-{turn}.json'),'applied_sha256':sha(run_root/f'applied-{turn}.json'),'before_sha256':sha(before),'after_sha256':sha(after)},'output':{'path':image_path.name,'sha256':sha(image_path),'bytes':image_path.stat().st_size}}
    (out/'manifest.json').write_bytes((json.dumps(manifest,indent=2)+'\n').encode('utf-8'));return manifest

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('run_root',type=Path);parser.add_argument('turn',type=int);parser.add_argument('out',type=Path);args=parser.parse_args();print(json.dumps(build(args.run_root,args.turn,args.out),indent=2))
