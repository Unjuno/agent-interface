import base64,hashlib,json,math,sys
N=128
PIX=[.005,.01,.02,.04,.08]; GROW=[1.02,1.05,1.10,1.15,1.25]; TTC=[1.5,2.,2.5,2.8,3.,4.]
def pgm(s):
 b=base64.b64decode(s,validate=True); h,p=b.split(b'\n255\n',1)
 if h!=b'P5\n128 128' or len(p)!=N*N: raise ValueError('bad_pgm')
 return b,p
def comps(p,lo,hi):
 m=bytearray(1 if lo<=x<=hi else 0 for x in p); seen=bytearray(N*N); out=[]
 for start,on in enumerate(m):
  if not on or seen[start]: continue
  st=[start];seen[start]=1; pts=[]; edge=0
  while st:
   i=st.pop();pts.append(i);x=i%N;y=i//N
   for xx,yy in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
    if not(0<=xx<N and 0<=yy<N):edge+=1;continue
    j=yy*N+xx
    if not m[j]:edge+=1
    elif not seen[j]:seen[j]=1;st.append(j)
  a=len(pts);out.append({'area':a,'cx':sum(i%N for i in pts)/a,'cy':sum(i//N for i in pts)/a,'edge':edge})
 return sorted(out,key=lambda x:x['area'],reverse=True)
def analyze(s):
 fs=s['frames']; rows=[]
 for f in fs:
  b,p=pgm(f['pgm_b64']); t=comps(p,181,255); m=comps(p,80,130)
  if not t or len(m)<4: raise ValueError('missing_target_or_markers')
  q=t[0]; cir=4*math.pi*q['area']/q['edge']**2
  rms=math.sqrt(sum((i%N-64)**2+(i//N-64)**2 for i,v in enumerate(p) if 80<=v<=130)/sum(1 for v in p if 80<=v<=130))
  rows.append({'t_s':f['t_s'],'track_id':f['track_id'],'sha256':hashlib.sha256(b).hexdigest(),'area':q['area'],'r':math.sqrt(q['area']/math.pi),'cx':q['cx'],'cy':q['cy'],'circularity':cir,'marker_rms':rms})
 first,last=pgm(fs[0]['pgm_b64'])[1],pgm(fs[-1]['pgm_b64'])[1]
 delta=sum(abs(a-b)>=32 for a,b in zip(first,last))/(N*N)
 dt=rows[-1]['t_s']-rows[-2]['t_s']; dr=rows[-1]['r']-rows[-2]['r']
 tau=rows[-1]['r']*dt/dr if dr>0 else None;growth=rows[-1]['r']/rows[0]['r'];bg=rows[-1]['marker_rms']/rows[0]['marker_rms']
 ts=[f['t_s'] for f in fs]; tracks=[f['track_id'] for f in fs]; why=None
 if any(b<=a for a,b in zip(ts,ts[1:])):why='invalid_capture_clock'
 elif max(b-a for a,b in zip(ts,ts[1:]))>.15:why='capture_gap'
 elif len(set(tracks))!=1:why='track_identity_changed'
 elif math.hypot(rows[-1]['cx']-rows[0]['cx'],rows[-1]['cy']-rows[0]['cy'])>4:why='lateral_motion'
 elif any(x['circularity']<.70 or x['circularity']>1.30 for x in rows):why='shape_or_occlusion'
 elif abs(bg-1)>.05:why='global_scale_change'
 status='UNKNOWN' if why else 'TRACKABLE'
 return {'sequence_id':s['sequence_id'],'status':status,'reason':why,'features':rows,'pixel_change_fraction':delta,'target_radius_growth_ratio':growth,'secant_ttc_s':tau,'background_scale_ratio':bg,'release_latency_s':.2,'selected_ttc_threshold_s':4.,'yield_request':bool(status=='TRACKABLE' and tau is not None and .2<tau<=4.),
 'pixel_grid':{str(x):delta>=x for x in PIX},'growth_grid':{str(x):growth>=x for x in GROW},'ttc_grid':{str(x):bool(status=='TRACKABLE' and tau is not None and .2<tau<=x) for x in TTC}}
def main(inp,out):
 d=json.load(open(inp,encoding='utf8'))
 if d.get('schema')!='looming-image-only-observations-a02-v1':raise SystemExit('STOP_SCHEMA')
 r={'schema':'looming-image-only-candidate-raw-a02-v1','frame_budget_per_sequence':5,'thresholds':{'pixel':PIX,'growth':GROW,'ttc':TTC},'sequences':[analyze(s) for s in d['sequences']]}
 with open(out,'w',encoding='utf8') as f:json.dump(r,f,sort_keys=True,separators=(',',':'));f.write('\n')
if __name__=='__main__':main(sys.argv[1],sys.argv[2])