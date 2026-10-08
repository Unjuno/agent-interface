"""Deterministic structured RGB corpus; not held-out or independent random noise."""
from pathlib import Path
import hashlib
import json
import zlib

SHAPES = [(319, 239), (1023, 767), (1537, 1025)]
SCENES = ['UNCHANGED', 'SPARSE', 'DENSE_SOLID', 'DENSE_TEXTURE']


def make(w, h, scene):
    texture = bytes((17*(i//3 % w % 64) + 29*(i//(w*3) % 64)
                     + 71*(i % 3)) % 256 for i in range(w*h*3))
    if scene == 'UNCHANGED':
        return texture, texture
    if scene == 'SPARSE':
        after = bytearray(texture)
        after[((h//2)*w+w//2)*3] ^= 255
        return texture, bytes(after)
    if scene == 'DENSE_SOLID':
        return bytes(w*h*3), bytes([127])*(w*h*3)
    if scene == 'DENSE_TEXTURE':
        return bytes(w*h*3), texture
    raise ValueError(scene)


def prepare(root):
    root = Path(root)
    folder = root/'inputs'
    folder.mkdir(exist_ok=False)
    schedule=[]
    for w,h in SHAPES:
        for scene in SCENES:
            idx=len(schedule)
            row=dict(index=idx, width=w, height=h, mode='RGB', scene=scene,
                     tile_size=64, warmup_pairs=2, timing_pairs=11, memory_pairs=3)
            for name,raw in zip(('before','after'),make(w,h,scene)):
                digest=hashlib.sha256(raw).hexdigest()
                path=folder/(digest+'.z')
                if not path.exists(): path.write_bytes(zlib.compress(raw,9))
                row[name]=dict(path=str(path.relative_to(root)),sha256=digest,bytes=len(raw))
            row['metadata']=dict(stream='m6r1-'+str(idx),action_id='update',observed_ns=2,context=['structured-corpus',idx])
            schedule.append(row)
    (root/'SCHEDULE.json').write_text(json.dumps(schedule,indent=2)+'\n')
    return schedule


if __name__=='__main__':
    import sys
    print(len(prepare(sys.argv[1])))
