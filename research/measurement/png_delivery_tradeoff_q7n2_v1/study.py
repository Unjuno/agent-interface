"""A finite producer/file/anonymous-pipe/decoded-ACK comparison, not a runtime."""
import hashlib, io, json, os, select, subprocess, sys, time
from dataclasses import dataclass
from pathlib import Path
from PIL import Image
from image_artifact import ImageArtifactSink

ROOT = Path(__file__).resolve().parent
SCENES = ('form', 'table', 'canvas')
RATES = (0, 65536)
CHUNK = 4096


def digest(data):
    return hashlib.sha256(data).hexdigest()


def dump(path, data):
    Path(path).write_text(json.dumps(data, indent=2, sort_keys=True)+'\n')


def read_line(pipe):
    if not select.select([pipe], [], [], 5)[0]:
        raise TimeoutError('receiver line')
    line = pipe.readline()
    if not line or len(line)>8192: raise RuntimeError('receiver framing')
    return line


def write_all(pipe, data):
    sent = 0
    while sent < len(data):
        count = os.write(pipe.fileno(), data[sent:])
        if count <= 0: raise RuntimeError('pipe write made no progress')
        sent += count
    return sent


def receiver(path):
    os.sched_setaffinity(0, {1})
    Image.init()
    print(json.dumps({'ready':True,'pid':os.getpid(),'affinity':sorted(os.sched_getaffinity(0))}),flush=True)
    header = json.loads(sys.stdin.buffer.readline(8192))
    n = header['length']
    if type(n) is not int or not 0<n<=4194304: raise ValueError('payload length')
    data = bytearray()
    begin = time.monotonic_ns()
    while len(data)<n:
        part = sys.stdin.buffer.read(min(CHUNK,n-len(data)))
        if not part: raise EOFError('short PNG')
        data.extend(part)
    received = time.monotonic_ns()
    raw = bytes(data)
    decode_start = time.monotonic_ns()
    with Image.open(io.BytesIO(raw),formats=['PNG']) as image:
        image.load()
        mode, size, pixels = image.mode, image.size, image.tobytes()
    decode_end = time.monotonic_ns()
    response = {'id':header['id'],'pid':os.getpid(),'read_start_ns':begin,'received_ns':received,
                'decode_start_ns':decode_start,'decode_end_ns':decode_end,'length':n,
                'png_sha256':digest(raw),'rgb_sha256':digest(pixels),'mode':mode,'size':list(size),
                'authority':'none'}
    response['ack_emit_ns']=time.monotonic_ns()
    print(json.dumps(response,sort_keys=True),flush=True)
    # Evidence persistence is after the measured ACK, never a substitute for it.
    Path(path).write_bytes(raw)


@dataclass(frozen=True)
class Frame:
    width: int
    height: int
    mode: str
    pixels: bytes


