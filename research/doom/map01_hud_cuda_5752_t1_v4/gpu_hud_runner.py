#!/usr/bin/env python3
import argparse, hashlib, importlib.util, json, os, platform, statistics, sys, time
from pathlib import Path
import numpy as np
import torch
from PIL import Image

SIGNALS=("health","ammo")
ANCHORS={"ammo":(10,411),"health":(102,411)}
GLYPH_W,GLYPH_H,SLOTS=26,38,3
MIN_SCORE,MIN_MARGIN=0.80,0.05
REPEATS=30
ROOT=Path(__file__).resolve().parent
MIN_FREE_BYTES=64*1024*1024

def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def frozen_identity(freeze): return freeze["allocation"],freeze["base_main_sha"]
def disk_gate_status(available_bytes,required_bytes=MIN_FREE_BYTES):
    return "PREFLIGHT_OK" if available_bytes>=required_bytes else "STOP_INSUFFICIENT_DISK_SPACE"
def check_disk_reserve(path,required_bytes=MIN_FREE_BYTES):
    return disk_gate_status(__import__("shutil").disk_usage(Path(path)).free,required_bytes)
def load_reader(wad):
    modpath=ROOT/"hud_independent.py"
    spec=importlib.util.spec_from_file_location("frozen_hud_independent",modpath)
    mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    reader=mod.IndependentHudReader(Path(wad))
    if mod.sha256(Path(wad))!=mod.WAD_SHA256: raise RuntimeError("WAD hash mismatch")
    return reader,mod

def make_templates(reader):
    pixels=torch.zeros((10,GLYPH_H,GLYPH_W,3),dtype=torch.uint8,device="cuda")
    masks=torch.zeros((10,GLYPH_H,GLYPH_W),dtype=torch.bool,device="cuda")
    counts=[]
    for d,fg in enumerate(reader.templates):
        counts.append(len(fg))
        for x,y,rgb in fg:
            pixels[d,y,x]=torch.tensor(rgb,dtype=torch.uint8,device="cuda")
            masks[d,y,x]=True
    return pixels,masks,torch.tensor(counts,dtype=torch.float64,device="cuda")

def frame_tensor(path):
    with Image.open(path) as im:
        arr=np.asarray(im.convert("RGB"),dtype=np.uint8)
    return torch.from_numpy(arr).to("cuda")

def score_frames(frames,bindings,templates):
    pixels,masks,counts=templates
    signal_crops=[]
    for name in SIGNALS:
        rows=[]
        for i,(frame,binding) in enumerate(zip(frames,bindings)):
            geom=binding.get("geometry") if isinstance(binding,dict) else None
            if not isinstance(geom,list) or len(geom)!=4 or tuple(geom[2:])!=(640,480):
                raise ValueError("unsupported geometry in frozen dataset")
            x0=geom[0]+ANCHORS[name][0]; y0=geom[1]+ANCHORS[name][1]
            if x0<0 or y0<0 or x0+SLOTS*GLYPH_W>frame.shape[1] or y0+GLYPH_H>frame.shape[0]:
                raise ValueError("HUD crop outside frame")
            rows.append(torch.stack([frame[y0:y0+GLYPH_H,x0+s*GLYPH_W:x0+(s+1)*GLYPH_W,:] for s in range(SLOTS)]))
        signal_crops.append(torch.stack(rows))
    crops=torch.stack(signal_crops) # [signal,batch,slot,h,w,c]
    eq=(crops.unsqueeze(3)==pixels.unsqueeze(0).unsqueeze(0).unsqueeze(0)).all(dim=-1)
    hits=(eq & masks.unsqueeze(0).unsqueeze(0).unsqueeze(0)).sum(dim=(-1,-2))
    scores=hits.to(torch.float64)/counts.unsqueeze(0).unsqueeze(0).unsqueeze(0)
    return scores.permute(1,0,2,3).cpu().tolist() # [batch,signal,slot,digit]

def decode_gpu(scores):
    out={}
    for si,name in enumerate(SIGNALS):
        digits=[]; details=[]
        for slot in range(SLOTS):
            row=scores[si][slot]
            order=sorted(range(10),key=lambda d:row[d],reverse=True)
            best,second=order[:2]
            digit=None if row[best]<MIN_SCORE else best
            if digit is not None and row[best]-row[second]<MIN_MARGIN:
                return {name:{"status":"unknown","reason":"ambiguous_digit","value":None,
                             "detail":{"slot":slot,"scores":row}}}
            digits.append(digit)
            details.append({"slot":slot,"digit":digit,"best_digit":best,"best_score":row[best],"second_score":row[second]})
        first=next((i for i,d in enumerate(digits) if d is not None),None)
        if first is None or any(d is None for d in digits[first:]) or any(d is not None for d in digits[:first]):
            out[name]={"status":"unknown","reason":"invalid_right_aligned_number","value":None,"slots":details}
        else:
            out[name]={"status":"observed","value":int("".join(str(d) for d in digits[first:])),"slots":details}
    return out

