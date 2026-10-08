#!/usr/bin/env python3
"""Independent raw-input/package/scoring audit; does not import the model runner."""
import base64, hashlib, json
import os
from pathlib import Path
from PIL import Image, ImageChops, ImageStat

ROOT=Path(__file__).resolve().parent
ARMS=["FULL_RESOLUTION","OVERVIEW_PLUS_CANDIDATE_CROP","OVERVIEW_ONLY","CANDIDATE_CROP_ONLY"]
MODEL="gemma3:4b"

def canonical(obj): return json.dumps(obj,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()
def png(img):
    import io
    b=io.BytesIO();img.save(b,format="PNG",optimize=False);return b.getvalue()
def selected_tile(img):
    scores=[]
    for k in range(4):
        x0=(k%2)*512;y0=(k//2)*320
        gray=img.crop((x0,y0,x0+512,y0+320)).convert("L")
        # Independent vectorized adjacent-pixel calculation.
        h=ImageChops.difference(gray.crop((1,0,512,320)),gray.crop((0,0,511,320)))
        v=ImageChops.difference(gray.crop((0,1,512,320)),gray.crop((0,0,512,319)))
        hs=sum(ImageStat.Stat(h).mean)*h.width*h.height
        vs=sum(ImageStat.Stat(v).mean)*v.width*v.height
        scores.append((hs+vs)/(h.width*h.height+v.width*v.height))
    return sorted(range(4),key=lambda k:(-scores[k],k))[0]

def expected_images(task,arm):
    src=Image.open(ROOT/"candidate_inputs"/"screens"/task["screen_file"]).convert("RGB")
    tile=selected_tile(src);box=(tile%2*512,tile//2*320,(tile%2+1)*512,(tile//2+1)*320)
    crop=src.crop(box);overview=src.resize((512,320),Image.Resampling.LANCZOS)
    all_variants={"FULL_RESOLUTION":[("full",src,(0,0,1024,640))],
      "OVERVIEW_PLUS_CANDIDATE_CROP":[("overview",overview,(0,0,512,320)),("candidate_crop",crop,box)],
      "OVERVIEW_ONLY":[("overview",overview,(0,0,512,320))],
      "CANDIDATE_CROP_ONLY":[("candidate_crop",crop,box)]}
    return tile,box,all_variants[arm]

def request_for(task,arm,items):
    mapping="; ".join(f"image {k+1} is {role}, source box {list(box)}, encoded size {img.size[0]}x{img.size[1]}"
      for k,(role,img,box) in enumerate(items))
    prompt=(task["prompt"]+"\n"+mapping+"\nReturn exactly one JSON object: "
      '{"abstain":boolean,"x":integer-or-null,"y":integer-or-null,"label":string-or-null}. '
      "Coordinates must be in the original 1024x640 source screenshot. Abstain if the requested target is absent, ambiguous, or cannot be localized from the attached evidence.")
    return {"model":MODEL,"messages":[{"role":"user","content":prompt,
      "images":[base64.b64encode(png(img)).decode("ascii") for _,img,_ in items]}],"stream":False,"format":"json",
      "options":{"temperature":0,"seed":2031,"num_predict":128}}

def score(answer,truth):
    if type(answer.get("abstain")) is not bool: return False,"invalid_abstention_type"
    if truth["expected"]=="abstain":
        return answer["abstain"] is True,"expected_abstention"
    box=truth.get("target_box")
    if box is None: return answer["abstain"] is True,"no_unique_ground_truth"
    x,y=answer.get("x"),answer.get("y")
    good=(answer["abstain"] is False and type(x) is int and type(y) is int and box[0]<=x<=box[2] and box[1]<=y<=box[3])
    return good,"point_inside_target_box" if good else "target_localization_miss_or_false_abstention"

def audit():
    tasks=json.loads((ROOT/"candidate_inputs"/"task_prompts.json").read_text())
    truth=json.loads((ROOT/"oracle"/"oracle_truth.json").read_text())
    idx=json.loads((ROOT/"formal"/"candidate"/"candidate_index.json").read_text())
    assert idx["schema"]=="issue2031-gemma3-t1-v1" and idx["model"]==MODEL
    rows=idx["calls"]; assert len(rows)==len(tasks)*len(ARMS)==32
    truth_map={x["case_id"]:x for x in truth}; expected_ids=[]; aud=[]
    for i,task in enumerate(tasks):
        order=ARMS[i%4:]+ARMS[:i%4]
        for arm in order:
            call=f"{i:02d}-{arm.lower()}"; expected_ids.append(call)
    assert [x["call_id"] for x in rows]==expected_ids
    for row,task in zip(rows,[tasks[int(x["call_id"].split("-",1)[0])] for x in rows],strict=True):
        arm=row["arm"]; tile,box,items=expected_images(task,arm)
        cdir=ROOT/"formal"/"candidate"/"calls"/row["call_id"]
        body=(cdir/"request.json").read_bytes(); response=(cdir/"response.json").read_bytes()
        assert hashlib.sha256(body).hexdigest()==row["request_sha256"] and len(body)==row["request_bytes"]
        assert hashlib.sha256(response).hexdigest()==row["response_sha256"] and len(response)==row["response_bytes"]
        expected_body=canonical(request_for(task,arm,items)); assert body==expected_body
        parsed=json.loads(response); assert parsed["model"]==MODEL
        answer=json.loads(parsed["message"]["content"]); assert answer==row["answer"]
        assert parsed.get("prompt_eval_count")==row["prompt_eval_count"] and parsed.get("eval_count")==row["eval_count"]
        raw_images=[base64.b64decode(x) for x in json.loads(body)["messages"][0]["images"]]
        expected_blobs=[png(img) for _,img,_ in items]; assert raw_images==expected_blobs
        target=truth_map[task["case_id"]]; is_correct,rule=score(answer,target)
        crop_box=(tile%2*512,tile//2*320,(tile%2+1)*512,(tile//2+1)*320)
        tb=target.get("target_box"); missing=bool(tb and not(crop_box[0]<=((tb[0]+tb[2])//2)<crop_box[2] and crop_box[1]<=((tb[1]+tb[3])//2)<crop_box[3]))
        aud.append({"case_id":task["case_id"],"arm":arm,"correct":is_correct,"score_rule":rule,
          "selected_tile":tile,"selected_box":list(crop_box),"target_absent_from_candidate_crop":missing,
          "request_bytes":len(body),"image_bytes":sum(map(len,raw_images)),
          "prompt_eval_count":row["prompt_eval_count"],"eval_count":row["eval_count"],
          "wall_elapsed_ns":row["wall_elapsed_ns"],"total_duration_ns":row["total_duration_ns"]})
    byarm={a:[r for r in aud if r["arm"]==a] for a in ARMS}
    stats={a:{"correct":sum(r["correct"] for r in rs),"n":len(rs),
      "request_bytes":sum(r["request_bytes"] for r in rs),
      "image_bytes":sum(r["image_bytes"] for r in rs),
      "prompt_eval_count":sum(r["prompt_eval_count"] or 0 for r in rs),
      "eval_count":sum(r["eval_count"] or 0 for r in rs),
      "missing_crop_cases":sum(r["target_absent_from_candidate_crop"] for r in rs),
      "missing_crop_false_target":sum(r["target_absent_from_candidate_crop"] and not r["correct"] for r in rs)} for a,rs in byarm.items()}
    result={"disposition":"AUDIT_COMPLETE_SCOPED_ONLY","model":MODEL,"audited_calls":len(aud),"arms":stats,"rows":aud,
      "scope":"single frozen synthetic case family and one local vision model; no GUI, human, runtime, broad localization, or universal cost claim"}
    out=Path(os.environ.get("AI2031_AUDIT_OUTPUT",ROOT/"formal"/"audit"));out.mkdir(parents=True,exist_ok=True)
    (out/"audit.json").write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
    print(json.dumps({"audited_calls":len(aud),"arms":stats},sort_keys=True))
    return result

if __name__=="__main__": audit()
