#!/usr/bin/env python3
"""Compose exact native ROI counting into the retained native-XGetImage watcher."""
import argparse, base64, ctypes, hashlib, importlib.util, importlib.machinery, importlib.util as iu
import json, os, platform, random, statistics, subprocess, sys, threading, time, traceback, zlib
from pathlib import Path

HERE = Path(__file__).resolve().parent
UPSTREAM = HERE.parent / 'quiet_watch_poll_period_v1' / 'run_quiet_watch_poll_period_v1.py'
UPSTREAM_SHA256 = 'd50233d9584876f119e78251728ccbf682a4b46b5485197ae60229970d9d520d'
ACQUIRE_C_SHA256 = '682742c79ee86f50e1052826bdb7754c80013a9f38c7cc400a26219dd7db7751'
PREDICATE_C_SHA256 = 'ff69a2281b1081be80cb0051517c4eb5ce1ea13092f3baf0934bb01630d7528c'
PUBLICATION_BASE = 'a08cbd02e284d2dc9bf000f9daa3b673a230b07e'
SEED = 27020260916
OFFSETS = (150, 152, 154, 156, 158)
TARGET_REPS = 3
NUISANCE_OFFSETS = (150, 152, 154, 156)
PERIOD_MS = 2


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_upstream():
    if digest(UPSTREAM) != UPSTREAM_SHA256:
        raise RuntimeError('upstream source mismatch')
    spec = importlib.util.spec_from_file_location('q231', UPSTREAM)
    old = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(old)
    return old


def load_acquire_lib():
    p = HERE / 'native_acquire.so'
    lib = ctypes.CDLL(str(p))
    lib.q_init.restype = ctypes.c_int
    lib.q_open.argtypes = [ctypes.c_char_p]
    lib.q_open.restype = ctypes.c_void_p
    lib.q_close.argtypes = [ctypes.c_void_p]
    lib.q_close.restype = None
    lib.q_read.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_size_t]
    lib.q_read.restype = ctypes.c_int
    if not lib.q_init():
        raise RuntimeError('XInitThreads failed')
    return lib


def load_predicate_module():
    candidates = sorted(HERE.glob('native_predicate*.so'))
    if len(candidates) != 1:
        raise RuntimeError(f'expected one native_predicate extension, found {len(candidates)}')
    spec = iu.spec_from_file_location('native_predicate', candidates[0])
    mod = iu.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod, candidates[0]


def schedule():
    pairs = [('target', o, r) for r in range(TARGET_REPS) for o in OFFSETS]
    pairs += [('nuisance', o, r) for r, o in enumerate(NUISANCE_OFFSETS)]
    rng = random.Random(SEED)
    rng.shuffle(pairs)
    seen = {'target': 0, 'nuisance': 0}
    out = []
    for kind, offset, rep in pairs:
        k = seen[kind]
        seen[kind] += 1
        arms = ('python_count', 'native_count') if k % 2 == 0 else ('native_count', 'python_count')
        pair_id = f'{kind}-o{offset}-r{rep}'
        for arm in arms:
            out.append({
                'case_id': f'{pair_id}-{arm}', 'pair_id': pair_id, 'kind': kind,
                'offset_ms': offset, 'period_ms': PERIOD_MS, 'count_backend': arm,
                'order': len(out),
            })
    return out


class Reader:
    def __init__(self, old, acquire_lib, predicate, display_name, arm):
        self.old = old
        self.acquire_lib = acquire_lib
        self.predicate = predicate
        self.arm = arm
        self.handle = acquire_lib.q_open(display_name.encode())
        if not self.handle:
            raise RuntimeError('native display unavailable')
        self.buf = ctypes.create_string_buffer(4096)
        self.samples = []

    def read_raw(self):
        status = self.acquire_lib.q_read(self.handle, self.buf, 4096)
        if status:
            raise RuntimeError(f'native capture/ABI failure: {status}')
        return self.buf.raw

    def __call__(self, dpy, root):
        del dpy, root
        cpu0 = time.thread_time_ns()
        s = time.perf_counter_ns()
        raw = self.read_raw()
        acquire_end = time.perf_counter_ns()
        cpu1 = time.thread_time_ns()
        count_start = time.perf_counter_ns()
        if self.arm == 'python_count':
            count = self.old.roi_match_count(raw)
        elif self.arm == 'native_count':
            count = self.predicate.count_target(raw)
        else:
            raise RuntimeError(f'unknown arm {self.arm}')
        count_end = time.perf_counter_ns()
        cpu2 = time.thread_time_ns()
        self.samples.append({
            'start_ns': s,
            'acquire_end_ns': acquire_end,
            'count_start_ns': count_start,
            'count_end_ns': count_end,
            'acquire_thread_cpu_ns': cpu1 - cpu0,
            'count_thread_cpu_ns': cpu2 - cpu1,
            'total_thread_cpu_ns': cpu2 - cpu0,
        })
        # Preserve the inherited run_case acquisition-end timestamp semantics.
        return s, acquire_end, raw, count

    def close(self):
        if self.handle:
            self.acquire_lib.q_close(self.handle)
            self.handle = None


