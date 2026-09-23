#!/usr/bin/env python3
"""Lossless timestamp-delta transport, with byte-exact canonical JSON readback."""
import base64, copy, hashlib, json, sys, zlib
from pathlib import Path

def enc(x): return (json.dumps(x,sort_keys=True,separators=(',',':'))+'\n').encode()
def digest(b): return hashlib.sha256(b).hexdigest()

def compress_rows(raw):
    obj=copy.deepcopy(raw)
    for block in obj['blocks']:
        rows=block.pop('samples'); origin=rows[0][0]; data=bytearray(); previous=0
        for i,(due,wake,late) in enumerate(rows):
            if due!=origin+i*2000000 or wake-due!=late: raise ValueError('nonconforming tuple')
            delta=late-previous; previous=late; value=delta*2 if delta>=0 else -delta*2-1
            while value>=128: data.append((value&127)|128); value>>=7
            data.append(value)
        block['sample_codec']={'origin_ns':origin,'n':len(rows),'delta_b64':base64.b64encode(data).decode()}
    return obj

def expand_rows(obj):
    raw=copy.deepcopy(obj)
    for block in raw['blocks']:
        spec=block.pop('sample_codec'); data=base64.b64decode(spec['delta_b64'],validate=True)
        values=[]; value=0; shift=0; previous=0
        for byte in data:
            value|=(byte&127)<<shift
            if byte&128:
                shift+=7
                if shift>63: raise ValueError('oversized varint')
            else:
                previous+=(value//2 if value%2==0 else -(value//2)-1)
                values.append(previous); value=0; shift=0
        if shift or len(values)!=spec['n']: raise ValueError('truncated or surplus varints')
        block['samples']=[[spec['origin_ns']+i*2000000,spec['origin_ns']+i*2000000+v,v] for i,v in enumerate(values)]
    return raw

def pack(path, dest):
    original=Path(path).read_bytes(); raw=json.loads(original)
    compact=compress_rows(raw)
    if enc(expand_rows(compact))!=original: raise ValueError('non-exact roundtrip')
    compressed=zlib.compress(enc(compact),9); ascii_data=base64.b64encode(compressed)
    dest=Path(dest); dest.mkdir(parents=True,exist_ok=True); chunks=[]
    for i in range(0,len(ascii_data),4096):
        name=f'raw.part{i//4096:02d}.b64'; b=ascii_data[i:i+4096]+b'\n'
        (dest/name).write_bytes(b); chunks.append({'name':name,'sha256':digest(b),'size':len(b)})
    manifest={'schema':'cpu-placement-lossless-v1','raw_sha256':digest(original),'raw_bytes':len(original),
              'compressed_sha256':digest(compressed),'compressed_bytes':len(compressed),'chunks':chunks}
    (dest/'transport.json').write_bytes(enc(manifest)); return manifest

def unpack(folder):
    folder=Path(folder); m=json.loads((folder/'transport.json').read_text()); parts=[]
    for s in m['chunks']:
        if Path(s['name']).name!=s['name']: raise ValueError('invalid chunk name')
        b=(folder/s['name']).read_bytes()
        if len(b)!=s['size'] or digest(b)!=s['sha256']: raise ValueError('chunk digest')
        parts.append(b.strip())
    compressed=base64.b64decode(b''.join(parts),validate=True)
    if digest(compressed)!=m['compressed_sha256']: raise ValueError('compressed digest')
    result=enc(expand_rows(json.loads(zlib.decompress(compressed))))
    if len(result)!=m['raw_bytes'] or digest(result)!=m['raw_sha256']: raise ValueError('raw digest')
    return result

if __name__=='__main__':
    if sys.argv[1]=='pack': print(json.dumps(pack(sys.argv[2],sys.argv[3]),indent=2))
    elif sys.argv[1]=='unpack': Path(sys.argv[3]).write_bytes(unpack(sys.argv[2]))
    else: raise SystemExit('usage: codec.py pack RAW DIR | unpack DIR OUT')
