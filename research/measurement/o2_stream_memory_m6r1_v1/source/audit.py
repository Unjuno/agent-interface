"""Independent stdlib raw audit. Never imports codec, runner, NumPy or corpus."""
from pathlib import Path
import hashlib,json,statistics,struct,sys,zlib

def sha(b):return hashlib.sha256(b).hexdigest()
def pack(meta,data):
    h=json.dumps(meta,sort_keys=True,separators=(',',':')).encode()
    return struct.pack('!4sI',b'AIT1',len(h))+h+zlib.compress(data,1)

def expected(before,after,spec):
    w,h=spec['width'],spec['height'];kw=spec['metadata']
    meta=dict(stream=kw['stream'],sequence=2,base=1,width=w,height=h,mode='RGB',
              action_id=kw['action_id'],observed_ns=kw['observed_ns'],context=kw['context'])
    initial=pack(dict(meta,sequence=1,base=0,kind='full',action_id='initial',observed_ns=1),before)
    if before==after:return initial,pack(dict(meta,kind='unchanged'),b''),0
    pieces=[];count=0
    for top in range(0,h,64):
        for left in range(0,w,64):
            tw,th=min(64,w-left),min(64,h-top)
            old=b''.join(before[((top+r)*w+left)*3:((top+r)*w+left+tw)*3] for r in range(th))
            new=b''.join(after[((top+r)*w+left)*3:((top+r)*w+left+tw)*3] for r in range(th))
            if old!=new:
                pieces.append(struct.pack('!IIII',left,top,tw,th)+new);count+=1
    full=pack(dict(meta,kind='full'),after)
    tiled=pack(dict(meta,kind='tiles',count=count),b''.join(pieces))
    return initial,tiled if len(tiled)<len(full) else full,count

def decode(wire,base):
    magic,n=struct.unpack_from('!4sI',wire)
    if magic!=b'AIT1':raise ValueError('magic')
    meta=json.loads(wire[8:8+n]);obj=zlib.decompressobj();data=obj.decompress(wire[8+n:])+obj.flush()
    if not obj.eof or obj.unused_data or obj.unconsumed_tail:raise ValueError('compressed stream')
    if meta['kind']=='full':return meta,data
    if meta['kind']=='unchanged':
        if data:raise ValueError('unchanged data')
        return meta,base
    if meta['kind']!='tiles':raise ValueError('kind')
    out=bytearray(base);pos=0;used=set();width=meta['width'];height=meta['height']
    for _ in range(meta['count']):
        x,y,w,h=struct.unpack_from('!IIII',data,pos);pos+=16
        if w<=0 or h<=0 or x+w>width or y+h>height:raise ValueError('tile bounds')
        for r in range(h):
            for c in range(w):
                pixel=(y+r)*width+x+c
                if pixel in used:raise ValueError('overlap')
                used.add(pixel)
            length=w*3
            row=data[pos:pos+length]
            if len(row)!=length:raise ValueError('tile truncated')
            out[((y+r)*width+x)*3:((y+r)*width+x+w)*3]=row;pos+=length
    if pos!=len(data):raise ValueError('trailing tile data')
    return meta,bytes(out)

