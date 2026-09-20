"""Independent audit for the one direct host-image task allocation."""
import base64
import hashlib
import json
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

root = Path(sys.argv[1])
failures = []
def need(condition, label):
    if not condition:
        failures.append(label)
def read(name):
    return json.loads((root/name).read_text())

freeze = read('source-freeze.json')
source_sha = freeze.get('source_main_sha', freeze.get('main_sha'))
start = read('start.json')
start_content = start.get('content', [])
raw_start_image = [b for b in start_content if b.get('type') == 'image']
start_png = root/'start-image-1.png'
need(len(raw_start_image) == 1, 'one MCP start image block')
if raw_start_image:
    bytes_from_block = base64.b64decode(raw_start_image[0]['data'], validate=True)
    need(bytes_from_block == start_png.read_bytes(), 'unmodified MCP image bytes forwarded')
    need(hashlib.sha256(bytes_from_block).hexdigest() == read('start-boundary.json')['image_sha256'],
         'start image SHA-256 identity')
need(read('tools.json') == sorted(['native_observe','native_start','native_status','native_submit','native_resume']),
     'expected public tool inventory')
decisions = [read(f'decision-{stage}.json') for stage in (1, 2)
             if (root/f'decision-{stage}.json').exists()]
need(1 <= len(decisions) <= 2, 'one action decision, with at most one bounded refusal recovery')
for stage, decision in enumerate(decisions, 1):
    source = read(f'allocation/run/source-{stage}.json')
    need(decision.get('source_sequence') == source['sequence'],
         f'decision {stage} names exact reviewed source sequence')
need(bool(decisions) and decisions[-1].get('finish_after') is True,
     'actual action decision is terminally bounded')
if len(decisions) == 2:
    first = read('allocation/run/reply-1.json')
    refusal = first.get('target_refusal', {})
    need(first.get('status') == 'boundary' and refusal.get('input_dispatched') is False
         and refusal.get('action_attempted') is False,
         'only pre-dispatch typed refusal may precede the action')
need(read('client-result.json')['status'] == 'returned', 'client completed persistent session')
need(read('client-result.json')['same_request_resume_count'] <= 10, 'bounded same-request resumes')
final_stage = len(decisions)
submit = read(f'submit-{final_stage}.json')
submit_blocks = submit.get('content', [])
need(not submit.get('isError', False), 'MCP submit returned without transport error')
submit_meta = json.loads(next((b['text'] for b in submit_blocks if b.get('type') == 'text'), '{}'))
need(len([b for b in submit_blocks if b.get('type') == 'image']) == 1,
     'one MCP submit feedback image block')
reply = read(f'allocation/run/reply-{final_stage}.json')
need(reply.get('decision_sha256') == hashlib.sha256(
     (root/f'allocation/run/request-{final_stage}.json').read_bytes()).hexdigest(),
     'final decision and immutable request identity')
need(reply.get('evaluation', {}).get('success') is True, 'independent task oracle succeeded')
need(reply.get('cleanup', {}).get('status') == 'completed', 'harness cleanup completed')
actions = read('allocation/run/actions.json')
need(len(actions) == 1, 'exactly one native input action')
if actions:
    exec_row = actions[0].get('result', {}).get('execution', {})
    releases = exec_row.get('releases', [])
    need(bool(releases) and all(r.get('verified') is True and r.get('keys_down') == [] and
         r.get('buttons_down') == [] for r in releases), 'all releases verified empty')
goal = read('allocation/run/goal.json')['task']
svg = ET.parse(root/'allocation/run/shape.svg')
rects = [n for n in svg.iter() if n.tag.endswith('}rect')]
need(len(rects) == 1, 'exactly one scored rectangle')
if rects:
    rect = rects[0]
    x,y,w,h = [float(rect.get(k)) for k in ('x','y','width','height')]
    need(x > goal['x_greater_than'] and abs(y-goal['y']) < goal['geometry_tolerance_exclusive'] and
         abs(w-goal['width']) < goal['geometry_tolerance_exclusive'] and
         abs(h-goal['height']) < goal['geometry_tolerance_exclusive'] and
         rect.get('transform') == goal['transform'], 'saved SVG matches public task geometry')
terminal = read('status.json')
terminal_meta = json.loads(terminal['content'][0]['text'])
need(terminal_meta.get('allocation',{}).get('status') == 'terminal' and
     terminal_meta.get('allocation',{}).get('returncode') == 0, 'managed process exited zero')
audit = {'schema':'agent-interface/issue-3370-direct-host-image-single-task-audit-v1',
         'result':'PASS_DIRECT_HOST_IMAGE_SINGLE_TASK_SCOPED' if not failures else 'HOLD_OR_FAIL',
         'source_main_sha':source_sha,'failures':failures,
         'limits':['host presentation timestamp unavailable',
                   'model interpretation timestamp unavailable',
                   'no saved-file route comparison',
                   'no stale/delayed/no-image/disconnect control',
                   'no token/cost or latency benefit claim']}
(root/'audit.json').write_text(json.dumps(audit,indent=2,sort_keys=True)+'\n')
print(json.dumps(audit,sort_keys=True))
raise SystemExit(0 if not failures else 1)
