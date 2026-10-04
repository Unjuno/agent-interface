import ast,copy,queue,time,json,hashlib
from pathlib import Path
from types import SimpleNamespace

def extract(path,output):
 source=path.read_bytes();module=ast.parse(source)
 main=next(n for n in module.body if isinstance(n,ast.FunctionDef) and n.name=='main')
 wait=copy.deepcopy(next(n for n in main.body if isinstance(n,ast.FunctionDef) and n.name=='wait'))
 factory=ast.parse('def factory():\n latest=None\n').body[0];factory.body.extend([wait,ast.Return(value=ast.Name(id='wait',ctx=ast.Load()))]);m=ast.fix_missing_locations(ast.Module(body=[factory],type_ignores=[]))
 incoming=queue.Queue();ns={'incoming':incoming,'process':SimpleNamespace(poll=lambda:None),'time':time,'queue':queue,'args':SimpleNamespace(out=output),'json':json}
 exec(compile(m,str(path),'exec'),ns)
 return ns['factory'](),incoming,hashlib.sha256(source).hexdigest()

out=Path('/out');results=[]
for label,source in [('original','current-game-source-07'),('derived','current-game-source-08')]:
 for case,event in [('delivery_unknown',{'event':'terminal','id':'plan-1','input_release_publication':{'status':'delivery_unknown'}}),('unverified',{'event':'input_release_unverified','id':'plan-1'}),('valid_release',{'event':'input_released','id':'plan-1'})]:
  folder=out/(label+'-'+case);folder.mkdir()
  wait,q,digest=extract(Path('/study')/source/'research/doom/map01_overlap_controller_v39.py',folder);q.put(event);start=time.perf_counter_ns();returned=None;error=None
  try:returned=wait(lambda r:r.get('event')=='input_released' and r.get('id')=='plan-1',timeout=.1)
  except Exception as exc:error=type(exc).__name__
  results.append({'source':label,'case':case,'source_sha256':digest,'returned':returned,'exception':error,'elapsed_ns':time.perf_counter_ns()-start,'stop_file':(folder/'release-boundary-stop.json').is_file()})
expected=all((r['exception']=='TimeoutError' if r['source']=='original' else r['exception']=='RuntimeError' and r['stop_file']) if r['case']!='valid_release' else r['returned'] is not None and r['exception'] is None for r in results)
r={'scope':'actual AST-extracted nested controller wait; authored protocol events only; zero game/model/input; shortened timeout does not measure production40s','results':results,'boundary_checks_pass':expected};(out/'RESULT.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r));raise SystemExit(0 if expected else 1)
