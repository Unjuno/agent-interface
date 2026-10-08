import copy,json,hashlib,shutil,tempfile
from pathlib import Path
import audit_all_v2 as A

def sha(b): return hashlib.sha256(b).hexdigest()
def remanifest(root):
    m={str(p.relative_to(root)):sha(p.read_bytes()) for p in sorted(root.rglob('*')) if p.is_file() and p.name not in ('manifest.json','audit_r3.json','audit_r4.json','audit_r2.json','audit.json')}
    (root/'manifest.json').write_text(json.dumps(m,sort_keys=True,indent=2)+'\n')
def attempt(name,src,mutate,audit):
    with tempfile.TemporaryDirectory() as td:
        dst=Path(td)/src.name;shutil.copytree(src,dst);mutate(dst);remanifest(dst)
        try:audit(dst)
        except Exception as e:return {'name':name,'rejected':True,'error_type':type(e).__name__,'error':str(e)[:300]}
        return {'name':name,'rejected':False}
def corrupt_r4(root):
    rows=[json.loads(x) for x in (root/'raw.jsonl').read_text().splitlines() if x.strip()]
    r=next(r for r in rows if r['mode']=='refreshed_token' and r['case']=='edit_A_before_arm' and r['effect_file'])
    p=root/r['effect_file'];o=json.loads(p.read_text());o['before']['active']='A';o['before']['docs']['A']={'value':0,'revision':0};p.write_text(json.dumps(o,sort_keys=True,indent=2)+'\n')
def corrupt_r3(root):
    rows=[json.loads(x) for x in (root/'raw.jsonl').read_text().splitlines() if x.strip()]
    idx=next(i for i,r in enumerate(rows) if r['mode']=='effect_atomic' and r['case']=='concurrent_edit_A')
    r=rows[idx];e=json.loads((root/r['effect_file']).read_text());r['transitions'][0]['ns']=e['mutated_ns']-1;rows[idx]=r;(root/'raw.jsonl').write_text('\n'.join(json.dumps(x,sort_keys=True) for x in rows)+'\n')
def main():
    base=Path(__file__).parent;res=[attempt('disguise_refreshed_stale_effect',base/'run-r4-a1',corrupt_r4,A.audit_r4),attempt('invert_atomic_linearization_order',base/'run-r3-a1',corrupt_r3,A.audit_r3)]
    if not all(x['rejected'] for x in res):raise SystemExit(res)
    (base/'corruption_check_result.json').write_text(json.dumps({'passed':True,'tests':res},sort_keys=True,indent=2)+'\n');print(json.dumps({'passed':True,'tests':res},indent=2))
if __name__=='__main__':main()
