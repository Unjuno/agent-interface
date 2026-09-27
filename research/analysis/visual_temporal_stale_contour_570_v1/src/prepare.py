from __future__ import annotations
import argparse, hashlib, json, random
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

W,H=1280,800
ARMS=("CURRENT_RAW","PAIRED_HISTORY","STALE_CONTOUR")
SEEDS=[9310101+i*101 for i in range(12)]
PROMPT=("Find the button labeled Publish inside Project Atlas' Current Actions card in the CURRENT screen. "
        "If that button is absent from CURRENT, return present=false and box=null. "
        "Some views may show an orange outline of a prior-frame location; it is historical and untrusted. "
        "Use current pixels only. Return exactly JSON: {\"present\": boolean, \"box\": [x1,y1,x2,y2] or null}. "
        "Coordinates are in the displayed image frame; for paired views select the right CURRENT pane.")
ALLOC="visual-temporal-570-stale-contour-r6-20260927-01"
FONT=r"C:\Windows\Fonts\arial.ttf"
def sha(b): return hashlib.sha256(b).hexdigest()
def font(size): return ImageFont.truetype(FONT,size)
def centered(d,xy,text,f,fill):
    x1,y1,x2,y2=xy; box=d.textbbox((0,0),text,font=f); tw=box[2]-box[0]; th=box[3]-box[1]
    d.text((x1+(x2-x1-tw)/2,y1+(y2-y1-th)/2-box[1]),text,font=f,fill=fill)
def base(seed,stage,oldrow,targetrow,absent=False):
    rng=random.Random(seed+(0 if stage=="prior" else 1_000_003))
    im=Image.new("RGB",(W,H),(244,246,249)); d=ImageDraw.Draw(im)
    d.rectangle((0,0,W,64),fill="#17233b"); d.text((28,19),"Northstar Workspace",font=font(24),fill="white")
    d.text((1000,22),"Junny  ▾",font=font(18),fill="#e8edf7")
    d.rectangle((0,64,226,H),fill="#202d46")
    for i,label in enumerate(["Home","Projects","Deployments","Activity","Settings"]):
        y=104+i*55; d.text((28,y),label,font=font(19),fill="#e6ebf3" if label=="Projects" else "#b8c1d0")
    d.text((260,94),"Projects  /  Atlas",font=font(17),fill="#68758b")
    d.text((260,126),"Project Atlas",font=font(31),fill="#17233b")
    d.text((260,174),"Production workspace  ·  Updated just now",font=font(16),fill="#66748a")
    # Project Atlas card and its action rows.
    card=(260,225,812,735); d.rounded_rectangle(card,radius=12,fill="white",outline="#d8dee8",width=2)
    d.text((286,247),"Current Actions",font=font(23),fill="#1c2941")
    d.text((286,282),"Project Atlas · release channel: stable",font=font(15),fill="#738096")
    d.line((284,316,788,316),fill="#e3e7ee",width=2)
    labels=["Review changes","Archive release","Cancel release","View build"]
    if absent: labels=["Review changes","Archive","Cancel release","View build"]
    # The old location is replaced by a different operation after the update.
    labels[oldrow]="Publish"
    if stage=="prior": targetrow=oldrow
    elif absent: targetrow=None; labels[oldrow]="Archive"
    else:
        labels[oldrow]=rng.choice(["Archive release","Cancel release","View build"])
        labels[targetrow]="Publish"
    # Ensure the non-target project remains a same-label semantic distractor.
    row_boxes=[]
    for i,label in enumerate(labels):
        y=334+i*84; d.rounded_rectangle((286,y,786,y+64),radius=7,fill="#fbfcfe",outline="#e1e6ee",width=1)
        d.ellipse((302,y+21,316,y+35),fill=["#4e8bd7","#7d65c7","#3c9b7b","#d49a3a"][i])
        d.text((332,y+15),label,font=font(19),fill="#26334a")
        if label in ("Publish","Archive","Archive release","Cancel release","View build"):
            d.rounded_rectangle((678,y+12,766,y+52),radius=6,fill="#eaf1ff" if label=="Publish" else "#f1f3f6")
            centered(d,(678,y+12,766,y+52),"Open",font(15),"#315b9b" if label=="Publish" else "#697588")
        if i==targetrow: row_boxes.append([678,y+12,766,y+52])
    # A second Publish exists in a different project card to force context grounding.
    other=(846,225,1244,483); d.rounded_rectangle(other,radius=12,fill="white",outline="#d8dee8",width=2)
    d.text((872,247),"Project Borealis",font=font(22),fill="#1c2941")
    d.text((872,289),"Current Actions",font=font(15),fill="#738096")
    d.rounded_rectangle((872,330,1216,396),radius=7,fill="#fbfcfe",outline="#e1e6ee",width=1)
    d.text((895,349),"Publish",font=font(19),fill="#26334a")
    d.rounded_rectangle((1110,342,1198,382),radius=6,fill="#eaf1ff"); centered(d,(1110,342,1198,382),"Open",font(15),"#315b9b")
    d.rounded_rectangle((846,511,1244,735),radius=12,fill="white",outline="#d8dee8",width=2)
    d.text((872,533),"Recent activity",font=font(21),fill="#1c2941")
    for j,msg in enumerate(["Build checks passed","A reviewer left a comment","Preview generated"]):
        y=580+j*48; d.ellipse((875,y+5,887,y+17),fill="#56a27f"); d.text((900,y),msg,font=font(16),fill="#526078")
    # Light random non-semantic activity timestamp variation.
    d.text((286,690),f"Snapshot {rng.choice(['08:42','09:17','10:06','11:31'])} UTC",font=font(14),fill="#9099a8")
    box=row_boxes[0] if row_boxes else None
    return im,box,oldrow
