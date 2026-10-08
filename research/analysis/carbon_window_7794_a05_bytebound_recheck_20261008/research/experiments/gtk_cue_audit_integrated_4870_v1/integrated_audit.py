import copy
import hashlib
import json
from pathlib import Path
import numpy as np

EXPECTED_SOURCE_SHA256 = "f42ce1c014a5c6a50dd13efdbed083b63fce284386665254559b280e9ff87e75"
EXPECTED_COLORS = {"base-target": "#22cc44", "base-other": "#2244cc", "shift-target": "#55dd66", "shift-other": "#5566dd"}
EXPECTED_SEEDS = [40, 41, 42, 43, 44]


def sha(data): return hashlib.sha256(data).hexdigest()

def weight_digest(weights):
    arr = np.ascontiguousarray(weights)
    header = f"dtype={arr.dtype.str};shape={arr.shape};".encode("ascii")
    return sha(header + arr.tobytes())

def predict(frame, weight, bias):
    x = frame.reshape(-1).astype(np.float32) / 255.0
    z = float(np.clip(x @ weight + bias, -30.0, 30.0))
    return 1.0 / (1.0 + np.exp(-z))

def validate(result, arrays, source_sha, expected_weight_digests):
    if source_sha != EXPECTED_SOURCE_SHA256: return "source_digest"
    if result.get("label") != "FIXTURE ITEM" or result.get("layout", [None])[0] != "FIXTURE ITEM": return "label_or_layout"
    if result.get("colors") != EXPECTED_COLORS or result.get("seeds") != EXPECTED_SEEDS: return "conditions"
    if result.get("base_capture_count") != 16 or result.get("input_dims") != 172800: return "training_dimensions"
    if result.get("gradient_steps") != 100 or result.get("learning_rate") != .3: return "training_recipe"
    required = {"base_target", "base_other", "shift_target", "shift_other", "weights", "biases"}
    if set(arrays) != required: return "array_keys"
    if arrays["base_target"].shape != (8,180,320,3) or arrays["base_other"].shape != (8,180,320,3): return "base_shapes"
    if arrays["shift_target"].shape != (180,320,3) or arrays["shift_other"].shape != (180,320,3): return "shift_shapes"
    w, b = arrays["weights"], arrays["biases"]
    if w.dtype != np.dtype(np.float32): return "weight_dtype"
    if w.shape != (5,172800) or b.shape != (5,): return "weight_shape"
    if not np.isfinite(w).all() or not np.isfinite(b).all(): return "finite"
    actual_digests = [weight_digest(row) for row in w]
    if actual_digests != expected_weight_digests: return "weight_bytes_digest"
    if result.get("weights_sha256") != [sha(row.tobytes()) for row in w]: return "result_weight_digest"
    hashes = result.get("base_frame_hashes", {})
    for name, key in (("base-target","base_target"),("base-other","base_other")):
        got=[sha(f.tobytes()) for f in arrays[key]]
        if got != hashes.get(name) or len(set(got)) != 1: return "base_frame_hash"
    for name,key in (("shift-target","shift_target"),("shift-other","shift_other")):
        if [sha(arrays[key].tobytes())] != hashes.get(name): return "shift_frame_hash"
    if len({hashes.get("base-target",[None])[0],hashes.get("base-other",[None])[0]}) != 2: return "base_class_hash"
    if sha(arrays["shift_target"].tobytes()) == sha(arrays["shift_other"].tobytes()): return "shift_class_hash"
    rows=result.get("rows",[])
    if len(rows)!=10 or {(x.get("seed"),x.get("case")) for x in rows}!={(s,c) for s in EXPECTED_SEEDS for c in ("shift-target","shift-other")}: return "row_set"
    by={(r["seed"],r["case"]):r for r in rows}
    for i,seed in enumerate(EXPECTED_SEEDS):
        for case,y,key in (("shift-target",1,"shift_target"),("shift-other",0,"shift_other")):
            p=predict(arrays[key],w[i],b[i]); row=by[(seed,case)]
            if abs(p-row.get("p_target",-1))>1e-6: return "prediction"
            if bool(p>=.5)!=bool(y) or row.get("correct") is not True: return "class"
            if row.get("threshold_pass") is not (bool(p>=.75) if y else bool(p<.5)): return "threshold"
            if row.get("frame_sha256") != sha(arrays[key].tobytes()): return "row_frame_hash"
    if result.get("accuracy")!=1.0 or result.get("threshold_pass_count")!=10 or result.get("all_finite") is not True: return "summary"
    return None

