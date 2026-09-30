import hashlib, json
from pathlib import Path
import torch
from PIL import Image

ROOT = Path(__file__).resolve().parents[3]
STUDY = Path(__file__).resolve().parent
RUN = ROOT / "research/doom/results/map01-astra-attempt-v1"
BOX = (440, 585, 535, 635)
THRESHOLD = 32
MIN_CHANGED = 100

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def changed_cpu(a, b):
    x = a.crop(BOX).convert("RGB")
    y = b.crop(BOX).convert("RGB")
    return sum(max(abs(i-j) for i,j in zip(px,py)) > THRESHOLD
               for px,py in zip(x.getdata(),y.getdata()))

def main():
    prereg = json.loads((STUDY / "PREREGISTRATION_V2.json").read_text(encoding="utf-8"))
    manifest = json.loads((RUN / "frame-manifest.json").read_text(encoding="utf-8"))
    frames=[]
    for row in manifest:
        path=RUN / row["file"]
        if sha(path) != row["sha256"]:
            raise SystemExit(f"STOP_FRAME_HASH:{row['file']}")
        im=Image.open(path).convert("RGB")
        if im.size != (1280,800):
            raise SystemExit(f"STOP_FRAME_GEOMETRY:{row['file']}:{im.size}")
        frames.append(im)
    if len(frames) != prereg["decision_frames"]:
        raise SystemExit("STOP_FRAME_COUNT")
    start,end=BOX[0],BOX[2]
    top,bottom=BOX[1],BOX[3]
    cpu=[]; gpu=[]
    device=torch.device("cuda:0")
    peak_start = torch.cuda.memory_allocated(device)
    torch.cuda.synchronize()
    t0=torch.cuda.Event(enable_timing=True); t1=torch.cuda.Event(enable_timing=True)
    t0.record()
    tensors=[torch.frombuffer(bytearray(im.crop(BOX).tobytes()),dtype=torch.uint8).reshape(50,95,3).to(device) for im in frames]
    for a,b in zip(frames,frames[1:]):
        cpu.append(changed_cpu(a,b))
    for a,b in zip(tensors,tensors[1:]):
        gpu.append(int(((a.to(torch.int16)-b.to(torch.int16)).abs().amax(dim=2)>THRESHOLD).sum().item()))
    t1.record(); torch.cuda.synchronize()
    if len(gpu) != prereg["adjacent_pairs"]:
        raise SystemExit("STOP_PAIR_COUNT")
    rows=[]
    for idx,(c,g) in enumerate(zip(cpu,gpu)):
        status="INVALIDATED" if c >= MIN_CHANGED else "UNCHANGED"
        rows.append({"from_iteration":idx,"to_iteration":idx+1,"cpu_changed_pixels":c,"gpu_changed_pixels":g,"cpu_status":status,"gpu_status":"INVALIDATED" if g>=MIN_CHANGED else "UNCHANGED","exact_count_match":c==g,"status_match":(c>=MIN_CHANGED)==(g>=MIN_CHANGED)})
    cpu_status=[r["cpu_status"] for r in rows]
    invalidated=cpu_status.count("INVALIDATED")
    unchanged=cpu_status.count("UNCHANGED")
    report={"schema":"map01-health-roi-gpu-replay-result-v1","allocation":prereg["allocation"],"result":"PASS_GPU_CPU_EXACT_PARITY" if all(r["exact_count_match"] and r["status_match"] for r in rows) else "FAIL_GPU_CPU_PARITY","device":torch.cuda.get_device_name(0),"torch":torch.__version__,"cuda_runtime":torch.version.cuda,"source_run":"map01-astra-attempt-v1","frame_manifest_sha256":sha(RUN/"frame-manifest.json"),"failure_analysis_sha256":sha(RUN/"failure-analysis-v1.json"),"roi":{"xyxy":list(BOX),"size":[95,50],"rgb_threshold_exclusive":THRESHOLD,"minimum_changed_pixels_inclusive":MIN_CHANGED},"rows":rows,"summary":{"pairs":len(rows),"invalidated":invalidated,"unchanged":unchanged,"manual_expected_invalidated":7,"manual_expected_unchanged":5,"matches_retained_manual_decision_labels":invalidated==7 and unchanged==5,"cpu_cuda_mismatches":sum(not r["exact_count_match"] for r in rows),"cuda_allocation_before_bytes":peak_start,"cuda_allocation_after_bytes":torch.cuda.memory_allocated(device),"gpu_timing_ms_including_transfer_and_compute":t0.elapsed_time(t1),"timing_scope":"single diagnostic replay; descriptive only, no performance claim"},"limits":["one postselected failed run; no live sampling, treatment, causal survival, or MAP01 exit evidence","health-ROI change signals only one-way policy invalidation; it does not prove semantic threat identity or task success","manual health labels and prior threshold are reused, not independently re-annotated"]}
    out=STUDY/"RESULT.json"
    out.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"result":report["result"],"device":report["device"],"summary":report["summary"],"rows":rows},indent=2))
if __name__=="__main__":
    if not torch.cuda.is_available(): raise SystemExit("STOP_CUDA_UNAVAILABLE")
    main()