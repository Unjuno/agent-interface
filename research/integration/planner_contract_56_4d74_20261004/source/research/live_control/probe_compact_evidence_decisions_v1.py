"""Predeclared fixed-image full/compact decision comparison; executes no actions."""
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path
from calc_proposal_schema_v1 import parse as parse_calc
from form_proposal_schema_v1 import parse as parse_form
from planner_evidence_v1 import present

H = Path(__file__).resolve().parent
R = H / 'results/compact-evidence-decisions-01'
R.mkdir(exist_ok=False)
read = lambda p: json.loads(p.read_text(encoding='utf-8'))
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()

form_root = H / 'results/checkpoint-recovery-form-01'
calc_root = H / 'results/checkpoint-decision-calc-01'
form_turn = read(form_root / 'turns.json')[0]
form_losses = read(form_root / 'losses.json')
calc_turns = read(calc_root / 'turns.json')

cases = []


def add(name, domain, image, prefix, full, compact, order, expected):
    cases.append({'name': name, 'domain': domain, 'image': image, 'prefix': prefix,
                  'A': full, 'B': compact, 'order': order, 'expected': expected})


form_prefix = (form_root / 'prompt-1.txt').read_text(encoding='utf-8').split('Evidence: ')[0]
form_unknown_full = form_turn['feedback']
form_unknown_compact = present(form_losses[0]['recovered']['state']['last_resolution'], recovered=True)
add('form_unknown', 'form', form_root / 'runtime' / Path(form_turn['source']['image']).name,
    form_prefix, form_unknown_full, form_unknown_compact, ['A', 'B', 'B', 'A'], 'act_exact_value_once')
form_verified_resolution = form_losses[1]['recovered']['state']['last_resolution']
form_verified_full = {'checkpoint_resolution': form_verified_resolution,
                      'query_recovery': 'one command-free read; no query resend'}
form_verified_compact = present(form_verified_resolution, recovered=True)
add('form_verified', 'form', form_root / 'runtime' / '014.png', form_prefix,
    form_verified_full, form_verified_compact, ['B', 'A', 'A', 'B'], 'verify_visible_saved')

calc_prefix = (calc_root / 'prompt-2.txt').read_text(encoding='utf-8').split('Evidence: ')[0]
calc_unknown_full = calc_turns[1]['feedback']
calc_unknown_compact = present(calc_turns[1]['feedback']['checkpoint_resolution'],
                               phase_report=calc_turns[0]['phases'],
                               prior_steps=calc_turns[0]['proposal']['steps'])
add('calc_unknown_dialog', 'calc', calc_root / 'runtime' / Path(calc_turns[1]['source']['image']).name,
    calc_prefix, calc_unknown_full, calc_unknown_compact, ['B', 'A', 'A', 'B'], 'click_dialog_without_save')
calc_verified_resolution = calc_turns[1]['checkpoint']['state']['last_resolution']
calc_verified_full = {'checkpoint_resolution': calc_verified_resolution}
calc_verified_compact = present(calc_verified_resolution)
add('calc_verified', 'calc', calc_root / 'runtime' / '016.png', calc_prefix,
    calc_verified_full, calc_verified_compact, ['A', 'B', 'B', 'A'], 'verify_visible_saved')

sources = [Path(__file__), H / 'planner_evidence_v1.py', H / 'checkpoint_contract_v1.py',
           H / 'calc_proposal_schema_v1.py', H / 'form_proposal_schema_v1.py',
           H / 'model_context_runner_v1.py', H / 'screenshot_responder_v1.txt',
           form_root / 'turns.json', form_root / 'losses.json', calc_root / 'turns.json']
plan = {'scope': '16 predeclared fixed-image calls; A full retained caller evidence, B compact typed view; no actions execute',
        'conditions': {'A': 'full', 'B': 'compact'},
        'primary': 'expected next-decision class and actual model input tokens',
        'secondary': 'save/resubmit proposals and runner duration, interpreted descriptively',
        'model': 'gpt-5.6-luna', 'effort': 'low', 'instruction_mode': 'responder',
        'limits': 'two calls per mode/case; served identity and cost unavailable; no live task-speed claim',
        'cases': [{k: v for k, v in case.items() if k not in ('prefix', 'A', 'B', 'image')} |
                  {'image': str(case['image']), 'image_sha256': sha(case['image']),
                   'full_bytes': len(json.dumps(case['A'], separators=(',', ':')).encode()),
                   'compact_bytes': len(json.dumps(case['B'], separators=(',', ':')).encode())} for case in cases],
        'sources': {str(path.relative_to(H)): sha(path) for path in sources}}
