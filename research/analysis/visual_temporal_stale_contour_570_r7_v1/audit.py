from __future__ import annotations
import argparse,base64,hashlib,json,math
from pathlib import Path
MODEL='qwen2.5vl:3b'; DIGEST='fb90415cde1ef08aa669ae74b082d49b158729b6db1ab183c941417d507e71a1'
ARMS=['CURRENT_RAW','PAIRED_HISTORY','STALE_CONTOUR']
def sha(b): return hashlib.sha256(b).hexdigest()
def map_box(box,m):
    if box is None:return None
    if not isinstance(box,list) or len(box)!=4 or not all(type(x) in (int,float) for x in box):return None
    if m['kind']=='current_right_pane_scaled':
        return [round((box[0]-640)*2),round((box[1]-40)*800/760),round((box[2]-640)*2),round((box[3]-40)*800/760)]
    return [round(x) for x in box]
def iou(a,b):
    if a is None or b is None:return 0.0
    x1=max(a[0],b[0]); y1=max(a[1],b[1]); x2=min(a[2],b[2]); y2=min(a[3],b[3]); inter=max(0,x2-x1)*max(0,y2-y1)
    area_a=max(0,a[2]-a[0])*max(0,a[3]-a[1]); area_b=max(0,b[2]-b[0])*max(0,b[3]-b[1]); return inter/(area_a+area_b-inter) if area_a+area_b>inter else 0
def center_error(a,b):
    if a is None or b is None:return None
    dx=(a[0]+a[2]-b[0]-b[2])/2; dy=(a[1]+a[3]-b[1]-b[3])/2
    return math.hypot(dx,dy)/math.hypot(1280,800)
def expected_mapping(c):
    if c['arm']=='CURRENT_RAW': return {'kind':'identity'}
    if c['arm']=='PAIRED_HISTORY': return {'kind':'current_right_pane_scaled','pane':[640,40,1280,800],'scale':[2.0,800/760]}
    return {'kind':'stale_contour_identity','old_target_box':c['stale_box'],'outline_color':'#e04b32'}
def verify_freeze_and_manifest(root,errors):
    try:
        freeze=json.loads((root/'FREEZE.json').read_text(encoding='utf-8'))
        side=(root/'FREEZE.sha256').read_text(encoding='utf-8').split()[0]
        if side!=sha((root/'FREEZE.json').read_bytes()): errors.append('freeze_sidecar_hash')
        if freeze.get('pref_sha256')!=sha((root/'data/PREFORMAL.json').read_bytes()): errors.append('freeze_pref_hash')
        for name,digest in freeze.get('source_sha256',{}).items():
            if sha((root/name).read_bytes())!=digest: errors.append('freeze_source_hash:'+name)
        manifest_path=root/'EVIDENCE_MANIFEST.json'
        if sha(manifest_path.read_bytes())!=freeze.get('evidence_manifest_sha256'): errors.append('evidence_manifest_digest')
        manifest=json.loads(manifest_path.read_text(encoding='utf-8'))
        for item in manifest.get('artifacts',[]):
            f=root/item['path']
            if not f.is_file() or sha(f.read_bytes())!=item['sha256']: errors.append('manifest_artifact_hash:'+item['path'])
    except Exception: errors.append('freeze_or_manifest_missing_or_invalid')
