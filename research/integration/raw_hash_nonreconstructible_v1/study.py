from __future__ import annotations
import hashlib, json, sys
from pathlib import Path
from vendor_capture_artifacts import CaptureArtifacts
from png_stdlib import decode_rgb8_png

CASES=[
 ('BGRX_BASE',0,bytes([0x11,0x22,0x33,0x00])),
 ('BGRX_X_CHANGED',0,bytes([0x11,0x22,0x33,0xff])),
 ('BGRX_VISIBLE_CHANGED',0,bytes([0x11,0x22,0x44,0x00])),
 ('XRGB_BASE',1,bytes([0x00,0x33,0x22,0x11])),
 ('XRGB_X_CHANGED',1,bytes([0xff,0x33,0x22,0x11])),
 ('XRGB_VISIBLE_CHANGED',1,bytes([0x00,0x44,0x22,0x11])),
]

def main(root: str):
    out=Path(root); out.mkdir(parents=True,exist_ok=False)
    rows=[]
    for name,order,raw in CASES:
        d=out/name; art=CaptureArtifacts(d).write(raw,1,1,depth=24,bits_per_pixel=32,scanline_pad=32,byte_order=order,masks=(0xff0000,0x00ff00,0x0000ff),true_color=True)
        png=Path(art['path']).read_bytes(); dec=decode_rgb8_png(png)
        row={'case':name,'byte_order':order,'raw_hex':raw.hex(),'raw_sha256':hashlib.sha256(raw).hexdigest(),'artifact':art,
             'png_sha256':hashlib.sha256(png).hexdigest(),'png_hex':png.hex(),'decoded_rgb_hex':dec['rgb'].hex(),'decoded_width':dec['width'],'decoded_height':dec['height']}
        rows.append(row)
    (out/'RAW.json').write_text(json.dumps(rows,sort_keys=True,indent=2)+'\n')
    return 0
if __name__=='__main__': raise SystemExit(main(sys.argv[1]))
