import hashlib, http.server, json, os, queue, select, socket, subprocess, sys, tempfile, threading, time
from pathlib import Path
CLI=sys.argv[1]
WINDOW_S=1.0
TIMEOUT_S=12.0
events=[]
event_lock=threading.Lock()
next_seq=0
def mark(name, **extra):
    global next_seq
    with event_lock:
        next_seq+=1
        row={"seq":next_seq,"event":name,"perf_counter_ns":time.perf_counter_ns()}
        row.update(extra); events.append(row); return row["perf_counter_ns"]
gate=threading.Event()
first_seen=threading.Event()
disconnected=threading.Event()
state={"requests":[],"disconnect_ns":None,"errors":[]}
class Handler(http.server.BaseHTTPRequestHandler):
    protocol_version="HTTP/1.1"
    def log_message(self,*args): pass
    def do_POST(self):
        try:
            raw=self.rfile.read(int(self.headers.get("Content-Length","0")))
            parsed=json.loads(raw)
            state["requests"].append({"sha256":hashlib.sha256(raw).hexdigest(),"bytes":len(raw),"model":parsed.get("model")})
            mark("mock_request_received",request_index=len(state["requests"]))
            if len(state["requests"])==1:
                first_seen.set()
                while not gate.is_set():
                    readable,_,_=select.select([self.connection],[],[],0.01)
                    if readable:
                        try:
                            if self.connection.recv(1,socket.MSG_PEEK)==b"":
                                state["disconnect_ns"]=mark("http_client_disconnected")
                                disconnected.set(); return
                        except OSError:
                            state["disconnect_ns"]=mark("http_client_disconnected",via="socket_error")
                            disconnected.set(); return
                payload={"id":"resp_1","object":"response","created_at":1,"status":"completed","model":"gpt-5.6-luna","output":[{"id":"msg_1","type":"message","status":"completed","role":"assistant","content":[{"type":"output_text","text":"mock final","annotations":[]}]}],"usage":{"input_tokens":1,"output_tokens":1,"total_tokens":2}}
                records=[("response.created",{"response":{**payload,"status":"in_progress","output":[]}}),("response.output_item.added",{"output_index":0,"item":{"id":"msg_1","type":"message","status":"in_progress","role":"assistant","content":[]}}),("response.output_text.delta",{"item_id":"msg_1","output_index":0,"content_index":0,"delta":"mock final"}),("response.output_item.done",{"output_index":0,"item":payload["output"][0]}),("response.completed",{"response":payload})]
                body="".join("event: "+typ+"\ndata: "+json.dumps({"type":typ,**val})+"\n\n" for typ,val in records).encode()
                self.send_response(200); self.send_header("Content-Type","text/event-stream"); self.send_header("Content-Length",str(len(body))); self.end_headers(); self.wfile.write(body); self.wfile.flush()
                mark("mock_response_written")
        except Exception as exc:
            state["errors"].append(type(exc).__name__+": "+str(exc))
            mark("mock_handler_error",error=state["errors"][-1])
server=http.server.ThreadingHTTPServer(("127.0.0.1",0),Handler)
server.daemon_threads=True
threading.Thread(target=server.serve_forever,daemon=True).start()
messages=queue.Queue()
stderr=[]
completed_event=threading.Event()
def read_stdout(pipe):
    for line in pipe:
        try: msg=json.loads(line)
        except Exception: msg={"raw":line}
        if msg.get("method")=="turn/completed":
            mark("turn_completed_notification",status=msg.get("params",{}).get("turn",{}).get("status"),turn_id=msg.get("params",{}).get("turn",{}).get("id"))
            completed_event.set()
        messages.put(msg)
def read_stderr(pipe): stderr.extend(pipe.readlines())
def wait_for(pred,seconds=TIMEOUT_S):
    end=time.perf_counter()+seconds
    seen=[]
    while time.perf_counter()<end:
        try: m=messages.get(timeout=max(.005,end-time.perf_counter()))
        except queue.Empty: break
        seen.append(m)
        if pred(m): return m
    raise TimeoutError(json.dumps(seen[-8:],default=str))
