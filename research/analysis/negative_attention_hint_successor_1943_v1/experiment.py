from hashlib import sha256

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

def package(source, changed, mode):
    if mode == "FULL": return {"mode": mode, "full": source}
    # Advisory hint never removes authoritative evidence: retain changed crops.
    out = {"mode": mode, "base": frame()}
    if mode == "ADVISORY_LOW_PRIORITY":
        out["patches"] = [(name, v) for name, v in changed]
    # Negative control intentionally drops the low-priority changed region.
    if mode == "FORCED_EXCLUSION":
        out["patches"] = [(name, v) for name, v in changed if name != "low_priority_changed"]
    return out

def reconstruct(pkg):
    if pkg["mode"] == "FULL": return pkg["full"]
    p = bytearray(pkg["base"])
    for name, v in pkg["patches"]:
        x, y, w, h, _ = REGIONS[name]
        for yy in range(y, y+h):
            for xx in range(x, x+w): p[yy*W+xx] = v
    return bytes(p)

def main():
    cases = [(), (("target", 91),), (("low_priority_changed", 220),), (("effect", 121),), (("low_priority_changed", 220), ("target", 91))]
    rows = []
    for changed in cases:
        source = frame(changed)
        for mode in ("FULL", "ADVISORY_LOW_PRIORITY", "FORCED_EXCLUSION"):
            rebuilt = reconstruct(package(source, changed, mode))
            rows.append((changed, mode, rebuilt == source, len(rebuilt)))
    for mode in ("FULL", "ADVISORY_LOW_PRIORITY", "FORCED_EXCLUSION"):
        xs = [r for r in rows if r[1] == mode]
        print(mode, "exact", sum(r[2] for r in xs), "/", len(xs))
    print("rows", len(rows), "source_sha", digest(frame((("low_priority_changed", 220),))))
    assert all(r[2] for r in rows if r[1] != "FORCED_EXCLUSION")
    assert any(not r[2] for r in rows if r[1] == "FORCED_EXCLUSION")

if __name__ == "__main__": main()