def main():
    import argparse
    p=argparse.ArgumentParser(); p.add_argument("result",type=Path); p.add_argument("raw",type=Path); p.add_argument("output",type=Path); args=p.parse_args()
    rb,ab=args.result.read_bytes(),args.raw.read_bytes(); result=json.loads(rb)
    with np.load(args.raw,allow_pickle=False) as z: arrays={k:z[k].copy() for k in z.files}
    source_sha=sha(Path("/src/run.py").read_bytes())
    expected=[weight_digest(row) for row in arrays["weights"]]
    original_reason=validate(result,arrays,source_sha,expected)
    controls={}
    def challenge(name,fn,expected_reason=None):
        r=copy.deepcopy(result); a={k:v.copy() for k,v in arrays.items()}; fn(r,a)
        reason=validate(r,a,source_sha,expected)
        controls[name]={"rejected":reason is not None,"reason":reason}
        if expected_reason and reason!=expected_reason: controls[name]["expected_reason_match"]=False
        elif expected_reason: controls[name]["expected_reason_match"]=True
    challenge("label",lambda r,a:r.__setitem__("label","TARGET"))
    challenge("capture_count",lambda r,a:r.__setitem__("base_capture_count",15))
    challenge("color_map",lambda r,a:r["colors"].__setitem__("shift-target","#ffffff"))
    challenge("prediction",lambda r,a:r["rows"][0].__setitem__("p_target",0.0))
    challenge("class",lambda r,a:r["rows"][0].__setitem__("case","shift-other"))
    challenge("frame_hash",lambda r,a:r["rows"][0].__setitem__("frame_sha256","0"*64))
    def tiny(r,a): a["weights"][0,0]=np.nextafter(a["weights"][0,0],np.float32(np.inf),dtype=np.float32)
    challenge("adjacent_float32_weights",tiny,"weight_bytes_digest")
    def large(r,a): a["weights"][0,0]=np.float32(float(a["weights"][0,0])+2.0)
    challenge("large_finite_weights",large,"weight_bytes_digest")
    def dtype(r,a): a["weights"]=a["weights"].astype(np.float64)
    challenge("weight_dtype",dtype,"weight_dtype")
    def shape(r,a): a["weights"]=a["weights"].reshape(5,172800,1)
    challenge("weight_shape",shape,"weight_shape")
    challenge("threshold_count",lambda r,a:r.__setitem__("threshold_pass_count",9))
    challenge("seed",lambda r,a:r["seeds"].__setitem__(0,99))
    def nonfinite(r,a): a["weights"][0,0]=np.nan
    challenge("finite",nonfinite)
    after=(sha(args.result.read_bytes()),sha(args.raw.read_bytes()))
    before=(sha(rb),sha(ab))
    errors=[]
    if original_reason is not None: errors.append("original_invalid:"+original_reason)
    if after!=before: errors.append("formal_inputs_changed")
    if not all(x["rejected"] for x in controls.values()): errors.append("corruption_control_escaped")
    if not all(x.get("expected_reason_match",True) for x in controls.values()): errors.append("unexpected_rejection_reason")
    audit={"passed":not errors,"errors":errors,"original_reason":original_reason,"controls":controls,"rejected_controls":sum(x["rejected"] for x in controls.values()),"source_sha256":source_sha,"result_sha256":before[0],"raw_npz_sha256":before[1],"inputs_unchanged":after==before,"formal_model_calls":0,"fits":0,"predictions_generated":0,"recaptures":0}
    args.output.write_text(json.dumps(audit,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(audit,sort_keys=True))
    if errors: raise SystemExit(1)
if __name__=="__main__": main()









