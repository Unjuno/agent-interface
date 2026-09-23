#!/usr/bin/env python3
import argparse,copy,json,pathlib,sys
sys.path.insert(0,str(pathlib.Path(__file__).parent));from audit import verify

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--result',required=True);ap.add_argument('--out',required=True);a=ap.parse_args();r=json.loads(pathlib.Path(a.result).read_text());tests={}
 def one(name,mut):
  q=copy.deepcopy(r);mut(q);tests[name]=bool(verify(q));assert tests[name]
 one('equality_launder',lambda q:q['rows'][1].__setitem__('episode_finished',True))
 one('1365_launder',lambda q:q['rows'][0].__setitem__('episode_finished',False))
 one('tick_drift',lambda q:q['rows'][2].__setitem__('episode_tic',1367))
 one('task_input_claim',lambda q:q.__setitem__('task_input_actions',1))
 one('rerun_claim',lambda q:q.__setitem__('reruns',1))
 one('predicate_launder',lambda q:q.__setitem__('predicate','timeout_tics <= fixture_tic'))
 out={'pass':all(tests.values()),'corruption_controls':tests};pathlib.Path(a.out).write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,sort_keys=True));raise SystemExit(0 if out['pass'] else 2)
if __name__=='__main__':main()
