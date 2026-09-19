from __future__ import annotations
import json, os, subprocess, time
from pathlib import Path

HOST_ROOT = Path(os.environ.get('FORMAL_REPO', '/tmp/formal-source'))
IPC = Path(os.environ.get('FORMAL_IPC', '/tmp/formal-ipc'))
CODEX = '/opt/homebrew/bin/codex'

def hp(value):
    if value is None: return None
    if value == '/repo': return str(HOST_ROOT)
    if value.startswith('/repo/'): return str(HOST_ROOT / value[6:])
    return value

def main():
    IPC.mkdir(parents=True, exist_ok=True)
    handled = set()
    while True:
        for path in sorted(IPC.glob('*.request.json')):
            if path.name in handled: continue
            handled.add(path.name)
            req = json.loads(path.read_text())
            instruction_path = hp(req.get('instructions'))
            schema_path = hp(req.get('schema'))
            contract = ''
            if instruction_path and Path(instruction_path).exists():
                contract += '\nSUPPLIED CONTRACT INSTRUCTIONS:\n' + Path(instruction_path).read_text()
            if schema_path and Path(schema_path).exists():
                contract += '\nSUPPLIED OUTPUT JSON SCHEMA:\n' + Path(schema_path).read_text()
            prompt = req['prompt'] + contract + '\nReturn only one JSON object valid under the supplied contract.\n'
            args = [CODEX, 'exec', '--ephemeral', '--skip-git-repo-check', '--sandbox', 'read-only', '--model', 'gpt-5.6-luna', '--json', '--cd', str(HOST_ROOT)]
            image = hp(req.get('image'))
            if image: args += ['--image', image]
            args += ['-']
            try:
                completed = subprocess.run(args, input=prompt, text=True, capture_output=True, timeout=600)
                if completed.returncode != 0:
                    raise RuntimeError(f'codex exec exit={completed.returncode}: {completed.stderr[-2000:]}')
                message = None
                usage = None
                for line in completed.stdout.splitlines():
                    try:
                        obj = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    if obj.get('type') == 'item.completed' and obj.get('item', {}).get('type') == 'agent_message':
                        message = obj['item'].get('text')
                    if obj.get('type') == 'turn.completed':
                        usage = obj.get('usage')
                if message is None:
                    raise RuntimeError('codex exec returned no JSON object')
                if not isinstance(usage, dict):
                    raise RuntimeError('codex exec returned no usage')
                events = [
                    {'type':'thread.started','thread_id':'exec-'+req['request_id']},
                    {'type':'item.completed','item':{'type':'agent_message','text':message}},
                    {'type':'turn.completed','thread_id':'exec-'+req['request_id'],
                     'usage':usage},
                ]
                (IPC/f"{req['request_id']}.response.jsonl").write_text('\n'.join(json.dumps(x) for x in events)+'\n')
            except Exception as exc:
                (IPC/f"{req['request_id']}.error.txt").write_text(str(exc)+'\n')
        time.sleep(.05)

if __name__ == '__main__': main()
