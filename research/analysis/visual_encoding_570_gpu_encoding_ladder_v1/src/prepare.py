from __future__ import annotations

import argparse, hashlib, json, random
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

W, H = 1280, 800
ALLOCATION = "visual-encoding-570-grid-context-r5-20260927-01"
SEEDS = [12011, 12037, 12071, 12101, 12107, 12109, 12113, 12119, 12131, 12137, 12203, 12211]
ARMS = ["RAW", "BORDER_RULER", "COARSE_GRID", "CONTEXT_CROP", "GRID_CONTEXT"]
SLOTS = [(105,238,435,355),(475,238,805,355),(845,238,1175,355),(105,442,435,559),(475,442,805,559),(845,442,1175,559)]
PROMPT = ("Inspect this synthetic application panel and locate the single blue Apply button. "
          "Return only JSON matching the supplied schema. The image is 1280x800 pixels; "
          "report [left,top,right,bottom] pixel-edge coordinates in THIS presented image. "
          "If no Apply button is visible, return present=false and box=null. Do not guess from other labels.")

def sha(b: bytes) -> str: return hashlib.sha256(b).hexdigest()

def draw_source(seed: int, present: bool, font_path: Path, out: Path) -> dict:
    rng=random.Random(seed); im=Image.new("RGB",(W,H),"#f2f5f9"); d=ImageDraw.Draw(im)
    font=ImageFont.truetype(str(font_path),29); head=ImageFont.truetype(str(font_path),39); small=ImageFont.truetype(str(font_path),22)
    d.rounded_rectangle((40,35,1240,765),radius=24,fill="white",outline="#ccd4df",width=3)
    d.rectangle((43,38,1237,126),fill="#24364b"); d.text((82,58),"APPLICATION SETTINGS",font=head,fill="white")
    d.text((82,157),"Review the available actions",font=small,fill="#526273")
    labels=["Save","Cancel","Reset","Close","Help","More"]
    if present: labels[rng.randrange(6)]="Apply"
    rng.shuffle(labels); order=list(range(6)); rng.shuffle(order); target=None; buttons=[]
    for label,slot in zip(labels,order):
        x1,y1,x2,y2=SLOTS[slot]; yes=(label=="Apply"); fill="#2367c9" if yes else "#e9eef5"; ink="white" if yes else "#304154"
        d.rounded_rectangle((x1,y1,x2,y2),radius=18,fill=fill,outline="#8796a8",width=2)
        bb=d.textbbox((0,0),label,font=font); tx=x1+((x2-x1)-(bb[2]-bb[0]))//2; ty=y1+((y2-y1)-(bb[3]-bb[1]))//2-bb[1]
        d.text((tx,ty),label,font=font,fill=ink); box=[x1,y1,x2,y2]; buttons.append({"label":label,"box":box})
        if yes: target=box
    d.text((82,694),"Changes are not saved until you choose an action.",font=small,fill="#647386")
    im.save(out,format="PNG",optimize=False)
    return {"seed":seed,"present":present,"target_box":target,"buttons":buttons,"width":W,"height":H,"source_path":out.name,"source_sha256":sha(out.read_bytes())}

def transform(src: Image.Image, arm: str, dst: Path, font_path: Path) -> dict:
    im=src.copy(); mapping={"kind":"identity"}
    if arm=="BORDER_RULER":
        d=ImageDraw.Draw(im); f=ImageFont.truetype(str(font_path),13)
        for x in range(0,W+1,100):
            d.line((x,0,x,15),fill="#ff2020",width=2)
            if x<W: d.text((x+2,1),str(x),font=f,fill="#b00000")
        for y in range(0,H+1,100):
            d.line((0,y,15,y),fill="#ff2020",width=2)
            if y<H: d.text((1,y+2),str(y),font=f,fill="#b00000")
    elif arm in ("COARSE_GRID","GRID_CONTEXT"):
        # Sparse 200-pixel grid is deterministic and non-occluding at button centers.
        if arm=="GRID_CONTEXT":
            crop=im.crop((40,130,1240,700)); resized=crop.resize((1200,570),Image.Resampling.LANCZOS)
            canvas=Image.new("RGB",(W,H),"#dbe5f0"); canvas.paste(resized,(40,130)); im=canvas
            mapping={"kind":"crop_resize","crop":[40,130,1240,700],"paste_xy":[40,130],"resized_wh":[1200,570]}
        d=ImageDraw.Draw(im); f=ImageFont.truetype(str(font_path),15)
        for x in range(200,W,200):
            d.line((x,0,x,H),fill="#19a0a0",width=1); d.text((x+2,18),str(x),font=f,fill="#006a6a")
        for y in range(200,H,200):
            d.line((0,y,W,y),fill="#19a0a0",width=1); d.text((18,y+2),str(y),font=f,fill="#006a6a")
        if arm=="GRID_CONTEXT": mapping["grid_step_px"]=200
    elif arm=="CONTEXT_CROP":
        # Enlarges the same fixed application body; crop selection is independent of target identity.
        crop_box=(40,130,1240,700); crop=im.crop(crop_box); resized=crop.resize((1200,684),Image.Resampling.LANCZOS)
        canvas=Image.new("RGB",(W,H),"#dbe5f0"); canvas.paste(resized,(40,58)); d=ImageDraw.Draw(canvas)
        d.rectangle((39,57,1241,743),outline="#24364b",width=3); im=canvas
        mapping={"kind":"crop_resize","crop":list(crop_box),"paste_xy":[40,58],"resized_wh":[1200,684]}
    elif arm!="RAW": raise ValueError(arm)
    im.save(dst,format="PNG",optimize=False)
    return {"arm":arm,"image_path":dst.name,"image_sha256":sha(dst.read_bytes()),"mapping":mapping}

