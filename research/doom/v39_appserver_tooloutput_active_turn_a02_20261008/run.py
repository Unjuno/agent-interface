import base64, json, os, subprocess, threading, time, zlib, struct
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

root=Path(r'C:\Users\user\Documents\Codex\2026-10-03\new-chat-7\outputs\v39-appserver-tooloutput-active-turn-a02')
home=root/'codex-home'; cwd=root/'cwd'; home.mkdir(); cwd.mkdir()
reqs=[]; lock=threading.Lock(); first_open=threading.Event(); release_first=threading.Event(); second_seen=threading.Event(); timing={}; errors=[]
def png_chunk(kind,data):
    return struct.pack('!I',len(data))+kind+data+struct.pack('!I',zlib.crc32(kind+data)&0xffffffff)
def png_rgb_2x2():
    raw=b'\x00'+bytes((10,20,30))*2+b'\x00'+bytes((40,50,60))*2
    return b'\x89PNG\r\n\x1a\n'+png_chunk(b'IHDR',struct.pack('!2I5B',2,2,8,2,0,0,0))+png_chunk(b'IDAT',zlib.compress(raw))+png_chunk(b'IEND',b'')
valid_png=png_rgb_2x2()
def sse(*events): return ''.join('event: '+e['type']+'\ndata: '+json.dumps(e,separators=(',',':'))+'\n\n' for e in events).encode()
def ev_created(rid): return {'type':'response.created','response':{'id':rid}}
def ev_message(rid,txt): return {'type':'response.output_item.done','item':{'type':'message','role':'assistant','id':'msg-'+rid,'content':[{'type':'output_text','text':txt}]}}
def ev_completed(rid): return {'type':'response.completed','response':{'id':rid,'usage':{'input_tokens':3,'output_tokens':2,'total_tokens':5}}}
class Handler(BaseHTTPRequestHandler):
    protocol_version='HTTP/1.1'
    def log_message(self,*a): pass
    def do_GET(self):
        if self.path.endswith('/models'):
            b=json.dumps({'object':'list','data':[{'id':'mock-model','object':'model','created':0,'owned_by':'openai'}]}).encode(); self.send_response(200); self.send_header('content-type','application/json'); self.send_header('content-length',str(len(b))); self.end_headers(); self.wfile.write(b); return
        self.send_error(404)
    def do_POST(self):
        obj=json.loads(self.rfile.read(int(self.headers.get('content-length','0'))))
        with lock: idx=len(reqs); reqs.append({'at':time.monotonic(),'body':obj})
        if not self.path.endswith('/responses'): self.send_error(404); return
        self.send_response(200); self.send_header('content-type','text/event-stream'); self.send_header('connection','close'); self.end_headers(); rid='mock-response-'+str(idx+1)
        try:
            self.wfile.write(sse(ev_created(rid))); self.wfile.flush()
            if idx==0:
                first_open.set(); release_first.wait(8); timing['first_response_completed_at']=time.monotonic()
                self.wfile.write(sse(ev_message(rid,'{"kind":"first"}'),ev_completed(rid))); self.wfile.flush()
            else:
                timing['second_response_started_at']=time.monotonic(); second_seen.set()
                self.wfile.write(sse(ev_message(rid,'{"kind":"observation_received"}'),ev_completed(rid))); self.wfile.flush()
        except (BrokenPipeError,ConnectionResetError,OSError) as e: errors.append(type(e).__name__)
        finally: self.close_connection=True