def deliver(frame, out, identity, level, rate):
    out = Path(out); out.mkdir(parents=True,exist_ok=False)
    command=[sys.executable,'-B',str(Path(__file__).resolve()),'receiver',str(out/'received.png')]
    child=subprocess.Popen(command,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,bufsize=0)
    record={'id':identity,'level':level,'rate':rate,'command':command,'pid':child.pid,
            'parent_pid':os.getpid(),'parent_affinity':sorted(os.sched_getaffinity(0)),
            'emits_input':False,'writes':[]}
    try:
        ready_line=read_line(child.stdout)
        record['ready_wire']=ready_line.decode(); record['ready']=json.loads(ready_line)
        if record['ready']!={'ready':True,'pid':child.pid,'affinity':[1]}: raise ValueError('readiness')
        sink=ImageArtifactSink(out/'producer',compress_level=level,reuse=False)
        record['start_ns']=time.monotonic_ns(); record['cpu_start_ns']=time.process_time_ns()
        record['sink']=sink.publish(frame)
        record['prepared_ns']=time.monotonic_ns(); record['cpu_prepared_ns']=time.process_time_ns()
        raw=Path(record['sink']['image']).read_bytes()
        record['read_file_ns']=time.monotonic_ns()
        header=(json.dumps({'id':identity,'length':len(raw)},sort_keys=True)+'\n').encode()
        record['header_wire']=header.decode()
        write_all(child.stdin,header)
        record['transfer_start_ns']=time.monotonic_ns()
        for offset in range(0,len(raw),CHUNK):
            end=min(offset+CHUNK,len(raw))
            due=record['transfer_start_ns']+((end*1000000000+rate-1)//rate if rate else 0)
            if rate:
                while True:
                    rem=due-time.monotonic_ns()
                    if rem<=0: break
                    time.sleep(rem/1000000000)
            before=time.monotonic_ns()
            count=write_all(child.stdin,raw[offset:end])
            after=time.monotonic_ns()
            record['writes'].append({'offset':offset,'end':end,'count':count,'due_ns':due,'before_ns':before,'after_ns':after})
        record['transfer_end_ns']=time.monotonic_ns()
        child.stdin.close()
        ack_line=read_line(child.stdout)
        record['ack_ns']=time.monotonic_ns()
        record['ack_wire']=ack_line.decode(); record['ack']=json.loads(ack_line)
        record['exit']=child.wait(timeout=3)
        record['stderr']=child.stderr.read().decode()
        if record['exit']!=0 or record['stderr']: raise RuntimeError('receiver exit')
        if record['ack']['rgb_sha256']!=digest(frame.pixels): raise ValueError('decoded pixels')
        record['png_sha256']=digest(raw); record['rgb_sha256']=digest(frame.pixels); record['length']=len(raw)
        record['retention_end_ns']=time.monotonic_ns()
        return record
    except BaseException as exc:
        record['error']=repr(exc)
        raise
    finally:
        if child.poll() is None:
            child.terminate()
            try: child.wait(timeout=2)
            except subprocess.TimeoutExpired: child.kill(); child.wait()
        record['observed_final_exit']=child.returncode
        dump(out/'ROW.json',record)
        for pipe in (child.stdin,child.stdout,child.stderr):
            if pipe and not pipe.closed: pipe.close()


def verify_freeze(expected):
    raw=(ROOT/'FREEZE.json').read_bytes()
    if digest(raw)!=expected: raise ValueError('freeze identity')
    for name,sha in json.loads(raw)['files'].items():
        if digest((ROOT/name).read_bytes())!=sha: raise ValueError('source/corpus changed: '+name)


def block(index, expected):
    if not 0<=index<6: raise ValueError('block range')
    verify_freeze(expected)
    os.sched_setaffinity(0,{0}); Image.init()
    formal=ROOT/'formal'; formal.mkdir(exist_ok=True)
    if index:
        previous=json.loads((formal/f'block-{index-1}'/'OUTER.json').read_text())
        if previous['returncode']!=0 or previous['timeout']: raise ValueError('previous block incomplete')
    out=formal/f'block-{index}'; out.mkdir(exist_ok=False)
    scene=SCENES[index//2]; rate=RATES[index%2]
    frame=Frame(800,480,'RGB',(ROOT/'corpus'/(scene+'.rgb')).read_bytes())
    rows=[]
    for rep in range(3):
        order=(1,6) if (index+rep)%2==0 else (6,1)
        for level in order:
            identity=f'{scene}-r{rate}-p{rep}-l{level}'
            row=deliver(frame,out/identity,identity,level,rate)
            row.update(scene=scene,repeat=rep,block=index)
            dump(out/identity/'ROW.json',row)
            rows.append(row)
            dump(out/'ROWS.json',rows)
    dump(out/'END.json',{'index':index,'rows':len(rows),'freeze':expected,'end_ns':time.monotonic_ns()})

if __name__=='__main__':
    if sys.argv[1]=='receiver': receiver(sys.argv[2])
    elif sys.argv[1]=='block': block(int(sys.argv[2]),sys.argv[3])
    else: raise SystemExit('usage: study.py receiver OUTPUT | block INDEX FREEZE_SHA256')
