import hashlib
import json
from pathlib import Path
from agent_review import review_native
from receipt_references import expand_native_receipt

root = Path.cwd()
run = root / 'results-local/native-calc-final-action-01'
report = run / 'reply-2.json'
raw = report.read_bytes()
source = json.loads(raw)
png = Path(source['observation']['native']['artifact']['path'])
pixels = png.read_bytes()
full = review_native(report, run)
compact = review_native(report, run, compact=True)
assert full['receipt']['native_result'] == source
assert expand_native_receipt(compact['receipt']) == full['receipt']
assert full['outcome_summary'] == compact['outcome_summary'] == {
    'reported_status': 'finished', 'evaluation_success': True,
    'action_status': 'completed', 'feedback_status': 'needs_review',
    'cleanup_status': 'completed'}
assert full['image'] == compact['image']
assert full['image_reference']['sha256'] == hashlib.sha256(pixels).hexdigest()
assert report.read_bytes() == raw and png.read_bytes() == pixels
def size(value):
    return len(json.dumps(value, separators=(',', ':'), ensure_ascii=False).encode())
full.pop('image')
with_summary = size(full)
summary = full.pop('outcome_summary')
result = {'scope': 'read-only historical representation; no new GUI execution',
          'outcome_summary': summary,
          'source_report_sha256': hashlib.sha256(raw).hexdigest(),
          'image_sha256': hashlib.sha256(pixels).hexdigest(),
          'metadata_bytes_with_summary': with_summary,
          'metadata_bytes_without_summary': size(full),
          'added_bytes': with_summary - size(full),
          'source_sha256': {p: hashlib.sha256((root/p).read_bytes()).hexdigest() for p in [
              'research/live_control/agent_review.py',
              'research/live_control/test_agent_review.py']},
          'checks': 'PASS_SCOPED', 'model_accuracy_speed_tokens': 'unmeasured'}
target = root/'runtime/results/native-outcome-summary-01'
target.mkdir(parents=True, exist_ok=True)
(target/'result.json').write_text(json.dumps(result, indent=2)+'\n')
print(json.dumps(result, indent=2))
