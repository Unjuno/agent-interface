#!/usr/bin/env python3
"""Lossless archive transport only; never used during measurement or scoring."""
import argparse, base64, copy, hashlib, json, lzma, struct
from pathlib import Path

def canonical(obj):
    return (json.dumps(obj,sort_keys=True,separators=(',',':'))+'\n').encode()

def encode_ints(values):
    out=bytearray()
    for x in values:
        u=2*x if x>=0 else -2*x-1
        while u>=128:
            out.append((u&127)|128); u>>=7
        out.append(u)
    return bytes(out)

def decode_ints(data):
    answer=[]; u=shift=0
    for b in data:
        u|=(b&127)<<shift
        if b&128:
            shift+=7
            if shift>63: raise ValueError('oversize integer')
        else:
            answer.append(-(u//2)-1 if u&1 else u//2);u=shift=0
    if shift: raise ValueError('truncated integer')
    return answer

def pack(raw):
    obj=json.loads(raw); assert canonical(obj)==raw
    db={};streams=[];lengths=[]
    for r in obj['records']:
        db.update(r.pop('pixel_payloads'))
        keys=sorted({a['digest'] for a in r['acquisitions']}|{r['final']['digest']})
        r['pixel_keys']=keys
        ac=r.pop('acquisitions');ms=r.pop('acquisition_metrics')
        assert len(ac)==len(ms)
        origin=ac[0]['start_ns']; r['origin_ns']=origin;r['n']=len(ac)
        rows=[];previous=origin
        for a,m in zip(ac,ms):
            assert [a['start_ns'],a['end_ns']]==m[:2]
            rows.append([m[0]-previous,m[1]-m[0],m[2],m[3]-m[1],m[4]-m[2],keys.index(a['digest']),a['match_count']])
            previous=m[0]
        values=[]
        for col in zip(*rows):
            values.extend([col[0]]+[b-a for a,b in zip(col,col[1:])])
        stream=encode_ints(values);streams.append(stream);lengths.append(len(stream))
    obj['pixel_database']=db
    header=canonical(dict(schema='qna1',raw_sha256=hashlib.sha256(raw).hexdigest(),
        raw_bytes=len(raw),lengths=lengths,payload=obj))
    return lzma.compress(b'QNA1'+struct.pack('<Q',len(header))+header+b''.join(streams),preset=9)

def unpack(packed):
    data=lzma.decompress(packed)
    assert data[:4]==b'QNA1'
    size=struct.unpack('<Q',data[4:12])[0]
    header=json.loads(data[12:12+size]);obj=header['payload'];pos=12+size
    db=obj.pop('pixel_database');assert len(header['lengths'])==len(obj['records'])
    for r,length in zip(obj['records'],header['lengths']):
        values=decode_ints(data[pos:pos+length]);pos+=length
        n=r.pop('n');assert len(values)==7*n
        cols=[]
        for i in range(7):
            col=[];v=0
            for delta in values[i*n:(i+1)*n]:v+=delta;col.append(v)
            cols.append(col)
        origin=r.pop('origin_ns');keys=r.pop('pixel_keys')
        ac=[];ms=[];s=origin
        for dt,wall,cpu,pred,predcpu,index,count in zip(*cols):
            s+=dt;e=s+wall
            ac.append(dict(start_ns=s,end_ns=e,digest=keys[index],match_count=count))
            ms.append([s,e,cpu,e+pred,cpu+predcpu])
        r['acquisitions']=ac;r['acquisition_metrics']=ms
        r['pixel_payloads']={k:db[k] for k in keys}
    assert pos==len(data)
    raw=canonical(obj)
    assert len(raw)==header['raw_bytes'] and hashlib.sha256(raw).hexdigest()==header['raw_sha256']
    return raw

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('mode',choices=['pack','unpack'])
    ap.add_argument('source',type=Path);ap.add_argument('destination',type=Path)
    args=ap.parse_args()
    if args.mode=='pack': result=pack(args.source.read_bytes())
    else:
        packed=(b''.join(p.read_bytes() for p in sorted(args.source.glob('part-*.bin')))
                if args.source.is_dir() else args.source.read_bytes())
        result=unpack(packed)
    with args.destination.open('xb') as f:f.write(result)
