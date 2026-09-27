from __future__ import annotations
import hashlib,json,sys
from pathlib import Path
from png_stdlib import decode_rgb8_png

def audit(root):
    rows=json.loads((Path(root)/'RAW.json').read_text()); by={r['case']:r for r in rows}; errors=[]; checks=0
    for r in rows:
        raw=bytes.fromhex(r['raw_hex']); png=bytes.fromhex(r['png_hex']); dec=decode_rgb8_png(png); checks+=7
        if hashlib.sha256(raw).hexdigest()!=r['raw_sha256']: errors.append([r['case'],'raw_sha'])
        if r['artifact']['source_raw_sha256']!=r['raw_sha256']: errors.append([r['case'],'source_raw'])
        if hashlib.sha256(png).hexdigest()!=r['png_sha256'] or r['artifact']['sha256']!=r['png_sha256']: errors.append([r['case'],'png_sha'])
        if dec['rgb'].hex()!=r['decoded_rgb_hex'] or (dec['width'],dec['height'])!=(1,1): errors.append([r['case'],'decode'])
    for prefix in ('BGRX','XRGB'):
        a=by[prefix+'_BASE']; x=by[prefix+'_X_CHANGED']; v=by[prefix+'_VISIBLE_CHANGED']; checks+=8
        if a['raw_sha256']==x['raw_sha256']: errors.append([prefix,'x_raw_not_distinct'])
        if a['png_hex']!=x['png_hex'] or a['png_sha256']!=x['png_sha256'] or a['decoded_rgb_hex']!=x['decoded_rgb_hex']: errors.append([prefix,'x_not_erased'])
        if a['decoded_rgb_hex']==v['decoded_rgb_hex'] or a['png_sha256']==v['png_sha256']: errors.append([prefix,'visible_not_changed'])
    return {'status':'PASS' if not errors else 'FAIL','checks':checks,'errors':errors}
if __name__=='__main__':
    out=audit(sys.argv[1]); print(json.dumps(out,sort_keys=True)); raise SystemExit(0 if not out['errors'] else 1)
