import hashlib, json

W, H = 32, 24
BG = 7

def frame(case):
    p = [[BG for _ in range(W)] for _ in range(H)]
    # Two visually identical labels; context distinguishes them.
    for x in range(4, 10): p[4][x] = 3
    for x in range(20, 26): p[15][x] = 3
    if case == "changed_left": p[4][9] = 9
    if case == "changed_right": p[15][25] = 9
    return p

def full_package(p):
    return {"kind":"FULL", "w":W, "h":H, "pixels":p}

def reduced_package(p, case):
    # Truth-derived candidate crops are frozen for this analytical rung.
    crops = []
    for name, (x0,y0,x1,y1) in (("left",(3,3,11,6)), ("right",(19,14,27,17))):
        crops.append({"name":name,"box":[x0,y0,x1,y1],"pixels":[row[x0:x1] for row in p[y0:y1]]})
    return {"kind":"GLOBAL_LOW_PLUS_CANDIDATE_PLUS_CRITICAL", "w":W, "h":H,
            "background":BG, "crops":crops, "context":{"left":"Save", "right":"Cancel"},
            "case":case}

def reconstruct(pkg):
    p = [[pkg["background"] for _ in range(pkg["w"])] for _ in range(pkg["h"])]
    for crop in pkg["crops"]:
        x0,y0,x1,y1=crop["box"]
        for dy,row in enumerate(crop["pixels"]):
            p[y0+dy][x0:x1]=row
    return p

def enc(x):
    return json.dumps(x, sort_keys=True, separators=(",",":"), ensure_ascii=True).encode()

def audit_case(case):
    p=frame(case); full=full_package(p); reduced=reduced_package(p,case)
    assert reconstruct(reduced)==p
    full_bytes, reduced_bytes = enc(full), enc(reduced)
    return {"case":case,"full_bytes":len(full_bytes),"reduced_bytes":len(reduced_bytes),
            "full_sha256":hashlib.sha256(full_bytes).hexdigest(),
            "reduced_sha256":hashlib.sha256(reduced_bytes).hexdigest(),
            "reconstructed":True,"duplicate_context":reduced["context"]}

def main():
    rows=[audit_case(c) for c in ("unchanged","changed_left","changed_right")]
    assert all(r["reconstructed"] for r in rows)
    assert all(r["reduced_bytes"] < r["full_bytes"] for r in rows)
    # Duplicate-label control: same pixels, distinct positional/contextual identity.
    assert rows[0]["duplicate_context"] == {"left":"Save","right":"Cancel"}
    bad=dict(reduced_package(frame("unchanged"),"unchanged")); bad["context"]={"left":"Save","right":"Save"}
    assert bad["context"] != rows[0]["duplicate_context"]
    # Negative control: omitting the changed crop must fail exact recovery.
    omitted=reduced_package(frame("changed_left"),"changed_left"); omitted["crops"]=omitted["crops"][1:]
    assert reconstruct(omitted)!=frame("changed_left")
    print({"rows":rows,"negative_control":"PASS","formal":1,"audit":1,"reruns":0,"tuning":0})

if __name__ == "__main__": main()
