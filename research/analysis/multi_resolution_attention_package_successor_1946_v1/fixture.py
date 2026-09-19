"""Deterministic analytical fixture for issue #1946.

The fixture is intentionally model/GUI/network independent. A package retains
the authoritative frame as a deterministic base recipe plus lossless patches;
the low-resolution view is only an attention hint and never authority.
"""
from dataclasses import dataclass
from hashlib import sha256

W, H = 64, 40
BG = 17


@dataclass(frozen=True)
class Region:
    name: str
    x: int
    y: int
    w: int
    h: int
    value: int


REGIONS = (
    Region("toolbar", 4, 4, 20, 8, 61),
    Region("dialog", 18, 14, 34, 17, 93),
    Region("tiny_status", 50, 6, 8, 3, 211),
    Region("duplicate_label", 6, 29, 14, 5, 137),
)


def frame(changes=()):
    px = bytearray([BG]) * (W * H)
    for r in REGIONS:
        for y in range(r.y, r.y + r.h):
            for x in range(r.x, r.x + r.w):
                px[y * W + x] = r.value
    for name, value in changes:
        r = next(x for x in REGIONS if x.name == name)
        for y in range(r.y, r.y + r.h):
            for x in range(r.x, r.x + r.w):
                px[y * W + x] = value
    return bytes(px)


def digest(data):
    return sha256(data).hexdigest()


def downsample(data, factor=4):
    return bytes(data[y * factor * W + x * factor] for y in range(H // factor) for x in range(W // factor))


def crop(data, r):
    return bytes(data[y * W + x] for y in range(r.y, r.y + r.h) for x in range(r.x, r.x + r.w))


def package(data, changed, arm):
    base = frame()
    out = {"arm": arm, "base_recipe": "fixture-v1", "global_low": downsample(data)}
    changed_names = {name for name, _ in changed}
    candidate_name = next((name for name in changed_names if name != "tiny_status"), "dialog")
    if arm in ("GLOBAL_LOW_PLUS_CANDIDATE", "GLOBAL_LOW_PLUS_CANDIDATE_PLUS_CRITICAL"):
        r = next(x for x in REGIONS if x.name == candidate_name)
        out["candidate"] = (r, crop(data, r))
    if arm == "GLOBAL_LOW_PLUS_CANDIDATE_PLUS_CRITICAL" and "tiny_status" in changed_names:
        r = next(x for x in REGIONS if x.name == "tiny_status")
        out["critical"] = (r, crop(data, r))
    return out


def reconstruct(pkg):
    if pkg["arm"] == "FULL":
        return pkg["full"]
    data = bytearray(frame())
    for key in ("candidate", "critical"):
        if key in pkg:
            r, values = pkg[key]
            i = 0
            for y in range(r.y, r.y + r.h):
                for x in range(r.x, r.x + r.w):
                    data[y * W + x] = values[i]
                    i += 1
    return bytes(data)


def run():
    cases = []
    for changed in ((), (("tiny_status", 233),), (("dialog", 117),), (("toolbar", 77),), (("duplicate_label", 155),)):
        source = frame(changed)
        for arm in ("FULL", "GLOBAL_LOW_ONLY", "GLOBAL_LOW_PLUS_CANDIDATE", "GLOBAL_LOW_PLUS_CANDIDATE_PLUS_CRITICAL"):
            p = package(source, changed, arm)
            if arm == "FULL":
                p["full"] = source
            rebuilt = reconstruct(p)
            cases.append({"changed": changed, "arm": arm, "source_sha": digest(source), "reconstructed_sha": digest(rebuilt), "exact": rebuilt == source, "bytes": sum(len(v) if isinstance(v, (bytes, bytearray)) else len(v[1]) for k, v in p.items() if k not in ("arm", "base_recipe"))})
    for row in cases:
        if row["arm"] == "FULL" and not row["exact"]:
            raise AssertionError(row)
    return cases


if __name__ == "__main__":
    rows = run()
    for arm in ("FULL", "GLOBAL_LOW_ONLY", "GLOBAL_LOW_PLUS_CANDIDATE", "GLOBAL_LOW_PLUS_CANDIDATE_PLUS_CRITICAL"):
        xs = [r for r in rows if r["arm"] == arm]
        print(arm, "exact", sum(r["exact"] for r in xs), "/", len(xs), "bytes", sorted(set(r["bytes"] for r in xs)))
    print("total_rows", len(rows))