def environment(predicate_binary: Path):
    import importlib.metadata, Xlib
    return {
        'platform': platform.platform(),
        'python': sys.version,
        'python_xlib': {
            'module': str(Xlib.__file__),
            'version': str(getattr(Xlib, '__version__', 'UNKNOWN')),
            'distributions': importlib.metadata.packages_distributions().get('Xlib', []),
        },
        'affinity': sorted(os.sched_getaffinity(0)),
        'cpu_frequency_pinned': False,
        'cpuinfo_first_block': Path('/proc/cpuinfo').read_text().split('\n\n')[0],
        'clock': {name: vars(time.get_clock_info(name)) for name in ('perf_counter', 'thread_time')},
        'compiler': subprocess.check_output(['gcc', '--version'], text=True).splitlines()[0],
        'packages': subprocess.check_output(['dpkg-query', '-W', 'libx11-6', 'xvfb', 'tk8.6'], text=True),
        'native_acquire_binary_sha256': digest(HERE / 'native_acquire.so'),
        'native_predicate_binary_sha256': digest(predicate_binary),
    }


def static_checks(old, acquire_lib, predicate, display_name):
    root = old.tk.Tk(); root.geometry('640x400+0+0')
    cv = old.tk.Canvas(root, width=640, height=400, highlightthickness=0)
    cv.pack(); root.update()
    reader = Reader(old, acquire_lib, predicate, display_name, 'native_count')
    rows = []
    try:
        for red_count in (0, 1, 511, 512, 513, 1023, 1024):
            colors = ['#dc3232' if i < red_count else '#db3232' for i in range(1024)]
            image = old.tk.PhotoImage(width=32, height=32)
            image.put(' '.join('{' + ' '.join(colors[i:i+32]) + '}' for i in range(0, 1024, 32)))
            cv.delete('all'); cv.create_image(48, 48, image=image, anchor='nw'); root.update()
            raw = reader.read_raw()
            py = old.roi_match_count(raw)
            native = predicate.count_target(raw)
            row = {
                'target_pixels': red_count,
                'python_count': py,
                'native_count': native,
                'threshold_python': py >= old.TARGET_THRESHOLD,
                'threshold_native': native >= old.TARGET_THRESHOLD,
                'raw_sha256': hashlib.sha256(raw).hexdigest(),
                'raw_b64': base64.b64encode(raw).decode('ascii'),
            }
            rows.append(row)
            if not (py == native == red_count and row['threshold_python'] == row['threshold_native']):
                raise RuntimeError('static predicate mismatch')
        acquire_guards = {
            'bad_capacity': acquire_lib.q_read(reader.handle, reader.buf, 4095) == -1,
            'null_handle': acquire_lib.q_read(None, reader.buf, 4096) == -1,
        }
        predicate_guards = {}
        for name, payload in [('short', b'\0' * 4092), ('long', b'\0' * 4100), ('wrong_type', bytearray(4096))]:
            try:
                predicate.count_target(payload)
                predicate_guards[name] = False
            except (ValueError, TypeError):
                predicate_guards[name] = True
        if not all(acquire_guards.values()) or not all(predicate_guards.values()):
            raise RuntimeError('guard failure')
    finally:
        reader.close(); root.destroy()
    return {'rows': rows, 'acquire_guards': acquire_guards, 'predicate_guards': predicate_guards}


def run_one(old, acquire_lib, predicate, display_name, case):
    reader = Reader(old, acquire_lib, predicate, display_name, case['count_backend'])
    original = old.acquire_roi
    exceptions = []
    old_hook = threading.excepthook
    threading.excepthook = lambda x: exceptions.append(str(x.exc_value))
    old.acquire_roi = reader
    try:
        result = old.run_case(case, display_name)
        result['observation_metrics'] = reader.samples[:-1]
        result['final_observation_metrics'] = reader.samples[-1]
        result['thread_errors'] = exceptions
        return result
    finally:
        old.acquire_roi = original
        threading.excepthook = old_hook
        # Emergency cleanup outside reported endpoints.
        d = old.display.Display(display_name)
        old.xtest.fake_input(d, old.X.KeyRelease, d.keysym_to_keycode(old.XK.string_to_keysym('Right')))
        d.sync(); d.close(); reader.close()


