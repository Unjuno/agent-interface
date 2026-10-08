"""Run one inert queue trace against frozen V39 and PR helper source."""
import ast
import hashlib
import json
import pathlib
import queue
import time

ROOT = pathlib.Path('/input')
OUT = pathlib.Path('/output')
MAIN = ROOT / 'main.py'
PR = ROOT / 'pr.py'
EXPECTED_MAIN_BLOB = 'cdf61eec2c030d7456b34a58907e9c43d5d72084'
EXPECTED_PR_BLOB = 'dd1f7ab589f25108e2ea1c7518cdd4444791a6d0'


class Clock:
    def __init__(self):
        self.value = 0.0

    def monotonic(self):
        self.value += .01
        return self.value


class Feed:
    def __init__(self, rows):
        self.rows = list(rows)

    def get(self, timeout):
        if not self.rows:
            raise queue.Empty()
        return self.rows.pop(0)


class Process:
    def poll(self):
        return None


class Monitor:
    event_types = frozenset({'observation'})

    def __init__(self):
        self.seen = []

    def observe(self, row):
        self.seen.append(row['sequence'])
        return {'reason': 'health_below_floor', 'sequence': row['sequence']}


def source_sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_blob_sha(path):
    data = path.read_bytes()
    return hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()


def extract_wait(path, feed):
    tree = ast.parse(path.read_bytes())
    main = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'main')
    fn = next(n for n in ast.walk(main) if isinstance(n, ast.FunctionDef) and n.name == 'wait')
    factory = ast.parse('def factory(process, incoming):\n latest = None\n').body[0]
    factory.body.append(fn)
    factory.body += ast.parse('return wait, lambda: latest').body
    module = ast.fix_missing_locations(ast.Module(body=[factory], type_ignores=[]))
    scope = {'queue': queue, 'time': Clock()}
    exec(compile(module, str(path), 'exec'), scope)
    return scope['factory'](Process(), feed)


def extract_helper(path):
    tree = ast.parse(path.read_bytes())
    fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef)
              and n.name == 'wait_for_cover_acceptance')
    module = ast.fix_missing_locations(ast.Module(body=[fn], type_ignores=[]))
    scope = {}
    exec(compile(module, str(path), 'exec'), scope)
    return scope['wait_for_cover_acceptance']


def check_source_contract():
    tree = ast.parse(MAIN.read_bytes())
    main = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'main')
    submit = next(n for n in ast.walk(main) if isinstance(n, ast.FunctionDef)
                  and n.name == 'submit_cover')
    wait_calls = [n for n in ast.walk(submit) if isinstance(n, ast.Call)
                  and isinstance(n.func, ast.Name) and n.func.id == 'wait']
    if len(wait_calls) != 1 or any(k.arg == 'observation_monitor'
                                    for k in wait_calls[0].keywords):
        raise AssertionError('main submit_cover source contract changed')
    pr_tree = ast.parse(PR.read_bytes())
    helper = next(n for n in pr_tree.body if isinstance(n, ast.FunctionDef)
                  and n.name == 'wait_for_cover_acceptance')
    calls = [n for n in ast.walk(helper) if isinstance(n, ast.Call)
             and isinstance(n.func, ast.Name) and n.func.id == 'wait']
    if len(calls) != 1 or not any(k.arg == 'observation_monitor' for k in calls[0].keywords):
        raise AssertionError('PR helper does not pass the observation monitor')


def run_case(use_pr_helper):
    obs = {'event': 'observation', 'sequence': 17, 'health': 70}
    accepted = {'event': 'accepted', 'id': 'cover-0', 'accepted_ns': 123}
    feed = Feed([obs, accepted])
    wait, latest = extract_wait(MAIN, feed)
    monitor = Monitor()
    if use_pr_helper:
        result = extract_helper(PR)(wait, 'cover-0', monitor)
    else:
        result = wait(lambda row: row['event'] in ('accepted', 'rejected') and
                      (row.get('id') == 'cover-0' or row['event'] == 'rejected'))
    return {
        'result': result,
        'monitor_seen_sequences': monitor.seen,
        'latest_sequence': None if latest() is None else latest().get('sequence'),
        'queued_events': feed.rows,
    }


def main():
    if (OUT / 'raw.json').exists():
        raise SystemExit('refusing to overwrite retained raw.json; use a fresh output directory')
    if git_blob_sha(MAIN) != EXPECTED_MAIN_BLOB or git_blob_sha(PR) != EXPECTED_PR_BLOB:
        raise SystemExit('source blob does not match the frozen current-main/PR inputs')
    check_source_contract()
    raw = {
        'schema': 'v39-cover-admission-main-replay-raw-v1',
        'main_source_sha256': source_sha(MAIN),
        'main_git_blob_sha1': git_blob_sha(MAIN),
        'pr_source_sha256': source_sha(PR),
        'pr_git_blob_sha1': git_blob_sha(PR),
        'main_wait': run_case(False),
        'pr_helper_with_main_wait': run_case(True),
        'live_game': False,
        'real_x_server': False,
        'gui': False,
        'model_calls': 0,
        'os_input': False,
    }
    OUT.mkdir(exist_ok=True)
    (OUT / 'raw.json').write_text(json.dumps(raw, indent=2, sort_keys=True) + '\n')
    print(json.dumps(raw, sort_keys=True))


if __name__ == '__main__':
    main()
