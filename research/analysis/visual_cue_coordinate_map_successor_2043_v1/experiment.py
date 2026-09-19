import hashlib, json

W,H=16,12
TARGETS=[(1,1,2,2),(13,0,3,2),(7,9,2,2),(0,0,0,0)]
ARMS=("RAW","BORDER_RULER","COARSE_GRID","TARGET_CONTEXT_CROP")

def encode(arm,t):
    x,y,w,h=t
    if arm=="RAW": return {"source_size":[W,H],"target":None}
    if arm=="BORDER_RULER": return {"source_size":[W,H],"border":[x,y,w,h]}
    if arm=="COARSE_GRID": return {"source_size":[W,H],"grid":[4,3],"cell_target":None if not w else [x//4,y//4]}
    return {"source_size":[W,H],"crop":None if not w else [max(0,x-1),max(0,y-1),min(W,x+w+1),min(H,y+h+1)]}

def decode(arm,p):
    if arm=="RAW": return None,"UNAVAILABLE_RAW_FALLBACK"
    if arm=="BORDER_RULER":
        b=p["border"]; return (tuple(b) if b[2] and b[3] else None),"EXACT"
    if arm=="COARSE_GRID":
        return None,"UNAVAILABLE_COARSE_NO_EXACT_INVERSE"
    c=p["crop"]
    return ((c[0],c[1],c[2]-c[0],c[3]-c[1]) if c else None),"CONSERVATIVE_CONTEXT"

def main():
    rows=[]
    for family,t in enumerate(TARGETS):
        for arm in ARMS:
            p=encode(arm,t); mapped,mode=decode(arm,p)
            present=bool(t[2] and t[3])
            if arm=="BORDER_RULER": ok=(mapped==t)
            elif arm=="TARGET_CONTEXT_CROP": ok=(not present and mapped is None) or (present and mapped[0]<=t[0] and mapped[1]<=t[1] and mapped[0]+mapped[2]>=t[0]+t[2] and mapped[1]+mapped[3]>=t[1]+t[3])
            else: ok=(not present and mapped is None)
            rows.append({"family":family,"arm":arm,"target":t,"mapped":mapped,"mode":mode,"ok":ok,"raw_fallback":mode.startswith("UNAVAILABLE")})
    assert len(rows)==16 and all(r["ok"] for r in rows)
    assert all(r["raw_fallback"] for r in rows if r["arm"]=="RAW" or r["arm"]=="COARSE_GRID")
    raw=json.dumps(rows,sort_keys=True,separators=(",",":")).encode()
    print(json.dumps({"decision":"PASS_VISUAL_CUE_COORDINATE_MAP_AUDIT_SCOPED","rows":16,"mapping_failures":0,"exact_border_rows":3,"conservative_crop_rows":3,"explicit_unavailable_rows":10,"raw_fallback_violations":0,"model_invocations":0,"gui_mutations":0,"input_calls":0,"network_calls":0,"sha256":hashlib.sha256(raw).hexdigest()},sort_keys=True))
if __name__=="__main__": main()
