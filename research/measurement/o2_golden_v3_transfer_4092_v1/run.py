"""One-shot retained-golden-frame transfer allocation for Issue #4103."""
from __future__ import annotations
import argparse, hashlib, json, os, platform, resource, sys, time, zlib
import numpy as np
import PIL
from pathlib import Path
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = Path(os.environ.get("AGENT_INTERFACE_ROOT", HERE.parents[2]))
sys.path.insert(0, str(HERE))
from transfer import VectorEncoder, ContiguousEncoder, reference

GOLDEN = ROOT / "runtime/results/golden-desktop-app-server-v3-live-01/arms/persistent/runtime"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git_blob(data: bytes) -> str:
    return hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()


def dump(path: Path, obj) -> None:
    path.write_text(json.dumps(obj, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def rgb_frame(path: Path):
    raw = path.read_bytes()
    with Image.open(path) as im:
        rgb = im.convert("RGB")
        width, height = rgb.size
        pixels = rgb.tobytes()
    return raw, reference.Frame(width, height, "RGB", pixels)


def canonical(pair, before, after):
    enc = reference.Encoder("golden-" + pair["id"], "O2", 64)
    kw1 = dict(action_id=pair["id"] + "-before", observed_ns=1, context=("golden-v3", pair["id"]))
    kw2 = dict(action_id=pair["id"] + "-after", observed_ns=2, context=("golden-v3", pair["id"]))
    w1 = enc.encode(before, **kw1)
    w2 = enc.encode(after, **kw2)
    dec = reference.Decoder("golden-" + pair["id"])
    assert dec.accept(w1) == before
    assert dec.accept(w2) == after
    return kw1, kw2, w1, w2, dict(enc.last)


def run_arm(cls, pair, before, after, kw1, kw2):
    enc = cls("golden-" + pair["id"], "O2", 64)
    w1 = enc.encode(before, **kw1)
    start_wall = time.perf_counter_ns()
    start_cpu = time.process_time_ns()
    w2 = enc.encode(after, **kw2)
    cpu = time.process_time_ns() - start_cpu
    wall = time.perf_counter_ns() - start_wall
    return w1, w2, wall, cpu, dict(enc.last)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    out = args.out
    if out.exists():
        raise SystemExit("output exists: formal allocation is immutable")
    out.mkdir(parents=True)
    schedule = json.loads((HERE / "schedule.json").read_text())
    freeze = json.loads((HERE / "FREEZE.json").read_text())
    if freeze["allocation_id"] != "o2-golden-v3-transfer-20260922-01":
        raise ValueError("freeze allocation mismatch")
    start = {
        "schema":"o2-golden-v3-transfer-start-v1",
        "pid":os.getpid(), "platform":platform.platform(), "python":sys.version,
        "cpu_affinity":sorted(os.sched_getaffinity(0)) if hasattr(os,"sched_getaffinity") else None,
        "freeze_sha256":sha256((HERE/"FREEZE.json").read_bytes()),
        "source_revision":os.environ.get("SOURCE_REVISION"),
        "numpy":np.__version__, "pillow":PIL.__version__, "zlib":zlib.ZLIB_VERSION,
        "started_ns":time.time_ns()
    }
    dump(out / "START.json", start)
    records = []
    for index, pair in enumerate(schedule["pairs"]):
        pb = GOLDEN / pair["before"]
        pa = GOLDEN / pair["after"]
        rb, before = rgb_frame(pb); ra, after = rgb_frame(pa)
        if git_blob(rb) != pair["before_blob"] or git_blob(ra) != pair["after_blob"]:
            raise ValueError("golden image identity mismatch: " + pair["id"])
        kw1, kw2, cw1, cw2, clast = canonical(pair, before, after)
        pdir = out / pair["id"]; pdir.mkdir()
        (pdir / "canonical-initial.wire").write_bytes(cw1)
        (pdir / "canonical-update.wire").write_bytes(cw2)
        samples = []
        total = schedule["warmups"] + schedule["timed"]
        for ordinal in range(total):
            phase = "warmup" if ordinal < schedule["warmups"] else "timed"
            order = ["vector","contiguous"] if (ordinal + index) % 2 == 0 else ["contiguous","vector"]
            arms = {}
            wires = {}
            for arm in order:
                cls = VectorEncoder if arm == "vector" else ContiguousEncoder
                w1,w2,wall,cpu,last = run_arm(cls,pair,before,after,kw1,kw2)
                if w1 != cw1 or w2 != cw2:
                    raise AssertionError(f"wire mismatch {pair['id']} {ordinal} {arm}")
                dec = reference.Decoder("golden-" + pair["id"])
                if dec.accept(w1) != before or dec.accept(w2) != after:
                    raise AssertionError("decode mismatch")
                arms[arm] = {
                    "wall_ns":wall, "cpu_ns":cpu,
                    "initial_sha256":sha256(w1), "wire_sha256":sha256(w2),
                    "wire_bytes":len(w2), "kind":last["kind"],
                    "changed_tiles":last["changed_tiles"]
                }
                wires[arm] = w2
            if ordinal == 0:
                for arm,w in wires.items(): (pdir / f"{arm}-update.wire").write_bytes(w)
            samples.append({"ordinal":ordinal,"phase":phase,"order":order,"arms":arms})
        rec = {
            "index":index, "id":pair["id"], "before":pair["before"], "after":pair["after"],
            "before_blob":git_blob(rb), "after_blob":git_blob(ra),
            "before_png_sha256":sha256(rb), "after_png_sha256":sha256(ra),
            "width":before.width, "height":before.height, "mode":before.mode,
            "before_pixel_sha256":sha256(before.pixels), "after_pixel_sha256":sha256(after.pixels),
            "canonical_initial_sha256":sha256(cw1), "canonical_update_sha256":sha256(cw2),
            "canonical_wire_bytes":len(cw2), "canonical_kind":clast["kind"],
            "canonical_changed_tiles":clast["changed_tiles"], "samples":samples
        }
        dump(pdir / "raw.json", rec)
        records.append(rec)
    end = {
        "schema":"o2-golden-v3-transfer-end-v1", "status":"COMPLETE",
        "pair_count":len(records), "timed_pairs":len(records)*schedule["timed"],
        "warmup_pairs":len(records)*schedule["warmups"],
        "finished_ns":time.time_ns(), "maxrss_kib":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    }
    dump(out / "END.json", end)
    print(json.dumps(end, sort_keys=True))

if __name__ == "__main__":
    main()
