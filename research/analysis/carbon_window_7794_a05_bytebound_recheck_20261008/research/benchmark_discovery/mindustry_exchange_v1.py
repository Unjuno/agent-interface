"""Single explicit socket request; persist full reply before compact console summary."""
import json,sys,time
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'live_control'))
from unix_json_deadline import exchange
socket,request_path,out=sys.argv[1:];out=Path(out);out.mkdir(exist_ok=False)
q=json.loads(Path(request_path).read_text(encoding='utf-8-sig'));(out/'request.json').write_text(json.dumps(q,indent=2)+'\n')
start=time.perf_counter_ns();r=exchange(socket,q,timeout=min(35,q['timeout']+3));end=time.perf_counter_ns()
(out/'reply.json').write_text(json.dumps(r,indent=2)+'\n');(out/'timing.json').write_text(json.dumps({'start_ns':start,'returned_ns':end,'scope':'local exchange; excludes model receipt'})+'\n')
print(json.dumps({'status':r['status'],'cursor':r.get('cursor'),'command_receipt':r.get('command_receipt'),'records':[{k:e[k] for k in ('event','id','status','reason','decision_reason','runtime_ns','sequence','image','pointer_binding','release','post_release_observation') if k in e} for e in r.get('records',[])]}))
