import json,pathlib
from saved_oracle import score_saved
R=pathlib.Path(__file__).resolve().parent;D=R/'runs/measured_shared11';raw=json.loads((D/'raw.json').read_text());client=json.loads((R/'CLIENT_RECEIPT.json').read_text())
ocr=[json.loads(v) for v in (D/'OCR_ATTEMPTS.jsonl').read_text().splitlines()]
out={'disposition':'HOLD_FIRST_OCR_UNAVAILABLE_SECOND_STAGE_CENSORED','first_saved_effect':score_saved((D/'first.fods').read_bytes(),17,23),'graph_outcome':raw['compiled_result']['outcome'],'graph_reason':raw['compiled_result']['reason'],'native_programs':len(raw['native_attempts']),'second_save_exists':(D/'second.fods').exists(),'ocr_stdout':[v['stdout'] for v in ocr],'model_summary':client['model_summary'],'first_auditor_failure':'FileNotFoundError second.fods; original audit source retained','correction':'Initial report draft wrongly asserted two saves before audit. Actual second stage censored, not completed. Draft retained separately.'}
p=R/'AUDIT_PARTIAL.json'
if p.exists():raise RuntimeError('output retained')
p.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k not in ('first_saved_effect','model_summary')}));print(json.dumps({'first_saved_effect':out['first_saved_effect']['pass_effect']}))
