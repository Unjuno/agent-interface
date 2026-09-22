import json,pathlib,subprocess,tempfile,shutil,sys
src=pathlib.Path(sys.argv[1]); aud=pathlib.Path(__file__).with_name('audit.py')
raw=json.loads((src/'RAW.json').read_text())
mut=[]
for name,fn in [
 ('drop',lambda x:x['rows'].pop()),
 ('dup',lambda x:x['rows'].__setitem__(1,x['rows'][0])),
 ('candidate',lambda x:x['rows'][0].__setitem__('candidate','LOCAL_TRUE')),
 ('oracle',lambda x:x['rows'][0].__setitem__('oracle','LOCAL_TRUE')),
 ('return_lineage',lambda x:(x['rows'][2].__setitem__('return_generation',x['rows'][2]['capture_generation']),x['rows'][2].__setitem__('return_window_id',x['rows'][2]['capture_window_id']))),
 ('capture_effect',lambda x:x['rows'][0].__setitem__('capture_effect',True)),
 ('timeout',lambda x:x['rows'][3].__setitem__('timeout_before',False)),
 ('expected_bytes',lambda x:x['rows'][5].__setitem__('expected_bytes',x['rows'][5]['expected_bytes']+1))]:
    td=pathlib.Path(tempfile.mkdtemp(prefix='o4mut2-')); shutil.copytree(src,td/'f'); x=json.loads(json.dumps(raw)); fn(x); (td/'f'/'RAW.json').write_text(json.dumps(x))
    p=subprocess.run([sys.executable,str(aud),str(td/'f')],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    mut.append((name,p.returncode!=0)); shutil.rmtree(td)
print(json.dumps({'version':'v2_postformal_readonly','controls':mut,'rejected':sum(v for _,v in mut),'total':len(mut)}));
raise SystemExit(0 if all(v for _,v in mut) else 1)
