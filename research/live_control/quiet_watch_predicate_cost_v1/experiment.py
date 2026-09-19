#!/usr/bin/env python3
import argparse, gc, hashlib, json, os, platform, statistics, subprocess, sys, time
from pathlib import Path

ROI_W = 32
ROI_H = 32
ROI_PIXELS = ROI_W * ROI_H
ROI_BYTES = ROI_PIXELS * 4
TARGET_BGR = bytes((50, 50, 220))
THRESHOLD = 512
SEED = b"quiet-watch-predicate-cost-v1|20260916"
CORPUS_N = 512
BOUNDARIES = (0, 1, 2, 255, 256, 510, 511, 512, 513, 514, 768, 1022, 1023, 1024)
PAIRS = 16
REPEATS_PER_BLOCK = 16
WARMUP_REPEATS = 2


def sha256(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def stream_bytes(frame_index: int, n: int) -> bytes:
    out = bytearray()
    ctr = 0
    prefix = SEED + frame_index.to_bytes(4, "little")
    while len(out) < n:
        out.extend(hashlib.sha256(prefix + ctr.to_bytes(4, "little")).digest())
        ctr += 1
    return bytes(out[:n])


def desired_count(frame_index: int) -> int:
    if frame_index < len(BOUNDARIES):
        return BOUNDARIES[frame_index]
    h = hashlib.sha256(SEED + b"count" + frame_index.to_bytes(4, "little")).digest()
    return int.from_bytes(h[:2], "little") % (ROI_PIXELS + 1)


def make_frame(frame_index: int) -> tuple[bytes, int]:
    raw = bytearray(stream_bytes(frame_index, ROI_BYTES))
    for i in range(0, ROI_BYTES, 4):
        if raw[i:i+3] == TARGET_BGR:
            raw[i] ^= 1
    count = desired_count(frame_index)
    digest = hashlib.sha256(SEED + b"perm" + frame_index.to_bytes(4, "little")).digest()
    m = (int.from_bytes(digest[:2], "little") | 1) % ROI_PIXELS
    if m == 0:
        m = 1
    offset = int.from_bytes(digest[2:4], "little") % ROI_PIXELS
    for j in range(count):
        pix = (offset + j * m) % ROI_PIXELS
        base = 4 * pix
        raw[base:base+3] = TARGET_BGR
    return bytes(raw), count


def build_corpus():
    frames, expected = [], []
    for i in range(CORPUS_N):
        b, c = make_frame(i)
        frames.append(b); expected.append(c)
    joined = b"".join(frames)
    return frames, expected, sha256(joined)


def python_count(raw: bytes) -> int:
    if len(raw) != ROI_BYTES:
        raise ValueError(f"expected {ROI_BYTES} bytes, got {len(raw)}")
    cnt = 0
    for i in range(0, len(raw), 4):
        if raw[i:i+3] == TARGET_BGR:
            cnt += 1
    return cnt


def import_native(root: Path):
    sys.path.insert(0, str(root))
    import native_predicate
    return native_predicate


def correctness(root: Path, out: Path | None):
    native = import_native(root)
    frames, expected, corpus_hash = build_corpus()
    py_counts = [python_count(x) for x in frames]
    native_counts = [native.count_target(x) for x in frames]
    mismatches = [i for i,(a,b,c) in enumerate(zip(expected, py_counts, native_counts)) if not (a == b == c)]
    threshold_mismatches = [i for i,(a,b) in enumerate(zip(py_counts, native_counts)) if (a >= THRESHOLD) != (b >= THRESHOLD)]
    guards = {}
    for name, payload in [("short", b"\0"*(ROI_BYTES-4)), ("long", b"\0"*(ROI_BYTES+4)), ("wrong_type", bytearray(ROI_BYTES))]:
        try:
            native.count_target(payload)
            guards[name] = False
        except (ValueError, TypeError):
            guards[name] = True
    result = {
        "schema":"quiet_watch_predicate_cost_v1_correctness",
        "corpus_n":CORPUS_N,
        "corpus_sha256":corpus_hash,
        "python_counts_sha256":sha256(json.dumps(py_counts,separators=(",",":"),ensure_ascii=True).encode()),
        "native_counts_sha256":sha256(json.dumps(native_counts,separators=(",",":"),ensure_ascii=True).encode()),
        "mismatch_indices":mismatches,
        "threshold_mismatch_indices":threshold_mismatches,
        "guards":guards,
        "pass":not mismatches and not threshold_mismatches and all(guards.values()),
    }
    if out:
        out.write_text(json.dumps(result, indent=2, sort_keys=True)+"\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    if not result["pass"]:
        raise SystemExit(2)


def run_block(fn, frames, order, repeats):
    checksum = 0
    t0w = time.perf_counter_ns(); t0c = time.thread_time_ns()
    for _ in range(repeats):
        for idx in order:
            checksum += fn(frames[idx])
    t1c = time.thread_time_ns(); t1w = time.perf_counter_ns()
    n = repeats * len(order)
    return {"n":n,"checksum":checksum,"wall_ns":t1w-t0w,"thread_cpu_ns":t1c-t0c,"wall_ns_per_eval":(t1w-t0w)/n,"thread_cpu_ns_per_eval":(t1c-t0c)/n}


def rotated_order(pair_index):
    m = ((2 * pair_index + 1) * 73) % CORPUS_N
    if m % 2 == 0: m += 1
    off = (pair_index * 137) % CORPUS_N
    return [(off + j*m) % CORPUS_N for j in range(CORPUS_N)]


def env_info(root: Path):
    allowed = sorted(os.sched_getaffinity(0)) if hasattr(os, "sched_getaffinity") else []
    return {"python":sys.version,"implementation":platform.python_implementation(),"platform":platform.platform(),"machine":platform.machine(),"processor":platform.processor(),"allowed_affinity":allowed,"selected_cpu":allowed[0] if allowed else None,"gcc":subprocess.run(["gcc","--version"],text=True,capture_output=True,check=True).stdout.splitlines()[0],"cflags":"-O3 -Wall -Wextra -fPIC -shared -Wl,--build-id=none","extension":next((p.name for p in root.glob("native_predicate*.so")), None)}


def measure(root: Path, out: Path):
    native = import_native(root)
    frames, expected, corpus_hash = build_corpus()
    py_counts = [python_count(x) for x in frames]
    native_counts = [native.count_target(x) for x in frames]
    if expected != py_counts or expected != native_counts:
        raise RuntimeError("semantic precondition failed")
    allowed = sorted(os.sched_getaffinity(0)) if hasattr(os, "sched_getaffinity") else []
    if allowed:
        os.sched_setaffinity(0, {allowed[0]})
    gc.collect(); gc.disable()
    try:
        warm_order = rotated_order(0)
        for fn in (python_count, native.count_target):
            checksum=0
            for _ in range(WARMUP_REPEATS):
                for idx in warm_order:
                    checksum += fn(frames[idx])
            if checksum <= 0: raise RuntimeError("invalid warmup checksum")
        blocks=[]
        for pair in range(PAIRS):
            order=rotated_order(pair)
            arms = ["python","native"] if pair % 2 == 0 else ["native","python"]
            rec={"pair":pair,"order_first":arms[0],"arms":{}}
            for arm in arms:
                fn = python_count if arm=="python" else native.count_target
                rec["arms"][arm]=run_block(fn,frames,order,REPEATS_PER_BLOCK)
            blocks.append(rec)
    finally:
        gc.enable()
    wall_ratios=[]; cpu_ratios=[]
    for rec in blocks:
        p=rec["arms"]["python"]; n=rec["arms"]["native"]
        if p["checksum"] != n["checksum"]:
            raise RuntimeError("block checksum mismatch")
        wall_ratios.append(n["wall_ns_per_eval"]/p["wall_ns_per_eval"])
        cpu_ratios.append(n["thread_cpu_ns_per_eval"]/p["thread_cpu_ns_per_eval"])
    med_wall=statistics.median(wall_ratios); med_cpu=statistics.median(cpu_ratios)
    decision = "PASS_COST_SCOPED" if med_wall <= 1/3 and med_cpu <= 1/3 else "HOLD_COST"
    result={"schema":"quiet_watch_predicate_cost_v1_result","task":"QUIET-WATCH-PREDICATE-COST-20260916-001","constants":{"roi":[ROI_W,ROI_H],"roi_bytes":ROI_BYTES,"target_bgr":[50,50,220],"threshold":THRESHOLD,"corpus_n":CORPUS_N,"pairs":PAIRS,"repeats_per_block":REPEATS_PER_BLOCK,"warmup_repeats":WARMUP_REPEATS,"gate_ratio_max":1/3},"corpus_sha256":corpus_hash,"python_counts":py_counts,"native_counts":native_counts,"blocks":blocks,"summary":{"median_paired_wall_ratio":med_wall,"median_paired_thread_cpu_ratio":med_cpu,"python_wall_ns_per_eval_median":statistics.median([b["arms"]["python"]["wall_ns_per_eval"] for b in blocks]),"native_wall_ns_per_eval_median":statistics.median([b["arms"]["native"]["wall_ns_per_eval"] for b in blocks]),"python_thread_cpu_ns_per_eval_median":statistics.median([b["arms"]["python"]["thread_cpu_ns_per_eval"] for b in blocks]),"native_thread_cpu_ns_per_eval_median":statistics.median([b["arms"]["native"]["thread_cpu_ns_per_eval"] for b in blocks]),"wall_ratios":wall_ratios,"thread_cpu_ratios":cpu_ratios,"semantics_equal":py_counts==native_counts==expected,"decision":decision},"environment":env_info(root)}
    out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps(result["summary"],indent=2,sort_keys=True))


def main():
    ap=argparse.ArgumentParser(); ap.add_argument("mode",choices=["correctness","measure"]); ap.add_argument("--out",required=True); args=ap.parse_args(); root=Path(__file__).resolve().parent
    if args.mode=="correctness": correctness(root,Path(args.out))
    else: measure(root,Path(args.out))

if __name__=="__main__": main()
