from __future__ import annotations
import argparse,binascii,hashlib,json,struct,zlib
from pathlib import Path

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def req(x,m):
    if not x:raise AssertionError(m)
def png(path):
    data=Path(path).read_bytes();req(data[:8]==b'\x89PNG\r\n\x1a\n','sig');pos=8;raws=b'';head=None
    while pos<len(data):
        n=struct.unpack('>I',data[pos:pos+4])[0];kind=data[pos+4:pos+8];body=data[pos+8:pos+8+n];crc=struct.unpack('>I',data[pos+8+n:pos+12+n])[0];req((binascii.crc32(kind+body)&0xffffffff)==crc,'crc');pos+=n+12
        if kind==b'IHDR':head=struct.unpack('>IIBBBBB',body)
        elif kind==b'IDAT':raws+=body
        elif kind==b'IEND':break
    w,h,depth,color,comp,filt,inter=head;req(depth==8 and color in (2,6) and (comp,filt,inter)==(0,0,0),'repr');bpp=3 if color==2 else 4;stride=w*bpp;raw=zlib.decompress(raws);prior=bytearray(stride);pix=bytearray()
    for y in range(h):
        o=y*(stride+1);ft=raw[o];line=bytearray(raw[o+1:o+1+stride]);req(ft<=4,'filter')
        for x in range(stride):
            l=line[x-bpp] if x>=bpp else 0;u=prior[x];ul=prior[x-bpp] if x>=bpp else 0
            if ft==0:p=0
            elif ft==1:p=l
            elif ft==2:p=u
            elif ft==3:p=(l+u)//2
            else:
                q=l+u-ul;ds=(abs(q-l),abs(q-u),abs(q-ul));p=(l,u,ul)[ds.index(min(ds))]
            line[x]=(line[x]+p)&255
        if bpp==3:pix.extend(line)
        else:
            for x in range(0,stride,4):pix.extend(line[x:x+3])
        prior=line
    return [w,h],hashlib.sha256(pix).hexdigest()
def state(path,exp):
    size,h=png(path);req(size==[exp['width'],exp['height']],'size');return 'A' if h==exp['a_rgb_sha256'] else 'B' if h==exp['b_rgb_sha256'] else 'OTHER'
def audit_case(root,c,exp):
    d=root/'evidence'/c['id'];load=lambda n:json.loads((d/n).read_text());req(not(d/'harness-failure.txt').exists(),'harness')
    proc=load('process.json');events=load('publish-events.json');inp=load('input.json');fin=load('final-input.json');code=inp['keycode'];req(inp['down']['keymap'][code//8]&(1<<(code%8)),'keydown');req(inp['released']['empty'] and fin['empty'],'release')
    req(proc['a_returncode']==255 and proc['b_returncode']==0,'rc');req(proc['b_spawned_ns']<proc['b_reaped_ns']<proc['a_reaped_ns'],'B must really reap before A');req(proc['b_started_before_a_reap'],'overlap')
    req(state(d/'b-stage-retained.png',exp)=='B','B stage identity');a_stage=load('a-stage.json')['state'];req(a_stage in ('A','ABSENT'),'A stage state');
    if a_stage=='A':req(state(d/'a-stage-retained.png',exp)=='A','A stage identity')
    req(state(d/'final.png',exp)==load('final.json')['state'],'final receipt');req(load('after-b-publish.json')['state']=='B','B publish')
    req(events[0]['attempt_id']=='B' and events[0]['generation']==2 and events[0]['outcome']=='PUBLISHED','B event');req(events[1]['attempt_id']=='A' and events[1]['generation']==1,'A event')
    if a_stage=='ABSENT':req(events[1]['outcome']=='NO_EFFECT' and load('final.json')['state']=='B','absent A must not publish')
    elif c['mode']=='naive':req(events[1]['outcome']=='PUBLISHED' and load('final.json')['state']=='A','naive stale overwrite')
    else:req(events[1]['outcome']=='STALE_GENERATION' and load('final.json')['state']=='B','gate should retain B')
    return {'id':c['id'],'rep':c['rep'],'mode':c['mode'],'a_stage':a_stage,'final':load('final.json')['state'],'a_callback':events[1]['outcome'],'stop_to_b_publish_ms':(proc['b_publish_finished_ns']-load('stop.json')['finished_ns'])/1e6,'stop_to_a_reap_ms':(proc['a_reaped_ns']-load('stop.json')['finished_ns'])/1e6}
def main(root,plan_name='plan.json'):
    plan=json.loads((root/plan_name).read_text());exp=json.loads((root/'fixtures/expected.json').read_text())
    for p,h in {**plan['sources'],**plan['fixtures']}.items():req(sha(root/p)==h,'pin '+p)
    rows=[audit_case(root,c,exp) for c in plan['cases']];n=[r for r in rows if r['mode']=='naive'];g=[r for r in rows if r['mode']=='generation_gate'];naive_a=sum(r['final']=='A' for r in n);gate_b=sum(r['final']=='B' for r in g);return {'schema':'staged-promotion-result-v2','cases':len(rows),'rows':rows,'naive_final_a':naive_a,'naive_a_stage':sum(r['a_stage']=='A' for r in n),'gate_final_b':gate_b,'gate_a_stage':sum(r['a_stage']=='A' for r in g),'a_absent_total':sum(r['a_stage']=='ABSENT' for r in rows),'decision':'RETAIN_GENERATION_GATE' if naive_a>=1 and gate_b==len(g) else 'FAIL_OR_INCONCLUSIVE'}
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('root',type=Path);ap.add_argument('--plan',default='plan.json');ap.add_argument('--out');a=ap.parse_args();r=main(a.root.resolve(),a.plan);print(json.dumps({k:v for k,v in r.items() if k!='rows'},indent=2));
    if a.out:Path(a.out).write_text(json.dumps(r,indent=2,sort_keys=True)+'\n')
