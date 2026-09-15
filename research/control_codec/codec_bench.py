#!/usr/bin/env python3
"""Historical model-free C0/C1 serialization benchmark.

This file is retained from the original Control Codec research track. It is not
the authoritative current C1 wire contract; see research/runtime_portability_v0.
Bytes reported here are serialization proxies, not provider tokens.
"""
from __future__ import annotations
import argparse, csv, json, random, statistics, time
from pathlib import Path
from typing import Any

KEYS=["A","C","G","X","ENTER","ESC","TAB","CTRL","SHIFT","ALT"]
BUTTONS=["L","R"]
WORDS=["hello","save","0.3","draft","node","layer","frame"]
WINDOWS=["editor","canvas","terminal","browser"]
ASSERTS=["changed","focused","dialog_closed","selection_exists"]

def _split(program:str)->list[str]:
    out=[]; buf=[]; quoted=False; escaped=False
    for ch in program:
        if escaped: buf.append(ch); escaped=False; continue
        if quoted and ch=="\\": buf.append(ch); escaped=True; continue
        if ch=='"': quoted=not quoted; buf.append(ch); continue
        if ch==";" and not quoted:
            token="".join(buf)
            if token: out.append(token)
            buf.clear(); continue
        buf.append(ch)
    if quoted: raise ValueError("unterminated string")
    token="".join(buf)
    if token: out.append(token)
    return out

def encode_c1(ops:list[dict[str,Any]])->str:
    parts=[]
    for op in ops:
        t=op["type"]
        if t=="key": parts.append("k:"+"+".join(op["keys"]))
        elif t=="key_down": parts.append("kd:"+op["key"])
        elif t=="key_up": parts.append("ku:"+op["key"])
        elif t=="text": parts.append("t:"+json.dumps(op["text"],ensure_ascii=False,separators=(",",":")))
        elif t=="move_abs": parts.append(f"ma:{op['x']},{op['y']}")
        elif t=="move_rel": parts.append(f"mr:{op['dx']},{op['dy']}")
        elif t=="button_down": parts.append("bd:"+op["button"])
        elif t=="button_up": parts.append("bu:"+op["button"])
        elif t=="click": parts.append(f"c:{op['x']},{op['y']},{op['button']}")
        elif t=="scroll": parts.append(f"s:{op['dx']},{op['dy']}")
        elif t=="focus": parts.append("f:"+json.dumps(op["target"],ensure_ascii=False,separators=(",",":")))
        elif t=="wait_update": parts.append("w")
        elif t=="observe": parts.append(f"o:{op['x']},{op['y']},{op['w']},{op['h']}")
        elif t=="assert": parts.append("a:"+json.dumps(op["predicate"],ensure_ascii=False,separators=(",",":")))
        else: raise ValueError(f"unsupported op: {t}")
    return ";".join(parts)

def decode_c1(program:str)->list[dict[str,Any]]:
    ops=[]
    for token in _split(program):
        if token=="w": ops.append({"type":"wait_update"}); continue
        code,payload=token.split(":",1)
        if code=="k": ops.append({"type":"key","keys":payload.split("+")})
        elif code=="kd": ops.append({"type":"key_down","key":payload})
        elif code=="ku": ops.append({"type":"key_up","key":payload})
        elif code=="t": ops.append({"type":"text","text":json.loads(payload)})
        elif code=="ma": x,y=map(int,payload.split(",")); ops.append({"type":"move_abs","x":x,"y":y})
        elif code=="mr": dx,dy=map(int,payload.split(",")); ops.append({"type":"move_rel","dx":dx,"dy":dy})
        elif code=="bd": ops.append({"type":"button_down","button":payload})
        elif code=="bu": ops.append({"type":"button_up","button":payload})
        elif code=="c": x,y,b=payload.split(","); ops.append({"type":"click","x":int(x),"y":int(y),"button":b})
        elif code=="s": dx,dy=map(int,payload.split(",")); ops.append({"type":"scroll","dx":dx,"dy":dy})
        elif code=="f": ops.append({"type":"focus","target":json.loads(payload)})
        elif code=="o": x,y,w,h=map(int,payload.split(",")); ops.append({"type":"observe","x":x,"y":y,"w":w,"h":h})
        elif code=="a": ops.append({"type":"assert","predicate":json.loads(payload)})
        else: raise ValueError(f"unknown opcode: {code}")
    return ops

def encode_c0(ops): return json.dumps(ops,ensure_ascii=False,separators=(",",":"))

