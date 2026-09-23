from dataclasses import dataclass
from itertools import product
import hashlib
import json

@dataclass(frozen=True)
class Frame:
    epoch: int
    identity: str
    pixels: tuple

@dataclass(frozen=True)
class Request:
    epoch: int
    identity: str
    region: tuple
    reason: str

def crop(frame, region):
    x0, y0, x1, y1 = region
    return tuple(tuple(row[x0:x1]) for row in frame.pixels[y0:y1])

def oracle(frame, req):
    if req.reason != "uncertain" or req.epoch != frame.epoch or req.identity != frame.identity:
        return False
    x0, y0, x1, y1 = req.region
    return 0 <= x0 < x1 <= len(frame.pixels[0]) and 0 <= y0 < y1 <= len(frame.pixels)

frames = []
for epoch, identity, flip in product((1, 2), ("A", "B"), (0, 1)):
    base = [[0, 0, 0], [0, 1 + flip, 0], [0, 0, 0]]
    frames.append(Frame(epoch, identity, tuple(map(tuple, base))))
regions = ((1, 1, 2, 2), (0, 0, 3, 3), (-1, 0, 2, 2), (1, 1, 1, 2))
reasons = ("uncertain", "inferred")
rows = []
for frame, epoch, identity, region, reason in product(frames, (1, 2), ("A", "B"), regions, reasons):
    req = Request(epoch, identity, region, reason)
    valid = oracle(frame, req)
    observed = crop(frame, region) if valid else None
    assert (observed is not None) == valid
    rows.append({"frame": frame.identity + str(frame.epoch), "request": req.__dict__, "valid": valid, "observed": observed})
assert sum(r["valid"] for r in rows) == 16
raw = json.dumps(rows, sort_keys=True, separators=(",", ":"))
print(json.dumps({"rows": len(rows), "valid": sum(r["valid"] for r in rows), "rejected": sum(not r["valid"] for r in rows), "sha256": hashlib.sha256(raw.encode()).hexdigest()}))