server=ThreadingHTTPServer(('127.0.0.1',0),Handler); server.daemon_threads=True; threading.Thread(target=server.serve_forever,daemon=True).start()
(home/'config.toml').write_text(f'''model = "mock-model"\napproval_policy = "never"\nsandbox_mode = "read-only"\nmodel_provider = "mock_provider"\n[model_providers.mock_provider]\nname = "local mock"\nbase_url = "http://127.0.0.1:{server.server_port}/v1"\nwire_api = "responses"\nrequest_max_retries = 0\nstream_max_retries = 0\n''')
env=os.environ.copy(); env['CODEX_HOME']=str(home); env['CODEX_APP_SERVER_DISABLE_MANAGED_CONFIG']='1'; env['RUST_LOG']='warn'
proc=subprocess.Popen(['codex.exe','app-server','--stdio'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,encoding='utf-8',bufsize=1,env=env,cwd=str(cwd))
out=[]; outlock=threading.Lock()
def reader():
    try:
        for line in proc.stdout:
            try: msg=json.loads(line)
            except Exception: continue
            with outlock: out.append((time.monotonic(),msg))
    except Exception as e: errors.append('reader:'+type(e).__name__)
threading.Thread(target=reader,daemon=True).start(); sendlock=threading.Lock(); seq=0
def send(method,params):
    global seq
    seq+=1; ident=seq
    with sendlock: proc.stdin.write(json.dumps({'jsonrpc':'2.0','id':ident,'method':method,'params':params})+'\n'); proc.stdin.flush()
    return ident
def response(ident,timeout=6):
    end=time.monotonic()+timeout
    while time.monotonic()<end:
        with outlock:
            for _,msg in out:
                if msg.get('id')==ident: return msg
        if proc.poll() is not None: break
        time.sleep(.01)
    raise TimeoutError('missing JSON-RPC response '+str(ident))
try:
    response(send('initialize',{'clientInfo':{'name':'a02','title':'A02','version':'1'},'capabilities':{'experimentalApi':False,'requestAttestation':False}}))
    with sendlock: proc.stdin.write(json.dumps({'jsonrpc':'2.0','method':'initialized','params':{}})+'\n'); proc.stdin.flush()
    tr=response(send('thread/start',{'model':'mock-model','cwd':str(cwd),'approvalPolicy':'never','sandbox':'read-only','baseInstructions':'Use supplied context.','ephemeral':True,'threadSource':'exec'})); tid=tr['result']['thread']['id']
    first=response(send('turn/start',{'threadId':tid,'input':[{'type':'text','text':'Initial request','text_elements':[]}],'model':'mock-model','effort':'low','outputSchema':{'type':'object','properties':{'kind':{'type':'string'}},'required':['kind'],'additionalProperties':False}})); turn=first['result']['turn']['id']
    if not first_open.wait(6): raise TimeoutError('first mock Responses request did not arrive')
    sent_at=time.monotonic(); b64=base64.b64encode(valid_png).decode()
    steer=response(send('turn/start',{'threadId':tid,'input':[],'toolOutput':{'name':'live_observation','namespace':'agent-interface','output':[{'type':'input_text','text':'UNTRUSTED CURRENT OBSERVATION: ammo=37'},{'type':'input_image','image_url':'data:image/png;base64,'+b64,'detail':'auto'}]}}),timeout=4)
    if 'error' in steer: raise RuntimeError('active-turn toolOutput rejected: '+json.dumps(steer))
    steering_turn=steer.get('result',{}).get('turn',{}).get('id')
    second_before_release=second_seen.wait(1.5)
    if not second_before_release: release_first.set(); second_seen.wait(6)
    release_first.set()
    deadline=time.monotonic()+8; completed=[]
    while time.monotonic()<deadline:
        with outlock: completed=[m for _,m in out if m.get('method')=='turn/completed' and m.get('params',{}).get('threadId')==tid and m.get('params',{}).get('turn',{}).get('id')==turn]
        if completed or proc.poll() is not None: break
        time.sleep(.02)
    with lock: calls=list(reqs)
    req2=calls[1] if len(calls)>1 else None; second_json=json.dumps(req2['body']) if req2 else ''
    result={'disposition':'PASS_ACTIVE_TURN_TOOL_OUTPUT_QUEUED_AFTER_CURRENT_INFERENCE' if req2 and steering_turn==turn else 'FAIL_OR_INCOMPLETE',
      'app_server_version':subprocess.run(['codex.exe','--version'],capture_output=True,text=True,timeout=3).stdout.strip(),
      'requests_to_loopback_mock_only':len(calls),'initial_turn_id':turn,'steering_response_turn_id':steering_turn,'same_turn':steering_turn==turn,
      'tool_output_text_present_in_followup_request':'UNTRUSTED CURRENT OBSERVATION: ammo=37' in second_json,
      'valid_png_b64_present_in_followup_request':b64 in second_json,
      'followup_request_after_first_response_completed':bool(req2 and timing.get('first_response_completed_at') and req2['at']>=timing['first_response_completed_at']),
      'seconds_from_tool_output_send_to_first_response_completion':round(timing['first_response_completed_at']-sent_at,3) if timing.get('first_response_completed_at') else None,
      'followup_request_ms_after_first_response_completion':round((req2['at']-timing['first_response_completed_at'])*1000,3) if req2 and timing.get('first_response_completed_at') else None,
      'terminal_status':completed[0]['params']['turn'].get('status') if completed else None,'mock_transport_errors':errors}
    (root/'result.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8'); print(json.dumps(result,indent=2))
finally:
    release_first.set()
    try: proc.stdin.close()
    except Exception: pass
    try: proc.wait(timeout=5)
    except subprocess.TimeoutExpired: proc.kill(); proc.wait(timeout=3)
    server.shutdown(); server.server_close()
    (root/'process_exit.txt').write_text(str(proc.returncode)+'\n',encoding='ascii')

