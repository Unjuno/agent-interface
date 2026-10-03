"""Saved-only oracle joins source pixels/events to raw OCR; runs no OCR."""
import argparse
import hashlib
import json
import re
from pathlib import Path
from PIL import Image

EVENTS_SHA="2c917658e8bba0a94e5a34f0ee3d968553cd56950105196871012f2e3eedb381"
PILOT={37,62,76,81,90,97,103,115,144,154,167,193,200,218}
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()

def audit(raw,truth,phase,input_root,source):
    events_path=source/"events.jsonl"
    if sha(events_path) != EVENTS_SHA or truth["events_sha256"] != EVENTS_SHA: raise ValueError("source events hash")
    events=[json.loads(line) for line in events_path.read_text().splitlines()]
    typed={row["sequence"]:row for row in events if row.get("event")=="typed_observation"}
    observation={row["sequence"]:row for row in events if row.get("event")=="observation"}
    selected=set(PILOT if phase=="pilot" else set(typed)-PILOT)
    mapping=truth["phases"][phase]
    if {row["sequence"] for row in mapping} != selected or len(mapping) != len(selected): raise ValueError("source split")
    manifest=json.loads((input_root/"manifest.json").read_text())
    manifest_map={row["id"]:row for row in manifest}
    references={row["id"]:row for row in mapping}
    predictions={row["id"]:row for row in raw["rows"]}
    if len(manifest_map)!=len(mapping) or len(predictions)!=len(raw["rows"]) or set(predictions)!=set(references) or set(manifest_map)!=set(references): raise ValueError("row membership/duplicates")
    methods=raw["transforms"]
    if len(set(methods))!=len(methods) or "gray" not in methods or any(m not in ("gray","red","red_excess") for m in methods): raise ValueError("transform membership")
    counts={m:{"exact":0,"blank":0,"wrong_nonempty":0,"n":len(mapping)} for m in methods}
    for opaque,reference in references.items():
        sequence=reference["sequence"]
        event=typed[sequence]
        expected=event["signals"]["health"]["value"]
        if reference["reference_health"] != expected: raise ValueError("reference label")
        actual_file=Path(observation[sequence]["image"]).name
        if reference["image_file"]!=actual_file or reference["source_file_sha256"]!=sha(source/actual_file): raise ValueError("source image join")
        with Image.open(source/actual_file) as loaded: image=loaded.convert("RGB")
        if hashlib.sha256(image.tobytes()).hexdigest()!=event["frame_rgb_sha256"] or event["frame_rgb_sha256"]!=observation[sequence]["frame_rgb_sha256"]: raise ValueError("source RGB")
        item=manifest_map[opaque]
        crop_path=input_root/item["image"]
        if crop_path.parent!=input_root or sha(crop_path)!=item["sha256"] or item["sha256"]!=reference["crop_sha256"] or predictions[opaque]["crop_sha256"]!=item["sha256"]: raise ValueError("crop identity")
        with Image.open(crop_path) as loaded: crop=loaded.convert("RGB")
        if crop.size!=(78,38) or crop.tobytes()!=image.crop((423,591,501,629)).tobytes(): raise ValueError("source crop pixels")
        values=predictions[opaque]["predictions"]
        if set(values)!=set(methods): raise ValueError("prediction matrix")
        for method in methods:
            value=values[method]
            digits="".join(re.findall(r"[0-9]",value["text"]))
            if digits!=value["digits"] or type(value["elapsed_ns"]) is not int or value["elapsed_ns"]<0: raise ValueError("OCR normalization/time")
            category="exact" if digits==str(expected) else "blank" if digits=="" else "wrong_nonempty"
            counts[method][category]+=1
    resource=raw["cgroup"]
    if resource["cpu.max"]!="100000 100000" or resource["memory.max"]!="536870912" or resource["memory.swap.max"]!="0" or resource["pids.max"]!="64": raise ValueError("observed cgroup bounds")
    return {"status":"PASS_SAVED_SOURCE_AND_ARITHMETIC_AUDIT","phase":phase,"counts":counts,"cgroup":resource,"reference_ground_truth_independent":False}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--phase",choices=["pilot","evaluation"],required=True)
    args=parser.parse_args()
    result=audit(json.loads(Path("/raw/raw.json").read_text()),json.loads(Path("/truth/TRUTH.json").read_text()),args.phase,Path("/input"),Path("/source"))
    with Path("/out/audit.json").open("x") as output: json.dump(result,output,indent=2); output.write("\n")
    print(json.dumps(result))
if __name__=="__main__": main()
