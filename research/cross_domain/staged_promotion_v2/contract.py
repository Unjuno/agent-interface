from __future__ import annotations
import hashlib, os, shutil, time
from pathlib import Path
from PIL import Image

def sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def image_receipt(path: Path, expected: dict) -> dict:
    start=time.perf_counter_ns()
    if not path.exists():
        end=time.perf_counter_ns();return {'started_ns':start,'finished_ns':end,'state':'ABSENT','file_sha256':None,'rgb_sha256':None,'size':None}
    data=path.read_bytes()
    try:
        im=Image.open(path).convert('RGB'); rgb=im.tobytes(); size=list(im.size); rh=sha_bytes(rgb)
        state='A' if rh==expected['a_rgb_sha256'] else 'B' if rh==expected['b_rgb_sha256'] else 'OTHER'
    except Exception:
        rh=None;size=None;state='INVALID'
    end=time.perf_counter_ns()
    return {'started_ns':start,'finished_ns':end,'state':state,'file_sha256':sha_bytes(data),'rgb_sha256':rh,'size':size}

class Publisher:
    """Publish completed staged effects to one canonical path."""
    def __init__(self, canonical: Path, mode: str, current_generation: int):
        if mode not in {'naive','generation_gate'}: raise ValueError(mode)
        self.canonical=Path(canonical);self.mode=mode;self.current_generation=int(current_generation);self.events=[]
    def publish(self, stage: Path, *, generation: int, attempt_id: str) -> dict:
        start=time.perf_counter_ns();stage=Path(stage)
        if not stage.is_file(): raise FileNotFoundError(stage)
        eligible=(self.mode=='naive' or generation==self.current_generation)
        if eligible:
            os.replace(stage,self.canonical); outcome='PUBLISHED'
        else:
            outcome='STALE_GENERATION'
        end=time.perf_counter_ns();row={'attempt_id':attempt_id,'generation':generation,'current_generation':self.current_generation,'mode':self.mode,'eligible':eligible,'outcome':outcome,'started_ns':start,'finished_ns':end}
        self.events.append(row);return row
