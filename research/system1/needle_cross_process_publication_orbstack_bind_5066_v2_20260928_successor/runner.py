"""One-shot cross-process publication probe; formal entrypoint inside container only."""
from __future__ import annotations

import hashlib
import base64
import json
import multiprocessing as mp
import os
from pathlib import Path
import platform
import sys
import threading
import time

from protocol import ALLOCATION, IMAGE_ID, NEW, OLD, SEED_SHA256, canonical_bytes, successor, valid

EXP = Path("/src/research/system1/needle_cross_process_publication_orbstack_bind_5066_v2_20260928_successor")
SEED = Path("/src/research/needle_role_skill_reload_3780_v1/formal/seed-3788/builder/skill.json")
OUT = Path("/out")
READERS = 4
PHASES = 7


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def decode(raw: bytes) -> dict:
    encoded=base64.b64encode(raw).decode("ascii")
    try:
        value = json.loads(raw)
        return {"bytes": len(raw), "raw_sha256": sha(raw), "parse_ok": True,
                "valid": valid(value), "generation": value.get("generation"),
                "embedded_digest": value.get("payload_sha256"),"raw_b64":encoded}
    except (UnicodeDecodeError, json.JSONDecodeError, TypeError, AttributeError):
        return {"bytes": len(raw), "raw_sha256": sha(raw), "parse_ok": False,
                "valid": False, "generation": None, "embedded_digest": None,"raw_b64":encoded}


def reader(index: int, path: str, commands, responses):
    held = None
    while True:
        command = commands.get()
        if command is None:
            if held: held.close()
            return
        action, phase, request_id = command
        try:
            if action == "hold":
                if held is not None: held.close()
                held = open(path, "rb")
                responses.put({"action": action, "phase": phase, "request": request_id,
                               "reader": index, "pid": os.getpid(), "fd_open_ns": time.monotonic_ns()})
            elif action == "read_held_and_path":
                fd_read_start = time.monotonic_ns()
                held.seek(0); held_raw = held.read()
                fd_read_end = time.monotonic_ns()
                path_start = time.monotonic_ns(); path_raw = Path(path).read_bytes(); path_end = time.monotonic_ns()
                responses.put({"action": action, "phase": phase, "request": request_id,
                               "reader": index, "pid": os.getpid(), "fd_read_start_ns": fd_read_start,
                               "fd_read_end_ns": fd_read_end, "held": decode(held_raw),
                               "path_read_start_ns": path_start, "path_read_end_ns": path_end,
                               "path": decode(path_raw)})
                held.close(); held = None
            elif action == "read_partial_and_complete":
                a = time.monotonic_ns(); partial_raw = Path(path).read_bytes(); b = time.monotonic_ns()
                responses.put({"action": action, "phase": phase, "request": request_id,
                               "reader": index, "pid": os.getpid(), "partial_start_ns": a,
                               "partial_end_ns": b, "partial": decode(partial_raw)})
                done = commands.get()
                if done != ("read_complete", phase, request_id): raise RuntimeError("release command mismatch")
                c = time.monotonic_ns(); complete_raw = Path(path).read_bytes(); d = time.monotonic_ns()
                responses.put({"action": "read_complete", "phase": phase, "request": request_id,
                               "reader": index, "pid": os.getpid(), "complete_start_ns": c,
                               "complete_end_ns": d, "complete": decode(complete_raw)})
            else:
                raise ValueError("unknown reader action")
        except BaseException as exc:
            responses.put({"action": action, "phase": phase, "request": request_id,
                           "reader": index, "pid": os.getpid(), "error": type(exc).__name__ + ":" + str(exc)})


def launch(active: Path):
    workers = []
    for i in range(READERS):
        q, r = mp.Queue(), mp.Queue()
        p = mp.Process(target=reader, args=(i, str(active), q, r)); p.start()
        workers.append((p, q, r))
    pids = [p.pid for p, _, _ in workers]
    if len(set(pids)) != READERS or os.getpid() in pids: raise RuntimeError("reader identity failure")
    return workers


