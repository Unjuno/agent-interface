import argparse, json, shutil, tempfile
from pathlib import Path
from audit import audit

MUTS=['stale_reuse','expired_reuse','stale_active_run','tardy_active_run','rebuild_run','wrong_p','wrong_g','wrong_version','missing_case','publish_after_cancel','missing_partial','wrong_deadline']

def mutate(root,kind):
    files=sorted(Path(root).glob('batch-*/*/result.json'))
    if kind=='missing_case': files[-1].unlink(); return
    target=files[0]
    if kind in ('stale_active_run','tardy_active_run','wrong_p','wrong_g','wrong_version','publish_after_cancel','missing_partial','wrong_deadline'):
        target=next(f for f in files if 'active_' in f.name or 'active_' in str(f.parent))
    if kind=='rebuild_run': target=next(f for f in files if 'rebuild_' in str(f.parent))
    r=json.loads(target.read_text()); d=r['decisions'][0]
    if kind=='stale_reuse': d['current_versions']=[99]; d['disposition']='REUSE'
    elif kind=='expired_reuse': d['deadline_ns']=d['t_ns']-1; d['disposition']='REUSE'
    elif kind=='stale_active_run': d['current_versions']=[99]; d['disposition']='RUN'
    elif kind=='tardy_active_run': d['deadline_ns']=d['t_ns']; d['remaining_cost_ns']=1; d['disposition']='RUN'
    elif kind=='rebuild_run': d['disposition']='RUN'
    elif kind=='wrong_p': d['p_num']=d.get('p_den',4)+1
    elif kind=='wrong_g': d['g_ns']=int(d.get('g_ns',0))+999999999
    elif kind=='wrong_version': d['source_versions']=[123]
    elif kind=='publish_after_cancel': r['published_reusable']=True
    elif kind=='missing_partial':
        target=next(f for f in files if 'active_partial_cancel' in str(f.parent)); r=json.loads(target.read_text()); r['partial_result']=False
    elif kind=='wrong_deadline': d['deadline_ns']=0
    target.write_text(json.dumps(r,sort_keys=True,indent=2)+'\n')

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('root'); a=ap.parse_args(); results=[]
    for k in MUTS:
        td=Path(tempfile.mkdtemp(prefix='ec2766-mut-')); dst=td/'copy'; shutil.copytree(a.root,dst); mutate(dst,k); r=audit(dst); results.append({'mutation':k,'rejected':bool(r['errors']),'errors':r['errors'][:3]}); shutil.rmtree(td)
    out={'controls':len(results),'rejected':sum(x['rejected'] for x in results),'results':results}; print(json.dumps(out,sort_keys=True,indent=2)); raise SystemExit(0 if out['rejected']==len(results) else 1)
if __name__=='__main__': main()
