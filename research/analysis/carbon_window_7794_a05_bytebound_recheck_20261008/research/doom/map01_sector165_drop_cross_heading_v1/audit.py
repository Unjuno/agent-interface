"""Independent cross-heading audit; pixel metric comes from exact #733 audit bytes."""
from pathlib import Path
import argparse,json,statistics,sys
import base_audit as inherited

def main():
    p=argparse.ArgumentParser();p.add_argument('root');p.add_argument('--plan',required=True);p.add_argument('--prereg',required=True);a=p.parse_args()
    root=Path(a.root);plan=json.loads(Path(a.plan).read_text());pre=json.loads(Path(a.prereg).read_text())
    errors=[];rows=[]
    for name,h in pre['source_sha256'].items():
        if inherited.sha(Path(a.prereg).parent/name)!=h:errors.append('source_hash:'+name)
    for c in plan['cases']:
        d=root/c['id']
        try:
            score=json.loads((d/'score.json').read_text());cr=json.loads((d/'controller/result.json').read_text())
            n,med,status=inherited.metric(d/'pre.png',d/'controller/post.png')
            owners=json.loads((d/'controller/owner-records.json').read_text())
            release=all(r.get('verified') and not r.get('keys_down') and not r.get('buttons_down') for r in owners if r.get('event')=='owner_release')
            if score.get('error') is not None or score.get('controller_returncode')!=0:errors.append(c['id']+':case_error')
            if (n,med,status)!=(cr.get('valid_tracks'),cr.get('median_dy_px'),cr.get('status')):errors.append(c['id']+':metric')
            if not release or not score.get('setup_release_ok'):errors.append(c['id']+':release')
            hidden=score.get('hidden_effect');expected='DROP' if c['class']=='drop' else 'NO_DROP'
            if hidden!=expected:errors.append(c['id']+':fixture_effect')
            alignment=score.get('setup_alignment',{})
            requested=c.get('heading');actual=alignment.get('actual_heading');herr=alignment.get('heading_error')
            if c['class']=='drop':
                if alignment.get('requested_heading')!=requested:errors.append(c['id']+':requested_heading')
                if actual is None or herr is None or abs(float(herr))>=plan['heading_tolerance_deg']:errors.append(c['id']+':heading')
            if c['class']=='wall' and status=='DROP_COMPLETED':errors.append(c['id']+':false_drop')
            rows.append(dict(id=c['id'],class_=c['class'],seed=c['seed'],requested_heading=requested,
                             actual_heading=actual,heading_error=herr,valid_tracks=n,median_dy_px=med,
                             pixel_status=status,hidden_effect=hidden,release_ok=release))
        except Exception as e:errors.append(c['id']+':'+repr(e))
    positives=[r for r in rows if r['class_']=='drop'];walls=[r for r in rows if r['class_']=='wall']
    medians=[]
    for heading in plan['heading_groups_deg']:
        vals=[r['actual_heading'] for r in positives if r['requested_heading']==heading and r['actual_heading'] is not None]
        if len(vals)==2:medians.append([heading,float(statistics.median(vals))])
    span=(max(v for _,v in medians)-min(v for _,v in medians)) if len(medians)==3 else None
    if span is None or span<plan['minimum_heading_span_deg']: errors.append('heading_diversity')
    false=sum(r['pixel_status']=='DROP_COMPLETED' for r in walls)
    misses=sum(r['pixel_status']!='DROP_COMPLETED' for r in positives)
    if errors:decision='FAIL_INTEGRITY'
    elif false:decision='FAIL_FALSE_DROP_EFFECT'
    elif misses:decision='HOLD_PIXEL_DROP_VIEW_DEPENDENT'
    elif len(positives)==6:decision='PASS_PIXEL_DROP_CROSS_HEADING_SCOPED'
    else:decision='FAIL_INTEGRITY'
    out={'schema':'agent-interface/map01-sector165-drop-cross-heading-audit-v1','status':'PASS_AUDIT' if not errors else 'FAIL_AUDIT','scientific_decision':decision,
         'errors':errors,'positive_misses':int(misses),'wall_false_positives':int(false),'heading_group_medians':medians,'heading_span_deg':span,'rows':rows}
    print(json.dumps(out,indent=2,sort_keys=True));sys.exit(0 if not errors else 2)
if __name__=='__main__':main()
