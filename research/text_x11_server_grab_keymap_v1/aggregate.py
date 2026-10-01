#!/usr/bin/env python3
import argparse,json
from pathlib import Path
SCHEDULE=[('us','us0'),('de','de0'),('fr','fr0'),('fr','fr1'),('de','de1'),('us','us1'),('de','de2'),('fr','fr2'),('fr','fr3'),('de','de3'),('de','de4'),('fr','fr4')]
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();rows=[]
 for layout,sid in SCHEDULE:
  p=a.root/sid/'report.json'
  if not p.exists():raise SystemExit('missing '+str(p))
  r=json.loads(p.read_text())
  if r['layout']!=layout or r['session_id']!=sid:raise SystemExit('identity mismatch '+sid)
  rows.append(r)
 changed=[r for r in rows if r['changed']];wrong=[r for r in changed if r['final_text']!='@'];pre_effect=[r for r in rows if r['pre_ungrab']['shadow'] or r['pre_ungrab']['events']]
 all_mechanics=all(r['mechanics_pass'] and r['passed'] for r in rows)
 if not all_mechanics: disposition='INFRA_FAIL'
 elif not pre_effect and wrong: disposition='SEMANTIC_SERIALIZATION_FAIL'
 elif not pre_effect: disposition='HOLD_NO_PREUNGRAB_SEMANTIC_ACK'
 elif all(r['final_text']=='@' for r in changed): disposition='SEMANTIC_SERIALIZATION_PASS'
 else: disposition='SEMANTIC_SERIALIZATION_FAIL'
 out={'schema':'agent-interface/text-x11-server-grab-keymap-aggregate-v1','schedule':SCHEDULE,'session_count':len(rows),'changed_session_count':len(changed),'mechanics_pass':all_mechanics,'pre_ungrab_semantic_effect_count':len(pre_effect),'changed_exact_count':sum(r['final_text']=='@' for r in changed),'changed_wrong_count':len(wrong),'wrong_sessions':[{'session_id':r['session_id'],'layout':r['layout'],'final_text':r['final_text']} for r in wrong],'disposition':disposition,'sessions':rows}
 a.out.write_text(json.dumps(out,indent=2,ensure_ascii=False)+'\n');print(json.dumps({k:out[k] for k in ['session_count','mechanics_pass','pre_ungrab_semantic_effect_count','changed_exact_count','changed_wrong_count','wrong_sessions','disposition']},ensure_ascii=False,indent=2));return 0 if all_mechanics else 1
if __name__=='__main__':raise SystemExit(main())