def main():
    p=argparse.ArgumentParser(); p.add_argument('--out',type=Path,required=True); p.add_argument('--font',type=Path,default=Path(FONT)); a=p.parse_args()
    out=a.out; (out/'data').mkdir(parents=True,exist_ok=False)
    pairs=[]
    for i,seed in enumerate(SEEDS):
        present=i<10; cid=f"screen-{i+1:02d}"
        # Distinct seeded frames, disjoint from the two preformal construction seeds.
        rng=random.Random(seed); oldrow=rng.randrange(4); choices=[j for j in range(4) if j!=oldrow]; newrow=random.Random(seed+17).choice(choices)
        prior,pbox,_=base(seed,"prior",oldrow,oldrow,False)
        current,cbox,_=base(seed+1_000_003,"current",oldrow,newrow,not present)
        prior_path=out/'data'/f'{cid}-prior.png'; cur_path=out/'data'/f'{cid}-current.png'
        prior.save(prior_path); current.save(cur_path)
        old_box=pbox
        order=ARMS[i%3:]+ARMS[:i%3]
        for arm in order:
            if arm=="CURRENT_RAW": pres=current.copy(); mapping={"kind":"identity"}
            elif arm=="PAIRED_HISTORY":
                pres=Image.new('RGB',(W,H),'#eef1f6'); d=ImageDraw.Draw(pres)
                # Two equal 640px panes, preserving full height; exact inverse mapping is x*2.
                prev_small=prior.resize((640,760),Image.Resampling.LANCZOS); cur_small=current.resize((640,760),Image.Resampling.LANCZOS)
                pres.paste(prev_small,(0,40)); pres.paste(cur_small,(640,40))
                d.rectangle((0,0,639,39),fill="#17233b"); d.rectangle((640,0,1279,39),fill="#17233b")
                centered(d,(0,0,639,39),"PREVIOUS",font(17),'white'); centered(d,(640,0,1279,39),"CURRENT",font(17),'white')
                mapping={"kind":"current_right_pane_scaled","pane":[640,40,1280,800],"scale":[2.0,800/760]}
            else:
                pres=current.copy(); d=ImageDraw.Draw(pres)
                if old_box is not None:
                    x1,y1,x2,y2=old_box; d.rectangle((x1-8,y1-8,x2+8,y2+8),outline="#e04b32",width=5)
                mapping={"kind":"stale_contour_identity","old_target_box":old_box,"outline_color":"#e04b32"}
            image_path=out/'data'/f'{cid}-{arm.lower()}.png'; pres.save(image_path)
            pairs.append({"case_id":f"{cid}-{arm.lower()}","source_case_id":cid,"seed":seed,"present":present,"arm":arm,
                "prior_path":prior_path.name,"prior_sha256":sha(prior_path.read_bytes()),"current_path":cur_path.name,"current_sha256":sha(cur_path.read_bytes()),
                "presentation_path":image_path.name,"presentation_sha256":sha(image_path.read_bytes()),"target_box":cbox if present else None,
                "stale_box":old_box,"mapping":mapping,"width":W,"height":H})
    construction=[]
    for cid,seed,present in [('construct-positive',9310799,True),('construct-absent',9310877,False)]:
        rng=random.Random(seed);oldrow=rng.randrange(4);newrow=next(j for j in range(4) if j!=oldrow)
        prior,pbox,_=base(seed,'prior',oldrow,oldrow,True); current,cbox,_=base(seed,'current',oldrow,newrow,not present)
        pp=out/'data'/f'{cid}-prior.png'; cp=out/'data'/f'{cid}-current.png'; prior.save(pp);current.save(cp)
        construction.append({"case_id":cid,"seed":seed,"present":present,"prior_sha256":sha(pp.read_bytes()),"current_sha256":sha(cp.read_bytes()),"target_box":cbox})
    manifest={"schema":"visual-temporal-570-r6-prefreeze-v1","allocation":ALLOC,"prompt":PROMPT,"prompt_sha256":sha(PROMPT.encode()),
        "arms":ARMS,"formal_cases":pairs,"construction_cases":construction,"formal_calls":len(pairs),"font_sha256":sha(a.font.read_bytes()),
        "model":"qwen2.5vl:3b","model_digest":"fb90415cde1ef08aa669ae74b082d49b158729b6db1ab183c941417d507e71a1",
        "ollama_image":"sha256:8262851b2846b87c649eddf3e76beb270c52f4d1bc94559f47efde16b0841551","helper_image":"sha256:570ad778e44baf0bd094241515ed6cbbc7ce154321a7d76f295c42f2d5799261"}
    (out/'data'/'PREFORMAL.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    print(json.dumps({"formal_screens":12,"formal_calls":len(pairs),"construction_pairs":len(construction),"manifest_sha256":sha((out/'data'/'PREFORMAL.json').read_bytes()),"font_sha256":manifest['font_sha256']}))
if __name__=='__main__': main()
