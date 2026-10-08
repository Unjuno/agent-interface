"""Offline source/row/decision/effect audit; does not rerun a consumed GUI case."""
import argparse
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import statistics
from guard import Binding, select
HERE=Path(__file__).resolve().parent


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def check(ok,why):
    if not ok:raise AssertionError(why)


def audit(root):
    plan=json.loads((HERE/'plan.json').read_text());rows=[];files=0
    for n,h in plan['source_sha256'].items():check(sha(HERE/n)==h,'source: '+n)
    for seed in plan['seeds']:
        folder=root/str(seed);manifest=json.loads((folder/'manifest.json').read_text())
        for n,entry in manifest.items():
            p=folder/n;check(p.stat().st_size==entry['bytes'] and sha(p)==entry['sha256'],'artifact: '+n)
            files+=1
        block=[json.loads(x) for x in (folder/'raw.jsonl').read_text().splitlines()]
        check(len(block)==len(plan['cases'])*len(plan['methods']),'block count')
        for r in block:
            e=r['evidence'];binding=Binding(**e['binding'])
            check(r==json.loads((folder/(r['case']+'--'+r['method'])/'record.json').read_text()),'duplicate retention mismatch')
            for key in ('early','late'):
                obs=e[key]
                if obs is None:continue
                use_binding=None if r['method']=='current_semantic' else binding
                reason,n=select(obs['tree'],obs['document'],use_binding)
                if n is None:check(obs['point'] is None and obs['reason']==reason,'refusal replay')
                elif obs['point'] is not None:
                    check(obs['hit']['backendNodeId']==n['backendDOMNodeId'],'hit identity')
                    pts=obs['box']['model']['border']
                    check(obs['point']==[round(sum(pts[::2])/4),round(sum(pts[1::2])/4)],'geometry replay')
            last=e['late'] if e['late'] is not None else e['early']
            check(last['point']==r['point'] and last['reason']==r['reason'],'decision selection')
            check(e['transitions'][0]['end_ns']<=e['early']['start_ns'],'early order')
            check(e['early']['end_ns']<=e['transitions'][1]['start_ns'],'between order')
            if e['late']:
                check(e['transitions'][1]['end_ns']<=e['late']['start_ns'],'late order')
            check(last['end_ns']<=e['transitions'][2]['start_ns']<=r['image_clock']['start_ns'],'after order')
            event=r['event'];scores=r['scores']
            if event:
                check(r['point']==event['point'] and event['buttons_empty'] is True,'input/release')
                check(r['image_clock']['end_ns']<=event['start_ns']<=event['down_ack_ns']<=event['up_ack_ns'],'input clocks')
                if scores:
                    check(len(scores)==1 and scores[0]['trusted'] is True,'trusted effect')
                    check([scores[0]['x'],scores[0]['y']]==event['point'],'effect coordinates')
                outcome=scores[0]['hit'] if scores else 'no_event'
            else:
                check(not scores and r['point'] is None,'refusal input');outcome='abstain'
            check(r['outcome']==outcome,'outcome')
        rows.extend(block)
    keys={(r['case'],r['seed'],r['method']) for r in rows}
    check(len(keys)==len(rows)==162,'allocation coverage')
    summary={m:{k:sum(r['method']==m and r['outcome']==k for r in rows)
               for k in ['target','wrong','background','no_event','abstain']} for m in plan['methods']}
    for m in plan['methods']:
        summary[m]['selector_median_ms']=statistics.median(r['selector_us']/1000 for r in rows if r['method']==m)
    candidate=[r for r in rows if r['method']=='bound_final']
    scoped=all(r['outcome'] in ('target','abstain') for r in candidate if not r['boundary_negative'])
    for name in ['stable','move_before','other_scope','move_between']:
        scoped &= all(r['outcome']=='target' for r in candidate if r['case']==name)
    return {'audit_pass':True,'records':len(rows),'manifest_files':files,'summary':summary,
            'scoped_candidate_pass':scoped,'default_promotion':all(r['outcome']!='wrong' for r in candidate),
            'scope':'Retained local staged UI only. Backend identity != business identity. No atomicity.'}


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('root',type=Path);a=ap.parse_args()
    print(json.dumps(audit(a.root),indent=2))
