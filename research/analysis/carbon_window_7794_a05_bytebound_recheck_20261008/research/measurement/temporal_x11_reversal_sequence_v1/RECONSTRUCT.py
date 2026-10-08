from pathlib import Path
import base64,gzip,hashlib,json,math,statistics,struct
HERE=Path(__file__).resolve().parent
EXPECTED='e01d51bf2f176fec34e3a0099c99115c8b7808f2a78e0957c955ac1db94ee7e3'
W=320; SCAN_Y=100; BASE_X=160.0; STEP=7.3; BOUND=2.0; UNKNOWN=0
b=memoryview(gzip.decompress(base64.b64decode((HERE/'MINPACK.b64').read_bytes())))
pos=0; assert bytes(b[:5])==b'X11R1'; pos=5
first=struct.unpack_from('<Q',b,pos)[0]; pos+=8
def getv():
    global pos
    n=0; sh=0
    while True:
        v=b[pos]; pos+=1; n|=(v&127)<<sh
        if not (v&128): return n
        sh+=7
starts=[first]
for _ in range(3599): starts.append(starts[-1]+getv())
durs=[getv() for _ in range(3600)]
red=[int(b[pos+i]) for i in range(3600)]; pos+=3600; assert pos==len(b)
def ax(t,age,post):
    r=-age*1000; pre=-post
    return BASE_X + (pre if t<=r else post)*STEP*((t-r)/100000.0)
def times(phase):
    n=-int(round(phase*1000)); return n,n-100000,n-200000
def fs(d,mode):
    if mode=='STRICT_EXACT':
        if d==STEP:return 1
        if d==-STEP:return -1
        return None
    p=abs(d-STEP)<=BOUND; m=abs(d+STEP)<=BOUND
    if p==m:return None
    return 1 if p else -1
def est(n,p,o,mode):
    sn=fs(n-p,mode); sp=fs(p-o,mode)
    if sn is not None:
        if sp==sn:return UNKNOWN
        return sn
    if sp is not None:return -sp
    return UNKNOWN
rows=[]; fi=0; clean=[]
for sid,(disp,phases) in enumerate([(':231',range(0,25)),(':232',range(25,50)),(':233',range(50,75)),(':234',range(75,100))]):
    for age in (25,50,75,100,150,200):
        for post in (-1,1):
            for phase in phases:
                nt,pt,ot=times(phase); fr=[]; cent=[]
                for ordinal,t in enumerate((ot,pt,nt)):
                    x=ax(t,age,post); st=red[fi]; raw=bytearray(W*4)
                    for px in range(st,st+12):raw[4*px:4*px+4]=b'\x00\x00\xff\x00'
                    c=st+5.5; t0=starts[fi]; dur=durs[fi]; t1=t0+dur
                    fr.append({'ordinal_oldest_to_newest':ordinal,'sample_time_us':t,'authored_root_x':x,'centroid_x':c,'point_error_px':c-x,'red_count':12,'scanline_b64':base64.b64encode(raw).decode('ascii'),'capture_start_ns':t0,'capture_end_ns':t1,'capture_duration_ns':dur}); cent.append(c); fi+=1
                strict=est(cent[2],cent[1],cent[0],'STRICT_EXACT'); cand=est(cent[2],cent[1],cent[0],'X11_BOUND_1PX')
                rows.append({'session_id':sid,'display':disp,'age_ms':age,'post_dir':post,'phase_ms':phase,'sample_times_us_newest_prev_older':[nt,pt,ot],'d_prev_px':cent[1]-cent[0],'d_new_px':cent[2]-cent[1],'oracle':post,'strict_prediction':strict,'candidate_prediction':cand,'strict_correct':strict==post,'candidate_correct':cand==post,'strict_unknown':strict==UNKNOWN,'candidate_unknown':cand==UNKNOWN,'candidate_wrong':cand not in (UNKNOWN,post),'frames':fr})
    clean.append({'fixture_exit':0,'socket_removed':True,'xvfb_exit':0})
frames=[f for r in rows for f in r['frames']]
by={}
for age in (25,50,75,100,150,200):
    rr=[r for r in rows if r['age_ms']==age]; n=len(rr); by[str(age)]={'n':n,'strict_accuracy':sum(r['strict_correct'] for r in rr)/n,'candidate_accuracy':sum(r['candidate_correct'] for r in rr)/n,'candidate_unknown_rate':sum(r['candidate_unknown'] for r in rr)/n,'candidate_wrong_rate':sum(r['candidate_wrong'] for r in rr)/n}
pe=[abs(f['point_error_px']) for f in frames]
summary={'task':'TEMPORAL-X11-REVERSAL-SEQUENCE-R1-20260918-010','formal_invocation':1,'reruns':0,'trajectories':len(rows),'frames':len(frames),'missed_red':0,'point_envelope_violations':sum(abs(f['point_error_px'])>1.0+1e-12 for f in frames),'max_abs_point_error_px':max(pe),'by_age':by,'cleanup':clean,'capture_duration_ns_median':statistics.median([f['capture_duration_ns'] for f in frames])}
p={'task':'TEMPORAL-X11-REVERSAL-SEQUENCE-R1-20260918-010','mode':'formal','formal_invocation':1,'reruns':0,'exception':None,'trajectory_rows':rows,'summary':summary}
out=HERE/'FORMAL_RESULT.reconstructed.json'; out.write_text(json.dumps(p,separators=(',',':'),sort_keys=True),encoding='utf-8'); got=hashlib.sha256(out.read_bytes()).hexdigest(); assert got==EXPECTED,(got,EXPECTED); print(got)
