from __future__ import annotations
import argparse,base64,json,pathlib
W=320; CONTRASTS=(255,192,128,64)
def decode(raw):
    weighted=[];total=0
    if len(raw)!=W*4:raise ValueError('scanline_bytes')
    for x in range(W):
        b,g,r,a=raw[4*x:4*x+4]
        if r>=32 and r>=4*max(g,b):weighted.append((x,r));total+=r
    if not weighted:return None,0,0
    return sum(x*r for x,r in weighted)/total,len(weighted),total
def audit(path,formal=False):
    p=json.loads(pathlib.Path(path).read_text()); errors=[]; science=[]; rows=p.get('pairs_rows',[])
    exp=800 if formal else 32
    if p.get('exception') is not None:errors.append('exception')
    if len(rows)!=exp:errors.append('row_count')
    if p.get('formal_invocation')!=(1 if formal else 0):errors.append('invocation')
    if p.get('reruns')!=0:errors.append('reruns')
    seen=set(); metrics={}
    for r in rows:
        k=(r['red'],r['direction'],r['phase'])
        if k in seen:errors.append('duplicate')
        seen.add(k)
        if r['red'] not in CONTRASTS:errors.append('contrast')
        cs=[]
        for f in r.get('frames',[]):
            raw=base64.b64decode(f['scanline_b64']); c,n,w=decode(raw)
            if c!=f['centroid_x'] or n!=f['target_pixel_count'] or w!=f['red_weight_total']:errors.append('scanline_recompute')
            if c is not None and abs((c-f['authored_root_x'])-f['point_error_px'])>1e-12:errors.append('point_error')
            cs.append(c)
        if len(cs)!=2:errors.append('frame_count');continue
        od=None if None in cs else cs[1]-cs[0]
        if od != r['observed_displacement_px']:errors.append('observed_disp')
        if od is not None:
            res=od-r['authored_displacement_px']
            if abs(res-r['displacement_residual_px'])>1e-12:errors.append('residual')
            if (((od>0)==(r['direction']>0)) != r['direction_agreement']):errors.append('direction')
    for red in CONTRASTS:
        rr=[r for r in rows if r['red']==red]; res=[abs(r['displacement_residual_px']) for r in rr if r['displacement_residual_px'] is not None]
        metrics[str(red)]={'pairs':len(rr),'missed_frames':sum(f['centroid_x'] is None for r in rr for f in r['frames']),'direction_ok':sum(bool(r['direction_agreement']) for r in rr),'max_abs_residual_px':max(res) if res else None}
        if formal:
            if len(rr)!=200: errors.append(f'arm_count_{red}')
            if metrics[str(red)]['missed_frames']!=0: science.append(f'missed_{red}')
            if metrics[str(red)]['direction_ok']!=200: science.append(f'direction_{red}')
            if metrics[str(red)]['max_abs_residual_px'] is None or metrics[str(red)]['max_abs_residual_px']>0.75+1e-12: science.append(f'residual_{red}')
    clean=p.get('summary',{}).get('cleanup',[] if formal else {})
    if formal:
        if len(clean)!=4 or any(c.get('fixture_exit')!=0 or not c.get('socket_removed') for c in clean):errors.append('cleanup')
        c255=metrics['255']['max_abs_residual_px']
        for red in (192,128,64):
            v=metrics[str(red)]['max_abs_residual_px']
            if v is not None and c255 is not None and v-c255>=0.05-1e-12: science.append(f'delta_{red}')
    else:
        if clean.get('fixture_exit')!=0 or not clean.get('socket_removed'):errors.append('cleanup')
    if errors: decision='FAIL_INTEGRITY'
    elif not formal: decision=None
    elif any(x.startswith('missed_') or x.startswith('direction_') for x in science): decision='FAIL_X11_CONTRAST_OBSERVATION'
    elif science: decision='HOLD_X11_DIRECT_BOUND_CONTRAST_SPECIFIC'
    else: decision='PASS_X11_DISPLACEMENT_CONTRAST_TRANSFER_SCOPED'
    return {'errors':sorted(set(errors)),'science_gates':science,'decision':decision,'pass':(not errors if not formal else decision=='PASS_X11_DISPLACEMENT_CONTRAST_TRANSFER_SCOPED'),'metrics':metrics,'pairs':len(rows)}
def main():
    ap=argparse.ArgumentParser();ap.add_argument('path');ap.add_argument('--formal',action='store_true');ap.add_argument('--out');a=ap.parse_args();r=audit(a.path,a.formal);s=json.dumps(r,separators=(',',':'),sort_keys=True);print(s);pathlib.Path(a.out).write_text(s) if a.out else None
if __name__=='__main__':main()
