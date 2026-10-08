import http.server, json, os, queue, select, socket, subprocess, tempfile, threading, time, sys
from pathlib import Path
codex = sys.argv[1]; gate=threading.Event(); first_seen=threading.Event(); events=[]
state={"requests":[],"disconnect":False,"errors":[]}
class Handler(http.server.BaseHTTPRequestHandler):
    protocol_version="HTTP/1.1"
    def log_message(self,*a): pass
    def do_POST(self):
        try:
            body=self.rfile.read(int(self.headers.get("Content-Length","0"))); state["requests"].append(json.loads(body)); events.append({"event":"responses_request_received","t_ns":time.monotonic_ns()})
            if len(state["requests"])==1:
                first_seen.set(); deadline=time.monotonic()+8
                while not gate.is_set() and time.monotonic()<deadline:
                    readable,_,_=select.select([self.connection],[],[],.05)
                    if readable:
                        try:
                            if self.connection.recv(1,socket.MSG_PEEK)==b"": state["disconnect"]=True; events.append({"event":"client_disconnected_before_response","t_ns":time.monotonic_ns()}); return
                        except OSError: state["disconnect"]=True; return
                if not gate.is_set(): state["errors"].append("response gate timeout"); return
            payload={"id":"resp_1","object":"response","created_at":1,"status":"completed","model":"gpt-5.6-luna","output":[{"id":"msg_1","type":"message","status":"completed","role":"assistant","content":[{"type":"output_text","text":"mock final","annotations":[]}]}],"usage":{"input_tokens":1,"output_tokens":1,"total_tokens":2}}
            es=[("response.created",{"response":{**payload,"status":"in_progress","output":[]}}),("response.output_item.added",{"output_index":0,"item":{"id":"msg_1","type":"message","status":"in_progress","role":"assistant","content":[]}}),("response.output_text.delta",{"item_id":"msg_1","output_index":0,"content_index":0,"delta":"mock final"}),("response.output_item.done",{"output_index":0,"item":payload["output"][0]}),("response.completed",{"response":payload})]
            raw="".join("event: "+t+"\ndata: "+json.dumps({"type":t,**v})+"\n\n" for t,v in es).encode()
            self.send_response(200); self.send_header("Content-Type","text/event-stream"); self.send_header("Content-Length",str(len(raw))); self.end_headers(); self.wfile.write(raw); self.wfile.flush(); events.append({"event":"mock_response_sent","t_ns":time.monotonic_ns()})
        except Exception as e: state["errors"].append(type(e).__name__+": "+str(e))
server=http.server.ThreadingHTTPServer(("127.0.0.1",0),Handler); server.daemon_threads=True; threading.Thread(target=server.serve_forever,daemon=True).start()
msgs=queue.Queue(); stderr=[]
with tempfile.TemporaryDirectory(prefix="codex-turn-interrupt-a02-") as h:
    home=Path(h); (home/"config.toml").write_text(f'''model = "gpt-5.6-luna"\napproval_policy = "never"\nsandbox_mode = "read-only"\n[model_providers.mock]\nname = "loopback mock"\nbase_url = "http://127.0.0.1:{server.server_address[1]}/v1"\nwire_api = "responses"\nrequires_openai_auth = false\nsupports_websockets = false\n''')
    env=os.environ.copy(); env["CODEX_HOME"]=str(home)
    for k in ("OPENAI_API_KEY","OPENAI_BASE_URL","OPENAI_ORG_ID","OPENAI_PROJECT_ID","CODEX_API_KEY"): env.pop(k,None)
    p=subprocess.Popen([codex,"app-server","--listen","stdio://"],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,encoding="utf-8",bufsize=1,env=env,cwd=h)
    def readout():
        for line in p.stdout:
            try: msgs.put(json.loads(line))
            except Exception: msgs.put({"raw":line})
    def readerr(): stderr.extend(p.stderr.readlines())
    threading.Thread(target=readout,daemon=True).start(); threading.Thread(target=readerr,daemon=True).start()
    def send(x): p.stdin.write(json.dumps(x)+"\n"); p.stdin.flush()
    def wait(pred,timeout=12):
        end=time.monotonic()+timeout; seen=[]
        while time.monotonic()<end:
            try: m=msgs.get(timeout=max(.01,end-time.monotonic()))
            except queue.Empty: break
            seen.append(m)
            if pred(m): return m
        raise TimeoutError(json.dumps(seen[-10:]))
    result={"cli_version":subprocess.check_output([codex,"--version"],text=True).strip(),"cli_path":str(Path(codex).resolve()),"loopback_only":True,"temporary_codex_home":True,"api_credentials_cleared":all(k not in env for k in ("OPENAI_API_KEY","OPENAI_BASE_URL","OPENAI_ORG_ID","OPENAI_PROJECT_ID","CODEX_API_KEY"))}
    try:
        send({"id":1,"method":"initialize","params":{"clientInfo":{"name":"turn-interrupt-a02","title":"interrupt construction probe","version":"1"}}}); result["initialize_reply"]=wait(lambda m:m.get("id")==1); send({"method":"initialized"})
        send({"id":2,"method":"thread/start","params":{"cwd":str(home),"model":"gpt-5.6-luna","modelProvider":"mock","approvalPolicy":"never","sandbox":"read-only"}}); tr=wait(lambda m:m.get("id")==2); result["thread_reply"]=tr; tid=tr["result"]["thread"]["id"]
        send({"id":3,"method":"turn/start","params":{"threadId":tid,"input":[{"type":"text","text":"Say exactly INITIAL."}]}}); start=wait(lambda m:m.get("id")==3); result["turn_start_reply"]=start; turn=start["result"]["turn"]["id"]; result["thread_id"]=tid; result["turn_id"]=turn
        if not first_seen.wait(12): raise TimeoutError("mock did not receive initial Responses request")
        result["interrupt_sent_ns"]=time.monotonic_ns(); send({"id":4,"method":"turn/interrupt","params":{"threadId":tid,"turnId":turn}}); result["interrupt_reply"]=wait(lambda m:m.get("id")==4); result["interrupt_reply_ns"]=time.monotonic_ns()
        end=time.monotonic()+2
        while time.monotonic()<end and not state["disconnect"]:
            try:
                m=msgs.get(timeout=.05)
                if m.get("method")=="turn/completed": result["turn_completed_before_release"]=m; break
            except queue.Empty: pass
        gate.set(); result["mock_response_release_ns"]=time.monotonic_ns()
        end=time.monotonic()+6
        while time.monotonic()<end:
            try:
                m=msgs.get(timeout=.1)
                if m.get("method")=="turn/completed": result["turn_completed"]=m; break
            except queue.Empty: pass
        result.update({"mock_request_count":len(state["requests"]),"mock_client_disconnected_before_release":state["disconnect"],"mock_errors":state["errors"],"events":events,"app_server_stderr":"".join(stderr)[-3000:]})
    except Exception as e: result.update({"candidate_error":type(e).__name__+": "+str(e),"mock_request_count":len(state["requests"]),"mock_client_disconnected_before_release":state["disconnect"],"mock_errors":state["errors"],"events":events,"app_server_stderr":"".join(stderr)[-3000:]})
    finally:
        gate.set()
        try: p.stdin.close()
        except Exception: pass
        p.terminate()
        try: p.wait(timeout=3)
        except subprocess.TimeoutExpired: p.kill(); p.wait(timeout=3)
        server.shutdown(); server.server_close()
print(json.dumps(result,indent=2,sort_keys=True))
