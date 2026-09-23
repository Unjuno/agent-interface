import json, math
from pathlib import Path
from PIL import Image, ImageEnhance

MANIFEST=Path("/data/manifest.json"); ROOT=Path("/data")
def feat(image):
    return [value/255 for pixel in image.convert("RGB").resize((16,10)).getdata() for value in pixel]
def distance(left,right):
    return math.sqrt(sum((a-b)**2 for a,b in zip(left,right)))
def main():
    manifest=json.loads(MANIFEST.read_text())
    base=[(record,feat(Image.open(ROOT/record["image"]))) for record in manifest["records"]]
    results=[]
    for record,_ in base:
        image=Image.open(ROOT/record["image"]).convert("RGB")
        variants=[("dark",ImageEnhance.Brightness(image).enhance(.85)),("bright",ImageEnhance.Brightness(image).enhance(1.15)),("resize",image.resize((image.width-8,image.height-8)).resize(image.size))]
        for kind,variant in variants:
            nearest=min(base,key=lambda item:distance(feat(variant),item[1]))[0]
            results.append({"task_id":record["task_id"],"variant":kind,"gold_layout":record["layout"],"pred_layout":nearest["layout"],"exact_layout":record["layout"]==nearest["layout"]})
    report={"format":"real-image-robustness-baseline-v1","records":len(results),"exact_layout":sum(row["exact_layout"] for row in results),"status":"PASS" if all(row["exact_layout"] for row in results) else "STOP","results":results,"note":"existing images only; labels unchanged; no GUI or authority"}
    print(json.dumps(report,sort_keys=True))
if __name__=="__main__": main()
