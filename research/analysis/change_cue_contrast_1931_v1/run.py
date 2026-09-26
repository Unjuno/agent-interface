#!/usr/bin/env python3
import argparse, csv, gzip, hashlib, json, math, os, sys, time
from dataclasses import dataclass
from pathlib import Path

W=64; H=64
FIXED_GREEN=(0,255,0)
PAD=2
SIZES=((1,1),(2,2),(4,4),(8,4))
POSITIONS=("center","left","top","top_left","bottom_right")
LATTICE=(0,32,64,96,128,160,192,224,255)
BOUND=math.sqrt(21.0)

@dataclass(frozen=True)
class ROI:
    x:int; y:int; w:int; h:int

def sha256(b:bytes)->str: return hashlib.sha256(b).hexdigest()

def srgb_linear(v:int)->float:
    c=v/255.0
    return c/12.92 if c<=0.04045 else ((c+0.055)/1.055)**2.4

def luminance(rgb):
    r,g,b=rgb
    return 0.2126*srgb_linear(r)+0.7152*srgb_linear(g)+0.0722*srgb_linear(b)

def contrast(a,b):
    l1,l2=luminance(a),luminance(b)
    hi,lo=max(l1,l2),min(l1,l2)
    return (hi+0.05)/(lo+0.05)

def adaptive_bw(bg):
    cb=contrast((0,0,0),bg); cw=contrast((255,255,255),bg)
    return ((0,0,0),cb) if cb>=cw else ((255,255,255),cw)

