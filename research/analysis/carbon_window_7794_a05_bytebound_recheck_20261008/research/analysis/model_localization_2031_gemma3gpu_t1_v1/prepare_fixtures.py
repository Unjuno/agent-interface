#!/usr/bin/env python3
"""Create frozen synthetic GUI screenshots; truth remains in a separate oracle file."""
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
FIXTURES = ROOT / "candidate_inputs" / "screens"
FIXTURES.mkdir(parents=True, exist_ok=True)
FONT_PATH = "/fonts/NimbusSans-Regular.otf"
FONT_BOLD = "/fonts/NimbusSans-Bold.otf"
F_TITLE = ImageFont.truetype(FONT_BOLD, 25)
F_TEXT = ImageFont.truetype(FONT_PATH, 22)
F_SMALL = ImageFont.truetype(FONT_PATH, 16)

CASES = [
    {"case_id":"duplicate-context-top-left","prompt":"Select the Save button in the ARCHIVE panel, not the DRAFTS panel.","panels":[("ARCHIVE",["Save","Export"],0),("DRAFTS",["Save","Delete"],0),("RECENT",["Open","Copy"],0),("TRASH",["Restore","Empty"],0)],"target_panel":0,"target_label":"Save","expected":"select"},
    {"case_id":"edge-small-target","prompt":"Select the tiny Sync control at the far lower-right of the SETTINGS panel.","panels":[("PROJECTS",["Open","Share"],0),("SETTINGS",["General","Privacy"],0),("HELP",["Docs","About"],0),("SETTINGS",["Sync"],1)],"target_panel":3,"target_label":"Sync","expected":"select"},
    {"case_id":"small-text-discriminator","prompt":"Select the Shore button in the COAST panel (the other panel says Share).", "panels":[("COAST",["Shore","Walk"],0),("SOCIAL",["Share","Invite"],0),("FILES",["Save","Move"],0),("TOOLS",["Crop","Rotate"],0)],"target_panel":0,"target_label":"Shore","expected":"select"},
    {"case_id":"target-absent","prompt":"Select the Delete button in the ARCHIVE panel. If that exact target is absent, abstain.","panels":[("ARCHIVE",["Save","Export"],0),("DRAFTS",["Save","Rename"],0),("RECENT",["Open","Copy"],0),("TRASH",["Restore","Empty"],0)],"target_panel":-1,"target_label":"Delete","expected":"abstain"},
    {"case_id":"target-missed-candidate","prompt":"Select the Resume button in the QUIET panel at the lower-left.","panels":[("LOUD PANEL",["Preferences","Notifications","Keyboard","Display","Reset","About"],1),("TOOLS",["Import","Export"],0),("QUIET",["Resume"],2),("OTHER",["Help","Feedback"],0)],"target_panel":2,"target_label":"Resume","expected":"select"},
    {"case_id":"duplicate-context-bottom-right","prompt":"Select Open in the RECEIPTS panel, not Open in the DRAFTS panel.","panels":[("DRAFTS",["Open","Edit"],0),("ARCHIVE",["Save","Export"],0),("HELP",["About","Docs"],0),("RECEIPTS",["Open","Print"],0)],"target_panel":3,"target_label":"Open","expected":"select"},
    {"case_id":"ambiguous-duplicate-target","prompt":"Select the Open button. If more than one equally valid Open button is visible, abstain.","panels":[("LEFT",["Open","Copy"],0),("RIGHT",["Open","Copy"],0),("TOOLS",["Save","Print"],0),("HELP",["Docs","About"],0)],"target_panel":-2,"target_label":"Open","expected":"abstain"},
    {"case_id":"icon-adjacent-small-label","prompt":"Select the Export button beside the small blue download icon in the REPORTS panel.","panels":[("REPORTS",["Export","Preview"],2),("REPORTS",["Export","Share"],0),("FILES",["Save","Move"],0),("TOOLS",["Crop","Rotate"],0)],"target_panel":0,"target_label":"Export","expected":"select"}
]

def panel(draw, box, title, labels, complexity, panel_idx):
    x0,y0,x1,y1=box
    draw.rounded_rectangle(box, radius=14, fill=(248,250,252), outline=(90,105,120), width=3)
    draw.text((x0+20,y0+15), title, font=F_TITLE, fill=(22,36,52))
    if complexity == 1:
        for j in range(5):
            y=y0+58+j*31
            draw.text((x0+20,y), f"Activity {j+1}: item {panel_idx*7+j}", font=F_SMALL, fill=(55,66,77))
    if complexity == 2:
        draw.ellipse((x0+26,y0+74,x0+44,y0+92), fill=(28,120,230))
        draw.text((x0+53,y0+70), "download", font=F_SMALL, fill=(22,36,52))
    by=y0+122 if complexity==0 else y0+200
    if complexity == 2: by=y0+110
    for i,label in enumerate(labels):
        bx=x1-212 if label=="Sync" else x0+18+i*225
        if bx+205>x1-8: bx=x1-218
        h=44 if label=="Sync" else 54
        draw.rounded_rectangle((bx,by,bx+200,by+h),radius=7,fill=(228,239,250),outline=(54,100,150),width=2)
        draw.text((bx+12,by+8),label,font=F_SMALL if label=="Sync" else F_TEXT,fill=(12,35,58))
        if label=="Sync":
            draw.rectangle((bx+177,by+17,bx+186,by+26),fill=(22,132,90))

def main():
    prompts=[]; oracle=[]
    for n,case in enumerate(CASES):
        img=Image.new("RGB",(1024,640),(205,215,226)); d=ImageDraw.Draw(img)
        d.rectangle((0,0,1023,48),fill=(32,48,66)); d.text((20,10),"Agent Interface — Research Workspace",font=F_TEXT,fill=(255,255,255))
        boxes=[(12,58,506,346),(518,58,1012,346),(12,354,506,628),(518,354,1012,628)]
        targets=[]
        for i,(title,labels,complexity) in enumerate(case["panels"]):
            panel(d,boxes[i],title,labels,complexity,i)
            if i==case["target_panel"]:
                for j,label in enumerate(labels):
                    if label==case["target_label"]:
                        x0,y0,_,_=boxes[i]; x1=boxes[i][2]
                        by=y0+(110 if complexity==2 else (200 if complexity==1 else 122)); bx=x1-212 if label=="Sync" else x0+18+j*225
                        if bx+205>boxes[i][2]-8: bx=boxes[i][2]-218
                        targets.append([bx,by,bx+200,by+(44 if label=="Sync" else 54)])
        path=FIXTURES/f"{case['case_id']}.png"; img.save(path,format="PNG",optimize=False)
        prompts.append({"case_id":case["case_id"],"prompt":case["prompt"],"screen_file":path.name})
        target_box=targets[0] if len(targets)==1 else None
        oracle.append({"case_id":case["case_id"],"expected":case["expected"],"target_box":target_box,
                       "target_boxes":targets,"target_panel":case["target_panel"],"target_label":case["target_label"]})
    (ROOT/"candidate_inputs"/"task_prompts.json").write_text(json.dumps(prompts,sort_keys=True,indent=2)+"\n")
    (ROOT/"oracle" ).mkdir(exist_ok=True)
    (ROOT/"oracle"/"oracle_truth.json").write_text(json.dumps(oracle,sort_keys=True,indent=2)+"\n")
    print(json.dumps({"fixtures":len(prompts),"oracle_separate":True}))

if __name__=="__main__": main()
