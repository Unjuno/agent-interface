"""Deterministic successor fixture for Issue #1968.

This intentionally compares canonical serialized package bytes, not sums of
selected pixel buffers. Duplicate visual labels are distinguished by position.
"""
import json, hashlib

W,H=64,40
REG={"save_left":(4,6,12,4,137),"save_right":(44,6,12,4,137),
     "dialog":(18,16,28,12,93),"status":(50,30,8,3,211)}

def frame(changes=()):
    px=[17]*(W*H)
    for x,y,w,h,v in REG.values():
        for yy in range(y,y+h):
            for xx in range(x,x+w): px[yy*W+xx]=v
    for name,value in changes:
        x,y,w,h,_=REG[name]
        for yy in range(y,y+h):
            for xx in range(x,x+w): px[yy*W+xx]=value
    return bytes(px)

def low(b): return bytes(b[y*4*W+x*4] for y in range(H//4) for x in range(W//4))
def crop(b,r):
    x,y,w,h,_=r
    return bytes(b[yy*W+xx] for yy in range(y,y+h) for xx in range(x,x+w))

def package(source,changed,arm):
    out={"arm":arm,"recipe":"serialized-successor-v1","low":list(low(source))}
    names=[n for n,_ in changed]
    selected=[n for n in names if n in ("save_left","save_right")]
    if arm in ("CANDIDATE","CRITICAL"):
        selected += [n for n in names if n not in selected and n != "status"][:1]
    if arm=="CRITICAL" and "status" in names: selected += ["status"]
    out["patches"]=[{"region":n,"x":REG[n][0],"y":REG[n][1],"w":REG[n][2],
                     "h":REG[n][3],"pixels":list(crop(source,REG[n]))}
                    for n in selected]
    if arm=="FULL": out["full"]=list(source)
    return json.dumps(out,sort_keys=True,separators=(",",":")).encode()

def rebuild(blob):
    p=json.loads(blob); b=bytearray(frame())
    if p["arm"]=="FULL": return bytes(p["full"])
    for q in p["patches"]:
        i=0
        for yy in range(q["y"],q["y"]+q["h"]):
            for xx in range(q["x"],q["x"]+q["w"]):
                b[yy*W+xx]=q["pixels"][i]; i+=1
    return bytes(b)

def run():
    cases=[(),(("save_left",151),),(("save_right",151),),
           (("save_left",151),("save_right",151)),(("status",233),),
           (("dialog",117),)]
    rows=[]
    for c in cases:
        src=frame(c)
        for arm in ("FULL","LOW_ONLY","CANDIDATE","CRITICAL"):
            raw=package(src,c,arm)
            rows.append({"case":c,"arm":arm,"exact":rebuild(raw)==src,
                         "bytes":len(raw),
                         "sha":hashlib.sha256(raw).hexdigest()})
    return rows

if __name__=="__main__":
    rows=run()
    for arm in ("FULL","LOW_ONLY","CANDIDATE","CRITICAL"):
        xs=[r for r in rows if r["arm"]==arm]
        print(arm,"exact",sum(r["exact"] for r in xs),"/",len(xs),
              "bytes",[r["bytes"] for r in xs])
    print("rows",len(rows))
