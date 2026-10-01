#!/usr/bin/env python3
"""One-shot synthetic CUDA supervisor parity probe; no authority or external effects."""
import hashlib, json, platform, statistics, sys, time
from pathlib import Path
import torch

ROOT=Path(__file__).resolve().parent
THRESHOLD=700
REPEATS=30

def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def cpu_hint(rows): return [int(r["confidence_milli"] >= THRESHOLD) for r in rows]
def gate(rows,hints):
    return [int(h and r["observed_sequence"]==r["current_sequence"] and not r["ambiguous"] and not r["forced_yield"]) for r,h in zip(rows,hints)]
def main():
    freeze=json.loads((ROOT/"FREEZE.json").read_text())
    data_path=ROOT/"dataset.json"; doc=json.loads(data_path.read_text())
    assert sha(Path(__file__))==freeze["runner_sha256"]
    assert sha(data_path)==freeze["dataset_sha256"]
    assert torch.cuda.is_available(), "CUDA unavailable"
    device=torch.device("cuda:0")
    rows=doc["rows"]
    cpu=cpu_hint(rows)
    values=torch.tensor([r["confidence_milli"] for r in rows],dtype=torch.int32,device=device)
    _=values.ge(THRESHOLD); torch.cuda.synchronize()
    gpu_ms=[]; cpu_ms=[]
    for i in range(REPEATS):
        t=time.perf_counter_ns(); ch=cpu_hint(rows); cpu_ms.append(time.perf_counter_ns()-t)
        torch.cuda.synchronize(); t=time.perf_counter_ns()
        gh=values.ge(THRESHOLD).to("cpu").to(torch.int8).tolist(); torch.cuda.synchronize()
        gpu_ms.append(time.perf_counter_ns()-t)
    gh=[int(v) for v in gh]
    result={"schema":"gpu-supervisor-cuda-4972-result-v1","allocation":freeze["allocation"],
      "base_main_sha":freeze["base_main_sha"],"dataset_sha256":sha(data_path),
      "source_sha256":{"runner":sha(Path(__file__))},
      "environment":{"python":sys.version,"platform":platform.platform(),"torch":torch.__version__,
        "cuda_runtime":torch.version.cuda,"device":torch.cuda.get_device_name(0)},
      "threshold_milli":THRESHOLD,"row_count":len(rows),
      "rows":[{"id":r["id"],"cpu_hint":"CONTINUE" if c else "YIELD",
        "gpu_hint":"CONTINUE" if g else "YIELD","cpu_admitted":a,"gpu_admitted":b}
        for r,c,g,a,b in zip(rows,cpu,gh,gate(rows,cpu),gate(rows,gh))],
      "timing_diagnostic_only":{"repeats":REPEATS,"cpu_ns":cpu_ms,"gpu_ns":gpu_ms,
        "cpu_p50_ns":statistics.median(cpu_ms),"gpu_p50_ns":statistics.median(gpu_ms)},
      "disposition":"RAW_EMITTED_AWAITING_INDEPENDENT_AUDIT"}
    out=ROOT/"candidate_result.json"
    out.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"rows":len(rows),"cpu_gpu_hints_equal":cpu==gh,
      "cpu_gpu_admissions_equal":gate(rows,cpu)==gate(rows,gh),"output":str(out)},sort_keys=True))
if __name__=="__main__": main()

