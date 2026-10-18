import base64,gzip,hashlib,json,math,sys
N=128
PIX=[.003,.004,.005,.006,.008,.01]
GROW=[1.03,1.05,1.08,1.10,1.12,1.15]
TTC=[1.5,2.0,2.5,3.0,3.5,4.0]

def decode(frame):
    raw=base64.b64decode(frame['pgm_b64'],validate=True)
    header,pixels=raw.split(b'\n255\n',1)
    if header!=b'P5\n128 128' or len(pixels)!=N*N:raise ValueError('bad_pgm')
    if hashlib.sha256(raw).hexdigest()!=frame['sha256']:raise ValueError('frame_hash')
    return raw,pixels

def components(pixels,low,high):
    mask=bytearray(low<=v<=high for v in pixels);seen=bytearray(N*N);out=[]
    for start in range(N*N):
        if not mask[start] or seen[start]:continue
        seen[start]=1;stack=[start];pts=[];edge=0; xmin=ymin=N;xmax=ymax=-1
        while stack:
            i=stack.pop();x=i%N;y=i//N;pts.append(i);xmin=min(xmin,x);xmax=max(xmax,x);ymin=min(ymin,y);ymax=max(ymax,y)
            for nx,ny in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
                if nx<0 or nx>=N or ny<0 or ny>=N:edge+=1;continue
                j=ny*N+nx
                if not mask[j]:edge+=1
                elif not seen[j]:seen[j]=1;stack.append(j)
        area=len(pts);w=xmax-xmin+1;h=ymax-ymin+1
        out.append({'area':area,'cx':sum(i%N for i in pts)/area,'cy':sum(i//N for i in pts)/area,'width':w,'height':h,'fill':area/(w*h),'edge4':edge})
    return sorted(out,key=lambda c:c['area'],reverse=True)

def analyze(sequence):
    rows=[];images=[]
    for f in sequence['frames']:
        raw,pixels=decode(f);images.append(pixels)
        targets=components(pixels,181,255);markers=components(pixels,80,130)
        if not targets or len(markers)<4:raise ValueError('missing_target_or_markers')
        q=targets[0]
        marker_points=[i for i,v in enumerate(pixels) if 80<=v<=130]
        marker_rms=math.sqrt(sum((i%N-64)**2+(i//N-64)**2 for i in marker_points)/len(marker_points))
        rows.append({'t_s':f['t_s'],'track_id':f['track_id'],'sha256':hashlib.sha256(raw).hexdigest(),'area':q['area'],'r':math.sqrt(q['area']/math.pi),'cx':q['cx'],'cy':q['cy'],'fill':q['fill'],'bbox':[q['width'],q['height']],'marker_rms':marker_rms})
    times=[f['t_s'] for f in sequence['frames']];tracks=[f['track_id'] for f in sequence['frames']]
    deltas=[b-a for a,b in zip(times,times[1:])]
    clock_ok=all(d>0 and d<=.15 for d in deltas)
    drift=math.hypot(rows[-1]['cx']-rows[0]['cx'],rows[-1]['cy']-rows[0]['cy'])
    scale=rows[-1]['marker_rms']/rows[0]['marker_rms']
    reason=None
    if not clock_ok:reason='invalid_capture_clock'
    elif len(set(tracks))!=1:reason='track_identity_changed'
    elif drift>4:reason='lateral_motion'
    elif min(r['fill'] for r in rows)<.64:reason='shape_or_occlusion'
    elif abs(scale-1)>.05:reason='global_scale_change'
    status='TRACKABLE' if reason is None else 'UNKNOWN';eligible=status=='TRACKABLE'
    changed=sum(abs(a-b)>=32 for a,b in zip(images[0],images[-1]))/(N*N)
    growth=rows[-1]['r']/rows[0]['r'];dt=times[-1]-times[-2];dr=rows[-1]['r']-rows[-2]['r'];tau=rows[-1]['r']*dt/dr if dr>0 else None
    grids={'pixel':{str(v):bool(eligible and changed>=v) for v in PIX},'growth':{str(v):bool(eligible and growth>=v) for v in GROW},'ttc':{str(v):bool(eligible and tau is not None and .2<tau<=v) for v in TTC}}
    return {'sequence_id':sequence['sequence_id'],'status':status,'reason':reason,'features':rows,'gate':{'clock_ok':clock_ok,'stable_track':len(set(tracks))==1,'centroid_drift_px':drift,'min_target_fill':min(r['fill'] for r in rows),'background_scale_ratio':scale},'metrics':{'pixel_change_fraction':changed,'target_radius_growth_ratio':growth,'secant_ttc_s':tau},'grids':grids,'selected_ttc_threshold_s':4.0,'simulated_release_latency_s':.20,'yield_request':grids['ttc']['4.0']}

def main(path,out):
    with gzip.open(path,'rt',encoding='utf8') as f:data=json.load(f)
    if data.get('schema')!='looming-image-only-observations-a04-v1':raise SystemExit('STOP_SCHEMA')
    raw={'schema':'looming-image-only-raw-a04-v1','thresholds':{'pixel':PIX,'growth':GROW,'ttc':TTC},'frame_budget':5,'sequences':[analyze(s) for s in data['sequences']]}
    with open(out,'w',encoding='utf8',newline='\n') as f:json.dump(raw,f,sort_keys=True,separators=(',',':'));f.write('\n')
if __name__=='__main__':main(sys.argv[1],sys.argv[2])