def main():
    p=argparse.ArgumentParser(); p.add_argument("--font",type=Path,required=True); p.add_argument("--out",type=Path,required=True); a=p.parse_args()
    if not a.font.is_file(): raise SystemExit("font missing")
    a.out.mkdir(parents=True,exist_ok=False); cases=[]; construction=[]
    for n,seed in enumerate(SEEDS):
        present=n<10; cid=(f"positive-{n+1:02d}" if present else f"absent-{n-9:02d}")
        src=a.out/f"{cid}-source.png"; base=draw_source(seed,present,a.font,src)
        for arm in ARMS:
            path=a.out/f"{cid}-{arm.lower()}.png"; tr=transform(Image.open(src).convert("RGB"),arm,path,a.font)
            cases.append({"case_id":f"{cid}-{arm.lower()}","source_case_id":cid,"seed":seed,"present":present,"target_box":base["target_box"],"arm":arm,
                          "source_path":base["source_path"],"source_sha256":base["source_sha256"],"image_path":tr["image_path"],"image_sha256":tr["image_sha256"],"mapping":tr["mapping"],"width":W,"height":H})
    co=a.out/"construction"; co.mkdir()
    for cid,seed,present in [("construct-positive",12347,True),("construct-absent",12373,False)]:
        src=co/f"{cid}-source.png"; base=draw_source(seed,present,a.font,src)
        for arm in ARMS:
            path=co/f"{cid}-{arm.lower()}.png"; tr=transform(Image.open(src).convert("RGB"),arm,path,a.font)
            construction.append({"case_id":f"{cid}-{arm.lower()}","source_case_id":cid,"seed":seed,"present":present,"target_box":base["target_box"],"arm":arm,"source_path":str(src.relative_to(a.out)),"source_sha256":base["source_sha256"],"image_path":str(path.relative_to(a.out)),"image_sha256":tr["image_sha256"],"mapping":tr["mapping"],"width":W,"height":H})
    pref={"schema":"visual-encoding-570-r5-preformal-v1","allocation":ALLOCATION,"prompt":PROMPT,"prompt_sha256":sha(PROMPT.encode()),"arms":ARMS,"source_cases":12,"formal_cases":cases,"formal_requests":len(cases),"construction_cases":construction,"construction_model_calls":0,"font_sha256":sha(a.font.read_bytes()),"model":"qwen2.5vl:3b","model_digest":"fb90415cde1ef08aa669ae74b082d49b158729b6db1ab183c941417d507e71a1","model_layer_sha256":"e9758e589d443f653821b7be9bb9092c1bf7434522b70ec6e83591b1320fdb4d","model_layer_bytes":3200614720,"ollama_image":"sha256:8262851b2846b87c649eddf3e76beb270c52f4d1bc94559f47efde16b0841551","helper_image":"sha256:570ad778e44baf0bd094241515ed6cbbc7ce154321a7d76f295c42f2d5799261","no_network_or_provider":True}
    (a.out/"PREFORMAL.json").write_text(json.dumps(pref,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({"source_screens":12,"presentation_images":len(cases),"pref_sha256":sha((a.out/"PREFORMAL.json").read_bytes())}))
if __name__=="__main__": main()
