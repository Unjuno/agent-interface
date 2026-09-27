#!/usr/bin/env python3
import argparse,hashlib,json,pathlib
FIXTURE_TIC=1366
PRED='timeout_tics < fixture_tic'

def verify(r):
 e=[]
 rows=r.get('rows',[])
 if r.get('decision')!='PASS_MAP01_FIXTURE_TIMEOUT_PRECONDITION_SCOPED':e.append('decision')
 if r.get('formal_invocations')!=1 or any(r.get(k)!=0 for k in ('reruns','replacements','tuning')):e.append('budget')
 if r.get('predicate')!=PRED or r.get('fixture_tic')!=FIXTURE_TIC:e.append('predicate')
 if len(rows)!=6:e.append('row_count')
 for x in rows:
  exp=x.get('timeout_tics',-1)<FIXTURE_TIC
  if x.get('expected_terminal') is not exp or x.get('episode_finished') is not exp or x.get('match') is not True:e.append('row:'+str(x.get('case_id')))
  if x.get('episode_tic')!=FIXTURE_TIC:e.append('tic:'+str(x.get('case_id')))
  if x.get('player_dead') or x.get('kill_count')!=0 or x.get('death_count')!=0:e.append('counter:'+str(x.get('case_id')))
 if r.get('task_input_actions')!=0 or r.get('advance_action_calls')!=0:e.append('action')
 return e

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--result',required=True);ap.add_argument('--formal-source',required=True);ap.add_argument('--out',required=True);a=ap.parse_args()
 r=json.loads(pathlib.Path(a.result).read_text()); e=verify(r); src=pathlib.Path(a.formal_source).read_text()
 forbidden=['advance_action(','make_action(','set_action(','send_game_command(']
 found=[x for x in forbidden if x in src]
 if found:e.append('forbidden_source:'+','.join(found))
 o={'pass':not e,'errors':e,'decision':r.get('decision'),'result_sha256':hashlib.sha256(pathlib.Path(a.result).read_bytes()).hexdigest(),'formal_source_sha256':hashlib.sha256(pathlib.Path(a.formal_source).read_bytes()).hexdigest(),'forbidden_action_tokens':found}
 pathlib.Path(a.out).write_text(json.dumps(o,indent=2,sort_keys=True)+'\n');print(json.dumps(o,sort_keys=True));raise SystemExit(bool(e))
if __name__=='__main__':main()
