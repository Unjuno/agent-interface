"""Candidate reads only image-only manifest and fixed transform names."""
import argparse
import hashlib
import io
import json
import platform
import re
import subprocess
import time
from pathlib import Path
import PIL
from PIL import Image, ImageChops, ImageOps

parser=argparse.ArgumentParser()
parser.add_argument("--transforms",required=True)
args=parser.parse_args()
transforms=args.transforms.split(",")
if len(set(transforms)) != len(transforms) or any(value not in ("gray","red","red_excess") for value in transforms):
    raise SystemExit("STOP_TRANSFORM_CONTRACT")
output=Path("/out/raw.json")
with output.open("x") as stream:
    manifest=json.loads(Path("/input/manifest.json").read_text())
    result=[]
    for item in manifest:
        path=Path("/input")/item["image"]
        if path.parent != Path("/input") or hashlib.sha256(path.read_bytes()).hexdigest() != item["sha256"]:
            raise ValueError("image path/hash mismatch")
        with Image.open(path) as loaded:
            image=loaded.convert("RGB")
        channels=image.split()
        prepared={"gray":image.convert("L"),"red":ImageOps.invert(channels[0]),"red_excess":ImageOps.invert(ImageChops.subtract(channels[0],ImageChops.lighter(channels[1],channels[2])))}
        predictions={}
        for method in transforms:
            view=prepared[method].resize((image.width*10,image.height*10),Image.Resampling.NEAREST)
            buffer=io.BytesIO(); view.save(buffer,format="PNG")
            start=time.monotonic_ns()
            process=subprocess.run(["tesseract","stdin","stdout","--psm","8","-c","tessedit_char_whitelist=0123456789%"],input=buffer.getvalue(),stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=5)
            if process.returncode: raise ValueError(process.stderr.decode(errors="replace"))
            raw=process.stdout.decode().strip()
            predictions[method]={"text":raw,"digits":"".join(re.findall(r"[0-9]",raw)),"elapsed_ns":time.monotonic_ns()-start,"stderr":process.stderr.decode(errors="replace")}
        result.append({"id":item["id"],"crop_sha256":item["sha256"],"predictions":predictions})
    cg={}
    for name in ("cpu.max","memory.max","memory.swap.max","pids.max"):
        path=Path("/sys/fs/cgroup")/name
        cg[name]=path.read_text().strip() if path.exists() else None
    record={"rows":result,"transforms":transforms,"cgroup":cg,"python":platform.python_version(),"pillow":PIL.__version__,"tesseract":subprocess.run(["tesseract","--version"],capture_output=True,text=True,check=True).stdout,"traineddata_sha256":hashlib.sha256(Path("/usr/share/tesseract-ocr/5/tessdata/eng.traineddata").read_bytes()).hexdigest()}
    json.dump(record,stream,indent=2); stream.write("\n")
print(json.dumps({"rows":len(result),"transforms":transforms,"cgroup":cg}))