def ask(workers, action: str, phase: str, suffix: str) -> list[dict]:
    request_id = phase + ":" + suffix
    for _, q, _ in workers: q.put((action, phase, request_id))
    result = []
    for i, (_, _, r) in enumerate(workers):
        row = r.get(timeout=30)
        if row.get("request") != request_id or row.get("reader") != i or row.get("error"):
            raise RuntimeError("reader response mismatch: " + repr(row))
        result.append(row)
    return result


def finish(workers):
    for _, q, _ in workers: q.put(None)
    for p, _, _ in workers:
        p.join(10)
        if p.is_alive(): p.terminate(); p.join()
    exits = [p.exitcode for p, _, _ in workers]
    if exits != [0] * READERS: raise RuntimeError("reader exits: " + repr(exits))
    return exits


def try_publish(active: Path, temporary: Path, base_generation: int, candidate_raw: bytes) -> dict:
    before_raw=active.read_bytes(); before=decode(before_raw)
    try: package=json.loads(candidate_raw)
    except (UnicodeDecodeError,json.JSONDecodeError): package=None
    if not valid(package): disposition="YIELD_INVALID_CANDIDATE"
    elif before.get("generation")!=base_generation: disposition="YIELD_STALE_GENERATION"
    elif package.get("generation")!=base_generation+1: disposition="YIELD_INVALID_TRANSITION"
    else:
        temporary.write_bytes(candidate_raw)
        if not valid(json.loads(temporary.read_bytes())): raise RuntimeError("staged publication failed revalidation")
        start=time.monotonic_ns();os.replace(temporary,active);returned=time.monotonic_ns()
        after_raw=active.read_bytes()
        return {"disposition":"PUBLISHED","active_before_generation":before.get("generation"),
                "active_after_generation":json.loads(after_raw).get("generation"),
                "before_sha256":sha(before_raw),"after_sha256":sha(after_raw),
                "candidate_sha256":sha(candidate_raw),"replace_start_ns":start,"replace_return_ns":returned}
    after_raw=active.read_bytes()
    return {"disposition":disposition,"active_before_generation":before.get("generation"),
            "active_after_generation":json.loads(after_raw).get("generation"),
            "before_sha256":sha(before_raw),"after_sha256":sha(after_raw),
            "candidate_sha256":sha(candidate_raw),"replace_start_ns":None,"replace_return_ns":None}


def run_atomic(root: Path, old_raw: bytes, candidates: list[tuple[dict,bytes]]) -> dict:
    folder = root / "atomic"; folder.mkdir()
    active = folder / "ACTIVE.json"; active.write_bytes(old_raw)
    next_file = folder / "candidate.tmp"
    records, replacements, post_rows = [], [], []
    workers = launch(active)
    try:
        for n, (package,candidate) in enumerate(candidates,1):
            phase = f"phase_{n}"
            held = ask(workers, "hold", phase, "open")
            base_generation=OLD+n-1
            publication=try_publish(active,next_file,base_generation,candidate)
            if publication["disposition"]!="PUBLISHED":raise RuntimeError("candidate unexpectedly refused: "+repr(publication))
            start,returned=publication["replace_start_ns"],publication["replace_return_ns"]
            replacements.append({"phase": phase, "replace_start_ns": start, "replace_return_ns": returned})
            post = ask(workers, "read_held_and_path", phase, "post")
            opens = {r["reader"]: r["fd_open_ns"] for r in held}
            for row in post:
                records.append({"phase":phase,"reader":row["reader"],"pid":row["pid"],
                    "fd_open_ns":opens[row["reader"]],"replace_start_ns":start,
                    "replace_return_ns":returned,"fd_read_start_ns":row["fd_read_start_ns"],
                    "fd_read_end_ns":row["fd_read_end_ns"],"held":row["held"],
                    "previous_generation":base_generation,"target_generation":package["generation"],
                    "publication":publication})
                post_rows.append({"phase":phase,"reader":row["reader"],"pid":row["pid"],
                    "replace_return_ns":returned,"path_read_start_ns":row["path_read_start_ns"],
                    "path_read_end_ns":row["path_read_end_ns"],"path":row["path"],
                    "target_generation":package["generation"],"target_raw_sha256":sha(candidate)})
        return {"publisher_pid": os.getpid(), "reader_pids": [p.pid for p, _, _ in workers],
                "exit_codes": finish(workers), "rows": records, "post_rows": post_rows,
                "replacement_intervals": replacements}
    finally:
        if any(p.is_alive() for p, _, _ in workers): finish(workers)


