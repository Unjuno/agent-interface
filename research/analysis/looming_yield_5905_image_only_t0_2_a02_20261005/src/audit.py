import base64,hashlib,json,math,sys
N=128
def read(s):
 b=base64.b64decode(s,validate=True); h,p=b.split(b'\n255\n',1)
 if h!=b'P5\n128 128' or len(p)!=N*N:raise ValueError('format')
 return b,p
def measure(seq):
 fs=seq['frames']; imgs=[read(f['pgm_b64'])[1] for f in fs]; targ=[];marks=[]
 for p in imgs:
  ts=[i for i,v in enumerate(p) if v>180]; ms=[i for i,v in enumerate(p) if 80<=v<=130]
  if not ts or not ms:raise ValueError('missing')
  targ.append((len(ts),sum(i%N for i in ts)/len(ts),sum(i//N for i in ts)/len(ts)))
  marks.append(math.sqrt(sum((i%N-64)**2+(i//N-64)**2 for i in ms)/len(ms)))
 rad=[math.sqrt(x[0]/math.pi) for x in targ];dt=fs[-1]['t_s']-fs[-2]['t_s']
 return {'pixel':sum(abs(a-b)>=32 for a,b in zip(imgs[0],imgs[-1]))/(N*N),'growth':rad[-1]/rad[0],'tau':rad[-1]*dt/(rad[-1]-rad[-2]) if rad[-1]>rad[-2] else None,'bg':marks[-1]/marks[0],'drift':math.hypot(targ[-1][1]-targ[0][1],targ[-1][2]-targ[0][2])}
def audit(obs,truth,raw):
 e=[]; ss={x['sequence_id']:x for x in obs['sequences']}; rr={x['sequence_id']:x for x in raw['sequences']}
 if len(ss)!=13 or set(ss)!=set(rr):e.append('sequence_set')
 for sid,s in ss.items():
  r=rr.get(sid,{})
  if len(s['frames'])!=5 or len(r.get('features',[]))!=5:e.append('frame_count:'+sid);continue
  for f,g in zip(s['frames'],r['features']):
   try:
    b,_=read(f['pgm_b64'])
    if hashlib.sha256(b).hexdigest()!=f['sha256'] or f['sha256']!=g['sha256']:e.append('hash:'+sid)
    if (f['t_s'],f['track_id'])!=(g['t_s'],g['track_id']):e.append('binding:'+sid)
   except Exception:e.append('decode:'+sid)
  m=measure(s)
  for k,rk in [('pixel','pixel_change_fraction'),('growth','target_radius_growth_ratio'),('tau','secant_ttc_s'),('bg','background_scale_ratio')]:
   if m[k] is None:
    if r.get(rk) is not None:e.append('none:'+sid+':'+k)
   elif not isinstance(r.get(rk),(int,float)) or not math.isclose(m[k],r[rk],rel_tol=1e-8,abs_tol=1e-8):e.append('metric:'+sid+':'+k)
 a=ss['approach-1'];b=ss['animation-twin-1']
 if [(x['t_s'],x['track_id'],x['pgm_b64']) for x in a['frames']]!=[(x['t_s'],x['track_id'],x['pgm_b64']) for x in b['frames']]:e.append('twin_not_identical')
 elif rr['approach-1']['yield_request']!=rr['animation-twin-1']['yield_request']:e.append('twin_action_mismatch')
 expected={'camera-zoom-1':'global_scale_change','lateral-1':'lateral_motion','occlusion-1':'shape_or_occlusion','track-swap-1':'track_identity_changed','timestamp-regression-1':'invalid_capture_clock'}
 for sid,why in expected.items():
  if rr[sid]['status']!='UNKNOWN' or rr[sid]['reason']!=why or rr[sid]['yield_request']:e.append('abstention:'+sid)
 pos=set(truth['contact_cases']);neg=set(truth['control_labels']); curves={}
 for method in ('pixel','growth','ttc'):
  grid=next(iter(rr.values()))[method+'_grid']; points=[]
  for th in grid:
   tp=sum(bool(rr[s][method+'_grid'][th]) for s in pos);fp=sum(bool(rr[s][method+'_grid'][th]) for s in neg)
   points.append({'threshold':th,'tp':tp,'fp':fp})
  curves[method]={'points':points,'max_tp_at_fp_le_1':max([p['tp'] for p in points if p['fp']<=1] or [0])}
 outcomes={}
 for sid in pos:
  r=rr[sid]; lead=truth['contact_cases'][sid]['contact_at_s']-(r['features'][-1]['t_s']+r['release_latency_s'])
  outcomes[sid]={'request':r['yield_request'],'release_lead_s':lead,'estimated_ttc_s':r['secant_ttc_s']}
  if not r['yield_request'] or lead<=0:e.append('late_or_missing:'+sid)
 false=sorted(s for s in neg if rr[s]['yield_request'])
 if false!=['animation-twin-1']:e.append('false_yields:'+','.join(false))
 if curves['ttc']['max_tp_at_fp_le_1']<=max(curves['pixel']['max_tp_at_fp_le_1'],curves['growth']['max_tp_at_fp_le_1']):e.append('no_increment')
 return {'audit':'PASS_RAW_RECONSTRUCTION' if not e else 'FAIL_RAW_RECONSTRUCTION','errors':e,'selected_approaches':outcomes,'false_yield_controls':false,'false_yield_allowance':1,'frontier':curves,'identical_world_witness':True,'disposition':'PASS_METHOD_SCOPED_WITH_IDENTIFIABILITY_LIMIT' if not e else 'FAIL_OR_STOP'}
if __name__=='__main__':
 obs=json.load(open(sys.argv[1],encoding='utf8'));truth=json.load(open(sys.argv[2],encoding='utf8'));raw=json.load(open(sys.argv[3],encoding='utf8'));r=audit(obs,truth,raw)
 json.dump(r,open(sys.argv[4],'w',encoding='utf8'),sort_keys=True,indent=2)
 print(json.dumps({'audit':r['audit'],'errors':r['errors'],'disposition':r['disposition']}));sys.exit(0 if not r['errors'] else 1)