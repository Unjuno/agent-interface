"""Explicit CLI screenshot probe; local event arrivals are not model timestamps."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time


def main():
    node, cli, image, prompt_file, working, output = sys.argv[1:]
    root = Path(output).resolve()
    root.mkdir(parents=True, exist_ok=False)
    prompt = Path(prompt_file).read_text(encoding='utf-8')
    (root / 'prompt.txt').write_text(prompt, encoding='utf-8')
    args = [node, cli, 'exec', '--ignore-user-config', '--ephemeral',
            '--sandbox', 'read-only', '--skip-git-repo-check', '--json',
            '--model', 'gpt-5.6-luna', '-c', 'model_reasoning_effort="low"',
            '--disable', 'plugins', '--disable', 'remote_plugin',
            '--disable', 'shell_snapshot', '--disable', 'shell_tool',
            '-C', str(Path(working).resolve()), '-i', str(Path(image).resolve()), '-']
    plan = dict(args=args, requested_model='gpt-5.6-luna', requested_effort='low',
                image_sha256=hashlib.sha256(Path(image).read_bytes()).hexdigest(),
                runner_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                clock='perf_counter_ns in runner process; local arrival only',
                comparison='same requested model and working directory; actual served identity and full context unverified')
    (root / 'plan.json').write_text(json.dumps(plan, indent=2)+'\n')
    started = time.perf_counter_ns()
    with (root / 'stderr.txt').open('wb') as errors, (root / 'events.jsonl').open('wb') as raw, \
            (root / 'arrivals.jsonl').open('w') as arrivals:
        process = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                   stderr=errors)
        process.stdin.write(prompt.encode('utf-8'))
        process.stdin.close()
        sent = time.perf_counter_ns()
        for index, line in enumerate(process.stdout):
            received = time.perf_counter_ns()
            raw.write(line)
            arrivals.write(json.dumps(dict(line=index, received_ns=received,
                            sha256=hashlib.sha256(line).hexdigest(), bytes=len(line)))+'\n')
            raw.flush()
            arrivals.flush()
        code = process.wait()
    result = dict(exit_code=code, started_ns=started, stdin_closed_ns=sent,
                  exited_ns=time.perf_counter_ns(), model_received_ns=None,
                  observed_model_identity=None, cost=None)
    (root / 'process.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result))
    return code


if __name__ == '__main__':
    raise SystemExit(main())
