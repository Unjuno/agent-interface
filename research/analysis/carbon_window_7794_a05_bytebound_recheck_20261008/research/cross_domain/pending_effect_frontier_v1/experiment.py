"""Frozen finite native-GUI calibration; each output directory is consumed once."""
import argparse
from contextlib import closing
import hashlib
import json
import os
from pathlib import Path
import platform
import sqlite3
import subprocess
import sys
import time
from Xlib import X, XK, display
from Xlib.ext import xtest
from frontier import Effects, Frontier, matching_commit
from private_desktop import desktop

HERE = Path(__file__).resolve().parent
ORDER = ('A', 'D', 'B', 'C')
KEYS = dict(zip(ORDER, ('F1', 'F2', 'F3', 'F4')))


def write(path, data):
    Path(path).write_text(json.dumps(data, indent=2, sort_keys=True) + '\n')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def environment():
    cpu = next((s.split(':', 1)[1].strip() for s in Path('/proc/cpuinfo').read_text().splitlines()
                if s.startswith('model name')), 'unknown')
    return dict(python=platform.python_version(), kernel=platform.release(), cpu=cpu,
                cpu_affinity=sorted(os.sched_getaffinity(0)), cpu_clock='not pinned / not calibrated',
                sqlite=sqlite3.sqlite_version, clock=vars(time.get_clock_info('perf_counter')),
                input='private Xvfb/Openbox/Tk/XTEST; not Agent Interface InputOwner',
                feedback='trusted public application receipts; no screenshot grounding',
                model_calls=0, doom_episodes=0, concurrency='one controller + one GUI process; serial trials')