def audit(root,out):
    pre=json.loads((root/'data/PREFORMAL.json').read_text(encoding='utf-8')); errors=[]; rows=[]; samples=[]
    if (root/'FREEZE.json').is_file() and (root/'EVIDENCE_MANIFEST.json').is_file(): verify_freeze_and_manifest(root,errors)
    try: samples=[json.loads(x) for x in (root/'evidence/sampler.jsonl').read_text(encoding='utf-8').splitlines() if x.strip()]
    except Exception: errors.append('sampler_missing_or_invalid')
    try: baseline=json.loads((root/'evidence/baseline.json').read_text(encoding='utf-8'))
    except Exception: baseline={}; errors.append('baseline_missing')
    status={}
    try: status=json.loads((root/'evidence/RUN_STATUS.json').read_text(encoding='utf-8'))
    except Exception: errors.append('run_status_missing_or_invalid')
    if status and (status.get('completed_calls')!=36 or status.get('expected_calls')!=36 or status.get('failure') is not None or status.get('retries')!=0): errors.append('run_status_contract')
    try:
        callfiles=list((root/'evidence/formal').glob('*.json'))
        if len(callfiles)!=36: errors.append('raw_call_file_count')
    except Exception: errors.append('raw_call_directory')
    for c in pre['formal_cases']:
        f=root/'evidence/formal'/(c['case_id']+'.json')
        if not f.is_file(): errors.append('missing:'+c['case_id']); continue
        r=json.loads(f.read_text(encoding='utf-8')); img=(root/'data'/c['presentation_path']).read_bytes(); cur=(root/'data'/c['current_path']).read_bytes(); prior=(root/'data'/c['prior_path']).read_bytes()
        if sha(img)!=c['presentation_sha256'] or r.get('image_sha256')!=c['presentation_sha256']: errors.append('presentation_hash:'+c['case_id'])
        if sha(cur)!=c['current_sha256'] or r.get('current_sha256')!=c['current_sha256'] or sha(prior)!=c['prior_sha256'] or r.get('prior_sha256')!=c['prior_sha256']: errors.append('source_hash:'+c['case_id'])
        if r.get('model')!=MODEL or r.get('expected_digest')!=DIGEST or r.get('prompt_sha256')!=pre['prompt_sha256']: errors.append('identity:'+c['case_id'])
        if c.get('mapping')!=expected_mapping(c): errors.append('mapping_contract:'+c['case_id'])
        q=r.get('request',{}); opts=q.get('options',{})
        if q.get('model')!=MODEL or q.get('stream') is not False or opts!={'temperature':0,'seed':c['seed'],'num_predict':128}: errors.append('request_contract:'+c['case_id'])
        if q.get('messages',[{}])[0].get('content')!=pre['prompt'] or q.get('messages',[{}])[0].get('images')!=[base64.b64encode(img).decode('ascii')]: errors.append('request_binding:'+c['case_id'])
        rqhash=sha(json.dumps(q,sort_keys=True,separators=(',',':')).encode())
        if rqhash!=r.get('request_sha256'): errors.append('request_hash:'+c['case_id'])
        start,end=r.get('started_utc_ns',0),r.get('ended_utc_ns',0)
        if end<=start or start<=0: errors.append('call_interval:'+c['case_id'])
        overlap=[s for s in samples if start<=s.get('utc_ns',-1)<=end and isinstance(s.get('memory_used_mib'),int) and s['memory_used_mib']>baseline.get('memory_used_mib',0) and 'GPU' in s.get('ollama_ps_stdout','')]
        if not overlap: errors.append('gpu_overlap:'+c['case_id'])
        output=None
        try:
            payload=json.loads(r['response']['message']['content']); present=payload['present']; box=payload['box']
            if type(present) is not bool or (present and box is None) or (not present and box is not None): raise ValueError('schema')
            output=map_box(box,c['mapping']) if present else None
            if present and output is None: raise ValueError('box')
            if present and (output[0]<0 or output[1]<0 or output[2]>1280 or output[3]>800 or output[0]>=output[2] or output[1]>=output[3]): raise ValueError('bounds')
        except Exception: errors.append('response_schema:'+c['case_id']); present=False
        target=c['target_box']; hit=bool(c['present'] and present and iou(output,target)>=.5)
        abstain=bool(not c['present'] and not present and output is None)
        old=c['stale_box']; stale=bool(c['present'] and present and old is not None and iou(output,old)>=.5)
        dist=center_error(output,target) if c['present'] and present else (1.0 if c['present'] else None)
        rows.append({'case_id':c['case_id'],'source_case_id':c['source_case_id'],'arm':c['arm'],'present':c['present'],'hit':hit,'abstain':abstain,
            'stale_location_selection':stale,'iou':iou(output,target) if c['present'] and present else None,'normalized_center_error':dist,'source_box':output,'target_box':target,'stale_box':old,'gpu_samples':len(overlap)})
    metrics={}
    for arm in ARMS:
        group=[r for r in rows if r['arm']==arm]; pos=[r for r in group if r['present']]; neg=[r for r in group if not r['present']]
        metrics[arm]={'positive_hits':sum(r['hit'] for r in pos),'positive_total':len(pos),'absent_abstentions':sum(r['abstain'] for r in neg),'absent_total':len(neg),
            'stale_location_selections':sum(r['stale_location_selection'] for r in pos),'mean_normalized_center_error':sum(r['normalized_center_error'] for r in pos)/len(pos) if pos else None}
    complete=len(rows)==36 and all(metrics[a]['positive_total']==10 and metrics[a]['absent_total']==2 for a in ARMS)
    raw=metrics['CURRENT_RAW']; pair=metrics['PAIRED_HISTORY']; stale=metrics['STALE_CONTOUR']
    pair_pass=pair['positive_hits']>=raw['positive_hits'] and pair['absent_abstentions']>=raw['absent_abstentions'] and raw['mean_normalized_center_error']-pair['mean_normalized_center_error']>=.05
    stale_fail=stale['stale_location_selections']-raw['stale_location_selections']>=2 or any(r['arm']=='STALE_CONTOUR' and not r['present'] and not r['abstain'] for r in rows)
    decision='HOLD_AUDIT_OR_GPU' if errors or not complete else ('PASS_TEMPORAL_HELP_SCOPED' if pair_pass else 'REJECT_NO_TEMPORAL_GAIN')
    if stale_fail: decision += '+FAIL_STALE_CONTOUR_MISDIRECTION'
    return {'schema':'visual-temporal-570-r7-independent-audit-v1','allocation':pre['allocation'],'decision':decision,'errors':errors,'complete':complete,'model_calls':len(rows),'gpu_samples_total':sum(r['gpu_samples'] for r in rows),'arms':metrics,'rows':rows}
