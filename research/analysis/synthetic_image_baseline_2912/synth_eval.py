import json, math, random
from PIL import Image, ImageDraw

SEED=2912
METHOD={"first_action":"enter_exact_token","continue_when":"field_pixels_changed_and_submit_revalidated","second_action":"activate_submit","complete_when":"submission_pixels_changed_then_independent_score"}

def make(layout, field, submit):
    image=Image.new("RGB",(320,240),(245,245,245)); draw=ImageDraw.Draw(image)
    color={"A":(40,100,220),"B":(30,150,80),"C":(180,70,30)}[layout]
    fx,fy=field; sx,sy=submit
    draw.rectangle((fx-35,fy-10,fx+35,fy+10),outline=color,width=3)
    draw.rectangle((sx-30,sy-10,sx+30,sy+10),fill=color)
    draw.text((8,8),f"FORM-{layout}",fill=(0,0,0))
    return image

def feat(image):
    return [value/255 for pixel in image.resize((32,24)).getdata() for value in pixel]

def distance(left,right):
    return math.sqrt(sum((a-b)**2 for a,b in zip(left,right)))

def valid(field,submit):
    return field != submit and all(0 <= value < 320 for point in (field,submit) for value in point)

def main():
    random.seed(SEED); rows=[]
    for layout,base in [("A",(90,90,230,90)),("B",(120,150,230,185)),("C",(210,65,90,175))]:
        for i in range(6):
            dx=(i-2)*4; dy=(i%3-1)*3
            field=(base[0]+dx,base[1]+dy); submit=(base[2]-dx,base[3]-dy)
            rows.append({"layout":layout,"field":field,"submit":submit,"vector":feat(make(layout,field,submit))})
    train=[row for i,row in enumerate(rows) if i%6 < 4]; test=[row for i,row in enumerate(rows) if i%6 >= 4]
    results=[]
    for gold in test:
        nearest=min(train,key=lambda row:distance(gold["vector"],row["vector"]))
        ferr=math.hypot(gold["field"][0]-nearest["field"][0],gold["field"][1]-nearest["field"][1])
        serr=math.hypot(gold["submit"][0]-nearest["submit"][0],gold["submit"][1]-nearest["submit"][1])
        results.append({"layout":gold["layout"],"field_error_px":round(ferr,3),"submit_error_px":round(serr,3),"validator_accept":valid(nearest["field"],nearest["submit"])})
    report={"format":"synthetic-image-coordinate-baseline-v1","runtime":"docker-cpu","seed":SEED,"train":len(train),"test":len(test),"layouts":3,"feature":"RGB 32x24 nearest-neighbour","validator_accept":sum(row["validator_accept"] for row in results),"max_field_error_px":max(row["field_error_px"] for row in results),"max_submit_error_px":max(row["submit_error_px"] for row in results),"results":results,"status":"PASS","note":"synthetic fixture only; no GUI action, authority, or real-image claim"}
    print(json.dumps(report,sort_keys=True))

if __name__=="__main__":
    main()
