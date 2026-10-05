import base64,hashlib,json,math,sys
N=128
PIX=[.005,.01,.02,.04,.08]; GROW=[1.02,1.05,1.10,1.15,1.25]; TTC=[1.5,2.,2.5,2.8,3.,4.]

def read_frame(f):
 b=base64.b64decode(f['pgm_b64'],validate=True); h,p=b.split(b'\n255\n',1)
 if h!=b'P5\n128 128' or len(p)!=N*N: raise ValueError('bad_pgm')
 if hashlib.sha256(b).hexdigest()!=f['sha256']: raise ValueError('input_hash_mismatch')
 return b,p

def comps(p,lo,hi):
 m=bytearray(1 if lo<=x<=hi else 0 for x in p); seen=bytearray(N*N); out=[]
 for start,on in enumerate(m):
  if not on or seen[start]: continue
  st=[start]; seen[start]=1; pts=[]; edge=0
  while st:
   i=st.pop(); pts.append(i); x=i%N; y=i//N
   for xx,yy in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
    if not(0<=xx<N and 0<=yy<N): edge+=1; continue
    j=yy*N+xx
    if not m[j]: edge+=1
    elif not seen[j]: seen[j]=1; st.append(j)
  a=len(pts); out.append({'area':a,'cx':sum(i%N for i in pts)/a,'cy':sum(i//N for i in pts)/a,'edge':edge})
 return sorted(out,key=lambda x:x['area'],reverse=True)

def analyze(s):
 fs=s['frames']; rows=[]
 for f in fs:
  b,p=read_frame(f); t=comps(p,181,255); m=comps(p,80,130)
  if not t or len(m)<4: raise ValueError('missing_target_or_markers')
  q=t[0]; cir=4*math.pi*q['area']/q['edge']**2
  count=sum(1 for v in p if 80<=v<=130)
  rms=math.sqrt(sum((i%N-64)**2+(i//N-64)**2 for i,v in enumerate(p) if 80<=v<=130)/count)
  rows.append({'t_s':f['t_s'],'track_id':f['track_id'],'sha256':hashlib.sha256(b).hexdigest(),'area':q['area'],'r':math.sqrt(q['area']/math.pi),'cx':q['cx'],'cy':q['cy'],'circularity':cir,'marker_rms':rms})
 fs_img=[read_frame(f)[1] for f in fs]; delta=sum(abs(a-b)>=32 for a,b in zip(fs_img[0],fs_img[-1]))/(N*N)
 ts=[f['t_s'] for f in fs]; tracks=[f['track_id'] for f in fs]
 dt=ts[-1]-ts[-2]; dr=rows[-1]['r']-rows[-2]['r']; tau=rows[-1]['r']*dt/dr if dr>0 else None
 growth=rows[-1]['r']/rows[0]['r']; bg=rows[-1]['marker_rms']/rows[0]['marker_rms']; drift=math.hypot(rows[-1]['cx']-rows[0]['cx'],rows[-1]['cy']-rows[0]['cy'])
 why=None
 if any(b<=a for a,b in zip(ts,ts[1:])): why='invalid_capture_clock'
 elif max(b-a for a,b in zip(ts,ts[1:]))>.15: why='capture_gap'
 elif len(set(tracks))!=1: why='track_identity_changed'
 elif drift>4: why='lateral_motion'
 elif any(x['circularity']<.70 or x['circularity']>1.30 for x in rows): why='shape_or_occlusion'
 elif abs(bg-1)>.05: why='global_scale_change'
 status='UNKNOWN' if why else 'TRACKABLE'
 common=status=='TRACKABLE'
 return {'sequence_id':s['sequence_id'],'status':status,'reason':why,'features':rows,'gate':{'valid_clock':not any(b<=a for a,b in zip(ts,ts[1:])) and max(b-a for a,b in zip(ts,ts[1:]))<=.15,'stable_track':len(set(tracks))==1,'centroid_drift_px':drift,'circularity_min':min(x['circularity'] for x in rows),'circularity_max':max(x['circularity'] for x in rows),'background_scale_ratio':bg},'metrics':{'pixel_change_fraction':delta,'target_radius_growth_ratio':growth,'secant_ttc_s':tau},'yield_latency_s':.2,
 'pixel_grid':{str(x):bool(common and delta>=x) for x in PIX},'growth_grid':{str(x):bool(common and growth>=x) for x in GROW},'ttc_grid':{str(x):bool(common and tau is not None and .2<tau<=x) for x in TTC}}

def main(inp,out):
 d=json.load(open(inp,encoding='utf8'))
 if d.get('schema')!='looming-image-only-observations-a02-v1': raise SystemExit('STOP_SCHEMA')
 rows=[analyze(s) for s in d['sequences']]
 raw={'schema':'looming-image-only-candidate-raw-a03-v1','frame_budget_per_sequence':5,'thresholds':{'pixel':PIX,'growth':GROW,'ttc':TTC},'sequences':rows}
 with open(out,'w',encoding='utf8',newline='\n') as f: json.dump(raw,f,sort_keys=True,separators=(',',':')); f.write('\n')
if __name__=='__main__': main(sys.argv[1],sys.argv[2])
