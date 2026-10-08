"""Read saved evidence once; no app, OCR or model rerun."""
import hashlib, json
from pathlib import Path
from PIL import Image
from saved_oracle import score_saved
R=Path(__file__).resolve().parent
D=R/'runs/measured_boundedread12'
raw=json.loads((D/'raw.json').read_text(encoding='utf-8'))
plan=json.loads((R/'PLAN.json').read_text(encoding='utf-8'))
client=json.loads((R/'CLIENT_RECEIPT.json').read_text(encoding='utf-8'))
ocr=[json.loads(s) for s in (D/'OCR_ATTEMPTS.jsonl').read_text(encoding='utf-8').splitlines()]
errors=[]
for name,digest in plan['source_hashes'].items():
    if hashlib.sha256((R/name).read_bytes()).hexdigest()!=digest:errors.append('source '+name)
for im,pixel,obs in zip(raw['images'],raw['pixel_checks'],raw['compiled_result']['observations']):
    artifact=im['native']['artifact']; p=D/'guarded/images'/Path(artifact['path']).name
    if hashlib.sha256(p.read_bytes()).hexdigest()!=artifact['sha256']:errors.append('PNG digest')
    if hashlib.sha256(Image.open(p).convert('RGB').crop((36,161,305,175)).tobytes()).hexdigest()!=pixel['rgb_sha256']:errors.append('ROI association')
    if obs['evidence_digest']!=artifact['sha256'] or obs['captured_ns']!=im['native']['capture_started_ns']:errors.append('graph association')
effect=score_saved((D/'first.fods').read_bytes(),19,29)
if not effect['pass_effect']:errors.append('first saved effect')
if raw['cleanup_physical']['keys'] or raw['cleanup_physical']['buttons']:errors.append('physical release')
result=dict(disposition='HOLD_OCR_FALSE_NEGATIVE_CONTINUATION_UNEXERCISED',errors=errors,
    saved_effect=effect,graph=raw['compiled_result']['outcome'],reason=raw['compiled_result']['reason'],
    native_programs=len(raw['native_attempts']),second_save_exists=(D/'second.fods').exists(),
    read_continuations=len(raw.get('read_continuations',[])),ocr_stdout=[v['stdout'] for v in ocr],
    ocr_total_ns=sum(v['end_ns']-v['start_ns'] for v in ocr),model_summary=client['model_summary'],
    limitations=['Correct saved XML and visually inspected PNG show551; OCR returned951.',
    'No unavailable post-action decode, so bounded continuation hypothesis untested.',
    'Dormant source defect: ROI hash is computed before continuation and would refer to initial capture if continuation used.',
    'Parent cleanup receipts do not prove graceful application close or every descendant.'])
with (R/'AUDIT_RETAINED.json').open('x',encoding='utf-8') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps(result,ensure_ascii=False))