def run():
    clock=time.get_clock_info("perf_counter")
    result={"cli_version":subprocess.check_output([CLI,"--version"],text=True).strip(),"cli_path":str(Path(CLI).resolve()),"clock":{k:getattr(clock,k) for k in ("implementation","resolution","monotonic","adjustable")},"pending_window_s":WINDOW_S,"loopback_only":True}
    with tempfile.TemporaryDirectory(prefix="codex-turn-interrupt-a03-") as home_text:
        home=Path(home_text)
        (home/"config.toml").write_text(f'''model = "gpt-5.6-luna"\napproval_policy = "never"\nsandbox_mode = "read-only"\n[model_providers.mock]\nname = "loopback mock"\nbase_url = "http://127.0.0.1:{server.server_address[1]}/v1"\nwire_api = "responses"\nrequires_openai_auth = false\nsupports_websockets = false\n''',encoding="utf-8")
        env=os.environ.copy(); env["CODEX_HOME"]=str(home)
        for k in ("OPENAI_API_KEY","OPENAI_BASE_URL","OPENAI_ORG_ID","OPENAI_PROJECT_ID","CODEX_API_KEY"): env.pop(k,None)
        result["temporary_codex_home"]=True
        result["credentials_cleared"]=all(k not in env for k in ("OPENAI_API_KEY","OPENAI_BASE_URL","OPENAI_ORG_ID","OPENAI_PROJECT_ID","CODEX_API_KEY"))
        proc=subprocess.Popen([CLI,"app-server","--listen","stdio://"],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,encoding="utf-8",bufsize=1,env=env,cwd=home)
        threading.Thread(target=read_stdout,args=(proc.stdout,),daemon=True).start()
        threading.Thread(target=read_stderr,args=(proc.stderr,),daemon=True).start()
        def send(payload): proc.stdin.write(json.dumps(payload)+"\n"); proc.stdin.flush()
        try:
            send({"id":1,"method":"initialize","params":{"clientInfo":{"name":"turn-interrupt-a03-qpc","title":"interrupt timing construction","version":"1"}}})
            init=wait_for(lambda m:m.get("id")==1); result["initialize_ok"]="result" in init
            send({"method":"initialized"})
            send({"id":2,"method":"thread/start","params":{"cwd":str(home),"model":"gpt-5.6-luna","modelProvider":"mock","approvalPolicy":"never","sandbox":"read-only"}})
            thread_reply=wait_for(lambda m:m.get("id")==2); tid=thread_reply.get("result",{}).get("thread",{}).get("id"); result["thread_started"]=bool(tid)
            send({"id":3,"method":"turn/start","params":{"threadId":tid,"input":[{"type":"text","text":"Say exactly INITIAL."}]}})
            start=wait_for(lambda m:m.get("id")==3); turn=start.get("result",{}).get("turn",{}).get("id"); result["active_turn_started"]=bool(turn); result["turn_id"]=turn; result["thread_id"]=tid
            if not first_seen.wait(TIMEOUT_S): raise TimeoutError("first request did not reach loopback mock")
            result["interrupt_send_ns"]=mark("turn_interrupt_sent")
            send({"id":4,"method":"turn/interrupt","params":{"threadId":tid,"turnId":turn}})
            reply=wait_for(lambda m:m.get("id")==4)
            result["interrupt_reply"]=reply
            result["interrupt_ack_ns"]=mark("turn_interrupt_acknowledged",accepted=("result" in reply))
            deadline=result["interrupt_send_ns"]+int(WINDOW_S*1_000_000_000)
            while time.perf_counter_ns()<deadline:
                remaining=(deadline-time.perf_counter_ns())/1_000_000_000
                disconnected.wait(min(.01,max(.001,remaining)))
            result["response_release_ns"]=mark("mock_response_gate_released")
            gate.set()
            completed_event.wait(TIMEOUT_S)
            result["completed_notification_seen"]=completed_event.is_set()
            result["request_count"]=len(state["requests"]); result["request_summaries"]=state["requests"]
            result["http_disconnected_before_release"]=state["disconnect_ns"] is not None and state["disconnect_ns"]<result["response_release_ns"]
            result["http_disconnect_ns"]=state["disconnect_ns"]; result["mock_errors"]=list(state["errors"])
            result["events"]=events
            result["elapsed_ns"]={k:(result[k]-result["interrupt_send_ns"]) if result.get(k) is not None else None for k in ("interrupt_ack_ns","http_disconnect_ns","response_release_ns")}
            end=[e for e in events if e["event"]=="turn_completed_notification"]
            result["turn_completed_status"]=end[-1].get("status") if end else None
            result["turn_completed_turn_id"]=end[-1].get("turn_id") if end else None
            result["stderr"]="".join(stderr)[-2000:]
            return result
        finally:
            gate.set()
            try: proc.stdin.close()
            except Exception: pass
            proc.terminate()
            try: proc.wait(timeout=3)
            except subprocess.TimeoutExpired: proc.kill(); proc.wait(timeout=3)
try:
    result=run()
    ok=all((result.get("initialize_ok"),result.get("thread_started"),result.get("active_turn_started"),result.get("interrupt_reply",{}).get("result")=={},result.get("request_count")==1,result.get("http_disconnected_before_release"),result.get("completed_notification_seen"),result.get("turn_completed_status")=="interrupted",result.get("turn_completed_turn_id")==result.get("turn_id"),not result.get("mock_errors")))
    info=result["clock"]
    timed=info.get("resolution",1)>0 and info.get("resolution",1)<=1e-6 and all(isinstance(result.get(k),int) and result[k]>0 for k in ("interrupt_send_ns","interrupt_ack_ns","http_disconnect_ns","response_release_ns"))
    result["candidate_gate"]="PASS_WINDOW_ABORT" if ok else "FAIL_OR_STOP"
    result["timing_gate"]="TIMING_MEASURABLE_SINGLE_SAMPLE" if timed else "TIMING_UNRESOLVED"
    print(json.dumps(result,indent=2,sort_keys=True))
    sys.exit(0 if ok and timed else 1)
finally:
    gate.set(); server.shutdown(); server.server_close()
