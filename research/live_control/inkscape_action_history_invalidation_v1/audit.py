#!/usr/bin/env python3
import argparse, hashlib, json
from pathlib import Path
import xml.etree.ElementTree as ET
from PIL import Image

EXPECTED_GUARD_SHA = '45f96568c969d5fb1ff04769a469d45ecc79c27849da4e43dc9cd48e1abd6ee5'
EXPECTED_COUNTS = {'top':64,'right':176,'bottom':64}
EXPECTED_ROI_SIZE = (178,145)
OBJ_W, OBJ_H = 158,105

def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def guard_recompute(path):
    im=Image.open(path).convert('RGB')
    if im.size != EXPECTED_ROI_SIZE:
        raise ValueError(f'guard_roi_size:{im.size}')
    w,h=im.size
    def dark(x0,y0,x1,y1):
        return sum(1 for y in range(max(0,y0),min(h,y1)) for x in range(max(0,x0),min(w,x1)) if max(im.getpixel((x,y)))<=60)
    counts={
        'top':dark(0,0,OBJ_W,20),
        'right':dark(OBJ_W,0,OBJ_W+20,OBJ_H+40),
        'bottom':dark(0,OBJ_H+20,OBJ_W,OBJ_H+40),
    }
    rgb_sha=hashlib.sha256(im.tobytes()).hexdigest()
    return counts,rgb_sha

def svg_xy(path):
    root=ET.parse(path).getroot(); ns='{http://www.w3.org/2000/svg}'; out={}
    for r in root.findall('.//'+ns+'rect'):
        if r.attrib.get('id') in ('A','B'):
            out[r.attrib['id']]=(float(r.attrib['x']), float(r.attrib['y']))
    return out

def main():
    p=argparse.ArgumentParser(); p.add_argument('--schedule',required=True); p.add_argument('--results',required=True); p.add_argument('--prereg',required=True); p.add_argument('--src-root',required=True); p.add_argument('--out',required=True); a=p.parse_args()
    schedule=json.load(open(a.schedule)); prereg=json.load(open(a.prereg)); root=Path(a.results); src=Path(a.src_root)
    errors=[]; rows=[]; guard_hashes=set(); strata={}
    for name,expected in prereg['source_sha256'].items():
        actual=sha256(src/name)
        if actual!=expected: errors.append(f'source_hash:{name}:{actual}')
    if len(schedule['cases'])!=16: errors.append(f'schedule_count:{len(schedule["cases"])}')
    seen=set()
    for exp in schedule['cases']:
        cid=exp['case_id']; d=root/cid
        if cid in seen: errors.append(f'{cid}:duplicate_schedule')
        seen.add(cid)
        try:
            r=json.load(open(d/'result.json'))
            if r.get('context')!=exp['context'] or r.get('policy')!=exp['policy']:
                errors.append(f'{cid}:identity')
            counts,rgb_sha=guard_recompute(d/'guard_roi.png'); guard_hashes.add(rgb_sha)
            if counts!=EXPECTED_COUNTS: errors.append(f'{cid}:guard_counts:{counts}')
            if rgb_sha!=EXPECTED_GUARD_SHA: errors.append(f'{cid}:guard_hash:{rgb_sha}')
            if r.get('guard',{}).get('dark_pixels')!=counts: errors.append(f'{cid}:guard_claim_counts')
            if r.get('guard',{}).get('rgb_sha256')!=rgb_sha: errors.append(f'{cid}:guard_claim_hash')
            xy=svg_xy(d/'fixture.svg')
            ax,bx=xy['A'][0],xy['B'][0]
            receipts=r.get('action_receipts',[])
            stable=exp['context']=='stable'; hist=exp['policy']=='history_invalidate'
            if stable:
                expected_decision='ADMIT'; expected_effect=True; expected_xy=(60.0,220.0); expected_receipts=0; expected_semantic=True
            elif hist:
                expected_decision='STOP_HISTORY_INVALIDATED'; expected_effect=False; expected_xy=(50.0,220.0); expected_receipts=1; expected_semantic=True
            else:
                expected_decision='ADMIT'; expected_effect=True; expected_xy=(50.0,230.0); expected_receipts=1; expected_semantic=False
            if r.get('decision')!=expected_decision: errors.append(f'{cid}:decision:{r.get("decision")}')
            if bool(r.get('effect_input_sent'))!=expected_effect: errors.append(f'{cid}:effect_input')
            if abs(ax-expected_xy[0])>1e-9 or abs(bx-expected_xy[1])>1e-9: errors.append(f'{cid}:svg_xy:{ax}:{bx}')
            if len(receipts)!=expected_receipts: errors.append(f'{cid}:receipt_count:{len(receipts)}')
            if bool(r.get('semantic_correct'))!=expected_semantic: errors.append(f'{cid}:semantic_correct')
            if not stable:
                if len(receipts)==1:
                    q=receipts[0]
                    rv=r['timestamps']['revalidate_end_ns']; gs=r['timestamps']['guard_start_ns']
                    if q.get('kind')!='selection_navigation' or q.get('key')!='Tab': errors.append(f'{cid}:receipt_kind')
                    if not (rv < q['start_ns'] <= q['end_ns'] < gs): errors.append(f'{cid}:receipt_order')
                if r.get('relevant_history_count')!=1: errors.append(f'{cid}:relevant_history_count')
            else:
                if r.get('relevant_history_count')!=0: errors.append(f'{cid}:stable_history_count')
            if any(bool(v) for v in r.get('keys_down',{}).values()) or not r.get('all_relevant_keys_empty') or not r.get('button_empty'):
                errors.append(f'{cid}:release')
            if not r.get('revalidation',{}).get('success'): errors.append(f'{cid}:revalidation')
            key=f"{exp['context']}|{exp['policy']}"; strata.setdefault(key,{'n':0,'expected_ok':0}); strata[key]['n']+=1
            expected_ok=(r.get('decision')==expected_decision and abs(ax-expected_xy[0])<=1e-9 and abs(bx-expected_xy[1])<=1e-9)
            strata[key]['expected_ok']+=int(expected_ok)
            rows.append({'case_id':cid,'context':exp['context'],'policy':exp['policy'],'decision':r.get('decision'),'A_x':ax,'B_x':bx,'guard_rgb_sha256':rgb_sha,'guard_counts':counts,'receipt_count':len(receipts),'release_ok':not any(bool(v) for v in r.get('keys_down',{}).values()) and bool(r.get('button_empty'))})
        except Exception as e:
            errors.append(f'{cid}:exception:{type(e).__name__}:{e}')
    for k in ['stable|current_guard_only','self_switch|current_guard_only','stable|history_invalidate','self_switch|history_invalidate']:
        if strata.get(k,{}).get('n')!=4 or strata.get(k,{}).get('expected_ok')!=4: errors.append(f'stratum:{k}:{strata.get(k)}')
    if guard_hashes != {EXPECTED_GUARD_SHA}: errors.append(f'unique_guard_hashes:{sorted(guard_hashes)}')
    decision='PASS_SELF_ACTION_HISTORY_INVALIDATION_SCOPED' if not errors else 'FAIL_INTEGRITY_OR_GATE'
    out={'decision':decision,'errors':errors,'rows':rows,'strata':strata,'unique_guard_rgb_hashes':sorted(guard_hashes),'expected_guard_counts':EXPECTED_COUNTS}
    Path(a.out).write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'decision':decision,'error_count':len(errors),'strata':strata,'unique_guard_rgb_hashes':sorted(guard_hashes)},sort_keys=True))
    raise SystemExit(0 if not errors else 1)
if __name__=='__main__': main()
