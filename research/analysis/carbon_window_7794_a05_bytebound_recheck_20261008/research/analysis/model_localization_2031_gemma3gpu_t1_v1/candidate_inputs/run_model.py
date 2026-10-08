#!/usr/bin/env python3
"""One-shot four-arm model evaluation against the local Ollama HTTP endpoint."""
import base64, hashlib, json, os, time, urllib.request
from pathlib import Path
from PIL import Image

ROOT=Path(__file__).resolve().parent
PROMPTS=json.loads((ROOT/"task_prompts.json").read_text())
ARMS=["FULL_RESOLUTION","OVERVIEW_PLUS_CANDIDATE_CROP","OVERVIEW_ONLY","CANDIDATE_CROP_ONLY"]
MODEL=os.environ.get("AI2031_MODEL","gemma3:4b")
HOST=os.environ.get("OLLAMA_HOST","http://ollama:11434")
OUT=Path(os.environ.get("AI2031_OUTPUT","/out"))

def propose(image):
    scores=[]
    for idx in range(4):
        col,row=idx%2,idx//2; box=(col*512,row*320,(col+1)*512,(row+1)*320)
        tile=image.crop(box).convert("L"); px=tile.load(); total=0; count=0
        for y in range(tile.height):
            for x in range(tile.width):
                v=px[x,y]
                if x: total+=abs(v-px[x-1,y]); count+=1
                if y: total+=abs(v-px[x,y-1]); count+=1
        scores.append({"tile":idx,"box":list(box),"edge_mean":total/max(count,1)})
    selected=sorted(scores,key=lambda r:(-r["edge_mean"],r["tile"]))[0]
    return selected,scores

def image_bytes(image,fmt="PNG"):
    import io
    b=io.BytesIO(); image.save(b,format=fmt,optimize=False); return b.getvalue()

def canonical(obj): return json.dumps(obj,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()

def build_images(task,arm):
    src=Image.open(ROOT/"screens"/task["screen_file"]).convert("RGB")
    selected,scores=propose(src); crop=src.crop(tuple(selected["box"]))
    overview=src.resize((512,320),Image.Resampling.LANCZOS)
    variants={"FULL_RESOLUTION":[("full",src,(0,0,1024,640))],
      "OVERVIEW_PLUS_CANDIDATE_CROP":[("overview",overview,(0,0,512,320)),("candidate_crop",crop,tuple(selected["box"]))],
      "OVERVIEW_ONLY":[("overview",overview,(0,0,512,320))],
      "CANDIDATE_CROP_ONLY":[("candidate_crop",crop,tuple(selected["box"]))]}
    items=[]
    for role,img,box in variants[arm]: items.append((role,image_bytes(img),box,img.size))
    return items,selected,scores

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/"calls").mkdir(exist_ok=True)
    index=[]; base_order=ARMS
    for ci,task in enumerate(PROMPTS):
        order=base_order[ci%4:]+base_order[:ci%4]
        for ai,arm in enumerate(order):
            images,selected,scores=build_images(task,arm)
            mapping="; ".join(f"image {k+1} is {role}, source box {list(box)}, encoded size {size[0]}x{size[1]}" for k,(role,_,box,size) in enumerate(images))
            prompt=(task["prompt"]+"\n"+mapping+"\nReturn exactly one JSON object: "
              '{"abstain":boolean,"x":integer-or-null,"y":integer-or-null,"label":string-or-null}. '
              "Coordinates must be in the original 1024x640 source screenshot. Abstain if the requested target is absent, ambiguous, or cannot be localized from the attached evidence.")
            msg={"role":"user","content":prompt,"images":[base64.b64encode(b).decode("ascii") for _,b,_,_ in images]}
            request={"model":MODEL,"messages":[msg],"stream":False,"format":"json",
              "options":{"temperature":0,"seed":2031,"num_predict":128}}
            body=canonical(request); call_id=f"{ci:02d}-{arm.lower()}"; call_dir=OUT/"calls"/call_id;call_dir.mkdir()
            started=time.monotonic_ns(); req=urllib.request.Request(HOST+"/api/chat",data=body,headers={"Content-Type":"application/json"},method="POST")
            with urllib.request.urlopen(req,timeout=180) as response: raw=response.read(); status=response.status
            elapsed=time.monotonic_ns()-started
            (call_dir/"request.json").write_bytes(body); (call_dir/"response.json").write_bytes(raw)
            parsed=json.loads(raw); answer=json.loads(parsed["message"]["content"])
            image_rows=[{"role":role,"sha256":hashlib.sha256(b).hexdigest(),"bytes":len(b),"source_box":list(box),"encoded_size":list(size)} for role,b,box,size in images]
            record={"case_id":task["case_id"],"arm":arm,"call_id":call_id,"http_status":status,
              "request_sha256":hashlib.sha256(body).hexdigest(),"request_bytes":len(body),
              "response_sha256":hashlib.sha256(raw).hexdigest(),"response_bytes":len(raw),"images":image_rows,
              "proposal":{"tile":selected["tile"],"box":selected["box"],"edge_mean":selected["edge_mean"],"all_scores":scores},
              "answer":answer,"prompt_eval_count":parsed.get("prompt_eval_count"),"eval_count":parsed.get("eval_count"),
              "total_duration_ns":parsed.get("total_duration"),"load_duration_ns":parsed.get("load_duration"),
              "prompt_eval_duration_ns":parsed.get("prompt_eval_duration"),"eval_duration_ns":parsed.get("eval_duration"),
              "wall_elapsed_ns":elapsed}
            (call_dir/"record.json").write_text(json.dumps(record,sort_keys=True,indent=2)+"\n")
            index.append(record)
            print(json.dumps({"call_id":call_id,"arm":arm,"request_bytes":len(body),"prompt_eval_count":record["prompt_eval_count"],"answer":answer}),flush=True)
    (OUT/"candidate_index.json").write_text(json.dumps({"schema":"issue2031-gemma3-t1-v1","model":MODEL,"calls":index},sort_keys=True,indent=2)+"\n")
    print(json.dumps({"formal_calls":len(index),"order":"case-rotated-arm-order"}))

if __name__=="__main__": main()
