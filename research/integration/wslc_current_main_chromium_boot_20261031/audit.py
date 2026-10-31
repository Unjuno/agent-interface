"""Verify retained failed main boot and candidate Chromium ready smoke."""
from pathlib import Path
from zipfile import ZipFile
import hashlib,json
p=Path(__file__).with_name('public.zip')
assert hashlib.sha256(p.read_bytes()).hexdigest()=='5c6dd28f10d5d0ff22a2699d37cebba18c2671077e7d202b5182d7d2f744ca4c'
with ZipFile(p) as z:
 m=json.loads(z.read('manifest.json'));assert set(z.namelist())==set(m['files'])|{'manifest.json'}
 for n,h in m['files'].items():assert hashlib.sha256(z.read(n)).hexdigest()==h,n
 setup=json.loads(z.read('ax01/setup-failure.json'));assert setup['exit_code']==1 and not setup['model_call_started']
 pre=json.loads(z.read('ay01/preflight-summary.json'));assert len(pre)==1 and pre[0]['completed'] and pre[0]['usage'] is not None
 run=json.loads(z.read('ay01/out/result.json'));assert run['passed'] is False and run['calls']==0
 assert b'FileNotFoundError' in z.read('ay01/out/arms/persistent/stderr.txt')
 launch=json.loads(z.read('az01/out/launcher.json'));receipt=json.loads(z.read('az01/out/receipt.json'))
 assert launch['exit_code']==0 and launch['timeout'] is False
 assert receipt=={'status':'ready','ready_event':'ready','app':'chromium','configured_chromium':'/usr/bin/chromium'}
 print(json.dumps({'status':'audited','setup':'failed_before_model','main_preflight':'completed','main_gui':'failed_missing_chromium','candidate_smoke':'ready','preflight_input_tokens':pre[0]['usage']['input_tokens'],'preflight_output_tokens':pre[0]['usage']['output_tokens']},indent=2))
