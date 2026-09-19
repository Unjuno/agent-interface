from pathlib import Path
import base64, hashlib, json, math, statistics, struct
HERE=Path(__file__).resolve().parent
EXPECTED='d5de4ba8137264fc1f7f444825dac94327722e7e9decc9284fd868847f8658b6'
D=7.3; W=320; SCAN_Y=100
b=memoryview(base64.b64decode((HERE/'MINPACK.b64').read_bytes()))
pos=0
assert bytes(b[:5])==b'X11C1'; pos=5
first=struct.unpack_from('<Q',b,pos)[0]; pos+=8

def getv():
    global pos
    n=0; sh=0
    while True:
        v=b[pos]; pos+=1
        n |= (v&127)<<sh
        if not (v&128): return n
        sh += 7
starts=[first]
for _ in range(799): starts.append(starts[-1]+getv())
durs=[getv() for _ in range(800)]
redstarts=[]
for _ in range(800):
    redstarts.append(struct.unpack_from('<H',b,pos)[0]); pos+=2
assert pos==len(b)
fi=0; rows=[]; clean=[]
for sid,(direction,display) in enumerate([(1,':221'),(-1,':222'),(1,':223'),(-1,':224')]):
    for i in range(100):
        phase=i/100
        x0=100.0+phase; x1=x0+direction*D
        pair=[]
        for label,x in [('x0',x0),('x1',x1)]:
            st=redstarts[fi]
            raw=bytearray(W*4)
            for px in range(st,st+12): raw[4*px:4*px+4]=b'\x00\x00\xff\x00'
            centroid=st+5.5
            t0=starts[fi]; dur=durs[fi]; t1=t0+dur
            fr={'session_id':sid,'display':display,'direction':direction,'phase':phase,'label':label,'authored_local_x':x,'fixture_rootx':0,'fixture_rooty':0,'authored_root_x':x,'scan_y':SCAN_Y,'scanline_b64':base64.b64encode(raw).decode('ascii'),'scanline_bytes':len(raw),'red_count':12,'centroid_x':centroid,'point_error_px':centroid-x,'capture_start_ns':t0,'capture_end_ns':t1,'capture_duration_ns':dur}
            pair.append(fr); fi+=1
        od=pair[1]['centroid_x']-pair[0]['centroid_x']
        rows.append({'session_id':sid,'display':display,'direction':direction,'phase':phase,'authored_displacement_px':direction*D,'observed_displacement_px':od,'displacement_residual_px':od-direction*D,'direction_agreement':((od>0)==(direction>0)),'frames':pair})
    clean.append({'fixture_exit':0,'socket_removed':True,'xvfb_exit':0})
frames=[f for r in rows for f in r['frames']]
points=[abs(f['point_error_px']) for f in frames]
res=[abs(r['displacement_residual_px']) for r in rows]
def pn(vals,p):
    s=sorted(vals); k=max(0,min(len(s)-1,math.ceil(p*len(s))-1)); return s[k]
summary={'task':'TEMPORAL-X11-CENTROID-LOCALIZATION-A2-20260918-009','formal_invocation':1,'reruns':0,'pairs':len(rows),'frames':len(frames),'missed_red':0,'direction_agreement_count':sum(r['direction_agreement'] for r in rows),'max_abs_point_error_px':max(points),'p99_abs_point_error_px':pn(points,.99),'max_abs_displacement_residual_px':max(res),'capture_duration_ns_median':statistics.median([f['capture_duration_ns'] for f in frames]),'cleanup':clean}
p={'task':'TEMPORAL-X11-CENTROID-LOCALIZATION-A2-20260918-009','mode':'formal','formal_invocation':1,'reruns':0,'exception':None,'pairs_rows':rows,'summary':summary}
out=HERE/'FORMAL_RESULT.reconstructed.json'
out.write_text(json.dumps(p,separators=(',',':'),sort_keys=True),encoding='utf-8')
got=hashlib.sha256(out.read_bytes()).hexdigest()
assert got==EXPECTED,(got,EXPECTED)
print(got)
