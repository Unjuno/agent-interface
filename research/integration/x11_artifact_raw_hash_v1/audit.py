from __future__ import annotations
import argparse, hashlib, json, shutil, struct, tempfile, zlib
from pathlib import Path

def decode_png(data):
 if data[:8] != b'\x89PNG\r\n\x1a\n': raise ValueError('signature')
 pos=8; idat=b''; w=h=None
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
  if p>=len(raw): raise ValueError('scanline')
  f=raw[p]; p+=1; scan=list(raw[p:p+stride]); p+=stride
  if len(scan)!=stride: raise ValueError('scanline')
  recon=[]
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
 if p!=len(raw): raise ValueError('trailing scan data')
 return (w,h,bytes(out))

def audit(root):
 root=Path(root); errs=[]
 try: rows=json.loads((root/'rows.json').read_text())
 except Exception as e: return {'status':'FAIL','case_count':0,'errors':[['rows','read '+str(e)]]}
 if not isinstance(rows,list) or len(rows)!=6: errs.append(['rows','denominator'])
 by={r.get('case'):r for r in rows if isinstance(r,dict)}
 expected=['bgrx_base','bgrx_xdiff','bgrx_vis','xrgb_base','xrgb_xdiff','xrgb_vis']
 if sorted(by)!=sorted(expected): errs.append(['rows','identity'])
 for idx,name in enumerate(expected):
  case_dir=root/f'{idx:02d}-{name}'
  try: proc=json.loads((case_dir/'process.json').read_text())
  except Exception as e: errs.append([name,'process '+str(e)]); continue
  if proc.get('case')!=name or proc.get('index')!=idx or proc.get('returncode')!=0 or proc.get('stderr')!='': errs.append([name,'process receipt'])
 for r in rows:
  if not isinstance(r,dict) or 'case' not in r: continue
  try: raw=bytes.fromhex(r['raw_hex']); png=bytes.fromhex(r['png_hex'])
  except Exception as e: errs.append([r.get('case'),'hex '+str(e)]); continue
  if hashlib.sha256(raw).hexdigest()!=r.get('raw_sha256'): errs.append([r['case'],'raw hash'])
  art=r.get('artifact') if isinstance(r.get('artifact'),dict) else {}
  if art.get('source_raw_sha256')!=r.get('raw_sha256'): errs.append([r['case'],'source link'])
  if hashlib.sha256(png).hexdigest()!=art.get('sha256') or r.get('png_sha256')!=art.get('sha256'): errs.append([r['case'],'png hash'])
  try: w,h,rgb=decode_png(png)
  except Exception as e: errs.append([r['case'],'decode '+str(e)]); continue
  r['_rgb']=rgb.hex(); r['_size']=[w,h]
  if [w,h]!=[1,1] or art.get('width')!=1 or art.get('height')!=1: errs.append([r['case'],'size'])
 for pre in ('bgrx','xrgb'):
  if any(pre+x not in by for x in ('_base','_xdiff','_vis')): continue
  a,b,c=by[pre+'_base'],by[pre+'_xdiff'],by[pre+'_vis']
  if a.get('raw_sha256')==b.get('raw_sha256'): errs.append([pre,'x raw same'])
  if a.get('png_hex')!=b.get('png_hex') or a.get('_rgb')!=b.get('_rgb'): errs.append([pre,'x changed visible'])
  if a.get('png_hex')==c.get('png_hex') or a.get('_rgb')==c.get('_rgb'): errs.append([pre,'visible unchanged'])
 return {'status':'PASS_RAW_HASH_NONRECONSTRUCTIBLE_FROM_PNG_SCOPED' if not errs else 'FAIL','case_count':len(rows),'errors':errs,
         'witnesses':{p:{'raw_hash_diff':by.get(p+'_base',{}).get('raw_sha256')!=by.get(p+'_xdiff',{}).get('raw_sha256'),'png_equal':by.get(p+'_base',{}).get('png_hex')==by.get(p+'_xdiff',{}).get('png_hex'),'rgb_equal':by.get(p+'_base',{}).get('_rgb')==by.get(p+'_xdiff',{}).get('_rgb')} for p in ('bgrx','xrgb')}}

def controls(root):
 root=Path(root); specs=[]
 def mutate(tag,fn):
  with tempfile.TemporaryDirectory() as td:
   dst=Path(td)/'copy'; shutil.copytree(root,dst); fn(dst); verdict=audit(dst)
   specs.append({'control':tag,'rejected':verdict['status']!='PASS_RAW_HASH_NONRECONSTRUCTIBLE_FROM_PNG_SCOPED','status':verdict['status']})
 def rows_mut(fn):
  def f(dst):
   p=dst/'rows.json'; rows=json.loads(p.read_text()); fn(rows); p.write_text(json.dumps(rows,sort_keys=True,indent=2)+'\n')
  return f
 mutate('raw_hex',rows_mut(lambda r:r[0].__setitem__('raw_hex','00000000')))
 mutate('raw_hash',rows_mut(lambda r:r[0].__setitem__('raw_sha256','0'*64)))
 mutate('source_link',rows_mut(lambda r:r[0]['artifact'].__setitem__('source_raw_sha256','0'*64)))
 mutate('png_hash',rows_mut(lambda r:r[0]['artifact'].__setitem__('sha256','0'*64)))
 mutate('png_bytes',rows_mut(lambda r:r[0].__setitem__('png_hex',r[0]['png_hex'][:-2]+'00')))
 mutate('drop_row',rows_mut(lambda r:r.pop()))
 def proc(dst):
  p=dst/'00-bgrx_base/process.json'; row=json.loads(p.read_text()); row['returncode']=7; p.write_text(json.dumps(row,sort_keys=True,indent=2)+'\n')
 mutate('process_exit',proc)
 return {'all_rejected':all(x['rejected'] for x in specs),'controls':specs}

if __name__=='__main__':
 ap=argparse.ArgumentParser(); ap.add_argument('root'); ap.add_argument('--controls',action='store_true'); a=ap.parse_args()
 print(json.dumps(controls(a.root) if a.controls else audit(a.root),sort_keys=True,indent=2))
