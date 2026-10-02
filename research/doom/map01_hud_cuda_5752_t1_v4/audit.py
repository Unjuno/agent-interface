#!/usr/bin/env python3
import argparse, copy, hashlib, importlib.util, json, statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parent
SIGNALS=("health","ammo")
def frozen_identity(freeze): return freeze["allocation"],freeze["base_main_sha"]

def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def reader_for(wad):
    spec=importlib.util.spec_from_file_location("frozen_hud_independent",ROOT/"hud_independent.py")
    mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    if sha(wad)!=mod.WAD_SHA256: raise ValueError("wad_sha")
    return mod.IndependentHudReader(wad)
def cpu_value(reader,path,binding):
    return {name:reader.read_signal(path,binding,name) for name in SIGNALS}
def validate(result,dataset,reader,root,runner_sha,audit_sha,expected_alloc,expected_base):
    errors=[]
    if result.get("schema")!="map01-hud-cuda-result-v1": errors.append("schema")
    if result.get("allocation")!=expected_alloc: errors.append("allocation")
    if result.get("main_base")!=expected_base: errors.append("main_base")
    if result.get("dataset_sha256")!=sha(root/"dataset.json"): errors.append("dataset_sha256")
    if result.get("source_sha256",{}).get("runner")!=runner_sha: errors.append("runner_sha")
    if result.get("source_sha256",{}).get("hud_independent")!=sha(root/"hud_independent.py"): errors.append("hud_source_sha")
    if audit_sha!=sha(Path(__file__)): errors.append("audit_source_sha")
    if sha(root/"data"/"freedoom2.wad")!="a8772e088847032510d97ba2312406a6998f21cbab44d4ff10696faa9c0ecd4b": errors.append("wad_sha")
    sources=dataset.get("runs",{})
    for key,meta in sources.items():
        p=root/"data"/key
        if not p.exists() or p.stat().st_size!=meta.get("bytes") or sha(p)!=meta.get("sha256"): errors.append("source:"+key)
    manifest=dataset.get("selected_records",[])
    rows=result.get("rows",[])
    if len(manifest)!=23 or len(rows)!=23: errors.append("row_count")
    for i,(spec,row) in enumerate(zip(manifest,rows)):
        keys=("run","plan_id","sequence","role","image","image_sha256","frame_rgb_sha256")
        if any(row.get(k)!=spec.get(k) for k in keys):
            errors.append(f"identity:{i}"); continue
        path=root/spec["image"]
        if not path.exists() or sha(path)!=spec["image_sha256"]:
            errors.append(f"png_sha:{i}"); continue
        from PIL import Image
        with Image.open(path) as im:
            rgb=hashlib.sha256(im.convert("RGB").tobytes()).hexdigest()
        if rgb!=spec["frame_rgb_sha256"]: errors.append(f"rgb_sha:{i}")
        expected=cpu_value(reader,path,spec["binding"])
        if row.get("cpu")!=expected: errors.append(f"cpu_oracle:{i}")
        if row.get("gpu")!=expected: errors.append(f"gpu_parity:{i}")
    m=result.get("measurement",{})
    n=23*30
    for field in ("cpu_ns","gpu_ns","pair_order"):
        if len(m.get(field,[]))!=n: errors.append("sample_count:"+field)
    for field in ("full_dataset_cpu_ns","full_dataset_gpu_ns"):
        if len(m.get(field,[]))!=30: errors.append("batch_count:"+field)
    orders=["cpu_gpu" if (rep+i)%2==0 else "gpu_cpu" for rep in range(30) for i in range(23)]
    if m.get("pair_order")!=orders: errors.append("pair_order")
    for field in ("cpu_ns","gpu_ns","full_dataset_cpu_ns","full_dataset_gpu_ns"):
        if any(not isinstance(v,(int,float)) or v<=0 for v in m.get(field,[])): errors.append("invalid_timing:"+field)
    if m.get("cpu_p50_ns")!=statistics.median(m.get("cpu_ns",[])): errors.append("cpu_p50")
    if m.get("gpu_p50_ns")!=statistics.median(m.get("gpu_ns",[])): errors.append("gpu_p50")
    return errors

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--raw",required=True); ap.add_argument("--out",required=True)
    a=ap.parse_args(); raw=Path(a.raw); dataset=json.loads((ROOT/"dataset.json").read_text(encoding="utf-8"))
    result=json.loads(raw.read_text(encoding="utf-8"))
    runner_sha=sha(ROOT/"gpu_hud_runner.py"); audit_sha=sha(Path(__file__))
    freeze=json.loads((ROOT/"FREEZE.json").read_text(encoding="utf-8"))
    expected_alloc,expected_base=frozen_identity(freeze)
    if runner_sha!=freeze["runner_sha256"] or audit_sha!=freeze["audit_sha256"]:
        raise RuntimeError("frozen source hash mismatch")
    if sha(ROOT/"dataset.json")!=freeze["dataset_sha256"] or sha(ROOT/"hud_independent.py")!=freeze["hud_independent_sha256"]:
        raise RuntimeError("frozen data/reference source hash mismatch")
    reader=reader_for(ROOT/"data"/"freedoom2.wad")
    errors=validate(result,dataset,reader,ROOT,runner_sha,audit_sha,expected_alloc,expected_base)
    controls={}
    bad=copy.deepcopy(result); bad["rows"][0]["gpu"]["health"]["value"]+=1
    controls["gpu_value_mutation_rejected"]=bool(validate(bad,dataset,reader,ROOT,runner_sha,audit_sha,expected_alloc,expected_base))
    bad=copy.deepcopy(result); bad["dataset_sha256"]="0"*64
    controls["dataset_hash_mutation_rejected"]=bool(validate(bad,dataset,reader,ROOT,runner_sha,audit_sha,expected_alloc,expected_base))
    bad=copy.deepcopy(result); bad["measurement"]["gpu_ns"][0]=-1
    controls["timing_mutation_rejected"]=bool(validate(bad,dataset,reader,ROOT,runner_sha,audit_sha,expected_alloc,expected_base))
    if not all(controls.values()): errors.append("mutation_controls")
    speed=(result["measurement"]["gpu_p50_ns"]<=0.5*result["measurement"]["cpu_p50_ns"]) if not errors else False
    disposition=("PASS_CUDA_HUD_EQUIVALENCE_SPEED_SCOPED" if not errors and speed else
      "FAIL_GPU_NO_PRACTICAL_SPEEDUP" if not errors else "FAIL_INDEPENDENT_AUDIT")
    out={"schema":"map01-hud-cuda-audit-v1","allocation":expected_alloc,"audit":"PASS" if not errors else "FAIL",
      "raw_sha256":sha(raw),"errors":errors,"mutation_controls":controls,"result_disposition":disposition,
      "all_23_exact_cpu_gpu_matches":not errors,
      "cpu_p50_ns":result["measurement"]["cpu_p50_ns"],"gpu_p50_ns":result["measurement"]["gpu_p50_ns"],
      "speed_gate_pass":speed,"median_ratio_gpu_over_cpu":result["measurement"]["gpu_p50_ns"]/result["measurement"]["cpu_p50_ns"]}
    Path(a.out).write_text(json.dumps(out,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(out,sort_keys=True))
    raise SystemExit(0 if not errors else 1)
if __name__=="__main__": main()