def generate_program(rng, nominal_ops):
    ops=[]; held_keys=set(); held_buttons=set(); choices=["key","text","move_abs","move_rel","click","scroll","focus","wait","observe","assert"]
    while len(ops)<nominal_ops:
        choice=rng.choice(choices); remaining=nominal_ops-len(ops)
        if choice=="key" and remaining>=2 and rng.random()<.20:
            key=rng.choice(["CTRL","SHIFT","ALT"])
            if key not in held_keys: held_keys.add(key); ops.append({"type":"key_down","key":key}); continue
        if held_keys and rng.random()<.12:
            key=rng.choice(sorted(held_keys)); held_keys.remove(key); ops.append({"type":"key_up","key":key}); continue
        if choice=="click" and remaining>=2 and rng.random()<.12:
            b=rng.choice(BUTTONS)
            if b not in held_buttons: held_buttons.add(b); ops.append({"type":"button_down","button":b}); continue
        if held_buttons and rng.random()<.12:
            b=rng.choice(sorted(held_buttons)); held_buttons.remove(b); ops.append({"type":"button_up","button":b}); continue
        if choice=="key":
            keys=[rng.choice(KEYS[:7])]
            if rng.random()<.18: keys.insert(0,rng.choice(["CTRL","SHIFT","ALT"]))
            ops.append({"type":"key","keys":keys})
        elif choice=="text": ops.append({"type":"text","text":rng.choice(WORDS)})
        elif choice=="move_abs": ops.append({"type":"move_abs","x":rng.randrange(1920),"y":rng.randrange(1080)})
        elif choice=="move_rel": ops.append({"type":"move_rel","dx":rng.randrange(-200,201),"dy":rng.randrange(-200,201)})
        elif choice=="click": ops.append({"type":"click","x":rng.randrange(1920),"y":rng.randrange(1080),"button":rng.choice(BUTTONS)})
        elif choice=="scroll": ops.append({"type":"scroll","dx":rng.randrange(-8,9),"dy":rng.randrange(-8,9)})
        elif choice=="focus": ops.append({"type":"focus","target":rng.choice(WINDOWS)})
        elif choice=="wait": ops.append({"type":"wait_update"})
        elif choice=="observe": ops.append({"type":"observe","x":rng.randrange(1500),"y":rng.randrange(800),"w":rng.randrange(32,401),"h":rng.randrange(32,301)})
        else: ops.append({"type":"assert","predicate":rng.choice(ASSERTS)})
    for k in sorted(held_keys): ops.append({"type":"key_up","key":k})
    for b in sorted(held_buttons): ops.append({"type":"button_up","button":b})
    return ops

def run(seed,programs,sizes):
    rng=random.Random(seed); rows=[]
    for size in sizes:
        samples=[]
        for _ in range(programs):
            ops=generate_program(rng,size); c0=encode_c0(ops); c1=encode_c1(ops); start=time.perf_counter_ns(); decoded=decode_c1(c1); parse_ns=time.perf_counter_ns()-start
            if decoded!=ops: raise AssertionError("C1 round-trip mismatch")
            samples.append({"c0":len(c0.encode()),"c1":len(c1.encode()),"parse_us":parse_ns/1000,"actual_ops":len(ops)})
        m0=statistics.median(s["c0"] for s in samples); m1=statistics.median(s["c1"] for s in samples)
        rows.append({"nominal_ops":size,"programs":programs,"median_actual_ops":statistics.median(s["actual_ops"] for s in samples),"median_c0_bytes":m0,"median_c1_bytes":m1,"median_reduction_pct":100*(1-m1/m0),"median_c1_parse_us":statistics.median(s["parse_us"] for s in samples),"roundtrip_failures":0})
    return rows

def main():
    p=argparse.ArgumentParser(); p.add_argument("--seed",type=int,default=20260913); p.add_argument("--programs",type=int,default=1000); p.add_argument("--sizes",default="4,8,16,32,64"); p.add_argument("--out",type=Path,default=Path("control_codec_summary.csv")); a=p.parse_args()
    rows=run(a.seed,a.programs,[int(x) for x in a.sizes.split(",") if x]); a.out.parent.mkdir(parents=True,exist_ok=True)
    with a.out.open("w",newline="",encoding="utf-8") as f: w=csv.DictWriter(f,fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    for r in rows: print(f"ops={r['nominal_ops']:>2} C0={r['median_c0_bytes']:>7.1f}B C1={r['median_c1_bytes']:>7.1f}B reduction={r['median_reduction_pct']:>5.1f}% parse={r['median_c1_parse_us']:>7.2f}us")
    print(f"wrote {a.out}")
if __name__=="__main__": main()
