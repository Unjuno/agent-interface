"""Twelve fresh private servers; parent evidence and planted faults are explicit."""
import hashlib, json, os, select, signal, subprocess, sys, time, uuid
from pathlib import Path
from Xlib import X, display
from policy import classify

ROOT = Path(__file__).resolve().parent
PLAN = json.loads((ROOT / 'PLAN.json').read_text())
now = time.monotonic_ns

def wait_until(t):
    time.sleep(max(0, (t - now()) / 1e9))

def read_line(pipe, timeout=5):
    assert select.select([pipe], [], [], timeout)[0], 'pipe enrollment timeout'
    line = pipe.readline()
    assert line, 'unexpected EOF'
    return line

def cell(mode, repeat, out):
    row = {'mode': mode, 'repeat': repeat, 'authority': False, 'input_emissions': 0, 'messages': [], 'events': [], 'cleanup': {}}
    server = worker = d = window = None
    grabbed = False
    err = (out / f'{mode}-{repeat}.stderr').open('xb')
    try:
        server = subprocess.Popen(['Xvfb', '-displayfd', '1', '-screen', '0', '160x100x24', '-nolisten', 'tcp', '-noreset'], stdout=subprocess.PIPE, stderr=err)
        name = ':' + read_line(server.stdout).decode().strip()
        d = display.Display(name)
        window = d.screen().root.create_window(0, 0, 80, 60, 0, d.screen().root_depth, X.InputOutput, X.CopyFromParent, override_redirect=True)
        window.map(); d.sync()
        window.set_input_focus(X.RevertToParent, X.CurrentTime); d.sync()
        row['expected_focus'] = window.id
        row['fixture_focus'] = d.get_input_focus().focus.id
        nonce = str(uuid.uuid4())
        worker = subprocess.Popen([sys.executable, '-B', str(ROOT / 'worker.py'), name, nonce, mode], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=err, bufsize=0)
        ready = json.loads(read_line(worker.stdout))
        row['ready'] = ready
        row['parent_observed_pid'] = worker.pid
        row['parent_start_ticks'] = int(Path(f'/proc/{worker.pid}/stat').read_text().rsplit(')', 1)[1].split()[19])
        assert ready['kind'] == 'READY' and ready['pid'] == worker.pid and ready['nonce'] == nonce
        if mode.endswith('server_blocked'):
            d.grab_server(); d.sync(); grabbed = True
            row['grab_confirmed_ns'] = now()
        row['go_ns'] = now()
        worker.stdin.write(b'GO\n'); worker.stdin.flush()
        budget = row['go_ns'] + PLAN['budget_ns']
        started = json.loads(read_line(worker.stdout))
        row['messages'].append(started)
        row['query_start_received_ns'] = now()
        if mode == 'killed_server_blocked':
            wait_until(row['go_ns'] + PLAN['kill_ns'])
            row['kill_ns'] = now(); worker.send_signal(signal.SIGKILL)
        wait_until(budget)
        row['budget_observed_ns'] = now()
        row['terminal_at_budget'] = worker.poll()
        row['result_available_at_budget'] = False
        if select.select([worker.stdout], [], [], 0)[0]:
            line = worker.stdout.readline()
            row['pipe_eof_at_budget'] = not bool(line)
            if line:
                row['messages'].append(json.loads(line)); row['result_available_at_budget'] = True
        else:
            row['pipe_eof_at_budget'] = False
        if grabbed:
            wait_until(row['go_ns'] + PLAN['release_ns'])
            row['ungrab_ns'] = now(); d.ungrab_server(); d.sync(); grabbed = False
        if mode != 'killed_server_blocked' and not row['result_available_at_budget']:
            row['messages'].append(json.loads(read_line(worker.stdout)))
        row['response_received_ns'] = now()
        row['worker_exit'] = worker.wait(timeout=3)
        row['waitpid_observed_ns'] = now()
        result = next((m for m in row['messages'] if m['kind'] == 'RESULT'), None)
        valid = None if result is None else (result['pid'] == ready['pid'] and result['start_ticks'] == ready['start_ticks'] and result['nonce'] == ready['nonce'] and result['focus'] == row['expected_focus'] and result['native_focus'] == row['expected_focus'])
        row['response_valid'] = valid
        at_budget_valid = valid if row['result_available_at_budget'] else None
        row['at_budget'] = classify(not row['result_available_at_budget'], row['terminal_at_budget'] == -9, at_budget_valid)
        row['final'] = classify(False, row['worker_exit'] == -9, valid, row['at_budget'])
        row['baseline_at_budget'] = 'FAILED' if not row['result_available_at_budget'] else row['at_budget']
        row['oracle_focus_after'] = d.get_input_focus().focus.id
    except Exception as exc:
        row['error'] = repr(exc)
    finally:
        if grabbed and d is not None:
            d.ungrab_server(); d.sync()
        if worker is not None:
            if worker.poll() is None: worker.kill()
            row['cleanup']['worker_exit'] = worker.wait(timeout=3)
        if d is not None:
            row['cleanup']['keymap_empty'] = not any(d.query_keymap())
            row['cleanup']['observed_buttons_1_to_3_neutral'] = not bool(d.screen().root.query_pointer().mask & (X.Button1Mask | X.Button2Mask | X.Button3Mask))
            if window is not None: window.destroy(); d.sync()
            d.close(); row['cleanup']['controller_closed'] = True
        if server is not None:
            server.terminate(); row['cleanup']['server_exit'] = server.wait(timeout=3)
        err.close()
    return row

def main():
    out = Path(sys.argv[1]); preflight = '--preflight' in sys.argv
    env = {'python': sys.version, 'cgroups': {p: Path('/sys/fs/cgroup', p).read_text().strip() for p in ('cpu.max', 'memory.max', 'memory.swap.max', 'pids.max')}, 'preflight_excluded': preflight}
    (out / 'ENV.json').write_text(json.dumps(env, indent=2) + '\n')
    with (out / 'raw.jsonl').open('x') as f:
        for repeat in range(1 if preflight else PLAN['repeats']):
            for mode in (['healthy_fast', 'healthy_server_blocked'] if preflight else PLAN['modes']):
                row = cell(mode, repeat, out)
                f.write(json.dumps(row, sort_keys=True) + '\n'); f.flush(); os.fsync(f.fileno())
                print(json.dumps({'mode': mode, 'repeat': repeat, 'error': row.get('error'), 'at_budget': row.get('at_budget'), 'final': row.get('final')}), flush=True)
                if 'error' in row: raise RuntimeError(row['error'])

if __name__ == '__main__': main()
