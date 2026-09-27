from __future__ import annotations
import argparse,hashlib,json,sqlite3
from pathlib import Path

def canon(o): return json.dumps(o,sort_keys=True,separators=(',',':')).encode()
def h(o): return hashlib.sha256(canon(o)).hexdigest()
def verify(req,p,co): return p==req['primary'] and ('collateral' not in req or co==req['collateral'])
def audit_case(d):
 r=json.loads((d/'result.json').read_text()); c=sqlite3.connect(d/'case.sqlite')
 p,co=c.execute('SELECT primary_value,collateral_value FROM state WHERE id=1').fetchone()
 cons=[{'gen':x[0],'hash':x[1],'receipt':json.loads(x[2]),'seq':x[3]} for x in c.execute('SELECT gen,receipt_hash,receipt_json,journal_seq FROM contracts ORDER BY gen')]
 journal=[{'seq':x[0],'kind':x[1],'payload':json.loads(x[2])} for x in c.execute('SELECT seq,kind,payload FROM journal ORDER BY seq')]
 integ=c.execute('PRAGMA integrity_check').fetchone()[0]; c.close()
 hashes=all(x['hash']==h(x['receipt']) for x in cons)
 effect_seq=next(x['seq'] for x in journal if x['kind']=='effect')
 active=max((x for x in cons if x['seq']<effect_seq),key=lambda x:x['gen'])
 latest=max(cons,key=lambda x:x['gen'])
 chosen=latest if r['policy']=='latest_contract' else active
 decision=verify(chosen['receipt']['requires'],p,co)
 truth=verify(active['receipt']['requires'],p,co)
 exp='COMPENSATION_COMPLETE' if decision else 'COMPENSATION_INCOMPLETE'
 checks={'integrity':integ=='ok','hashes':hashes,'state':(p,co)==(r['final_primary'],r['final_collateral']),
         'effect_binding':active['hash']==r['effect_contract']['hash'],'chosen':chosen['hash']==r['chosen_contract']['hash'],
         'outcome':r['outcome']==exp,'truth_field':r['ground_truth_complete']==truth,'correct_field':r['ground_truth_correct']==(decision==truth)}
 return {'id':r['id'],'scenario':r['scenario'],'policy':r['policy'],'pass':all(checks.values()),'checks':checks,
         'decision_complete':decision,'truth_complete':truth,'ground_truth_correct':decision==truth,
         'active_gen':active['gen'],'latest_gen':latest['gen'],'final':[p,co]}
def main():
 ap=argparse.ArgumentParser(); ap.add_argument('root',type=Path); a=ap.parse_args(); rows=[audit_case(d) for d in sorted(a.root.iterdir()) if d.is_dir() and (d/'result.json').exists()]
 print(json.dumps({'rows':rows,'count':len(rows),'all_integrity':all(x['pass'] for x in rows),'ground_truth_correct_count':sum(x['ground_truth_correct'] for x in rows)},indent=2,sort_keys=True))
if __name__=='__main__': main()