def audit_inputs(root):
    pre=json.loads((root/'data/PREFORMAL.json').read_text(encoding='utf-8')); errors=[]; cases=pre.get('formal_cases',[])
    if pre.get('prompt_sha256')!=sha(pre.get('prompt','').encode()): errors.append('prompt_hash')
    if (root/'FREEZE.json').is_file() and (root/'EVIDENCE_MANIFEST.json').is_file(): verify_freeze_and_manifest(root,errors)
    if pre.get('allocation')!='visual-temporal-570-stale-contour-r7-20260927-01' or len(cases)!=36: errors.append('denominator_or_allocation')
    grouped={}
    for c in cases:
        cid=c.get('source_case_id'); grouped.setdefault(cid,[]).append(c)
        for key,field in [('prior_path','prior_sha256'),('current_path','current_sha256'),('presentation_path','presentation_sha256')]:
            f=root/'data'/c[key]
            if not f.is_file() or sha(f.read_bytes())!=c[field]: errors.append('hash:'+str(c.get('case_id'))+':'+key)
        if c.get('mapping',{}).get('kind') not in ('identity','current_right_pane_scaled','stale_contour_identity'): errors.append('mapping_kind:'+str(c.get('case_id')))
        if c.get('mapping')!=expected_mapping(c): errors.append('mapping_contract:'+str(c.get('case_id')))
        if c['arm']=='STALE_CONTOUR' and (c['stale_box'] is None or (c['present'] and c['stale_box']==c['target_box'])): errors.append('stale_target_geometry:'+c['case_id'])
        if c['arm']=='CURRENT_RAW' and (root/'data'/c['presentation_path']).read_bytes()!=(root/'data'/c['current_path']).read_bytes(): errors.append('raw_not_current:'+c['case_id'])
    if len(grouped)!=12 or any(sorted(x['arm'] for x in g)!=sorted(ARMS) for g in grouped.values()): errors.append('case_arm_completeness')
    if sum(1 for g in grouped.values() if g[0]['present'])!=10 or sum(1 for g in grouped.values() if not g[0]['present'])!=2: errors.append('class_balance')
    cs=pre.get('construction_cases',[])
    if len(cs)!=2 or {c['seed'] for c in cs}&{c['seed'] for g in grouped.values() for c in g}: errors.append('construction_overlap')
    for c in cs:
        for side in ('prior','current'):
            f=root/'data'/f"{c['case_id']}-{side}.png"
            if not f.is_file() or sha(f.read_bytes())!=c[side+'_sha256']: errors.append('construction_hash:'+c['case_id']+':'+side)
    return {'schema':'visual-temporal-570-r7-input-audit-v1','formal_sources':len(grouped),'formal_present':sum(1 for g in grouped.values() if g[0]['present']),
        'formal_absent':sum(1 for g in grouped.values() if not g[0]['present']),'formal_presentations':len(cases),'construction_pairs':len(cs),'construction_model_calls':0,
        'errors':errors,'decision':'INPUT_AUDIT_PASS' if not errors else 'STOP_INPUT_OR_MAPPING'}
def main():
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--inputs-only',action='store_true');a=p.parse_args();r=audit_inputs(a.root) if a.inputs_only else audit(a.root,a.out);a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(r,indent=2,sort_keys=True)+'\n',encoding='utf-8');print(json.dumps({'decision':r['decision'],'errors':r['errors'],'calls':r.get('model_calls',0),'arms':r.get('arms',{})},sort_keys=True))
if __name__=='__main__':main()
