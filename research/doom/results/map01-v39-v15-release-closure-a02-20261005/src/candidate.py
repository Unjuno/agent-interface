import ast,hashlib,importlib,importlib.util,json,sys,threading,time,types
from pathlib import Path
R=Path("/src");O=Path("/out");F=json.loads((R/"FROZEN_INPUTS.json").read_text())
def blob(b):return hashlib.sha1(b"blob "+str(len(b)).encode()+bytes([0])+b).hexdigest()
def source_lock():
 d={}
 for p,h in F["source_blob_sha1"].items():
  b=(R/F.get("source_path_overrides",{}).get(p,p)).read_bytes();x=blob(b)
  if x!=h:raise RuntimeError("source blob mismatch "+p)
  d[p]={"blob":x,"sha256":hashlib.sha256(b).hexdigest(),"bytes":len(b)}
 own=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
 if own!=F["candidate_sha256"]:raise RuntimeError("candidate hash mismatch")
 return d,own
def route(flag):
 p=R/"research/doom/map01_overlap_controller_v39.py";t=ast.parse(p.read_text())
 fn=next(n for n in t.body if isinstance(n,ast.FunctionDef) and n.name=="session_command")
 ns={"sys":sys,"HERE":R/"research/doom"};exec(compile(ast.Module(body=[fn],type_ignores=[]),str(p),"exec"),ns)
 class A:
  measurement_session=flag;seed=217;load_fixture_manifest=Path("/fixture/m.json")
 return Path(ns["session_command"](A(),Path("/runtime"))[1]).name
def load(name,p):
 s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m