(R / 'plan.json').write_text(json.dumps(plan, indent=2) + '\n', encoding='utf-8')
runs = []
for case in cases:
    directory = R / case['name']
    directory.mkdir()
    metadata = {'image': str(case['image']), 'image_sha256': sha(case['image']),
                'prefix_sha256': hashlib.sha256(case['prefix'].encode()).hexdigest(),
                'expected': case['expected'], 'order': case['order']}
    (directory / 'case.json').write_text(json.dumps(metadata, indent=2) + '\n', encoding='utf-8')
    for mode in ('A', 'B'):
        evidence = case[mode]
        (directory / f'evidence-{mode}.json').write_text(json.dumps(evidence, indent=2) + '\n', encoding='utf-8')
        replay = ('Recorded fixed-image decision replay. No proposed action will execute. '
                  'Treat the depicted state and supplied evidence as current. A VERIFIED saved checkpoint '
                  'may request the schema\'s verify result; UNKNOWN cannot.\n')
        (directory / f'prompt-{mode}.txt').write_text(replay + case['prefix'] + 'Evidence: ' + json.dumps(evidence), encoding='utf-8')
    for index, mode in enumerate(case['order'], 1):
        out = directory / f'model-{index}-{mode}'
        print(json.dumps({'started': case['name'], 'index': index, 'mode': mode}), flush=True)
        begun = time.perf_counter_ns()
        process = subprocess.run([sys.executable, str(H / 'model_context_runner_v1.py'),
                                  r'C:\Program Files\nodejs\node.exe',
                                  str(Path.home() / 'AppData/Roaming/npm/node_modules/@openai/codex/bin/codex.js'),
                                  str(case['image']), str(directory / f'prompt-{mode}.txt'),
                                  str(H.parent.parent), str(out), 'responder'], capture_output=True, timeout=90)
        (directory / f'runner-{index}-stdout.txt').write_bytes(process.stdout)
        (directory / f'runner-{index}-stderr.txt').write_bytes(process.stderr)
        record = {'case': case['name'], 'domain': case['domain'], 'index': index, 'mode': mode,
                  'begin_ns': begun, 'end_ns': time.perf_counter_ns(), 'exit_code': process.returncode}
        if process.returncode == 0:
            try:
                events = [json.loads(line) for line in (out / 'events.jsonl').read_text(encoding='utf-8').splitlines()]
                items = [event['item'] for event in events if event['type'] == 'item.completed']
                assert len(items) == 1 and items[0]['type'] == 'agent_message'
                proposal = (parse_form(items[0]['text'], 't000240') if case['domain'] == 'form'
                            else parse_calc(items[0]['text']))
                record['proposal'] = proposal
                record['usage'] = events[-1]['usage']
                steps = proposal.get('steps', [])
                record['save_proposals'] = sum(step == {'op': 'chord', 'modifier': 'Control_L', 'key': 's'} for step in steps)
                record['return_proposals'] = sum(step == {'op': 'key', 'key': 'Return'} for step in steps)
                if case['expected'] == 'act_exact_value_once':
                    record['expected_decision'] = (proposal['kind'] == 'act' and
                        sum(step == {'op': 'text', 'text': 't000240'} for step in steps) == 1 and
                        record['return_proposals'] == 1)
                elif case['expected'] == 'click_dialog_without_save':
                    record['expected_decision'] = (proposal['kind'] == 'act' and len(steps) == 1 and
                                                   steps[0]['op'] == 'pointer_click' and record['save_proposals'] == 0)
                elif case['domain'] == 'form':
                    record['expected_decision'] = proposal['kind'] == 'verify' and proposal['submission_received_visible'] is True
                else:
                    record['expected_decision'] = (proposal['kind'] == 'verify' and
                        [proposal['visible_A1'], proposal['visible_A2'], proposal['confirmation_dialog_visible']] == [480, 192, False])
            except Exception as exc:
                record['parse_error'] = {'type': type(exc).__name__, 'detail': str(exc)}
        runs.append(record)
        (R / 'runs.json').write_text(json.dumps(runs, indent=2) + '\n', encoding='utf-8')
        print(json.dumps({'finished': case['name'], 'index': index, 'mode': mode,
                          'kind': record.get('proposal', {}).get('kind'),
                          'expected': record.get('expected_decision'), 'error': record.get('parse_error')}), flush=True)
(R / 'result.json').write_text(json.dumps({'calls': len(runs), 'actions_executed': 0,
    'all_predeclared_calls_retained': True}, indent=2) + '\n', encoding='utf-8')