def compare(cpu,gpu):
    for name in SIGNALS:
        a,b=cpu[name],gpu[name]
        if (a.get("status"),a.get("reason"),a.get("value"))!=(b.get("status"),b.get("reason"),b.get("value")):return False
        aa=a.get("slots",[]); bb=b.get("slots",[])
        if len(aa)!=len(bb): return False
        for x,y in zip(aa,bb):
            if (x.get("digit"),x.get("best_digit"))!=(y.get("digit"),y.get("best_digit")):return False
            if abs(x.get("best_score",0)-y.get("best_score",0))>1e-12 or abs(x.get("second_score",0)-y.get("second_score",0))>1e-12:return False
    return True

def write_parity_failure_evidence(path,rows,comparison):
    compared=[]; mismatch=None
    for row in rows:
        compared.append(row)
        if not comparison(row["cpu"],row["gpu"]):
            mismatch=row
            break
    evidence={"schema":"map01-hud-cuda-failure-v1",
      "candidate_disposition":"FAIL_CUDA_READER_MISMATCH" if mismatch else "HOLD",
      "compared_rows":len(compared),"rows":compared,
      "mismatch_ordinal":mismatch.get("ordinal") if mismatch else None}
    target=Path(path); temporary=target.with_name(target.name+".tmp")
    with temporary.open("w",encoding="utf-8",newline="\n") as stream:
        json.dump(evidence,stream,sort_keys=True,indent=2)
        stream.write("\n"); stream.flush(); os.fsync(stream.fileno())
    os.replace(temporary,target)
    return evidence["candidate_disposition"]

