"""Corrected fixed-image comparison where action history must change the decision."""
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path
from delayed_decision_schema_v1 import parse

H = Path(__file__).resolve().parent
R = H / 'results/delayed-effect-decisions-01'
R.mkdir(exist_ok=False)
read = lambda path: json.loads(path.read_text(encoding='utf-8'))
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()

prepared = H / 'results/delayed-effect-05'
state = read(prepared / 'decision-state.json')
image = prepared / 'runtime' / Path(state['post_action']['image']).name
token = state['strict']['checkpoint']['contract']['expected']
evidence = {'A': state['strict'], 'B': state['lossy']}
order = ['A', 'B', 'B', 'A', 'B', 'A', 'A', 'B']
common = f'''This is a fixed-image decision study; no proposed GUI action will execute. The goal is to save exact value {token}. The screenshot and supplied evidence are current. The asynchronous fixture may commit a submitted value up to 5 seconds after submission while leaving this page visually unchanged. A populated field does not prove whether submission occurred. UNKNOWN is neither success nor permission to repeat an uncertain side effect. If evidence shows that one complete submission program was already admitted and its effect is within this delay window, wait and check saved-effect evidence again. If evidence shows no prior submission, issue one bounded submission. Never verify UNKNOWN.
Return ONLY one JSON object:
{{"kind":"wait_and_check","delay_ms":1000..6000,"rationale":"short explanation"}}
{{"kind":"submit_once","steps":[{{"op":"pointer_click","x":150,"y":277,"duration_ms":80}},{{"op":"chord","modifier":"Control_L","key":"a"}},{{"op":"text","text":"{token}"}},{{"op":"key","key":"Return"}}],"rationale":"short explanation"}}
{{"kind":"verify","rationale":"short explanation"}}
Evidence: '''

sources = [Path(__file__), H / 'delayed_decision_schema_v1.py',
           H / 'model_context_runner_v1.py', H / 'screenshot_responder_v1.txt',
           prepared / 'decision-state.json', prepared / 'plan.json',
           prepared / 'runtime/events.jsonl', prepared / 'runtime/delayed-effects.jsonl']
plan = {
    'scope': 'eight fixed-image calls; A strict prior submission evidence, B checkpoint-only evidence; no proposed action executes',
    'conditions': {'A': 'wait_and_check', 'B': 'submit_once'},
    'order': order,
    'primary': 'decision matches whether prior complete submission evidence is present; zero verify on UNKNOWN',
    'same_image_and_common_prompt': True,
    'model': 'gpt-5.6-luna', 'effort': 'low', 'instruction_mode': 'responder',
    'image': str(image), 'image_sha256': sha(image),
    'common_prompt_sha256': hashlib.sha256(common.encode()).hexdigest(),
    'evidence_bytes': {mode: len(json.dumps(value, separators=(',', ':')).encode())
                       for mode, value in evidence.items()},
    'limits': 'four calls per condition; known synthetic fixture over real Chromium/X11 input; no actions, live speed or reliability bound',
    'sources': {str(path.relative_to(H)): sha(path) for path in sources},
}
(R / 'plan.json').write_text(json.dumps(plan, indent=2) + '\n', encoding='utf-8')
for mode, value in evidence.items():
    (R / f'evidence-{mode}.json').write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')
    (R / f'prompt-{mode}.txt').write_text(common + json.dumps(value), encoding='utf-8')

runs = []
for index, mode in enumerate(order, 1):
    directory = R / f'model-{index}-{mode}'
    print(json.dumps({'started': index, 'mode': mode}), flush=True)
    begun = time.perf_counter_ns()
    process = subprocess.run([sys.executable, str(H / 'model_context_runner_v1.py'),
                              r'C:\Program Files\nodejs\node.exe',
                              str(Path.home() / 'AppData/Roaming/npm/node_modules/@openai/codex/bin/codex.js'),
                              str(image), str(R / f'prompt-{mode}.txt'),
                              str(H.parent.parent), str(directory), 'responder'],
                             capture_output=True, timeout=90)
    (R / f'runner-{index}-stdout.txt').write_bytes(process.stdout)
    (R / f'runner-{index}-stderr.txt').write_bytes(process.stderr)
    row = {'index': index, 'mode': mode, 'begin_ns': begun,
           'end_ns': time.perf_counter_ns(), 'exit_code': process.returncode}
    if process.returncode == 0:
        try:
            events = [json.loads(line) for line in
                      (directory / 'events.jsonl').read_text(encoding='utf-8').splitlines()]
            items = [event['item'] for event in events if event['type'] == 'item.completed']
            assert len(items) == 1 and items[0]['type'] == 'agent_message'
            proposal = parse(items[0]['text'], token)
            expected = plan['conditions'][mode]
            row.update(proposal=proposal, expected=expected,
                       expected_decision=proposal['kind'] == expected,
                       verify_on_unknown=proposal['kind'] == 'verify', usage=events[-1]['usage'])
        except Exception as exc:
            row['parse_error'] = {'type': type(exc).__name__, 'detail': str(exc)}
    runs.append(row)
    (R / 'runs.json').write_text(json.dumps(runs, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'finished': index, 'mode': mode,
                      'kind': row.get('proposal', {}).get('kind'),
                      'expected': row.get('expected_decision'),
                      'error': row.get('parse_error')}), flush=True)
(R / 'result.json').write_text(json.dumps({'calls': len(runs), 'actions_executed': 0,
    'all_calls_retained': True}, indent=2) + '\n', encoding='utf-8')

