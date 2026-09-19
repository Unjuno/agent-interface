from hashlib import sha256
import json

W, H = 32, 20
REGIONS = {"toolbar": (2, 2, 10, 3, 40), "target": (8, 7, 12, 6, 90), "effect": (22, 6, 7, 8, 120), "decorative": (3, 15, 8, 3, 160), "low_priority_changed": (22, 16, 7, 3, 210)}

def frame(changes=()):
    p = bytearray([12] * (W * H))
    for x, y, w, h, v in REGIONS.values():
        for yy in range(y, y+h):
            for xx in range(x, x+w): p[yy*W+xx] = v
    for name, v in changes:
        x, y, w, h, _ = REGIONS[name]
        for yy in range(y, y+h):
            for xx in range(x, x+w): p[yy*W+xx] = v
    return bytes(p)

def digest(p): return sha256(p).hexdigest()

def serialize(pkg):
    return json.dumps(pkg, sort_keys=True, separators=(",", ":")).encode()

def package(source, changed, mode):
    if mode == "FULL": return {"mode": mode, "full": source.hex()}
    # Derive retained evidence from source itself; the hint is never authority.
    out = {"mode": mode, "base": frame().hex(), "manifest": []}
    if mode == "ADVISORY_LOW_PRIORITY":
        out["patches"] = []
        for name, _ in changed:
            x, y, w, h, _ = REGIONS[name]
            pixels = bytes(source[yy*W+xx] for yy in range(y,y+h) for xx in range(x,x+w))
            out["patches"].append({"name": name, "rect": (x,y,w,h), "pixels": pixels.hex()})
            out["manifest"].append((name, digest(pixels)))
    # Negative control intentionally drops the low-priority changed region.
    if mode == "FORCED_EXCLUSION":
        out["patches"] = []
        for name, _ in changed:
            if name == "low_priority_changed": continue
            x, y, w, h, _ = REGIONS[name]
            pixels = bytes(source[yy*W+xx] for yy in range(y,y+h) for xx in range(x,x+w))
            out["patches"].append({"name": name, "rect": (x,y,w,h), "pixels": pixels.hex()})
    return out

def reconstruct(pkg):
    if pkg["mode"] == "FULL": return bytes.fromhex(pkg["full"])
    p = bytearray(bytes.fromhex(pkg["base"]))
    for patch in pkg["patches"]:
        x, y, w, h = patch["rect"]; vals = bytes.fromhex(patch["pixels"]); i = 0
        for yy in range(y, y+h):
            for xx in range(x, x+w): p[yy*W+xx] = vals[i]; i += 1
    return bytes(p)

def main():
    cases = [(), (("target", 91),), (("low_priority_changed", 220),), (("effect", 121),), (("low_priority_changed", 220), ("target", 91))]
    rows = []
    for changed in cases:
        source = frame(changed)
        for mode in ("FULL", "ADVISORY_LOW_PRIORITY", "FORCED_EXCLUSION"):
            pkg = package(source, changed, mode)
            rebuilt = reconstruct(pkg)
            rows.append((changed, mode, rebuilt == source, len(serialize(pkg)), digest(source), digest(rebuilt)))
    for mode in ("FULL", "ADVISORY_LOW_PRIORITY", "FORCED_EXCLUSION"):
        xs = [r for r in rows if r[1] == mode]
        print(mode, "exact", sum(r[2] for r in xs), "/", len(xs), "package_bytes", sorted(set(r[3] for r in xs)))
    print("rows", len(rows), "source_sha", digest(frame((("low_priority_changed", 220),))))
    assert all(r[2] for r in rows if r[1] != "FORCED_EXCLUSION")
    assert any(not r[2] for r in rows if r[1] == "FORCED_EXCLUSION")
    assert all(r[4] == r[5] for r in rows if r[1] != "FORCED_EXCLUSION")

if __name__ == "__main__": main()

