from __future__ import annotations
import argparse, base64, json, math, pathlib

W=320
def decode(raw):
    if len(raw)!=W*4: raise ValueError('scanline_bytes')
    xs=[]
    for x in range(W):
        b,g,r,a=raw[4*x:4*x+4]
        if r>=200 and g<=32 and b<=32: xs.append(x)
    return (sum(xs)/len(xs),len(xs)) if xs else (None,0)
def p99(vals):
    s=sorted(vals); return s[max(0,min(len(s)-1,math.ceil(.99*len(s))-1))]
def audit(path,formal=True):
    p=json.loads(pathlib.Path(path).read_text())
    errors=[]; science=[]; rows=p.get('pairs_rows',[])
    exp_pairs=400 if formal else 4
    if p.get('exception') is not None: errors.append('exception')
    if len(rows)!=exp_pairs: errors.append('row_count')
    if p.get('formal_invocation')!=(1 if formal else 0): errors.append('invocation')
    if p.get('reruns')!=0: errors.append('reruns')
    points=[]; residuals=[]; missed=0; dirs=0
    for pr in rows:
        if pr['direction'] not in (-1,1): errors.append('direction')
        fs=pr.get('frames',[])
        if len(fs)!=2: errors.append('frame_count'); continue
        recom=[]
        for f in fs:
            raw=base64.b64decode(f['scanline_b64']); c,n=decode(raw)
            if n!=f['red_count'] or c!=f['centroid_x']: errors.append('scanline_recompute')
            if c is None: missed+=1
            else:
                pe=c-f['authored_root_x']
                if abs(pe-f['point_error_px'])>1e-12: errors.append('point_error')
                points.append(abs(pe))
            recom.append(c)
        od=None if None in recom else recom[1]-recom[0]
        if od is not None:
            rr=od-pr['authored_displacement_px']
            if abs(rr-pr['displacement_residual_px'])>1e-12: errors.append('residual')
            residuals.append(abs(rr)); da=((od>0)==(pr['direction']>0))
            if da!=pr['direction_agreement']: errors.append('direction_flag')
            dirs+=int(da)
    if missed: science.append('missed_red')
    if formal:
        if len(rows)==400 and dirs!=400: science.append('direction')
        if points and max(points)>.75+1e-12: science.append('point_max')
        if points and p99(points)>.75+1e-12: science.append('point_p99')
        if residuals and max(residuals)>1.50+1e-12: science.append('residual_max')
        clean=p.get('summary',{}).get('cleanup',[])
        if len(clean)!=4 or not all(c.get('socket_removed') for c in clean): errors.append('cleanup')
    decision='FAIL_INTEGRITY' if errors else ('FAIL_X11_LOCALIZATION_OBSERVATION' if ('missed_red' in science or 'direction' in science) else ('HOLD_X11_LOCALIZATION_BOUND_WIDER' if science else ('PASS_X11_CENTROID_LOCALIZATION_ENVELOPE_SCOPED' if formal else None)))
    return {'decision':decision,'pass':decision=='PASS_X11_CENTROID_LOCALIZATION_ENVELOPE_SCOPED','errors':sorted(set(errors)),'science_gates':science,'pairs':len(rows),'frames':sum(len(r.get('frames',[])) for r in rows),'missed':missed,'directions_ok':dirs,'max_abs_point_error_px':max(points) if points else None,'p99_abs_point_error_px':p99(points) if points else None,'max_abs_displacement_residual_px':max(residuals) if residuals else None}
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('path'); ap.add_argument('--construction',action='store_true'); ap.add_argument('--out')
    a=ap.parse_args(); r=audit(a.path,not a.construction); s=json.dumps(r,separators=(',',':'),sort_keys=True)
    if a.out: pathlib.Path(a.out).write_text(s)
    print(s)
if __name__=='__main__':main()