def read_cpu(reader,path,binding):
    return {name:reader.read_signal(path,binding,name) for name in SIGNALS}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--dataset",default=str(ROOT/"dataset.json"))
    ap.add_argument("--wad",default=str(ROOT/"data"/"freedoom2.wad"))
    ap.add_argument("--out-dir",required=True)
    a=ap.parse_args()
    output=Path(a.out_dir)
    if not output.is_dir() or any(output.iterdir()): raise RuntimeError("output directory must exist and be empty")
    disk_gate=check_disk_reserve(output)
    if disk_gate!="PREFLIGHT_OK": raise RuntimeError(disk_gate)
    if not torch.cuda.is_available(): raise RuntimeError("CUDA unavailable")
    dpath=Path(a.dataset); dataset=json.loads(dpath.read_text(encoding="utf-8"))
    freeze=json.loads((ROOT/"FREEZE.json").read_text(encoding="utf-8"))
    allocation,main_base=frozen_identity(freeze)
    if sha(Path(__file__))!=freeze["runner_sha256"] or sha(ROOT/"hud_independent.py")!=freeze["hud_independent_sha256"]:
        raise RuntimeError("frozen source hash mismatch")
    if sha(dpath)!=freeze["dataset_sha256"]:
        raise RuntimeError("frozen dataset hash mismatch")
    if dataset["unique_images"]!=23 or dataset["in_envelope_observations"]!=19 or dataset["baseline_records"]!=4:
        raise RuntimeError("frozen dataset denominator mismatch")
    for key,meta in dataset.get("runs",{}).items():
        path=ROOT/"data"/key
        if not path.exists() or path.stat().st_size!=meta["bytes"] or sha(path)!=meta["sha256"]:
            raise RuntimeError("retained report/event source mismatch: "+key)
    for item in dataset["selected_records"]:
        path=ROOT/item["image"]
        if sha(path)!=item["image_sha256"]:
            raise RuntimeError("PNG bytes mismatch: "+item["image"])
        with Image.open(path) as im:
            rgb=hashlib.sha256(im.convert("RGB").tobytes()).hexdigest()
        if rgb!=item["frame_rgb_sha256"]:
            raise RuntimeError("PNG RGB mismatch: "+item["image"])
    reader,mod=load_reader(a.wad)
    if sha(Path(a.wad))!="a8772e088847032510d97ba2312406a6998f21cbab44d4ff10696faa9c0ecd4b": raise RuntimeError("WAD SHA mismatch")
    templates=make_templates(reader)
    records=dataset["selected_records"]
    images=[ROOT/r["image"] for r in records]
    bindings=[r["binding"] for r in records]
    # Warm both implementations; retain cold GPU setup separately.
    cold_start=time.perf_counter_ns(); torch.cuda.synchronize()
    preframes=[frame_tensor(images[0])]
    _=score_frames(preframes,[bindings[0]],templates); torch.cuda.synchronize()
    cold_gpu_ms=(time.perf_counter_ns()-cold_start)/1e6
    _=read_cpu(reader,images[0],bindings[0])
    cpu_ns=[]; gpu_ns=[]; result_rows=[]
    for idx,(record,path,binding) in enumerate(zip(records,images,bindings)):
        cpu=read_cpu(reader,path,binding)
        gpu=decode_gpu(score_frames([frame_tensor(path)],[binding],templates)[0])
        torch.cuda.synchronize()
        result_rows.append({"run":record["run"],"plan_id":record["plan_id"],"sequence":record["sequence"],
          "role":record["role"],"image":record["image"],"image_sha256":record["image_sha256"],
          "frame_rgb_sha256":record["frame_rgb_sha256"],"cpu":cpu,"gpu":gpu})
        if not compare(cpu,gpu):
            failed_rows=[dict(row,ordinal=i+1) for i,row in enumerate(result_rows)]
            write_parity_failure_evidence(output/"candidate_result.json",failed_rows,
              compare)
            raise RuntimeError(f"CPU/GPU mismatch at {record['run']} seq {record['sequence']}")
    order_log=[]
    for rep in range(REPEATS):
        for idx,(record,path,binding) in enumerate(zip(records,images,bindings)):
            order=("cpu_gpu" if (rep+idx)%2==0 else "gpu_cpu")
            order_log.append(order)
            for method in (("cpu","gpu") if order=="cpu_gpu" else ("gpu","cpu")):
                if method=="cpu":
                    t=time.perf_counter_ns(); _=read_cpu(reader,path,binding); dt=time.perf_counter_ns()-t
                    cpu_ns.append(dt)
                else:
                    torch.cuda.synchronize(); t=time.perf_counter_ns()
                    _=score_frames([frame_tensor(path)],[binding],templates)
                    torch.cuda.synchronize(); dt=time.perf_counter_ns()-t
                    gpu_ns.append(dt)
    batch_cpu=[]; batch_gpu=[]
    for rep in range(REPEATS):
        t=time.perf_counter_ns()
        for path,binding in zip(images,bindings): _=read_cpu(reader,path,binding)
        batch_cpu.append(time.perf_counter_ns()-t)
        torch.cuda.synchronize(); t=time.perf_counter_ns()
        frames=[frame_tensor(path) for path in images]
        _=score_frames(frames,bindings,templates); torch.cuda.synchronize()
        batch_gpu.append(time.perf_counter_ns()-t)
    result={"schema":"map01-hud-cuda-result-v1","allocation":allocation,
      "main_base":main_base,"dataset_sha256":sha(dpath),
      "source_sha256":{"runner":sha(Path(__file__)),"hud_independent":sha(ROOT/"hud_independent.py")},
      "environment":{"python":sys.version,"platform":platform.platform(),"torch":torch.__version__,
       "cuda_runtime":torch.version.cuda,"cuda_device":torch.cuda.get_device_name(0),
       "gpu_cold_setup_ms":cold_gpu_ms},
      "rows":result_rows,"measurement":{"repeats":REPEATS,"paired_frame_samples_per_method":len(cpu_ns),
       "cpu_ns":cpu_ns,"gpu_ns":gpu_ns,"pair_order":order_log,
       "full_dataset_cpu_ns":batch_cpu,"full_dataset_gpu_ns":batch_gpu,
       "cpu_p50_ns":statistics.median(cpu_ns),"gpu_p50_ns":statistics.median(gpu_ns),
       "cpu_p95_ns":sorted(cpu_ns)[int(.95*(len(cpu_ns)-1))],
       "gpu_p95_ns":sorted(gpu_ns)[int(.95*(len(gpu_ns)-1))]},
      "counts":{"unique_images":len(images),"in_envelope":19,"baselines":4,"signals_per_image":2},
      "candidate_disposition":"CUDA_EQUIVALENT" if len(result_rows)==23 else "HOLD"}
    out=output/"candidate_result.json"
    out.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"rows":23,"pairs":len(cpu_ns),"cpu_p50_ns":result["measurement"]["cpu_p50_ns"],
      "gpu_p50_ns":result["measurement"]["gpu_p50_ns"],"candidate_disposition":result["candidate_disposition"]},sort_keys=True))
if __name__=="__main__": main()
