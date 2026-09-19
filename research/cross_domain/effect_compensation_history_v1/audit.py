from __future__ import annotations
import argparse, json, sqlite3
from pathlib import Path

def audit_case(d: Path):
    r=json.loads((d/'result.json').read_text()); db=d/'effect.sqlite'; c=sqlite3.connect(db)
    final=c.execute('SELECT value FROM state WHERE id=1').fetchone()[0]
    ev=[(x[0],x[1],x[2],x[3]) for x in c.execute('SELECT seq,kind,value,ns FROM events ORDER BY seq')]
    integ=c.execute('PRAGMA integrity_check').fetchone()[0]; c.close()
    s=r['scenario']
    exp_events={'correct':[('effect','target')], 'wrong_compensated':[('effect','wrong'),('compensation','old')], 'wrong_uncompensated':[('effect','wrong')]}[s]
    got=[(x[1],x[2]) for x in ev]
    exp_final={'correct':'target','wrong_compensated':'old','wrong_uncompensated':'wrong'}[s]
    exp_phase={'correct':'EFFECT_VERIFIED','wrong_compensated':'EFFECT_CONTRADICTED_COMPENSATED','wrong_uncompensated':'EFFECT_CONTRADICTED_UNCOMPENSATED'}[s]
    exp_final_only={'correct':'VERIFIED','wrong_compensated':'NO_EFFECT','wrong_uncompensated':'CONTRADICTED'}[s]
    checks={'integrity':integ=='ok','final':final==exp_final,'events':got==exp_events,'phase':r['phase_result']==exp_phase,
            'final_only':r['final_state_only_result']==exp_final_only,'timestamps':isinstance(r['started_ns'],int) and isinstance(r['finished_ns'],int) and r['started_ns']<=r['finished_ns']}
    return {'id':r['id'],'scenario':s,'checks':checks,'pass':all(checks.values()),'final':final,'events':got,
            'phase_result':r['phase_result'],'final_state_only_result':r['final_state_only_result'],
            'final_only_truthful': not (s=='wrong_compensated' and r['final_state_only_result']=='NO_EFFECT')}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('root',type=Path); a=ap.parse_args()
    rows=[]
    for d in sorted(a.root.iterdir()):
        if d.is_dir() and (d/'result.json').exists(): rows.append(audit_case(d))
    out={'rows':rows,'all_pass':all(x['pass'] for x in rows),'count':len(rows),
         'phase_truth_count':sum(x['pass'] for x in rows),
         'final_only_truthful_count':sum(x['final_only_truthful'] for x in rows)}
    print(json.dumps(out,indent=2,sort_keys=True))
if __name__=='__main__': main()
