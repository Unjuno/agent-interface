import json,sys,traceback
from pathlib import Path
from integrated_efficiency_app_server_model_v1 import PersistentGroundingModel
root=Path(sys.argv[2]);workspace=root/'workspace';workspace.mkdir(exist_ok=False);m=None;report={'attempted':False,'completed':False,'usage':None}
try:
 m=PersistentGroundingModel(root/'session',workspace,executable=sys.argv[1],model='gpt-6.1-sol',effort='low')
 report['attempted']=True
 result=m.call(root/'call','Locate the editable token field and the control that submits this visible form.',root/'fixture.png','compiled',workspace)
 report.update(completed=True,grounding=result['grounding'],usage=result['usage'],call_id=result['call_id'],runner_ns=result['runner_ns'])
except Exception as e:
 report.update(error=type(e).__name__,detail=str(e)[:1000],call_id=getattr(e,'call_id',None),usage=getattr(e,'usage',None),runner_ns=getattr(e,'wait_ns',None))
finally:
 if m is not None:
  try:m.close();report['close_returned']=True
  except Exception as e:report.update(close_returned=False,close_error=type(e).__name__)
(root/'summary.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report));raise SystemExit(0 if report['completed'] and report.get('close_returned') else 1)