def snapshot(conn):
    start = time.perf_counter_ns()
    bitmap = conn.query_keymap(); pointer = conn.screen().root.query_pointer()
    focus = conn.get_input_focus().focus
    return dict(start_ns=start, sample_ns=time.perf_counter_ns(), keys=[n for n in range(256) if bitmap[n//8] & (1 << (n % 8))],
                buttons=[b for b in (1, 2, 3) if pointer.mask & (X.Button1Mask << (b-1))],
                focus=getattr(focus, 'id', focus), end_ns=time.perf_counter_ns())


def press(name, conn, observer, wid, hold_ms):
    pre = snapshot(observer)
    if pre['keys'] or pre['buttons'] or pre['focus'] != wid:
        raise RuntimeError('fresh focus/empty-input gate failed')
    code = conn.keysym_to_keycode(XK.string_to_keysym(name))
    start = time.perf_counter_ns()
    try:
        xtest.fake_input(conn, X.KeyPress, code); conn.sync()
        ack = time.perf_counter_ns(); held = snapshot(observer)
        if code not in held['keys']:
            raise RuntimeError('independent key-down verification failed')
        time.sleep(hold_ms / 1000)
    finally:
        up_start = time.perf_counter_ns()
        xtest.fake_input(conn, X.KeyRelease, code); conn.sync()
        up_end = time.perf_counter_ns()
    released = snapshot(observer)
    if released['keys'] or released['buttons']:
        raise RuntimeError('independent release verification failed')
    return dict(key=name, code=code, start_ns=start, ack_ns=ack, up_start_ns=up_start, up_end_ns=up_end,
                pre=pre, held=held, released=released)


def score(root):
    with closing(sqlite3.connect('file:' + str((root/'private.sqlite').resolve()) + '?mode=ro', uri=True)) as db:
        rows = db.execute('SELECT rowid,operation,value,read_version,applied_ns FROM effects ORDER BY rowid').fetchall()
        docs = db.execute('SELECT * FROM documents ORDER BY name').fetchall()
        integrity = db.execute('PRAGMA integrity_check').fetchone()[0]
    return dict(effects=rows, documents=docs, integrity=integrity)


def run_case(root, spec, plan, env, conn, observer):
    root.mkdir()
    epoch = f'{plan["allocation_id"]}:{spec["index"]}'
    token = f'matched-{spec["scenario"]}-{spec["repetition"]}'
    # The application is never told which policy controls its inputs.
    write(root/'config.json', dict(epoch=epoch, token=token, scenario=spec['scenario']))
    log = (root/'fixture.log').open('w')
    proc = subprocess.Popen([sys.executable, str(HERE/'fixture.py'), str(root)], env=env, stdout=log, stderr=subprocess.STDOUT)
    trace = []; issued = {}; resolved = {}; seen = set(); query_count = 0
    try:
        deadline = time.monotonic() + 5
        while not (root/'ready.json').exists():
            if proc.poll() is not None or time.monotonic() > deadline:
                raise RuntimeError('fixture readiness failure')
            time.sleep(.005)
        ready = json.loads((root/'ready.json').read_text()); wid = ready['window_id']
        conn.create_resource_object('window', wid).set_input_focus(X.RevertToParent, X.CurrentTime); conn.sync(); time.sleep(.02)
        effects = {k: Effects(None if v['reads'] is None else frozenset(v['reads']),
                              None if v['writes'] is None else frozenset(v['writes'])) for k, v in ready['effects'].items()}
        frontier = Frontier(epoch, ready['catalogue_version'], ready['aliases'])
        start = time.perf_counter_ns(); stop = start + plan['window_ms'] * 1_000_000
        next_query = start + plan['lookup_after_ms'] * 1_000_000
        while time.perf_counter_ns() < stop:
            read_start = time.perf_counter_ns(); batch = []
            for path in sorted((root/'public').glob('*.json')):
                if path.name not in seen:
                    batch.append((path.name, json.loads(path.read_text()))); seen.add(path.name)
            observed = time.perf_counter_ns(); decisions = []
            for name, row in batch:
                op = row.get('operation')
                ok = op in issued and matching_commit(row, epoch=epoch, operation=op,
                    payload_hash=ready['effects'][op]['payload_sha256'], issued_ns=issued[op], observed_ns=observed)
                if ok:
                    resolved.setdefault(op, observed)
                decisions.append(dict(file=name, accepted=ok))
            if batch:
                trace.append(dict(event='feedback', start_ns=read_start, end_ns=observed, decisions=decisions))
            pending = {k: effects[k] for k in issued if k not in resolved}
            if len(resolved) == 4:
                break
            chosen = None; reasons = {}
            for op in ORDER:
                if op in issued:
                    continue
                policy = spec['policy']
                if policy == 'global_wait':
                    ok = not pending; reason = 'GLOBAL_WAIT' if pending else 'NO_PENDING_EFFECT'
                elif policy == 'release_only':
                    ok = True; reason = 'RELEASE_ONLY'
                else:
                    advice = frontier.advise(effects[op], pending, epoch=epoch, catalogue_version=ready['catalogue_version'],
                                             physical_empty=True, raw_names=policy == 'name_frontier')
                    ok, reason = advice['eligible'], advice['reason']
                reasons[op] = reason
                if ok:
                    chosen = op; break
            if chosen:
                trace.append(dict(event='selection', ns=time.perf_counter_ns(), operation=chosen,
                                  pending=sorted(pending), reasons=reasons, grants_input_authority=False))
                row = press(KEYS[chosen], conn, observer, wid, plan['hold_ms'])
                issued[chosen] = row['start_ns']
                trace.append(dict(event='input', operation=chosen, receipt=row))
            elif (spec['policy'] == 'frontier_lookup' and 'A' in pending and
                  query_count < plan['max_lookups'] and time.perf_counter_ns() >= next_query):
                row = press('F5', conn, observer, wid, plan['hold_ms'])
                trace.append(dict(event='lookup_input', operation='A', receipt=row))
                query_count += 1; next_query = row['start_ns'] + plan['lookup_every_ms'] * 1_000_000
            else:
                time.sleep(plan['poll_ms'] / 1000)
            if proc.poll() is not None:
                raise RuntimeError('fixture died during policy loop')
        end = time.perf_counter_ns()
        final_input = snapshot(observer)
        if final_input['keys'] or final_input['buttons']:
            raise RuntimeError('final input not empty')
        result = dict(spec=spec, start_ns=start, end_ns=end, issued=issued, resolved=resolved,
                      lookups=query_count, final_input=final_input, visible_complete=len(resolved)==4)
    except BaseException as exc:
        write(root/'failure.json', dict(type=type(exc).__name__, error=str(exc)))
        raise
    finally:
        (root/'stop').touch()
        try:
            proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            proc.terminate(); proc.wait(timeout=2)
        log.close()
        write(root/'trace.json', trace)
    if proc.returncode != 0:
        raise RuntimeError(f'fixture exit status {proc.returncode}')
    # No policy callback runs beyond here. This is independent evaluator state.
    result['score'] = score(root)
    write(root/'result.json', result)
    return result


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--plan', type=Path, required=True)
    ap.add_argument('--block', type=int, required=True); ap.add_argument('--out', type=Path, required=True)
    args = ap.parse_args(); plan = json.loads(args.plan.read_text())
    for name, h in plan['source_sha256'].items():
        if sha(HERE/name) != h:
            raise RuntimeError('frozen source mismatch: ' + name)
    selected = [s for s in plan['schedule'] if s['block'] == args.block]
    if not selected:
        raise ValueError('empty or unknown block')
    args.out.mkdir(parents=True, exist_ok=False)
    write(args.out/'plan.json', plan); write(args.out/'environment.json', environment())
    results = []
    try:
        with desktop(args.out) as env:
            with closing(display.Display(env['DISPLAY'])) as conn, closing(display.Display(env['DISPLAY'])) as observer:
                for spec in selected:
                    root = args.out/f'case-{spec["index"]:03d}'
                    result = run_case(root, spec, plan, env, conn, observer)
                    from audit import audit_case
                    audit = audit_case(root)
                    write(root/'audit.json', audit)
                    results.append(audit)
                    print(json.dumps(dict(index=spec['index'], policy=spec['policy'], scenario=spec['scenario'], audit=audit)), flush=True)
                    if not audit['pass']:
                        raise RuntimeError('first unexpected audit failure; allocation stopped')
        write(args.out/'block-result.json', dict(pass_all=True, cases=results))
    except BaseException as exc:
        write(args.out/'block-failure.json', dict(error=repr(exc), completed=len(results)))
        raise


if __name__ == '__main__':
    main()