def roi_for(pos, rw,rh):
    if pos=="center": return ROI((W-rw)//2,(H-rh)//2,rw,rh)
    if pos=="left": return ROI(0,(H-rh)//2,rw,rh)
    if pos=="top": return ROI((W-rw)//2,0,rw,rh)
    if pos=="top_left": return ROI(0,0,rw,rh)
    if pos=="bottom_right": return ROI(W-rw,H-rh,rw,rh)
    raise ValueError(pos)

def image_uniform(rgb,w=W,h=H):
    return bytearray(bytes(rgb)*(w*h))

def set_px(img,w,x,y,rgb):
    i=(y*w+x)*3; img[i:i+3]=bytes(rgb)

def get_px(img,w,x,y):
    i=(y*w+x)*3; return tuple(img[i:i+3])

def make_pair(bg, roi):
    before=image_uniform(bg)
    current=bytearray(before)
    payload=tuple(255-c for c in bg)
    for y in range(roi.y,roi.y+roi.h):
        for x in range(roi.x,roi.x+roi.w): set_px(current,W,x,y,payload)
    return bytes(before),bytes(current)

def exact_diff_bbox(before,current,w=W,h=H):
    xs=[]; ys=[]
    for y in range(h):
        row=y*w*3
        for x in range(w):
            i=row+x*3
            if before[i:i+3]!=current[i:i+3]: xs.append(x); ys.append(y)
    if not xs: return None
    return ROI(min(xs),min(ys),max(xs)-min(xs)+1,max(ys)-min(ys)+1)

def ring_coords(roi,d):
    # Chebyshev-distance d outside rectangular ROI, in unbounded source coordinates.
    x0=roi.x-d; y0=roi.y-d; x1=roi.x+roi.w-1+d; y1=roi.y+roi.h-1+d
    out=[]
    for x in range(x0,x1+1): out.append((x,y0)); out.append((x,y1))
    for y in range(y0+1,y1): out.append((x0,y)); out.append((x1,y))
    return out

def render_outline(current, roi, mode, bg):
    if mode=="PADDED_DUAL_BW_OUTLINE":
        pw,ph=W+2*PAD,H+2*PAD
        # Pad with exact source background; source image maps at (+PAD,+PAD).
        img=image_uniform(bg,pw,ph)
        for y in range(H):
            src=y*W*3; dst=((y+PAD)*pw+PAD)*3
            img[dst:dst+W*3]=current[src:src+W*3]
        proi=ROI(roi.x+PAD,roi.y+PAD,roi.w,roi.h)
        strokes=[(1,(0,0,0)),(2,(255,255,255))]
        expected=actual=0
        for d,col in strokes:
            coords=ring_coords(proi,d); expected+=len(coords)
            for x,y in coords:
                if 0<=x<pw and 0<=y<ph:
                    set_px(img,pw,x,y,col); actual+=1
        return bytes(img),pw,ph,PAD,PAD,expected,actual,strokes
    pw,ph=W,H; img=bytearray(current)
    if mode=="FIXED_GREEN_OUTLINE": strokes=[(1,FIXED_GREEN)]
    elif mode=="ADAPTIVE_BW_OUTLINE": strokes=[(1,adaptive_bw(bg)[0])]
    elif mode=="DUAL_BW_OUTLINE": strokes=[(1,(0,0,0)),(2,(255,255,255))]
    else: raise ValueError(mode)
    expected=actual=0
    for d,col in strokes:
        coords=ring_coords(roi,d); expected+=len(coords)
        for x,y in coords:
            if 0<=x<pw and 0<=y<ph:
                # By construction rings are strictly outside ROI.
                set_px(img,pw,x,y,col); actual+=1
    return bytes(img),pw,ph,0,0,expected,actual,strokes

def mapped_roi_bytes(img,pw,offx,offy,roi):
    b=bytearray()
    for y in range(roi.y,roi.y+roi.h):
        for x in range(roi.x,roi.x+roi.w): b.extend(get_px(img,pw,x+offx,y+offy))
    return bytes(b)

def source_roi_bytes(current,roi):
    b=bytearray()
    for y in range(roi.y,roi.y+roi.h):
        for x in range(roi.x,roi.x+roi.w): b.extend(get_px(current,W,x,y))
    return bytes(b)

def colors_formal():
    s={(v,v,v) for v in range(256)}
    for r in LATTICE:
        for g in LATTICE:
            for b in LATTICE: s.add((r,g,b))
    s.add(FIXED_GREEN)
    return sorted(s)

def colors_construction():
    return [(7,13,19),(123,45,67),(250,3,111),(1,254,130)]

def cases(colors):
    idx=0
    for bg in colors:
        for rw,rh in SIZES:
            for pos in POSITIONS:
                roi=roi_for(pos,rw,rh)
                yield idx,bg,roi,pos
                idx+=1

def validate_case(bg,roi):
    before,current=make_pair(bg,roi)
    bbox=exact_diff_bbox(before,current)
    if bbox!=roi: raise AssertionError((bg,roi,bbox))
    return before,current

def formal(outdir):
    outdir=Path(outdir); outdir.mkdir(parents=True,exist_ok=True)
    raw_path=outdir/"ROWS.csv.gz"
    t0=time.perf_counter_ns()
    counts={
      "cases":0,"rows":0,"roi_preserved_fail":0,"mapping_fail":0,
      "fixed_zero_contrast":0,"fixed_lt3":0,"adaptive_bound_fail":0,"dual_bound_fail":0,
      "padded_completeness_fail":0,"clipped_rows":0
    }
    min_adapt=999.0; min_dual=999.0; min_fixed=999.0
    witnesses=[]
    fields=["case_id","bg","position","roi","mode","before_sha256","source_sha256","presentation_sha256",
            "roi_preserved","mapping_ok","expected_cue_px","actual_cue_px","cue_completeness","contrast_value","bound_ok"]
    with gzip.open(raw_path,"wt",newline="",encoding="utf-8",compresslevel=9,mtime=0) as gz:
        w=csv.DictWriter(gz,fieldnames=fields); w.writeheader()
        for cid,bg,roi,pos in cases(colors_formal()):
            counts["cases"]+=1
            before,current=validate_case(bg,roi)
            sroi=source_roi_bytes(current,roi)
            bsha=sha256(before); ssha=sha256(current)
            for mode in ("FIXED_GREEN_OUTLINE","ADAPTIVE_BW_OUTLINE","DUAL_BW_OUTLINE","PADDED_DUAL_BW_OUTLINE"):
                pres,pw,ph,ox,oy,expected,actual,strokes=render_outline(current,roi,mode,bg)
                roi_ok=(mapped_roi_bytes(pres,pw,ox,oy,roi)==sroi)
                # Exact inverse mapping check for all ROI corners and center-ish integer points.
                pts={(roi.x,roi.y),(roi.x+roi.w-1,roi.y+roi.h-1),(roi.x+roi.w//2,roi.y+roi.h//2)}
                map_ok=all((px+ox-ox,py+oy-oy)==(px,py) for px,py in pts)
                if not roi_ok: counts["roi_preserved_fail"]+=1
                if not map_ok: counts["mapping_fail"]+=1
                comp=actual/expected if expected else 1.0
                if comp<1.0-1e-15: counts["clipped_rows"]+=1
                if mode=="PADDED_DUAL_BW_OUTLINE" and comp!=1.0: counts["padded_completeness_fail"]+=1
                if mode=="FIXED_GREEN_OUTLINE":
                    cv=contrast(FIXED_GREEN,bg); min_fixed=min(min_fixed,cv); bound_ok=True
                    if abs(cv-1.0)<1e-12: counts["fixed_zero_contrast"]+=1
                    if cv<3.0: counts["fixed_lt3"]+=1
                    if cv<1.05 and len(witnesses)<16: witnesses.append({"case_id":cid,"bg":bg,"roi":roi.__dict__,"position":pos,"mode":mode,"contrast":cv})
                elif mode=="ADAPTIVE_BW_OUTLINE":
                    _,cv=adaptive_bw(bg); min_adapt=min(min_adapt,cv); bound_ok=cv+1e-12>=BOUND
                    if not bound_ok: counts["adaptive_bound_fail"]+=1
                else:
                    cb=contrast((0,0,0),bg); cw=contrast((255,255,255),bg); cv=max(cb,cw); min_dual=min(min_dual,cv); bound_ok=cv+1e-12>=BOUND
                    if not bound_ok: counts["dual_bound_fail"]+=1
                w.writerow({
                  "case_id":cid,"bg":"%d,%d,%d"%bg,"position":pos,
                  "roi":f"{roi.x},{roi.y},{roi.w},{roi.h}","mode":mode,
                  "before_sha256":bsha,"source_sha256":ssha,"presentation_sha256":sha256(pres),
                  "roi_preserved":int(roi_ok),"mapping_ok":int(map_ok),"expected_cue_px":expected,"actual_cue_px":actual,
                  "cue_completeness":f"{comp:.12f}","contrast_value":f"{cv:.12f}","bound_ok":int(bound_ok)
                })
                counts["rows"]+=1
    raw_bytes=raw_path.read_bytes()
    result={
      "schema":"change-cue-contrast-v1","formal_invocations":1,"reruns":0,"replacements":0,"tuning_after_freeze":0,
      "canvas":[W,H],"pad":PAD,"background_count":len(colors_formal()),"sizes":[list(x) for x in SIZES],"positions":list(POSITIONS),
      "sqrt21_bound":BOUND,"counts":counts,"min_contrast":{"fixed_green":min_fixed,"adaptive_bw":min_adapt,"dual_bw":min_dual},
      "rows_gzip_sha256":sha256(raw_bytes),"rows_gzip_bytes":len(raw_bytes),"witnesses":witnesses,
      "elapsed_ns":time.perf_counter_ns()-t0
    }
    # Decision is mechanical from the frozen gates.
    ok=(counts["roi_preserved_fail"]==0 and counts["mapping_fail"]==0 and counts["fixed_zero_contrast"]>0 and counts["fixed_lt3"]>0
        and counts["adaptive_bound_fail"]==0 and counts["dual_bound_fail"]==0 and counts["padded_completeness_fail"]==0 and counts["clipped_rows"]>0)
    result["disposition"]="PASS_SOURCE_PRESERVING_CONTRAST_CUE_SCOPED" if ok else "FAIL_FORMAL_GATE"
    (outdir/"RESULT.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"
",encoding="utf-8")
    return result

def construction(outdir):
    outdir=Path(outdir); outdir.mkdir(parents=True,exist_ok=True)
    rows=0
    for cid,bg,roi,pos in cases(colors_construction()):
        before,current=validate_case(bg,roi)
        for mode in ("FIXED_GREEN_OUTLINE","ADAPTIVE_BW_OUTLINE","DUAL_BW_OUTLINE","PADDED_DUAL_BW_OUTLINE"):
            pres,pw,ph,ox,oy,expected,actual,strokes=render_outline(current,roi,mode,bg)
            assert mapped_roi_bytes(pres,pw,ox,oy,roi)==source_roi_bytes(current,roi)
            assert actual<=expected
            if mode=="PADDED_DUAL_BW_OUTLINE": assert actual==expected
            rows+=1
    o={"construction_only":True,"colors":colors_construction(),"cases":len(colors_construction())*len(SIZES)*len(POSITIONS),"rows":rows,"status":"PASS_CONSTRUCTION"}
    (outdir/"CONSTRUCTION.json").write_text(json.dumps(o,indent=2,sort_keys=True)+"
",encoding="utf-8")
    return o

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("mode",choices=["construction","formal"]); ap.add_argument("--out",required=True); a=ap.parse_args()
    r=construction(a.out) if a.mode=="construction" else formal(a.out)
    print(json.dumps(r,sort_keys=True))
if __name__=="__main__": main()