def audit(root):
    root=Path(root);errors=[];conditions=[];checks=0
    def require(test,label):
        nonlocal checks
        checks+=1
        if not test:errors.append(label)
    freeze=json.loads((root/'FREEZE.json').read_text());fs=sha((root/'FREEZE.json').read_bytes())
    for p,d in freeze['files'].items():require(sha((root/p).read_bytes())==d,'frozen:'+p)
    schedule=json.loads((root/'SCHEDULE.json').read_text());require(len(schedule)==12,'schedule count')
    require([s['index'] for s in schedule]==list(range(12)),'indices')
    parity=True;pixels=True
    for spec in schedule:
        i=spec['index'];folder=root/'formal'/f'{i:02d}'
        r=json.loads((folder/'record.json').read_text());rec=json.loads((root/'receipts'/f'{i:02d}.json').read_text())
        require(r['status']=='COMPLETE' and rec['status']=='TERMINAL' and rec['returncode']==0 and not rec.get('timeout',False),f'{i}:exit')
        require(r['spec']==spec and r['index']==i and r['pid']==rec['pid'],f'{i}:identity')
        require(r['freeze_sha256']==fs,f'{i}:freeze')
        require(r['affinity']==[freeze['cpu']],f'{i}:affinity')
        require(rec['end_ns']>=rec['start_ns'],f'{i}:receipt clock')
        for ext in ('stdout','stderr'):
            require(sha((root/'receipts'/f'{i:02d}.{ext}').read_bytes())==rec[ext+'_sha256'],f'{i}:{ext}')
        before,after=[zlib.decompress((root/spec[k]['path']).read_bytes()) for k in ('before','after')]
        for k,b in [('before',before),('after',after)]:
            require(sha(b)==spec[k]['sha256'] and len(b)==spec[k]['bytes']==spec['width']*spec['height']*3,f'{i}:{k}')
        initial,update,count=expected(before,after,spec)
        wires={}
        for arm in ('canonical','streaming'):
            for phase,b,original in [('initial',before,initial),('update',after,update)]:
                wire=(folder/(arm+'-'+phase+'.ait')).read_bytes();wires[(arm,phase)]=wire
                require(r['wire'][arm][phase]==sha(wire),f'{i}:{arm}:{phase}:hash')
                try:meta,decoded=decode(wire,before)
                except (ValueError,KeyError,struct.error,zlib.error,TypeError):
                    pixels=False;continue
                if decoded!=b:pixels=False
                if wire!=original:parity=False
                expectedmeta=json.loads(original[8:8+struct.unpack_from('!I',original,4)[0]])
                require(meta==expectedmeta,f'{i}:{arm}:{phase}:metadata')
        samples=r['samples'];require(len(samples)==32,f'{i}:sample count')
        want=[(p,j,a) for p,n in [('warmup',2),('timing',11),('memory',3)] for j in range(n)
              for a in (['canonical','streaming'] if (i+j)%2==0 else ['streaming','canonical'])]
        require([(s['phase'],s['pair'],s['arm']) for s in samples]==want,f'{i}:order')
        previous=-1
        for s in samples:
            label=f"{i}:{s['phase']}:{s['pair']}:{s['arm']}"
            require(s['wall_start_ns']>=previous and s['wall_end_ns']>s['wall_start_ns'],label+':clock')
            previous=s['wall_end_ns']
            require(s['wall_ns']==s['wall_end_ns']-s['wall_start_ns'] and s['cpu_ns']==s['cpu_end_ns']-s['cpu_start_ns'] and s['cpu_ns']>=0,label+':deltas')
            require(s['order']==(['canonical','streaming'] if (i+s['pair'])%2==0 else ['streaming','canonical']),label+':reported order')
            wire=wires[(s['arm'],'update')]
            require(s['wire_sha256']==sha(wire) and s['wire_bytes']==len(wire) and s['initial_sha256']==sha(wires[(s['arm'],'initial')]),label+':wire')
            require(s['state']['sequence']==2 and s['state']['previous_sha256']==sha(after) and s['state']['changed_tiles']==count and s['state']['kind']==json.loads(update[8:8+struct.unpack_from('!I',update,4)[0]])['kind'],label+':state')
            require(s['rss_highwater_after_kib']>=s['rss_highwater_before_kib']>0,label+':rss')
            if s['phase']=='memory':
                m=s['memory'];require(type(m)==dict and m['peak']>=m['current']>=0 and m['increment']==m['peak']-m['before'] and m['increment']>0,label+':memory')
            else:require(s['memory'] is None,label+':no tracer')
        ratios=[]
        for j in range(11):
            t={s['arm']:s['wall_ns'] for s in samples if s['phase']=='timing' and s['pair']==j}
            ratios.append(t['streaming']/t['canonical'])
        mm={a:statistics.median(s['memory']['increment'] for s in samples if s['phase']=='memory' and s['arm']==a) for a in ('canonical','streaming')}
        tm={a:statistics.median(s['wall_ns'] for s in samples if s['phase']=='timing' and s['arm']==a) for a in ('canonical','streaming')}
        row=dict(index=i,scene=spec['scene'],width=spec['width'],height=spec['height'],wall_ratio=statistics.median(ratios),wall_medians_ns=tm,peak_medians_bytes=mm,peak_ratio=mm['streaming']/mm['canonical'],kind=json.loads(update[8:8+struct.unpack_from('!I',update,4)[0]])['kind'])
        row['memory_gate']=(row['peak_ratio']<=.75 if spec['scene'].startswith('DENSE') else mm['streaming']<=1.2*mm['canonical']+32768)
        row['time_gate']=(True if spec['scene']=='UNCHANGED' else row['wall_ratio']<=1.2)
        conditions.append(row)
    dense=statistics.median(r['peak_ratio'] for r in conditions if r['scene'].startswith('DENSE'))
    decision=('HOLD_EVIDENCE' if errors else 'FAIL_CODEC_CORRECTNESS' if not pixels else 'HOLD_WIRE_PARITY' if not parity else 'PASS_STREAMING_O2_MEMORY_SCOPED' if dense<=.65 and all(r['memory_gate'] and r['time_gate'] for r in conditions) else 'HOLD_MEMORY_TRADEOFF')
    return dict(decision=decision,errors=errors,checks=checks,conditions=conditions,dense_peak_ratio_median=dense,wire_parity=parity,pixels_exact=pixels,timing_pairs=132,memory_pairs=36,formal_conditions=12)

if __name__=='__main__':
    try:r=audit(sys.argv[1])
    except (OSError,ValueError,KeyError,TypeError,IndexError) as e:r=dict(decision='HOLD_EVIDENCE',errors=[type(e).__name__+':'+str(e)])
    text=json.dumps(r,sort_keys=True,indent=2)+'\n'
    if len(sys.argv)>2:Path(sys.argv[2]).write_text(text)
    else:print(text,end='')
    sys.exit(bool(r['errors']))
