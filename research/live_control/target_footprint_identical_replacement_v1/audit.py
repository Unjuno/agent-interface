from __future__ import annotations
import argparse, hashlib, json, math
from pathlib import Path
from xml.etree import ElementTree as ET
import cv2
import numpy as np
from PIL import Image

ROOT=Path(__file__).resolve().parent
SRC=(175,155); TEMPLATE=61; SEARCH_RADIUS=120; MAX_RMSE=20.0; AMBIGUITY_SLACK=3.0
EXPECTED_BLOB='a8bb0e564bae738c9091b737ff2abe1922520ec1'

def sha(data): return hashlib.sha256(data).hexdigest()
def blob(data): return hashlib.sha1(f'blob {len(data)}\0'.encode()+data).hexdigest()
def rgb(p): return np.array(Image.open(p).convert('RGB'))
def ids(p): return sorted(e.attrib['id'] for e in ET.parse(p).iter() if 'id' in e.attrib)

def independent_resolve(image, template, prediction):
    th,tw=template.shape[:2]; h,w=image.shape[:2]; px,py=map(float,prediction); rx,ry=tw//2,th//2
    left=max(rx,math.ceil(px-SEARCH_RADIUS)); right=min(w-tw+rx,math.floor(px+SEARCH_RADIUS)); top=max(ry,math.ceil(py-SEARCH_RADIUS)); bottom=min(h-th+ry,math.floor(py+SEARCH_RADIUS))
    crop=image[top-ry:bottom-ry+th,left-rx:right-rx+tw]
    raw=cv2.matchTemplate(crop,template,cv2.TM_SQDIFF); rmse=np.sqrt(np.maximum(raw.astype(np.float64),0.0)/template.size)
    _,_,best,_=cv2.minMaxLoc(rmse); bx,by=best; value=float(rmse[by,bx]); distinct=rmse.copy(); suppression=max(8,min(th,tw)//2)
    distinct[max(0,by-suppression):by+suppression+1,max(0,bx-suppression):bx+suppression+1]=np.inf; second=float(np.min(distinct))
    status='MISSING' if value>MAX_RMSE else ('AMBIGUOUS' if second<=MAX_RMSE+AMBIGUITY_SLACK else 'UNIQUE')
    return {'status':status,'eligible':status=='UNIQUE','point':[left+bx,top+by],'best_rmse':value,'second_rmse':second if math.isfinite(second) else None}

def fail(msg): raise AssertionError(msg)
def main(out: Path):
    source=(ROOT/'upstream_resolver.py').read_bytes()
    if blob(source)!=EXPECTED_BLOB: fail('source blob mismatch')
    prereg=json.loads((ROOT/'prereg.json').read_text()); sched_bytes=(ROOT/'schedule.json').read_bytes()
    if sha(sched_bytes)!=prereg['schedule_sha256']: fail('schedule digest mismatch')
    schedule=json.loads(sched_bytes); by_pair={}; checked=[]
    for spec in schedule['pairs']:
        p=spec['pair']; pair={}
        for arm in spec['arm_order']:
            d=out/f'p{p:02d}-{arm}'; rec=json.loads((d/'result.json').read_text())
            if rec['mode']!='formal': fail('non-formal row')
            if rec['pair']!=p or rec['arm']!=arm: fail('case identity drift')
            ref=rgb(d/'reference.png'); cur=rgb(d/'current.png'); r=TEMPLATE//2; sx,sy=SRC; template=ref[sy-r:sy+r+1,sx-r:sx+r+1]
            actual=independent_resolve(cur,template,list(SRC)); got=rec['resolver']
            for key in ('status','eligible','point'):
                if got[key]!=actual[key]: fail(f'{rec["case"]} resolver {key} mismatch')
            for key in ('best_rmse','second_rmse'):
                if abs(float(got[key])-float(actual[key]))>1e-12: fail(f'{rec["case"]} resolver {key} mismatch')
            cur_ids=ids(d/'current.svg'); ref_ids=ids(d/'reference.svg')
            if cur_ids!=rec['current_ids'] or ref_ids!=rec['reference_ids']: fail('XML ID receipt mismatch')
            if 'target-A' not in ref_ids: fail('reference target absent')
            exp=[SRC[0]+spec['dx'],SRC[1]+spec['dy']]
            if got['status']!='UNIQUE' or not got['eligible'] or got['point']!=exp: fail(f'{rec["case"]} baseline visual retrieval not exact')
            if arm=='stable':
                if 'target-A' not in cur_ids or 'replacement-X' in cur_ids: fail('stable semantic identity wrong')
            else:
                if 'target-A' in cur_ids or 'replacement-X' not in cur_ids: fail('replacement semantic identity wrong')
            if rec['current_rgb_sha256']!=sha(cur.tobytes()) or rec['current_png_sha256']!=sha((d/'current.png').read_bytes()): fail('current image digest mismatch')
            pair[arm]=(rec,cur)
            checked.append(rec['case'])
        s,si=pair['stable']; q,qi=pair['replacement']
        if not np.array_equal(si,qi): fail(f'pair {p} current pixels differ')
        if s['current_png_sha256']!=q['current_png_sha256']: fail(f'pair {p} PNG bytes differ')
        for key in ('status','eligible','point','best_rmse','second_rmse','search_box','candidate_positions','template_shape','radius_px','max_rmse'):
            if s['resolver'][key]!=q['resolver'][key]: fail(f'pair {p} resolver evidence differs at {key}')
        by_pair[p]={'rgb_sha256':s['current_rgb_sha256'],'resolver_status':s['resolver']['status'],'point':s['resolver']['point'],'replacement_original_absent':True}
    if len(checked)!=prereg['formal_cases']: fail('formal case count mismatch')
    summary={'status':'PASS_INDEPENDENT_AUDIT','decision':'RETAIN_IDENTICAL_REPLACEMENT_BOUNDARY','formal_cases':len(checked),'matched_pairs':len(by_pair),'all_pair_pixels_identical':True,'all_stable_unique':True,'all_replacements_same_visual_evidence':True,'all_replacements_original_target_absent':True,'pairs':by_pair}
    (out/'audit_summary.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n')
    print(json.dumps(summary,sort_keys=True))
if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('out',type=Path); main(ap.parse_args().out)
