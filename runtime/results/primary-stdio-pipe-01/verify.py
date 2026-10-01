from pathlib import Path
import json
import hashlib
import subprocess

root=Path(__file__).resolve().parent
def require(value,message):
    if not value:raise ValueError(message)
raw=(root/'primary-stream.jsonl').read_bytes()
require(b'\x1b' not in raw,'raw output must not contain terminal control sequences')
rows=[json.loads(line) for line in raw.decode().splitlines()]
require([x['status'] for x in rows]==['ready','returned','terminal'],'exact stream boundaries')
require(all(x['schema']=='agent-interface/primary-stdio-v1' for x in rows),'typed raw stream')
events=[json.loads(line) for line in (root/'transport/host-events.jsonl').read_text().splitlines()]
require([x['tool'] for x in events if x['kind']=='send_requested']==['interface_clock'],'one read-only clock request')
reply=json.loads((root/'transport/reply-1.json').read_text())
value=json.loads((root/'exchange/original-reply-1.json').read_text())
require(value=={**reply,'attempt':1},'original returned response identity')
require(rows[1]['result']==json.loads((root/'exchange/presentation-1.json').read_text()),'stdout/file result identity')
text=next(x['text'] for x in reply['result']['content'] if x['type']=='text')
require(rows[1]['result']['presented_text']==[{'schema':'agent-interface/mcp-result-status-v1','isError':False},text],'unmodified metadata handoff')
clock=json.loads(text)
require(clock['schema']=='agent-interface/execution-clock-v1' and clock['input_dispatched'] is False and clock['authority_granted'] is False and clock['lease_issued'] is False,'clock-only semantics')
require(rows[1]['result']['images']==[],'no GUI image or hidden capture')
require(rows[2]['exit']==json.loads((root/'transport/exit.json').read_text())=={'code':0,'signal':None},'same transport terminal')
require(rows[2]['state']['caller_state']['stopped'] is None and rows[2]['state']['next_id']==2,'no hidden retry or STOP clearing')
manifest=json.loads((root/'manifest.json').read_text())
require(manifest['sha256']==hashlib.sha256((root/'runtime.pyz').read_bytes()).hexdigest(),'source artifact identity')
repo=root.parents[2]
for name in ('primary_stdio.mjs','primary_exchange.mjs','primary_caller.mjs','relay_host.mjs','relay_client.mjs','README.md','FEEDBACK.md'):
    expected=subprocess.check_output(['git','-C',str(repo),'show',manifest['source_revision']+':runtime/host_v1/'+name])
    require((root/'host'/name).read_bytes()==expected,'committed host export')
print(json.dumps({'status':'PASS_RAW_FILE_STDIO','source':manifest['source_revision'],
    'stream_records':len(rows),'public_requests':1,'native_input':0,'images':0,'transport_exit':0,
    'scope':'Actual primary terminal stdin with raw file stdout, no model GUI or efficiency proof'},indent=2))