def check_integrity(r):
    if r['thread_errors']:
        raise RuntimeError(f"thread errors: {r['thread_errors']}")
    if r['owner'].get('error') or r['watcher'].get('error'):
        raise RuntimeError('owner/watcher error')
    if not r['owner'].get('verified_empty') or r['right_down_final']:
        raise RuntimeError('release verification failed')
    kinds = [e['kind'] for e in r['events']]
    if kinds != ['app_key_press', 'app_key_release']:
        raise RuntimeError(f'unexpected app events {kinds}')
    if r['final']['match_count'] != 0:
        raise RuntimeError('final ROI not clear')
    if len(r['observation_metrics']) != len(r['acquisitions']):
        raise RuntimeError('metric/acquisition length mismatch')
    for a, m in zip(r['acquisitions'], r['observation_metrics']):
        if a['start_ns'] != m['start_ns'] or a['end_ns'] != m['acquire_end_ns']:
            raise RuntimeError('acquisition metric timestamp mismatch')


def write_json(path, obj):
    path.write_text(json.dumps(obj, sort_keys=True, separators=(',', ':')) + '\n', encoding='utf-8')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--mode', choices=['preflight', 'formal'], required=True)
    ap.add_argument('--display', default=':96')
    ap.add_argument('--out', required=True)
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=False)
    old = load_upstream()
    acquire_lib = load_acquire_lib()
    predicate, predicate_binary = load_predicate_module()
    sources = {
        'run.py': digest(HERE / 'run.py'),
        'audit.py': digest(HERE / 'audit.py'),
        'native_acquire.c': digest(HERE / 'native_acquire.c'),
        'native_predicate.c': digest(HERE / 'native_predicate.c'),
        'upstream_runner': digest(UPSTREAM),
    }
    if sources['native_acquire.c'] != ACQUIRE_C_SHA256 or sources['native_predicate.c'] != PREDICATE_C_SHA256:
        raise RuntimeError('dependency source mismatch')
    payload = {
        'schema': 'quiet_watch_native_predicate_integration_v1',
        'mode': args.mode,
        'publication_base': PUBLICATION_BASE,
        'sources': sources,
        'environment': environment(predicate_binary),
        'records': [], 'errors': [],
    }
    if args.mode == 'formal':
        frozen = json.loads((HERE / 'prereg.json').read_text())
        if sources != frozen['sources']:
            raise RuntimeError('frozen source mismatch')
        if payload['environment']['native_acquire_binary_sha256'] != frozen['binaries']['native_acquire.so']:
            raise RuntimeError('native acquisition binary mismatch')
        if payload['environment']['native_predicate_binary_sha256'] != frozen['binaries']['native_predicate.so']:
            raise RuntimeError('native predicate binary mismatch')
        if hashlib.sha256(json.dumps(schedule(), sort_keys=True).encode()).hexdigest() != frozen['schedule_sha256']:
            raise RuntimeError('schedule mismatch')
        payload['prereg_sha256'] = digest(HERE / 'prereg.json')
        cases = schedule()
    else:
        cases = [
            {'case_id': 'preflight-target-python_count', 'pair_id': 'preflight-target', 'kind': 'target', 'offset_ms': 150, 'period_ms': 2, 'count_backend': 'python_count', 'order': 0},
            {'case_id': 'preflight-target-native_count', 'pair_id': 'preflight-target', 'kind': 'target', 'offset_ms': 150, 'period_ms': 2, 'count_backend': 'native_count', 'order': 1},
            {'case_id': 'preflight-nuisance-native_count', 'pair_id': 'preflight-nuisance', 'kind': 'nuisance', 'offset_ms': 150, 'period_ms': 2, 'count_backend': 'native_count', 'order': 2},
            {'case_id': 'preflight-nuisance-python_count', 'pair_id': 'preflight-nuisance', 'kind': 'nuisance', 'offset_ms': 150, 'period_ms': 2, 'count_backend': 'python_count', 'order': 3},
        ]
    try:
        if args.mode == 'preflight':
            payload['static'] = static_checks(old, acquire_lib, predicate, args.display)
        for case in cases:
            r = run_one(old, acquire_lib, predicate, args.display, case)
            payload['records'].append(r)
            write_json(out / 'raw.json', payload)
            check_integrity(r)
            print(case['case_id'], r['derived']['detected'], len(r['acquisitions']), flush=True)
    except BaseException:
        payload['errors'].append(traceback.format_exc())
        raise
    finally:
        write_json(out / 'raw.json', payload)
        (out / 'raw.json.zlib').write_bytes(zlib.compress((out / 'raw.json').read_bytes(), 9))


if __name__ == '__main__':
    main()
