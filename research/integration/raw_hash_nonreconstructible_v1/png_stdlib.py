from __future__ import annotations
import struct, zlib

def decode_rgb8_png(data: bytes):
    if not data.startswith(b'\x89PNG\r\n\x1a\n'):
        raise ValueError('signature')
    off=8; ihdr=None; idat=[]; seen_iend=False
    while off < len(data):
        if off+12>len(data): raise ValueError('truncated chunk')
        n=struct.unpack('>I',data[off:off+4])[0]; typ=data[off+4:off+8]
        end=off+12+n
        if end>len(data): raise ValueError('truncated payload')
        payload=data[off+8:off+8+n]
        crc=struct.unpack('>I',data[off+8+n:off+12+n])[0]
        if (zlib.crc32(typ+payload)&0xffffffff)!=crc: raise ValueError('crc')
        if typ==b'IHDR': ihdr=payload
        elif typ==b'IDAT': idat.append(payload)
        elif typ==b'IEND': seen_iend=True; off=end; break
        off=end
    if not seen_iend or off!=len(data): raise ValueError('iend/trailing')
    if ihdr is None or len(ihdr)!=13: raise ValueError('ihdr')
    w,h,bd,ct,comp,filt,inter=struct.unpack('>IIBBBBB',ihdr)
    if (bd,ct,comp,filt,inter)!=(8,2,0,0,0): raise ValueError('unsupported png mode')
    raw=zlib.decompress(b''.join(idat))
    stride=w*3
    if len(raw)!=(stride+1)*h: raise ValueError('extent')
    rows=[]; prev=bytearray(stride); pos=0
    for _ in range(h):
        ft=raw[pos]; pos+=1; scan=bytearray(raw[pos:pos+stride]); pos+=stride
        recon=bytearray(stride)
        for i,x in enumerate(scan):
            a=recon[i-3] if i>=3 else 0
            b=prev[i]
            c=prev[i-3] if i>=3 else 0
            if ft==0: val=x
            elif ft==1: val=(x+a)&255
            elif ft==2: val=(x+b)&255
            elif ft==3: val=(x+((a+b)//2))&255
            elif ft==4:
                p=a+b-c; pa=abs(p-a); pb=abs(p-b); pc=abs(p-c)
                pr=a if pa<=pb and pa<=pc else (b if pb<=pc else c)
                val=(x+pr)&255
            else: raise ValueError('filter')
            recon[i]=val
        rows.append(bytes(recon)); prev=recon
    return {'width':w,'height':h,'rgb':b''.join(rows)}
