"""Host-side single-attempt image model bridge; invoked by formal driver later."""
from pathlib import Path
import hashlib,json,subprocess,time

def serve_request(request_path, cli, model, effort, workspace, output_root):
 request_path=Path(request_path);request=json.loads(request_path.read_text(encoding='utf-8'))
 root=Path(output_root)/request['call_id'];root.mkdir(parents=True,exist_ok=False)
 schema=root/'schema.json';schema.write_text(json.dumps(request['schema']))
 image=None
 if request.get('image_relative'):
  image=Path(output_root).parent/request['image_relative']
  if not image.is_file() or hashlib.sha256(image.read_bytes()).hexdigest()!=request['image_sha256']:raise ValueError('image custody mismatch')
 answer=root/'answer.json'
 argv=[str(cli),'exec','--ephemeral','--ignore-user-config','--ignore-rules','--disable','plugins','--disable','remote_plugin','--disable','shell_snapshot','--disable','shell_tool','--skip-git-repo-check','--sandbox','read-only','--json','--color','never','--model',model,'-c','model_reasoning_effort='+json.dumps(effort),'-c','project_doc_max_bytes=0','-c','approval_policy="never"','--cd',str(workspace),'--output-schema',str(schema),'--output-last-message',str(answer)]
 if image:argv.extend(['--image',str(image)])
 argv.append('-')
 (root/'argv.json').write_text(json.dumps(argv,indent=2));(root/'request.json').write_bytes(request_path.read_bytes())
 started=time.perf_counter_ns();timed=False
 try:p=subprocess.run(argv,input=request['prompt'].encode(),capture_output=True,timeout=90);code=p.returncode;stdout=p.stdout;stderr=p.stderr
 except subprocess.TimeoutExpired as e:code=None;stdout=e.stdout or b'';stderr=e.stderr or b'';timed=True
 elapsed=time.perf_counter_ns()-started
 (root/'events.jsonl').write_bytes(stdout);(root/'stderr.txt').write_bytes(stderr)
 events=[];parse_errors=[]
 for line in stdout.splitlines():
  try:events.append(json.loads(line))
  except Exception:parse_errors.append(line.decode(errors='replace'))
 completed=[r for r in events if r.get('type')=='turn.completed'];threads=[r['thread_id'] for r in events if r.get('type')=='thread.started']
 tools=[r for r in events if r.get('item',{}).get('type') not in (None,'reasoning','agent_message')]
 try:value=json.loads(answer.read_text())
 except Exception:value=None
 ok=code==0 and not timed and not parse_errors and not tools and len(completed)==1 and len(threads)==1 and isinstance(value,dict)
 record={'requested_model':model,'requested_effort':effort,'thread_ids':threads,'exit':code,'timeout':timed,'wait_ns':elapsed,'visible_images_submitted':1 if image else 0,'usage':completed[0].get('usage') if len(completed)==1 else None,'parse_errors':parse_errors,'tool_items':tools,'output':value,'transport_ok':ok,'image_sha256':request.get('image_sha256'),'schema_sha256':hashlib.sha256(schema.read_bytes()).hexdigest()}
 (root/'result.json').write_text(json.dumps(record,indent=2))
 reply=request_path.with_suffix('.response.json');tmp=reply.with_suffix('.tmp');tmp.write_text(json.dumps(record));tmp.replace(reply)
 return record

