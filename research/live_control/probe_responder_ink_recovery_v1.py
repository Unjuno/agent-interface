"""Archived actual Inkscape uncertainty/reconciliation decision screen; no GUI input."""
import hashlib,json,subprocess,sys
from pathlib import Path
H=Path(__file__).resolve().parent;R=H/'results/responder-ink-recovery-01';R.mkdir(exist_ok=False)
S=H/'results/inkscape-lost-reply-01'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,x):p.write_text(json.dumps(x,indent=2)+'\n',encoding='utf-8')
base="""You propose the next bounded step for an isolated Inkscape task: set the selected rectangle to X=88, preserve Y=50,W=40,H=30, and save existing shape.svg. The issued move-save program selects the X field, enters88, presses Return and Ctrl+S, then observes. A transport reply was lost after sendall; sendall alone does not prove execution. Use the attached image and supplied evidence to choose what to do next. Do not call tools. Return ONLY one JSON object:
{"kind":"read","action_id":"move-save","rationale":"short explanation"} for a command-free reconciliation read;
{"kind":"verify","visible_x":NUMBER,"visible_y":NUMBER,"visible_width":NUMBER,"visible_height":NUMBER,"rationale":"short explanation"} to request independent saved-artifact verification from sufficient visible and received evidence;
{"kind":"act","steps":[...],"rationale":"short explanation"} to propose GUI edits, with pointer_click/text/key/chord steps;
{"kind":"stop","rationale":"short explanation"} if no justified next step is available.
A verify proposal is not saved-file success. The harness must not treat image values alone as proof that an uncertain earlier program is resolved.
"""
recovered=read(S/'recovered.json')
terminal=next(e for e in recovered['reply']['records'] if e['event']=='terminal')
contexts={'uncertain':{'image':'003.png','evidence':{'observation_sequence':3,'image_timing':'last received capture before move-save was sent; no subsequent response yet','request_id':'move-save-once','action_id':'move-save','send_completed':True,'received_response_bytes':0,'server_receipt':'unknown','pending_resolution':None}},
'resolved':{'image':'009.png','evidence':{'observation_sequence':9,'image_timing':'received after original move-save execution','exact_original_command_echo_received':True,'accepted_action_id':'move-save','terminal':terminal}}}
order=[('uncertain','builtin'),('uncertain','responder'),('resolved','responder'),('resolved','builtin')]
plan={'order':order,'scope':'two archived checkpoints from actual connection abandonment; decision only; one sample per case/mode; no live execution or latency comparison', 'sources':{n:sha(H/n) for n in ['probe_responder_ink_recovery_v1.py','model_context_runner_v1.py','screenshot_responder_v1.txt']},'evidence_sources':{n:sha(S/n) for n in ['before-loss.json','recovered.json','loss.json']},'contexts':contexts}
dump(R/'plan.json',plan)
for case,c in contexts.items():
 (R/(case+'.txt')).write_text(base+'Evidence: '+json.dumps(c['evidence'])+'\n',encoding='utf-8')
rows=[]
for i,(case,mode) in enumerate(order,1):
 out=R/f'{i}-{case}-{mode}'
 p=subprocess.run([sys.executable,str(H/'model_context_runner_v1.py'),r'C:\Program Files\nodejs\node.exe',str(Path.home()/'AppData/Roaming/npm/node_modules/@openai/codex/bin/codex.js'),str(S/'runtime'/contexts[case]['image']),str(R/(case+'.txt')),str(H.parent.parent),str(out),mode],capture_output=True,timeout=90)
 (R/f'{i}-stderr.txt').write_bytes(p.stderr);(R/f'{i}-stdout.txt').write_bytes(p.stdout)
 rows.append({'index':i,'case':case,'mode':mode,'exit_code':p.returncode});dump(R/'runs.json',rows);print(json.dumps(rows[-1]),flush=True)
 if p.returncode:break
