from pathlib import Path
import argparse,json,statistics,hashlib
import numpy as np
from PIL import Image
from resolver import resolve,MAX_AGE_NS
from oracle import svg_snapshot

def derive(im):
    a=np.asarray(im.convert('RGB'));mask=(a[:,:,0]>220)&(a[:,:,1]<20)&(a[:,:,2]>150)&(a[:,:,2]<200);yy,xx=np.where(mask)
    if len(xx)<40:raise ValueError('magenta missing')
    cutoff=float(np.median(xx));sel=xx<cutoff;xs=xx[sel];ys=yy[sel]
    if len(xs)<20:xs=xx;ys=yy
    cx,cy=int(round(float(xs.mean()))),int(round(float(ys.mean())));r=25
    return [float(cx),float(cy)],a[cy-r:cy+r+1,cx-r:cx+r+1].copy()

def releases_ok(rows):
    rel=[x for x in rows if x.get('event')=='owner_release']
    return bool(rel) and all(x.get('verified') and not x.get('keys_down') and not x.get('buttons_down') for x in rel)

def main():
    p=argparse.ArgumentParser();p.add_argument('root',type=Path);p.add_argument('--plan',type=Path,required=True);p.add_argument('--out',type=Path);a=p.parse_args();plan=json.loads(a.plan.read_text());errs=[];rows=[]
    for c in plan['cases']:
        d=a.root/f"case-{c['case']:02d}"; req=['score.json','prewait.png','template.png','before.svg','board.svg']
        if c['mode']=='late_bind':req+=['postwait.png']
        miss=[x for x in req if not (d/x).exists()]
        if miss:errs.extend([f"missing_{c['case']}_{x}" for x in miss]);continue
        s=json.loads((d/'score.json').read_text())
        if s.get('mode')!=c['mode'] or s.get('seed')!=c['seed']:errs.append(f"identity_{c['case']}")
        if s.get('error') is not None:errs.append(f"runtime_error_{c['case']}")
        if s.get('wait_ns',0)<6_400_000_000:errs.append(f"wait_short_{c['case']}")
        relok=releases_ok(s.get('setup_owner_records',[]))+releases_ok(s.get('task_owner_records',[]))==2
        if not relok:errs.append(f"release_{c['case']}")
        before_items,broot=svg_snapshot(d/'before.svg');after_items,aroot=svg_snapshot(d/'board.svg');lost=sorted(set(before_items)-set(after_items));added=sorted(set(after_items)-set(before_items));changed=sorted(k for k in before_items.keys()&after_items.keys() if before_items[k]!=after_items[k]);unchanged=(d/'before.svg').read_bytes()==(d/'board.svg').read_bytes()
        age=s.get('evidence_age_ns');fresh=isinstance(age,int) and age<=plan['observation_max_age_ns']
        if c['mode']=='snapshot_bound':
            ok=(not fresh and s.get('task_input_count')==0 and unchanged and relok)
            if not ok:errs.append(f"snapshot_gate_{c['case']}")
            independent=False;unique=None;best=None
        else:
            point,template=derive(Image.open(d/'prewait.png'));cur=np.asarray(Image.open(d/'postwait.png').convert('RGB'));res=resolve(cur,template,point);unique=res.get('eligible') is True;best=res.get('best_rmse')
            independent=(lost==['task-target'] and not added and not changed and broot==aroot)
            ok=(fresh and unique and independent and not s.get('wrong_target_deleted',False) and relok and s.get('task_input_count')==3)
            if not ok:errs.append(f"late_bind_gate_{c['case']}")
            if s.get('resolver',{}).get('status')!=res.get('status') or s.get('resolver',{}).get('point')!=res.get('point'):errs.append(f"resolver_receipt_{c['case']}")
        rows.append({'case':c,'age_ns':age,'fresh':fresh,'release_ok':relok,'independent_success':independent,'unique':unique,'best_rmse':best,'lost':lost,'unchanged':unchanged,'task_input_count':s.get('task_input_count')})
    snap=[r for r in rows if r['case']['mode']=='snapshot_bound'];late=[r for r in rows if r['case']['mode']=='late_bind']
    diffs=[];pairs=[]
    for seed in plan['formal_seeds']:
        sn=next((r for r in snap if r['case']['seed']==seed),None);lb=next((r for r in late if r['case']['seed']==seed),None)
        if not sn or not lb:errs.append(f"pair_missing_{seed}");continue
        diff=sn['age_ns']-lb['age_ns'];diffs.append(diff);pairs.append({'seed':seed,'snapshot_age_ns':sn['age_ns'],'late_bind_age_ns':lb['age_ns'],'snapshot_minus_late_ns':diff})
    med=int(statistics.median(diffs)) if diffs else None
    snapok=len(snap)==4 and all((not r['fresh']) and r['task_input_count']==0 and r['unchanged'] and r['release_ok'] for r in snap)
    lateok=len(late)==4 and all(r['fresh'] and r['unique'] and r['independent_success'] and r['release_ok'] and r['task_input_count']==3 for r in late)
    if not snapok or not lateok: decision='FAIL_TRANSFER'
    elif med is not None and med>=5_000_000_000: decision='PASS_CROSS_DOMAIN_LATE_BIND'
    else: decision='HOLD_TRANSFER'
    out={'schema':'agent-interface/gui-target-late-bind-audit-v2','status':'PASS_AUDIT' if not errs else 'FAIL_AUDIT_INTEGRITY','scientific_decision':decision,'errors':errs,'counts':{'snapshot_bound':{'cases':len(snap),'safe_yields':sum((not r['fresh']) and r['task_input_count']==0 and r['unchanged'] for r in snap),'release_failures':sum(not r['release_ok'] for r in snap),'median_age_ns':int(statistics.median([r['age_ns'] for r in snap])) if snap else None},'late_bind':{'cases':len(late),'fresh':sum(r['fresh'] for r in late),'target_only_deletes':sum(r['independent_success'] for r in late),'unique_retrieval':sum(bool(r['unique']) for r in late),'release_failures':sum(not r['release_ok'] for r in late),'median_age_ns':int(statistics.median([r['age_ns'] for r in late])) if late else None}},'paired_age_rows':pairs,'paired_median_snapshot_minus_late_ns':med}
    txt=json.dumps(out,indent=2,sort_keys=True)+'\n';print(txt,end='');
    if a.out:a.out.write_text(txt)
    raise SystemExit(0 if not errs else 2)
if __name__=='__main__':main()