def main():
 O.mkdir(parents=True,exist_ok=True);info,own=source_lock()
 if (route(False),route(True))!=("session_map01_v12.py","session_map01_v15.py"):raise RuntimeError("session route mismatch")
 live=R/"research/live_control";doom=R/"research/doom";sys.path[:0]=[str(live),str(doom)]
 xl=types.ModuleType("Xlib");X=types.SimpleNamespace(KeyPress=2,KeyRelease=3,ButtonRelease=5,Button1Mask=256,AnyPropertyType=0,IsViewable=2)
 XK=types.SimpleNamespace(string_to_keysym=lambda x:x);err=types.SimpleNamespace(BadWindow=type("BadWindow",(Exception,),{}),BadDrawable=type("BadDrawable",(Exception,),{}))
 disp=types.ModuleType("Xlib.display");disp.Display=lambda n:None;xt=types.ModuleType("Xlib.ext.xtest");xt.fake_input=lambda *a,**k:None;ext=types.ModuleType("Xlib.ext");ext.xtest=xt
 xl.X,xl.XK,xl.error,xl.display,xl.__path__=X,XK,err,disp,[];sys.modules.update({"Xlib":xl,"Xlib.display":disp,"Xlib.ext":ext,"Xlib.ext.xtest":xt})
 pil=types.ModuleType("PIL");pil.ImageGrab=types.SimpleNamespace(grab=lambda **k:None);sys.modules["PIL"]=pil
 owner=load("input_owner_v12",live/"input_owner_v12.py")
 base=types.ModuleType("session_map01_v12");base.vd=types.SimpleNamespace(DoomGame=type("DoomGame",(),{}),GameVariable=object());base.Backend=type("DefaultBackend",(),{});base.Executor=type("DefaultExecutor",(),{});base.sys=sys
 picked={};base.main=lambda:picked.update(backend=base.Backend,executor=base.Executor);sys.modules["session_map01_v12"]=base
 sc=types.ModuleType("map01_scorer_stdio_adapter_v1")
 class Sink:
  def __init__(self,o):pass
  def finalize(self,s):pass
 class Poll:
  def __init__(self,*a,**k):pass
  def stats(self):return {}
 sc.ScorerFileSink=Sink;sc.MainThreadScorerStdin=Poll;sys.modules["map01_scorer_stdio_adapter_v1"]=sc
 clk=types.ModuleType("independent_progress_clock_v2");clk.ProgressSample=type("ProgressSample",(),{});sys.modules["independent_progress_clock_v2"]=clk
 par=types.ModuleType("doom_typed_release_backend_v1")
 class Parent:
  def execute(self,s,c,i,n):
   for k,d in s["actions"]:self.raw(k,d)
 par.Backend=Parent;par.suite=object();sys.modules["doom_typed_release_backend_v1"]=par
 session_out=O/"session";session_out.mkdir(parents=True,exist_ok=True)
 old=sys.argv;sys.argv=["session_map01_v15.py","--out",str(session_out),"--timeout-seconds","600"]
 try:load("session_map01_v15",doom/"session_map01_v15.py").main()
 finally:sys.argv=old
 B=picked["backend"];E=picked["executor"]
 if B.__module__!="doom_owner_thread_release_batch_backend_v1" or E.__module__!="executor_v13":raise RuntimeError("V15 main selected unexpected classes")
 hp=R/"harness/test_input_owner_v12.py";hm=load("harness_v12",hp);h=hm.Harness(owner)
 keys={"F8":74,"SPACE":65};XK.string_to_keysym=lambda x:keys[x];h.d.keysym_to_keycode=lambda x:x
 ops=[];oq=h.d.query_keymap;of=owner.xtest.fake_input
 def q():
  v=oq();down=[c for c in sorted(keys.values()) if v[c//8]&(1<<(c%8))]
  ops.append({"op":"query","down":down,"ns":time.perf_counter_ns()});return v
 def fake(d,t,c=None,**kw):
  ops.append({"op":"down" if t==X.KeyPress else "up","code":c,"ns":time.perf_counter_ns()});return of(d,t,c,**kw)
 h.d.query_keymap=q;owner.xtest.fake_input=fake
 class Fixed:
  def __new__(c,n):return h.owner
 A=importlib.import_module("input_transition_owner_v4").InputOwner(":fake",_owner_cls=Fixed)
 ev=[];b=object.__new__(B);b.owner=A;b.lease=hm.Lease(intent="intent-v15-a01");b.held=set();b._input_event_context=None;b._release_batch=threading.local();b._last_release_batch_delivery=None;b.emit=ev.append
 failure=None
 try:b.execute({"actions":[("F8",True),("SPACE",True),("SPACE",False),("F8",False)]},None,"cover-v15-a01",2)
 except BaseException as e:failure=type(e).__name__+": "+str(e)
 ups=[i for i,r in enumerate(ops) if r["op"]=="up"];between=ops[ups[0]+1:ups[1]] if len(ups)==2 else []
 downs=[r for r in ev if r.get("event")=="input_admission"];ups_ev=[r for r in ev if r.get("event")=="input_release_transition"]
 did={r.get("key"):r.get("physical_key_measurement",{}).get("actuation_id") for r in downs};uid={r.get("key"):r.get("physical_key_measurement",{}).get("actuation_id") for r in ups_ev}
 verified=all(r.get("owner_transition_verified") is True for r in ups_ev);authority=all(r.get("grants_input_authority") is False and r.get("physical_verification_authoritative") is False for r in ups_ev)
 owner.xtest.fake_input=of
 try:A.close()
 finally:h.close()
 exact=(failure is None and [r.get("key") for r in downs]==["F8","SPACE"] and [r.get("key") for r in ups_ev]==["SPACE","F8"] and did==uid and verified and authority and h.d.physical==set() and b.held==set() and h.owner.stopped.is_set())
 dispn="STOP_OR_FAIL_SELECTED_V15_CONSTRUCTION" if not exact else ("CONFIRMED_INTER_RELEASE_SAMPLING_IN_SELECTED_V15" if any(r["op"]=="query" for r in between) else "NO_INTER_RELEASE_QUERY_OBSERVED")
 res={"schema":"map01-v39-v15-release-closure-a02-v1","run_id":F["run_id"],"main_sha":F["main_sha"],"source_info":info,"candidate_sha256":own,"session_selection":{"default":"session_map01_v12.py","measurement":"session_map01_v15.py"},"selected_classes":{"backend":B.__module__+"."+B.__name__,"executor":E.__module__+"."+E.__name__},"events":ev,"operations":ops,"between":between,"queries_between":sum(r["op"]=="query" for r in between),"admission_keys":[r.get("key") for r in downs],"release_keys":[r.get("key") for r in ups_ev],"down_ids":did,"up_ids":uid,"release_verified":verified,"authority_false":authority,"physical_after":sorted(h.d.physical),"backend_held_after":sorted(b.held),"owner_stopped":h.owner.stopped.is_set(),"failure":failure,"disposition":dispn,"limitations":["V15 main used a stub V12 session main, scorer and stdin; no game/session startup.","Exact selected release backend and V12/V4 owner ran over fake display with a deterministic parent execution shim.","No live X11, OS input, task feedback, recovery, MAP01, safety or latency-bound evidence."]}
 (O/"candidate-result.json").write_text(json.dumps(res,indent=2,sort_keys=True)+"\n");(O/"operation-trace.jsonl").write_text("".join(json.dumps(r,sort_keys=True)+"\n" for r in ops))
 print(json.dumps({"disposition":dispn,"queries_between":res["queries_between"],"selected_classes":res["selected_classes"],"release_verified":verified,"authority_false":authority,"physical_after":res["physical_after"],"backend_held_after":res["backend_held_after"]},sort_keys=True))
if __name__=="__main__":main()