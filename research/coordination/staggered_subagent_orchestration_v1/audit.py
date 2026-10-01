import json, pathlib, sys
def main(root):
 d=json.loads((pathlib.Path(root)/'RAW.json').read_text()); rows=d['rows']; assert len(rows)==24
 cond=[r for r in rows if r['policy']=='CONDITION_STAGGER']
 assert not any(r['unsafe'] for r in cond)
 assert any(r['policy']=='IMMEDIATE' and r['unsafe'] for r in rows)
 assert any(r['policy']=='FIXED_STAGGER' and r['unsafe'] for r in rows)
 assert any(r['scenario']=='independent_read' and r['policy']=='CONDITION_STAGGER' and r['start']=='allowed' for r in rows)
 print('PASS_AUDIT rows=24 condition_unsafe=0 immediate_witness=1 fixed_witness=1 independent_parallel=1')
if __name__=='__main__': main(sys.argv[1])
