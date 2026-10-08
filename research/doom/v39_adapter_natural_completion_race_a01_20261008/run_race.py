import ast, collections, hashlib, json, threading, time, subprocess
from pathlib import Path
from types import MethodType, SimpleNamespace

ROOT = Path(__file__).resolve().parent
PKG = ROOT
freeze = json.loads((PKG / "FREEZE.json").read_text(encoding="utf-8"))
ADAPTER = (PKG / "source/persistent_planner_adapter_v2.py").read_text(encoding="utf-8")
CLIENT = (PKG / "source/codex_app_server_client_v2.py").read_text(encoding="utf-8")
events=[]
condition=threading.Condition()
def mark(name):
    with condition:
        events.append((name, time.perf_counter_ns()))
        condition.notify_all()
def wait_event(name, timeout=3):
    deadline=time.monotonic()+timeout
    with condition:
        while not any(e[0]==name for e in events):
            remaining=deadline-time.monotonic()
            if remaining<=0: raise TimeoutError(name)
            condition.wait(remaining)
def extract_method(source, cls_name, method_name, scope):
    tree=ast.parse(source)
    cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name==cls_name)
    node=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name==method_name)
    module=ast.Module(body=[node],type_ignores=[])
    exec(compile(ast.fix_missing_locations(module),method_name,"exec"),scope)
    return scope[method_name]
def extract_function(source, name, scope):
    tree=ast.parse(source)
    node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==name)
    exec(compile(ast.fix_missing_locations(ast.Module(body=[node],type_ignores=[])),name,"exec"),scope)
    return scope[name]

client_scope={"time":time,"threading":threading,"collections":collections,"json":json,"math":__import__("math"),"AppServerError":RuntimeError}
deadline=extract_function(CLIENT,"_deadline",client_scope)
request=extract_method(CLIENT,"CodexAppServerClient","request",client_scope)
wait_notification=extract_method(CLIENT,"CodexAppServerClient","wait_notification",client_scope)
wait_completed=extract_method(CLIENT,"CodexAppServerClient","wait_turn_completed",client_scope)
latest_usage=extract_method(CLIENT,"CodexAppServerClient","latest_turn_usage",client_scope)
interrupt_turn=extract_method(CLIENT,"CodexAppServerClient","interrupt_turn",client_scope)

class Client:
    def __init__(self):
        self._condition=threading.Condition()
        self._responses={}
        self._pending=set()
        self._notifications=collections.deque()
        self._next_id=1
        self._closed=False
    def _write(self,message,*,deadline=None,request_id=None):
        self._pending.add(request_id)
        self.interrupt_id=request_id
        mark("interrupt_request_written")
    def inject_turn_completion(self):
        row={"method":"turn/completed","params":{"threadId":"thread","turn":{"id":"turn","status":"completed","items":[{"type":"agentMessage","text":"{\"action\":\"stale\"}"}]}}}
        with self._condition:
            self._notifications.append(row)
            mark("turn_completed_notification_received")
            self._condition.notify_all()
    def inject_interrupt_response(self):
        with self._condition:
            self._responses[self.interrupt_id]={"result":{}}
            self._condition.notify_all()
            mark("interrupt_response_received")
Client.request=request
Client.wait_notification=wait_notification
Client.wait_turn_completed=wait_completed
Client.latest_turn_usage=latest_usage
Client.interrupt_turn=interrupt_turn

adapter_scope={"threading":threading,"json":json,"PlannerProtocolError":RuntimeError,"TurnResult":lambda **kw: SimpleNamespace(**kw)}
interrupt=extract_method(ADAPTER,"PersistentPlannerAdapter","interrupt",adapter_scope)
await_turn=extract_method(ADAPTER,"PersistentPlannerAdapter","await_turn",adapter_scope)
require_active=extract_method(ADAPTER,"PersistentPlannerAdapter","_require_active",adapter_scope)
handle=SimpleNamespace(thread_id="thread",turn_id="turn")
client=Client()
planner=SimpleNamespace(_lock=threading.RLock(),_active=handle,_terminal_status=None,_cancellation_requested=False,_interrupt_response=None,_transport_aborted=False,client=client,_output_schema={"type":"object"})
planner.interrupt=MethodType(interrupt,planner)
planner.await_turn=MethodType(await_turn,planner)
planner._require_active=MethodType(require_active,planner)
def cancel_cover():
    mark("executor_cancel_write")
    mark("executor_cancel_flush")
interrupt_result={}
await_result={}
def do_interrupt():
    interrupt_result["value"]=planner.interrupt(handle,before_transport=cancel_cover)
def do_await():
    await_result["value"]=planner.await_turn(handle,timeout=3)
it=threading.Thread(target=do_interrupt)
it.start()
wait_event("interrupt_request_written")
at_request=time.perf_counter_ns()
at=threading.Thread(target=do_await)
at.start()
client.inject_turn_completion()
at.join(2)
if at.is_alive(): raise AssertionError("await_turn did not return while interrupt request was pending")
completed_before_ack=not any(n=="interrupt_response_received" for n,_ in events)
client.inject_interrupt_response()
it.join(2)
if it.is_alive(): raise AssertionError("interrupt did not finish after response")
result=await_result["value"]
assert completed_before_ack
assert result.status=="completed"
assert result.cancellation_requested is True
assert result.answer_eligible is False
assert result.answer is None
assert result.error=="answer belongs to an invalidated observation"
ordered=[n for n,_ in events]
assert ordered.index("executor_cancel_flush")<ordered.index("interrupt_request_written")
assert ordered.index("turn_completed_notification_received")<ordered.index("interrupt_response_received")
main=freeze["main_commit"]
blobs={row["path"]:row["git_blob"] for row in freeze["sources"]}
out=PKG
result_doc={"schema":"v39-adapter-natural-completion-race-a01-v1","status":"PASS_COMPLETION_RETAINED_BUT_ANSWER_INVALIDATED","main":main,"source_blobs":blobs,"events":[{"event":n,"at_ns":t} for n,t in events],"planner_completion_before_interrupt_ack":completed_before_ack,"turn_result":{"status":result.status,"cancellation_requested":result.cancellation_requested,"answer_eligible":result.answer_eligible,"answer":result.answer,"error":result.error},"assertions":{"completion_observed_while_interrupt_response_pending":completed_before_ack,"late_answer_rejected":result.cancellation_requested and not result.answer_eligible and result.answer is None,"executor_cancel_before_interrupt_request":ordered.index("executor_cancel_flush")<ordered.index("interrupt_request_written")}}


print(json.dumps(result_doc,indent=2))
