from __future__ import annotations
import argparse, hashlib, json, struct, zlib
from pathlib import Path

def decode_png(data):
 if data[:8] != b'\x89PNG\r\n\x1a\n': raise ValueError('signature')
 pos=8; chunks=[]; idat=b''; w=h=ct=None
 while pos<len(data):
  if pos+12>len(data): raise ValueError('truncated')
  n=struct.unpack('>I',data[pos:pos+4])[0]; typ=data[pos+4:pos+8]; payload=data[pos+8:pos+8+n]; crc=data[pos+8+n:pos+12+n]
  if len(payload)!=n or len(crc)!=4: raise ValueError('truncated chunk')
  if zlib.crc32(typ+payload)&0xffffffff != struct.unpack('>I',crc)[0]: raise ValueError('crc')
  pos += 12+n
  if typ==b'IHDR':
   w,h,bd,ct,comp,flt,inter=struct.unpack('>IIBBBBB',payload)
   if (bd,ct,comp,flt,inter)!=(8,2,0,0,0): raise ValueError('unsupported')
  elif typ==b'IDAT': idat+=payload
  elif typ==b'IEND': break
 raw=zlib.decompress(idat); stride=w*3; out=[]; prev=[0]*stride; p=0
 for _ in range(h):
  f=raw[p]; p+=1; scan=list(raw[p:p+stride]); p+=stride; recon=[]
  for i,x in enumerate(scan):
   a=recon[i-3] if i>=3 else 0; b=prev[i]; c=prev[i-3] if i>=3 else 0
   if f==0: v=x
   elif f==1: v=(x+a)&255
   elif f==2: v=(x+b)&255
   elif f==3: v=(x+((a+b)//2))&255
   elif f==4:
    q=a+b-c; pa=abs(q-a); pb=abs(q-b); pc=abs(q-c); pr=a if pa<=pb and pa<=pc else (b if pb<=pc else c); v=(x+pr)&255
   else: raise ValueError('filter')
   recon.append(v)
  out.extend(recon); prev=recon
 return (w,h,bytes(out))

def audit(root):
 root=Path(root); rows=json.loads((root/'rows.json').read_text()); errs=[]
 by={r['case']:r for r in rows}
 for r in rows:
  raw=bytes.fromhex(r['raw_hex']); png=bytes.fromhex(r['png_hex']);
  if hashlib.sha256(raw).hexdigest()!=r['raw_sha256']: errs.append([r['case'],'raw hash'])
  if r['artifact']['source_raw_sha256']!=r['raw_sha256']: errs.append([r['case'],'source link'])
  if hashlib.sha256(png).hexdigest()!=r['artifact']['sha256'] or r['png_sha256']!=r['artifact']['sha256']: errs.append([r['case'],'png hash'])
  try: w,h,rgb=decode_png(png)
  except Exception as e: errs.append([r['case'],'decode '+str(e)]); continue
  r['_rgb']=rgb.hex(); r['_size']=[w,h]
  if [w,h]!=[1,1]: errs.append([r['case'],'size'])
 for pre in ('bgrx','xrgb'):
  a,b,c=by[pre+'_base'],by[pre+'_xdiff'],by[pre+'_vis']
  if a['raw_sha256']==b['raw_sha256']: errs.append([pre,'x raw same'])
  if a['png_hex']!=b['png_hex'] or a['_rgb']!=b['_rgb']: errs.append([pre,'x changed visible'])
  if a['png_hex']==c['png_hex'] or a['_rgb']==c['_rgb']: errs.append([pre,'visible unchanged'])
 return {'status':'PASS_RAW_HASH_NONRECONSTRUCTIBLE_FROM_PNG_SCOPED' if not errs else 'FAIL','case_count':len(rows),'errors':errs,
         'witnesses':{p:{'raw_hash_diff':by[p+'_base']['raw_sha256']!=by[p+'_xdiff']['raw_sha256'],'png_equal':by[p+'_base']['png_hex']==by[p+'_xdiff']['png_hex'],'rgb_equal':by[p+'_base']['_rgb']==by[p+'_xdiff']['_rgb']} for p in ('bgrx','xrgb')}}

if __name__=='__main__':
 ap=argparse.ArgumentParser(); ap.add_argument('root'); a=ap.parse_args(); print(json.dumps(audit(a.root),sort_keys=True,indent=2))
