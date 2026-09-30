import argparse,copy,json,pathlib,shutil,sqlite3,subprocess,sys,tempfile

def run_audit(audit_py,root):
    cp=subprocess.run([sys.executable,str(audit_py),str(root)],capture_output=True,text=True)
    return cp.returncode,cp.stdout,cp.stderr

def mutate(name,root):
    rawp=root/'RAW.json'; raw=json.loads(rawp.read_text()); rows=raw['rows']
    if name=='remove_case':
        shutil.rmtree(root/rows[0]['case_id'])
    elif name=='raw_delete_row':
        raw['rows']=rows[1:]; raw['case_count']=len(raw['rows']); rawp.write_text(json.dumps(raw,indent=2,sort_keys=True))
    elif name=='flip_accepted':
        row=next(x for x in rows if x['accepted'] is False); cid=row['case_id']; row['accepted']=True
        rawp.write_text(json.dumps(raw,indent=2,sort_keys=True)); cp=root/cid/'CASE.json'; c=json.loads(cp.read_text()); c['accepted']=True; cp.write_text(json.dumps(c,indent=2,sort_keys=True))
    elif name=='delete_effect':
        row=next(x for x in rows if x['accepted'] is True); db=root/row['case_id']/'case.db'; c=sqlite3.connect(db); c.execute('delete from effects'); c.commit(); c.close()
    elif name=='bool_exit':
        cid=rows[0]['case_id']; ep=root/cid/'EXIT.json'; e=json.loads(ep.read_text()); e['returncode']=True; ep.write_text(json.dumps(e,indent=2))
    elif name=='wrong_deps':
        row=next(x for x in rows if x['policy']=='SCHEMA_SCOPED_REPLACE' and x['target']=='b'); cid=row['case_id']; row['deps']=['a']; row['prepared_revisions']={'a':1}; row['current_revisions_at_validation']={'a':1}; rawp.write_text(json.dumps(raw,indent=2,sort_keys=True)); cp=root/cid/'CASE.json'; c=json.loads(cp.read_text()); c['deps']=['a']; c['prepared_revisions']={'a':1}; c['current_revisions_at_validation']={'a':1}; cp.write_text(json.dumps(c,indent=2,sort_keys=True))
    elif name=='wrong_callback':
        row=next(x for x in rows if x['target']=='b'); cid=row['case_id'];
        for ev in row['authorizer_events']:
            if ev.get('phase')=='final_prepare' and ev.get('table')=='b': ev['table']='a'; break
        rawp.write_text(json.dumps(raw,indent=2,sort_keys=True)); cp=root/cid/'CASE.json'; c=json.loads(cp.read_text());
        for ev in c['authorizer_events']:
            if ev.get('phase')=='final_prepare' and ev.get('table')=='b': ev['table']='a'; break
        cp.write_text(json.dumps(c,indent=2,sort_keys=True))
    elif name=='source_bytes':
        p=root/'source_snapshot'/'study.py'; p.write_bytes(p.read_bytes()+b'\n# mutation\n')
    else: raise ValueError(name)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('root'); ap.add_argument('--audit',required=True); ap.add_argument('--out',required=True); a=ap.parse_args()
    root=pathlib.Path(a.root); audit=pathlib.Path(a.audit)
    names=['remove_case','raw_delete_row','flip_accepted','delete_effect','bool_exit','wrong_deps','wrong_callback','source_bytes']
    results=[]
    for name in names:
        with tempfile.TemporaryDirectory(prefix='sqlread-corrupt-') as td:
            dst=pathlib.Path(td)/'evidence'; shutil.copytree(root,dst); mutate(name,dst); rc,so,se=run_audit(audit,dst); results.append({'name':name,'rejected':rc!=0,'audit_exit':rc,'stdout_tail':so[-1000:],'stderr':se[-500:]})
    out={'controls':results,'pass':all(x['rejected'] for x in results)}; pathlib.Path(a.out).write_text(json.dumps(out,indent=2,sort_keys=True)); print(json.dumps(out,indent=2,sort_keys=True)); raise SystemExit(0 if out['pass'] else 1)
if __name__=='__main__': main()
