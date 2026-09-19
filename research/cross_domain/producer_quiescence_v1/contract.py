from __future__ import annotations
import hashlib, time
from pathlib import Path
from PIL import Image

def sha(data: bytes) -> str: return hashlib.sha256(data).hexdigest()

def image_receipt(path: Path, expected: dict) -> dict:
    a=time.perf_counter_ns()
    if not path.exists():
        b=time.perf_counter_ns(); return {'started_ns':a,'finished_ns':b,'state':'ABSENT','file_sha256':None,'rgb_sha256':None,'size':None}
    data=path.read_bytes()
    try:
        im=Image.open(path).convert('RGB'); rgb=im.tobytes(); size=list(im.size)
        h=sha(rgb); state='A' if h==expected['a_rgb_sha256'] else 'B' if h==expected['b_rgb_sha256'] else 'OTHER'
    except Exception:
        h=None;size=None;state='INVALID'
    b=time.perf_counter_ns();return {'started_ns':a,'finished_ns':b,'state':state,'file_sha256':sha(data),'rgb_sha256':h,'size':size}
