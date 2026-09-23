"""Controlled temporal observation transfer fixture for Issue #2013."""
import hashlib,json
W,H=8,6
def capture(seq,t,scope,pixels):
    return {"seq":seq,"t":t,"scope":scope,"pixels":bytes(pixels)}
def query(frames,scope,now,window):
    xs=sorted([f for f in frames if f["scope"]==scope and now-window<=f["t"]<=now],key=lambda f:f["t"])
    drops=[(a["seq"],b["seq"]) for a,b in zip(xs,xs[1:]) if b["seq"]>a["seq"]+1]
    return {"current":xs[-1] if xs else None,"history":xs[:-1],"drops":drops,"raw_count":len(xs),"scope":scope}
def roi(frame,x,y,w,h):
    p=frame["pixels"]
    return bytes(p[yy*W+xx] for yy in range(y,y+h) for xx in range(x,x+w))
def run():
    base=bytes([0]*(W*H)); changed=bytearray(base); changed[2*W+3]=255
    frames=[capture(0,0,"A",base),capture(1,10,"A",base),
            capture(3,30,"A",changed),capture(4,40,"B",changed)]
    q=query(frames,"A",40,45)
    assert q["current"]["seq"]==3 and [f["seq"] for f in q["history"]]==[0,1]
    assert q["drops"]==[(1,3)] and q["scope"]=="A"
    assert roi(q["current"],3,2,1,1)==bytes([255])
    stale=query(frames,"A",100,20)
    assert stale["current"] is None and stale["history"]==[]
    return {"frames":len(frames),"current_seq":q["current"]["seq"],
            "history_seqs":[f["seq"] for f in q["history"]],"drops":q["drops"],
            "roi_sha":hashlib.sha256(roi(q["current"],3,2,1,1)).hexdigest(),
            "stale_current":stale["current"]}
if __name__=="__main__": print(json.dumps(run(),sort_keys=True,default=str))