def run_unsafe(root: Path, old_raw: bytes, candidates: list[tuple[dict,bytes]]) -> dict:
    folder = root / "unsafe"; folder.mkdir()
    active = folder / "ACTIVE.json"; active.write_bytes(old_raw)
    workers = launch(active); records, intervals = [], []
    try:
        for n,(_,candidate) in enumerate(candidates,1):
            phase = f"phase_{n}"
            prefix_ready, finish_write = threading.Event(), threading.Event()
            writer_errors = []
            writer_bounds={}
            def writer():
                try:
                    writer_bounds["start_ns"]=time.monotonic_ns()
                    with active.open("wb") as stream:
                        stream.write(candidate[:len(candidate)//2]); stream.flush(); os.fsync(stream.fileno())
                        prefix_ready.set()
                        if not finish_write.wait(30): raise RuntimeError("unsafe write release timeout")
                        stream.write(candidate[len(candidate)//2:]); stream.flush(); os.fsync(stream.fileno())
                    writer_bounds["end_ns"]=time.monotonic_ns()
                except BaseException as exc: writer_errors.append(type(exc).__name__ + ":" + str(exc))
            thread = threading.Thread(target=writer); thread.start()
            if not prefix_ready.wait(10): raise RuntimeError("partial prefix barrier missing")
            partial = ask(workers, "read_partial_and_complete", phase, "partial")
            finish_write.set(); thread.join(30)
            if thread.is_alive() or writer_errors: raise RuntimeError("unsafe writer failed: " + repr(writer_errors))
            for _, q, _ in workers: q.put(("read_complete", phase, phase + ":partial"))
            complete = []
            for i, (_, _, r) in enumerate(workers):
                row = r.get(timeout=30)
                if row.get("request") != phase + ":partial" or row.get("phase") != phase or row.get("reader") != i or row.get("action") != "read_complete":
                    raise RuntimeError("completion read mismatch: " + repr(row))
                complete.append(row)
            by_reader = {r["reader"]: r for r in complete}
            for row in partial:
                row["complete"] = by_reader[row["reader"]]["complete"]
                row["complete_start_ns"] = by_reader[row["reader"]]["complete_start_ns"]
                row["complete_end_ns"] = by_reader[row["reader"]]["complete_end_ns"]
                row["write_start_ns"], row["write_end_ns"] = writer_bounds["start_ns"], writer_bounds["end_ns"]
            records.extend(partial); intervals.append({"phase": phase, "start_ns": writer_bounds["start_ns"], "end_ns": writer_bounds["end_ns"]})
        return {"publisher_pid": os.getpid(), "reader_pids": [p.pid for p, _, _ in workers],
                "exit_codes": finish(workers), "rows": records, "write_intervals": intervals}
    finally:
        if any(p.is_alive() for p, _, _ in workers): finish(workers)


def main():
    if set(p.name for p in OUT.iterdir()) != {"invocation_receipt.json"}:
        raise RuntimeError("output must contain only the host-created invocation receipt")
    receipt = json.loads((OUT / "invocation_receipt.json").read_text())
    for key, env in (("source_commit", "OBSTAC_SOURCE_COMMIT"), ("image_id", "OBSTAC_IMAGE_ID"),
                     ("freeze_sha256", "OBSTAC_FREEZE_SHA256"), ("construction", "OBSTAC_CONSTRUCTION")):
        if receipt.get(key) != os.environ.get(env): raise RuntimeError("receipt/environment mismatch: " + key)
    if receipt["image_id"] != IMAGE_ID or receipt["construction"] != "0": raise RuntimeError("formal image/flag mismatch")
    old_raw = SEED.read_bytes()
    if sha(old_raw) != SEED_SHA256: raise RuntimeError("seed digest mismatch")
    old = json.loads(old_raw)
    if old.get("generation") != OLD or not valid(old): raise RuntimeError("seed validation failed")
    candidate_packages=[successor(old,NEW+n) for n in range(PHASES)]
    candidates=[(obj,canonical_bytes(obj)) for obj in candidate_packages]
    root = OUT / "work"; root.mkdir()
    atomic = run_atomic(root, old_raw, candidates)
    active_path = root / "atomic/ACTIVE.json"
    final_obj,final_raw=candidates[-1]
    invalid = dict(final_obj); invalid["payload_sha256"] = "0" * 64
    invalid_path = root / "atomic/invalid-proposal.json"
    invalid_raw = canonical_bytes(invalid); invalid_path.write_bytes(invalid_raw)
    reject_path=root/"atomic/rejected.tmp"
    invalid_result=try_publish(active_path,reject_path,final_obj["generation"],invalid_raw)
    stale_obj,stale_raw=candidates[0]
    stale_result=try_publish(active_path,reject_path,OLD,stale_raw)
    active_rejections={"invalid_proposal":{**decode(invalid_raw)},"invalid_result":invalid_result,
                       "stale_proposal":{"base_generation":OLD,"package":{**decode(stale_raw)},
                                         "target_generation":stale_obj["generation"]},
                       "stale_result":stale_result}
    if invalid_result["disposition"]!="YIELD_INVALID_CANDIDATE" or stale_result["disposition"]!="YIELD_STALE_GENERATION" or invalid_result["before_sha256"]!=invalid_result["after_sha256"] or stale_result["before_sha256"]!=stale_result["after_sha256"]:
        raise RuntimeError("invalid/stale candidate gate failed")
    unsafe = run_unsafe(root, old_raw, candidates)
    registry=[{"generation":obj["generation"],"raw_sha256":sha(raw),"bytes":len(raw),
               "payload_sha256":obj["payload_sha256"]} for obj,raw in candidates]
    raw = {"allocation":ALLOCATION,"issue":5134,
           "formal_invocations":1,"python":sys.version,
           "platform":"linux/arm64" if platform.machine() in ("aarch64","arm64") else platform.platform(),
           "image_id":receipt["image_id"],"source_commit":receipt["source_commit"],
           "live_main_sha":receipt["live_main_sha"],
           "source_tree_sha":receipt["source_tree_sha"],"source_blob_sha256":receipt["source_blob_sha256"],
           "source_sha256":receipt["source_sha256"],
           "freeze_sha256":receipt["freeze_sha256"],"construction":"0",
           "mounts":receipt["mounts"],"input_git_blob":"45b80150dac503f4eb6f3cb5d82f9afa2c587107",
           "input_sha256":sha(old_raw),"input_bytes":len(old_raw),"old_raw_sha256":sha(old_raw),
           "old_digest":old["payload_sha256"],"candidate_raw_sha256":sha(final_raw),
           "candidate_bytes":len(final_raw),"candidate_digest":final_obj["payload_sha256"],
           "candidate_registry":registry,
           "dispatch_count":0,"authority_granted":False,"atomic":atomic,"unsafe":unsafe,
           "rejection_gate":active_rejections}
    (OUT / "raw.json").write_text(json.dumps(raw,sort_keys=True,indent=2)+"\n")
    print(json.dumps({"formal":"RAW_CAPTURED","atomic_rows":len(atomic["rows"]),
                      "post_rows":len(atomic["post_rows"]),"unsafe_rows":len(unsafe["rows"])}))
    return 0


if __name__ == "__main__": raise SystemExit(main())
