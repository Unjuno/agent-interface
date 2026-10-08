from pathlib import Path
import sys,json
sys.path.insert(0,'/source')
import session_map01_v16 as candidate
previous=candidate.previous
oldmain=previous.main; oldoption=previous._option; oldsample=previous._coherent_progress_sample;oldproxy=previous._GameProxy
previous._option=lambda _: '/out/session'
def fail():
 p=Path('/out/session');p.mkdir();(p/'sources.json').write_text('{invalid')
 raise RuntimeError('SESSION_SENTINEL')
previous.main=fail
try:
 try:candidate.main()
 except BaseException as e:
  def tree(e):return {'type':type(e).__name__,'message':str(e),'children':[tree(x) for x in getattr(e,'exceptions',[])]}
  result={'exception':tree(e),'sample_restored':previous._coherent_progress_sample is oldsample,'proxy_restored':previous._GameProxy is oldproxy}
  result['original_explicitly_retained']='SESSION_SENTINEL' in json.dumps(result['exception'])
  Path('/out/RESULT.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
finally:previous.main=oldmain;previous._option=oldoption
