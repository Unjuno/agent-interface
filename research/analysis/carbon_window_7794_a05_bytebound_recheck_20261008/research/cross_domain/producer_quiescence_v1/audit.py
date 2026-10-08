from __future__ import annotations
import argparse,binascii,hashlib,json,struct,zlib
from pathlib import Path

def sha_bytes(b):return hashlib.sha256(b).hexdigest()
def sha_file(p):return sha_bytes(Path(p).read_bytes())
def req(x,m):
    if not x:raise ValueError(m)
def png_rgb(data):
    req(data[:8]==b'\x89PNG\r\n\x1a\n','png sig');pos=8;packed=b'';head=None;ended=False
    while pos<len(data):
        req(pos+12<=len(data),'chunk');n=struct.unpack('>I',data[pos:pos+4])[0];kind=data[pos+4:pos+8];body=data[pos+8:pos+8+n];req(len(body)==n,'body');crc=struct.unpack('>I',data[pos+8+n:pos+12+n])[0];req((binascii.crc32(kind+body)&0xffffffff)==crc,'crc')
        if kind==b'IHDR': head=struct.unpack('>IIBBBBB',body)
        elif kind==b'IDAT':packed+=body
        pos+=n+12
        if kind==b'IEND':ended=True;break
    req(ended and pos==len(data) and head,'end');w,h,depth,color,comp,filt,inter=head;req(depth==8 and color in (2,6) and (comp,filt,inter)==(0,0,0),'repr');bpp=3 if color==2 else 4;stride=w*bpp;raw=zlib.decompress(packed);req(len(raw)==h*(stride+1),'raw');pixels=bytearray();prior=bytearray(stride)
    for y in range(h):
        o=y*(stride+1);ft=raw[o];line=bytearray(raw[o+1:o+1+stride]);req(ft<=4,'filter')
        for x in range(stride):
            l=line[x-bpp] if x>=bpp else 0;u=prior[x];ul=prior[x-bpp] if x>=bpp else 0
            if ft==1:p=l
            elif ft==2:p=u
            elif ft==3:p=(l+u)//2
            elif ft==4:
                q=l+u-ul;ds=[abs(q-l),abs(q-u),abs(q-ul)];p=[l,u,ul][ds.index(min(ds))]
            else:p=0
            line[x]=(line[x]+p)&255
        if bpp==3:pixels.extend(line)
        else:
            for x in range(0,stride,4):pixels.extend(line[x:x+3])
        prior=line
    return w,h,bytes(pixels)
def img_kind(p,exp):
    data=Path(p).read_bytes();w,h,rgb=png_rgb(data);hsh=sha_bytes(rgb);req((w,h)==(exp['width'],exp['height']),'size');return ('A' if hsh==exp['a_rgb_sha256'] else 'B' if hsh==exp['b_rgb_sha256'] else 'OTHER'),sha_bytes(data),hsh

def audit_case(root,spec,exp):
    d=root/'evidence'/spec['id'];load=lambda n:json.loads((d/n).read_text())
    req(not (d/'harness-failure.txt').exists(),'harness fail');case=load('case.json');req(case['id']==spec['id'] and case['strategy']==spec['strategy'],'case drift')
    inp=load('input.json');code=inp['keycode'];req(inp['down']['keymap'][code//8]&(1<<(code%8)),'no physical keydown');req(inp['released']['empty'] and load('final-input.json')['empty'],'input not empty')
    stop=load('stop.json');proc=load('process.json');after=load('after-b.json');final=load('final.json')
    req(stop['signal']==15,'signal');req(proc['a_returncode']==255 and proc['b_returncode']==0,'return code');req(proc['a_spawned_ns']<=stop['started_ns']<=stop['finished_ns'],'stop order');req(proc['b_spawn_started_ns']<=proc['b_spawned_ns']<=proc['b_reaped_ns'],'b order')
    ak,af,ar=img_kind(d/'after_b.png',exp);fk,ff,fr=img_kind(d/'final.png',exp);req(ak=='B','B not complete before verdict');req(after['state']=='B' and after['file_sha256']==af and after['rgb_sha256']==ar,'after receipt');req(final['state']==fk and final['file_sha256']==ff and final['rgb_sha256']==fr,'final receipt')
    if spec['strategy']=='wait_reap':
        req(proc['a_reaped_ns']<=proc['b_spawn_started_ns'],'wait did not wait');req(fk=='B','quiescent final not B')
    else:req(proc['b_spawned_ns']<proc['a_reaped_ns'],'immediate not overlapping')
    return {'id':spec['id'],'rep':spec['rep'],'strategy':spec['strategy'],'after_b':'B','final':fk,'late_predecessor_overwrite':fk=='A','stop_to_a_reap_ms':(proc['a_reaped_ns']-stop['finished_ns'])/1e6,'stop_to_b_reap_ms':(proc['b_reaped_ns']-stop['finished_ns'])/1e6}
def main(root,plan_name='plan.json'):
    plan=json.loads((root/plan_name).read_text());exp=json.loads((root/'fixtures/expected.json').read_text())
    for p,h in {**plan['sources'],**plan['fixtures']}.items():req(sha_file(root/p)==h,'pin '+p)
    rows=[audit_case(root,c,exp) for c in plan['cases']];imm=[r for r in rows if r['strategy']=='immediate'];wait=[r for r in rows if r['strategy']=='wait_reap'];return {'schema':'producer-quiescence-result-v1','cases':len(rows),'rows':rows,'immediate_overwrites':sum(r['late_predecessor_overwrite'] for r in imm),'immediate_n':len(imm),'quiescent_final_b':sum(r['final']=='B' for r in wait),'quiescent_n':len(wait),'decision':'RETAIN_QUIESCENCE_GATE' if any(r['late_predecessor_overwrite'] for r in imm) and all(r['final']=='B' for r in wait) else 'INCONCLUSIVE_OR_FAIL'}
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('root',type=Path);ap.add_argument('--plan',default='plan.json');ap.add_argument('--out');a=ap.parse_args();r=main(a.root.resolve(),a.plan);print(json.dumps({k:v for k,v in r.items() if k!='rows'},indent=2));
    if a.out:Path(a.out).write_text(json.dumps(r,indent=2,sort_keys=True)+'\n')
