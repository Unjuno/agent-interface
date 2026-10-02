"""Independent raw-only audit. Does not import candidate.py or png_decode.py."""
import json
import struct
import sys
import zlib
import hashlib
from collections import Counter
from fractions import Fraction
from itertools import product
from pathlib import Path


def pixels(data, box, palette):
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("PNG signature")
    pos, compressed, dims, ctype = 8, bytearray(), None, None
    while pos < len(data):
        n = struct.unpack(">I", data[pos:pos+4])[0]
        tag, chunk = data[pos+4:pos+8], data[pos+8:pos+8+n]
        pos += n + 12
        if tag == b"IHDR":
            w, h, depth, ctype, comp, filt, inter = struct.unpack(">IIBBBBB", chunk)
            dims = (w, h)
            if depth != 8 or ctype not in (2, 6) or comp or filt or inter:
                raise ValueError("PNG format")
        elif tag == b"IDAT": compressed.extend(chunk)
        elif tag == b"IEND": break
    if dims is None: raise ValueError("IHDR missing")
    w, h = dims; bpp = 3 if ctype == 2 else 4; stride = w*bpp
    raw = zlib.decompress(compressed); prior = bytearray(stride); offset = 0; found = set()
    x, y, rw, rh = (box[k] for k in ("x", "y", "width", "height"))
    if x+rw>w or y+rh>h: raise ValueError("ROI bounds")
    allowed = {tuple(c) for c in palette}
    target_y = y + rh // 2
    target_x = (x + rw // 2) * bpp
    for rownum in range(target_y + 1):
        ft=raw[offset]; row=bytearray(raw[offset+1:offset+1+stride]); offset+=stride+1
        for i in range(target_x+3):
            a=row[i-bpp] if i>=bpp else 0; b=prior[i]; c=prior[i-bpp] if i>=bpp else 0
            if ft==1: row[i]=(row[i]+a)&255
            elif ft==2: row[i]=(row[i]+b)&255
            elif ft==3: row[i]=(row[i]+(a+b)//2)&255
            elif ft==4:
                p=a+b-c; pa,pb,pc=abs(p-a),abs(p-b),abs(p-c); pr=a if pa<=pb and pa<=pc else b if pb<=pc else c
                row[i]=(row[i]+pr)&255
            elif ft!=0: raise ValueError("PNG filter")
        if rownum == target_y:
            rgb=tuple(row[target_x:target_x+3])
            if rgb in allowed: found.add(rgb)
        prior=row
    if len(found)!=1: return "unresolved" if not found else "mixed"
    return "rgb:"+",".join(map(str,next(iter(found))))


def main(raw_dir, candidate_path, audit_path):
    root=Path(__file__).parent; raw=Path(raw_dir)
    states=json.loads((root/"states.json").read_text()); schedule=json.loads((root/"schedule.json").read_text())
    manifest=json.loads((raw/"manifest.json").read_text()); candidate=json.loads(Path(candidate_path).read_text())
    palette=states["allowed_pixel_rgb"]; counts={c:{s["id"]:Counter() for s in states["states"]} for c in states["channels"]}; errors=[]
    if len(manifest.get("captures", [])) != len(schedule["captures"]): errors.append("manifest-count")
    manifest_map={x.get("capture_id"):x for x in manifest.get("captures", [])}
    for item in schedule["captures"]:
        folder=raw/item["capture_id"]
        for field,filename in (("full_png","full_png.png"),("left_roi_png","left_roi_png.png"),("right_roi_png","right_roi_png.png"),("accessibility_snapshot","accessibility_snapshot.json"),("mutation_delta","mutation_delta.json")):
            if not (folder/filename).is_file(): errors.append(f"missing:{item['capture_id']}:{filename}")
        if errors and any(e.startswith(f"missing:{item['capture_id']}") for e in errors): continue
        mrow=manifest_map.get(item["capture_id"])
        if mrow is None or mrow.get("state") != item["state"]: errors.append("manifest-schedule:"+item["capture_id"])
        else:
            for filename,digest in mrow.get("artifacts", {}).items():
                file=folder/filename
                if not file.is_file() or hashlib.sha256(file.read_bytes()).hexdigest()!=digest:
                    errors.append("artifact-hash:"+item["capture_id"]+":"+filename)
        full_data=(folder/"full_png.png").read_bytes()
        full="|".join(pixels(full_data,box,palette) for box in states["pixel_regions"]["full_png"])
        counts["full_png"][item["state"]][full]+=1
        left=pixels((folder/"left_roi_png.png").read_bytes(),states["pixel_regions"]["left_roi_png"][0],palette)
        counts["left_roi_png"][item["state"]][left]+=1
        right=pixels((folder/"right_roi_png.png").read_bytes(),states["pixel_regions"]["right_roi_png"][0],palette)
        counts["right_roi_png"][item["state"]][right]+=1
        ax=(folder/"accessibility_snapshot.json").read_text(); state=next(s for s in states["states"] if s["id"]==item["state"]); label="exact:"+item["state"] if state["left"] in ax and state["right"] in ax else "unknown"; counts["accessibility_snapshot"][item["state"]][label]+=1
        delta=json.loads((folder/"mutation_delta.json").read_text()); counts["mutation_delta"][item["state"]]["changed" if delta else "quiet"]+=1
    reconstructed={}
    for channel,by_state in counts.items():
        outs=sorted({o for c in by_state.values() for o in c}); reconstructed[channel]={"outputs":outs,"counts_by_state":{s:[by_state[s][o] for o in outs] for s in sorted(by_state)},"kernel":[[[by_state[s][o],states["captures_per_state"]] for o in outs] for s in sorted(by_state)]}
        if reconstructed[channel]!=candidate.get("channels",{}).get(channel): errors.append("candidate-mismatch:"+channel)
        if any(sum(row)!=states["captures_per_state"] for row in reconstructed[channel]["counts_by_state"].values()): errors.append("incomplete-kernel:"+channel)
    # Reconstruct exact Bayes risks independently from raw observations.
    prior=[Fraction(*x) for x in states["prior"]]; risks={}
    for problem,spec in states["decision_problems"].items():
        risks[problem]={}
        for channel,by_state in counts.items():
            outputs=sorted({o for c in by_state.values() for o in c})
            kernel=[[Fraction(by_state[s][o],states["captures_per_state"]) for o in outputs] for s in sorted(by_state)]
            best=None
            for rule in product(range(len(spec["loss"][0])),repeat=len(outputs)):
                value=sum(prior[s]*kernel[s][o]*spec["loss"][s][rule[o]] for s in range(len(kernel)) for o in range(len(outputs)))
                best=value if best is None or value<best else best
            risks[problem][channel]=[best.numerator,best.denominator]
    if candidate.get("risks") != risks: errors.append("risk-reconstruction")
    rels=candidate.get("relations", {})
    if len(rels)!=len(counts)**2: errors.append("relation-count")
    # Verify positive garbling certificates directly; non-existence is not inferred from a candidate claim.
    for label,encoded in rels.items():
        left,right=label.split(">="); lc=reconstructed[left]; rc=reconstructed[right]
        if encoded is not None:
            k=[[Fraction(*x) for x in row] for row in encoded]
            src=[[Fraction(n,d) for n,d in row] for row in lc["kernel"]]
            dst=[[Fraction(n,d) for n,d in row] for row in rc["kernel"]]
            if len(k)!=len(src[0]) or any(len(r)!=len(dst[0]) or sum(r)!=1 or any(v<0 for v in r) for r in k): errors.append("garbling-shape:"+label); continue
            if any(sum(src[s][i]*k[i][j] for i in range(len(k)))!=dst[s][j] for s in range(len(src)) for j in range(len(dst[0]))): errors.append("garbling-invalid:"+label)
        elif not any(Fraction(*risks[p][left])>Fraction(*risks[p][right]) for p in risks):
            errors.append("no-nondominance-witness:"+label)
    if any(len(counts["accessibility_snapshot"][s])!=1 or next(iter(counts["accessibility_snapshot"][s])).startswith("unknown") for s in counts["accessibility_snapshot"]): errors.append("accessibility-positive-control")
    if len({tuple(sorted(counts["mutation_delta"][s].items())) for s in counts["mutation_delta"]})!=1: errors.append("mutation-negative-control")
    receipt={"schema":"blackwell-6678-t1-independent-audit-v1","errors":errors,"reconstructed_channels":reconstructed,"risks":risks,"captures_audited":len(schedule["captures"]),"disposition":"PASS_CHANNEL_RECONSTRUCTION_SCOPED" if not errors else "FAIL_AUDIT"}
    Path(audit_path).write_text(json.dumps(receipt,sort_keys=True,indent=2)+"\n")
    if errors: raise SystemExit(2)


if __name__=="__main__":
    if len(sys.argv)!=4: raise SystemExit("usage: auditor.py RAW_DIR CANDIDATE_JSON AUDIT_JSON")
    main(*sys.argv[1:])
