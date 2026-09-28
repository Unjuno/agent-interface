import binascii, hashlib, json, os, struct, tempfile, time, zlib
from pathlib import Path
from lattice import decide_cached, decide_active

WIDTH=32
HEIGHT=32

def ns():
    return time.monotonic_ns()

def atomic_json(path, obj):
    path=Path(path)
    tmp=path.with_suffix(path.suffix+'.tmp')
    tmp.write_text(json.dumps(obj,sort_keys=True,separators=(',',':'))+'\n',encoding='utf-8')
    os.replace(tmp,path)

def read_source(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))

def write_source(path, version, seed):
    atomic_json(path, {'version':int(version),'seed':int(seed),'width':WIDTH,'height':HEIGHT})

def pixels_for(state):
    v=int(state['version']); s=int(state['seed'])
    out=bytearray()
    for y in range(HEIGHT):
        for x in range(WIDTH):
            out.extend(((x*7+y*3+s+v)%256,(x*5+y*11+s*3+v*13)%256,(x*17+y+s*5+v*19)%256))
    return bytes(out)

def chunk(t,d):
    return struct.pack('>I',len(d))+t+d+struct.pack('>I',binascii.crc32(t+d)&0xffffffff)

def encode_png(rgb):
    rows=b''.join(b'\x00'+rgb[y*WIDTH*3:(y+1)*WIDTH*3] for y in range(HEIGHT))
    return b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',WIDTH,HEIGHT,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(rows,6))+chunk(b'IEND',b'')

def decode_png(png):
    if png[:8]!=b'\x89PNG\r\n\x1a\n': raise ValueError('bad png signature')
    pos=8; idat=[]; wh=None
    while pos<len(png):
        n=struct.unpack('>I',png[pos:pos+4])[0]; typ=png[pos+4:pos+8]; data=png[pos+8:pos+8+n]; crc=png[pos+8+n:pos+12+n]
        if struct.unpack('>I',crc)[0] != (binascii.crc32(typ+data)&0xffffffff): raise ValueError('bad crc')
        pos += 12+n
        if typ==b'IHDR':
            w,h,bd,ct,cm,fm,im=struct.unpack('>IIBBBBB',data); wh=(w,h,bd,ct,cm,fm,im)
        elif typ==b'IDAT': idat.append(data)
        elif typ==b'IEND': break
    if wh!=(WIDTH,HEIGHT,8,2,0,0,0): raise ValueError('bad ihdr')
    raw=zlib.decompress(b''.join(idat)); stride=WIDTH*3+1
    if len(raw)!=HEIGHT*stride: raise ValueError('bad raster length')
    rows=[]
    for y in range(HEIGHT):
        row=raw[y*stride:(y+1)*stride]
        if row[0]!=0: raise ValueError('unsupported filter')
        rows.append(row[1:])
    return b''.join(rows)

def capture(source_path, out_png, mutate_during=False):
    t0=ns(); before=read_source(source_path); rgb=pixels_for(before)
    if mutate_during:
        write_source(source_path,before['version']+1,before['seed'])
    png=encode_png(rgb); Path(out_png).write_bytes(png); after=read_source(source_path); t1=ns()
    return {
        'capture_start_ns':t0,'capture_end_ns':t1,
        'source_version_before':before['version'],'source_version_after':after['version'],
        'source_seed':before['seed'],'png_sha256':hashlib.sha256(png).hexdigest(),
        'rgb_sha256':hashlib.sha256(rgb).hexdigest(),'png_bytes':len(png)
    }

def compute_once(png_path, sleep_ns=0, partial_callback=None):
    png=Path(png_path).read_bytes(); rgb=decode_png(png); t0=ns()
    half=len(rgb)//2
    a=sum(rgb[:half]); partial_ns=ns()
    if partial_callback: partial_callback(partial_ns,a)
    if sleep_ns>0: time.sleep(sleep_ns/1e9)
    b=sum(rgb[half:]); t1=ns()
    return {'compute_start_ns':t0,'partial_ns':partial_ns,'compute_end_ns':t1,'partial_value':a,'value':a+b,'rgb_sha256':hashlib.sha256(rgb).hexdigest()}

def measure_compute(png_path, sleep_ns=0, reps=3):
    vals=[]
    for _ in range(reps):
        r=compute_once(png_path,sleep_ns=sleep_ns); vals.append(r['compute_end_ns']-r['compute_start_ns'])
    vals.sort()
    return {'samples_ns':vals,'median_ns':vals[len(vals)//2]}

def measure_wait(wait_ns, reps=3):
    vals=[]
    for _ in range(reps):
        t0=ns(); time.sleep(wait_ns/1e9); vals.append(ns()-t0)
    vals.sort(); return {'samples_ns':vals,'median_ns':vals[len(vals)//2]}

def calibrate_profile(profile,png_path,source_path):
    # p is measured from explicit source-version probes, not inserted as a scalar.
    if profile=='run': pattern=[0,0,0,1]; wait_target=4_000_000; compute_sleep=0
    elif profile=='wait': pattern=[1,1,1,0]; wait_target=200_000; compute_sleep=4_000_000
    elif profile=='tie': pattern=[0,1,0,1]; wait_target=0; compute_sleep=0
    else: raise ValueError(profile)
    initial=read_source(source_path); base=initial['version']; outcomes=[]
    for changed in pattern:
        write_source(source_path,base+changed,initial['seed']); outcomes.append(int(read_source(source_path)['version']!=base))
        write_source(source_path,base,initial['seed'])
    p_num=sum(outcomes); p_den=len(outcomes)
    if profile=='tie':
        shared=measure_compute(png_path,0,3)
        g=shared['median_ns']; w=shared['median_ns']; wait={'samples_ns':[g],'median_ns':g}; comp=shared
    else:
        wait=measure_wait(wait_target,3); comp=measure_compute(png_path,compute_sleep,3); g=wait['median_ns']; w=comp['median_ns']
    return {'profile':profile,'probe_invalidations':outcomes,'p_num':p_num,'p_den':p_den,'wait_measure':wait,'compute_measure':comp,'g_ns':g,'w_ns':w}

def active_decision(name, source_versions,current_versions,t_ns,remaining,deadline,cal,stage):
    d=decide_active(source_versions,current_versions,t_ns,remaining,deadline,cal['p_num'],cal['p_den'],cal['g_ns'],cal['w_ns'])
    return {'name':name,'object':'ACTIVE_JOB','stage':stage,'source_versions':list(source_versions),'current_versions':list(current_versions),'t_ns':int(t_ns),'remaining_cost_ns':int(remaining),'deadline_ns':int(deadline),'p_num':cal['p_num'],'p_den':cal['p_den'],'g_ns':cal['g_ns'],'w_ns':cal['w_ns'],'disposition':d}
