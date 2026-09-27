from __future__ import annotations
import hashlib,json,sys
from pathlib import Path
from png_stdlib import decode_rgb8_png
EXPECTED={
 'BGRX_BASE':0,'BGRX_X_CHANGED':0,'BGRX_VISIBLE_CHANGED':0,
 'XRGB_BASE':1,'XRGB_X_CHANGED':1,'XRGB_VISIBLE_CHANGED':1,
}
def audit(root):
    rows=json.loads((Path(root)/'RAW.json').read_text()); errors=[]; checks=0
    if not isinstance(rows,list) or len(rows)!=6: return {'status':'FAIL','checks':1,'errors':[['global','row_count']]}
    names=[r.get('case') for r in rows if isinstance(r,dict)]
    if sorted(names)!=sorted(EXPECTED): errors.append(['global','case_set'])
    by={r.get('case'):r for r in rows if isinstance(r,dict)}
    for name,order in EXPECTED.items():
        r=by.get(name); checks+=12
        if not isinstance(r,dict): errors.append([name,'missing']); continue
        if type(r.get('byte_order')) is not int or r['byte_order']!=order: errors.append([name,'byte_order'])
        try: raw=bytes.fromhex(r['raw_hex']); png=bytes.fromhex(r['png_hex']); dec=decode_rgb8_png(png)
        except Exception: errors.append([name,'decode_input']); continue
        if len(raw)!=4: errors.append([name,'raw_extent'])
        if hashlib.sha256(raw).hexdigest()!=r.get('raw_sha256'): errors.append([name,'raw_sha'])
        art=r.get('artifact')
        if not isinstance(art,dict): errors.append([name,'artifact']); continue
        if art.get('source_raw_sha256')!=r.get('raw_sha256'): errors.append([name,'source_raw'])
        if hashlib.sha256(png).hexdigest()!=r.get('png_sha256') or art.get('sha256')!=r.get('png_sha256'): errors.append([name,'png_sha'])
        if art.get('width')!=1 or art.get('height')!=1 or art.get('bytes')!=len(png) or art.get('mime_type')!='image/png': errors.append([name,'artifact_geometry'])
        if dec['rgb'].hex()!=r.get('decoded_rgb_hex') or dec['width']!=r.get('decoded_width') or dec['height']!=r.get('decoded_height') or (dec['width'],dec['height'])!=(1,1): errors.append([name,'decode_claim'])
    if all(k in by for k in EXPECTED):
        for prefix in ('BGRX','XRGB'):
            a=by[prefix+'_BASE']; x=by[prefix+'_X_CHANGED']; v=by[prefix+'_VISIBLE_CHANGED']; checks+=8
            if a['raw_sha256']==x['raw_sha256']: errors.append([prefix,'x_raw_not_distinct'])
            if a['png_hex']!=x['png_hex'] or a['png_sha256']!=x['png_sha256'] or a['decoded_rgb_hex']!=x['decoded_rgb_hex']: errors.append([prefix,'x_not_erased'])
            if a['decoded_rgb_hex']==v['decoded_rgb_hex'] or a['png_sha256']==v['png_sha256']: errors.append([prefix,'visible_not_changed'])
    return {'status':'PASS' if not errors else 'FAIL','checks':checks,'errors':errors}
if __name__=='__main__':
    out=audit(sys.argv[1]); print(json.dumps(out,sort_keys=True)); raise SystemExit(0 if not out['errors'] else 1)
