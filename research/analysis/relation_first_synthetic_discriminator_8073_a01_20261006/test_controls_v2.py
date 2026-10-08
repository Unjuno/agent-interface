import json,tempfile,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).parent
if len(sys.argv)!=3:
    raise SystemExit('usage: test_controls_v2.py RESULT_JSON CONTROLS_JSON')
result_path=Path(sys.argv[1])
controls_path=Path(sys.argv[2])
base=json.loads(result_path.read_text())
controls=[]
def run(name,mut):
    with tempfile.TemporaryDirectory() as td:
        p=Path(td)/'r.json'; a=Path(td)/'a.json'; p.write_text(json.dumps(mut))
        q=subprocess.run([sys.executable,str(ROOT/'audit.py'),str(ROOT/'corpus.json'),str(p),str(a)],capture_output=True,text=True)
        controls.append({'name':name,'rejected':q.returncode!=0})
m=json.loads(json.dumps(base)); m['rows'][0]['relation_first']['top3'][0]='S2'; run('relation_rank',m)
m=json.loads(json.dumps(base)); m['rows'][1]['relation_first']['valid']=0; run('valid_count',m)
m=json.loads(json.dumps(base)); m['rows'][2]['keyword_first']['decoys']=0; run('decoy_count',m)
m=json.loads(json.dumps(base)); m['rows'][3]['relation_first']['seeded_positive']=0; run('positive_count',m)
m=json.loads(json.dumps(base)); m['rows']=m['rows'][:-1]; run('missing_row',m)
m=json.loads(json.dumps(base)); m['rows'][0]['target']='BAD'; run('target_id',m)
m=json.loads(json.dumps(base)); m['authority']=True; run('authority',m)
m=json.loads(json.dumps(base)); m['totals']['relation_first']['valid']=0; run('total_valid',m)
m=json.loads(json.dumps(base)); m['totals']['relation_first']['decoys']=99; run('total_decoy',m)
m=json.loads(json.dumps(base)); m['totals']['keyword_first']['seeded_positive']=8; run('keyword_positive',m)
out={'controls':controls,'all_rejected':all(x['rejected'] for x in controls)}
controls_path.parent.mkdir(parents=True,exist_ok=True)
controls_path.write_text(json.dumps(out,sort_keys=True,indent=2)+'\n')
raise SystemExit(0 if out['all_rejected'] else 1)
